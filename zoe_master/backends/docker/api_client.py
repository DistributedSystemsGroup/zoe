# Copyright (c) 2016, Daniele Venzano
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Interface to the low-level Docker API."""

import logging
from typing import List, Callable, Dict, Any

import docker
import docker.tls
import docker.errors
import docker.utils
import docker.models.containers

import requests.exceptions

from zoe_lib.config import get_conf
from zoe_lib.state import Service, VolumeDescriptionHostPath
from zoe_master.backends.service_instance import ServiceInstance
from zoe_master.backends.docker.config import DockerHostConfig  # pylint: disable=unused-import
from zoe_master.exceptions import ZoeException, ZoeNotEnoughResourcesException

log = logging.getLogger(__name__)

try:
    docker.DockerClient()
except AttributeError:
    log.error('Docker package does not have the DockerClient attribute')
    raise ImportError('Wrong Docker library version')


class DockerClient:
    """The client class that wraps the Docker API."""
    def __init__(self, docker_config: DockerHostConfig, mock_client=None) -> None:
        self.name = docker_config.name
        self.docker_config = docker_config
        if not docker_config.tls:
            tls = None
        else:
            tls = docker.tls.TLSConfig(client_cert=(docker_config.tls_cert, docker_config.tls_key), verify=docker_config.tls_ca)

        # Simplify testing
        if mock_client is not None:
            self.cli = mock_client
            return

        try:
            self.cli = docker.DockerClient(base_url=docker_config.address, version="auto", tls=tls)
        except docker.errors.DockerException as e:
            raise ZoeException("Cannot connect to Docker host {} at address {}: {}".format(docker_config.name, docker_config.address, str(e)))

    def info(self) -> Dict:
        """Retrieve engine statistics."""
        return self.cli.info()

    def spawn_container(self, service_instance: ServiceInstance) -> Dict[str, Any]:
        """Create and start a new container."""
        run_args = {
            'detach': True,
            'ports': {},
            'environment': {},
            'volumes': {},
            'working_dir': service_instance.work_dir,
            'mem_limit': 0,
            'mem_reservation': 0,
            'memswap_limit': 0,
            'name': service_instance.name,
            'network_disabled': False,
            'network_mode': get_conf().overlay_network_name,
            'image': service_instance.image_name,
            'command': service_instance.command,
            'hostname': service_instance.hostname,
            'labels': service_instance.labels,
            'cpu_period': 100000,
            'cpu_quota': 100000,
            'log_config': {
                "type": "json-file",
                "config": {}
            }
        }
        for port in service_instance.ports:
            run_args['ports'][str(port.number) + '/' + port.proto] = None

        for name, value in service_instance.environment:
            run_args['environment'][name] = value

        for volume in service_instance.volumes:
            if volume.type == "host_directory":
                assert isinstance(volume, VolumeDescriptionHostPath)
                run_args['volumes'][volume.path] = {'bind': volume.mount_point, 'mode': ("ro" if volume.readonly else "rw")}
            else:
                log.error('Swarm backend does not support volume type {}'.format(volume.type))

        if service_instance.memory_limit is not None:
            run_args['mem_limit'] = service_instance.memory_limit.max
            run_args['mem_reservation'] = service_instance.memory_limit.min
            if service_instance.memory_limit.max == service_instance.memory_limit.min:
                run_args['mem_reservation'] -= 1

        if service_instance.core_limit is not None:
            run_args['cpu_quota'] = int(100000 * service_instance.core_limit.min)

        if get_conf().gelf_address != '':
            run_args['log_config'] = {
                "type": "gelf",
                "config": {
                    'gelf-address': get_conf().gelf_address,
                    'labels': ",".join(service_instance.labels)
                }
            }

        cont = None
        try:
            cont = self.cli.containers.run(**run_args)
        except docker.errors.ImageNotFound:
            raise ZoeException(message='Image not found')
        except docker.errors.APIError as e:
            if cont is not None:
                cont.remove(force=True)
            if e.explanation == b'no resources available to schedule container':
                raise ZoeNotEnoughResourcesException(message=str(e))
            else:
                raise ZoeException(message=str(e))
        except Exception as e:
            if cont is not None:
                cont.remove(force=True)
            raise ZoeException(str(e))

        cont = self.cli.containers.get(cont.id)
        return self._container_summary(cont)

    def _container_summary(self, container: docker.models.containers.Container):
        """Translate a docker-specific container object into a simple dictionary."""
        info = {
            "id": container.id,
            "ip_address": {},
            "name": container.name,
            'labels': container.attrs['Config']['Labels'],
            'external_address': self.docker_config.external_address
        }  # type: Dict[str, Any]
        try:
            info['host'] = container.attrs['Node']['Name'],
        except KeyError:
            info['host'] = 'N/A'

        if container.status == 'running' or container.status == 'restarting':
            info["state"] = Service.BACKEND_START_STATUS
            info["running"] = True
        elif container.status == 'paused' or container.status == 'exited' or container.status == 'dead':
            info["state"] = Service.BACKEND_DIE_STATUS
            info["running"] = False
        elif container.status == 'OOMKilled':
            info["state"] = Service.BACKEND_OOM_STATUS
            info["running"] = False
        elif container.status == 'created':
            info["state"] = Service.BACKEND_CREATE_STATUS
            info["running"] = False
        else:
            log.error('Unknown container status: {}'.format(container.status))
            info["state"] = Service.BACKEND_UNDEFINED_STATUS
            info["running"] = False

        info['ports'] = {}
        if 'Ports' in container.attrs['NetworkSettings'] and container.attrs['NetworkSettings']['Ports'] is not None:
            for port in container.attrs['NetworkSettings']['Ports']:
                if container.attrs['NetworkSettings']['Ports'][port] is not None:
                    info['ports'][port] = container.attrs['NetworkSettings']['Ports'][port][0]['HostPort']
                else:
                    info['ports'][port] = None

        info['cpu_period'] = container.attrs['HostConfig']['CpuPeriod']
        info['cpu_quota'] = container.attrs['HostConfig']['CpuQuota']
        info['memory_hard_limit'] = container.attrs['HostConfig']['Memory']
        info['memory_soft_limit'] = container.attrs['HostConfig']['MemoryReservation']

        return info

    def inspect_container(self, docker_id: str) -> Dict[str, Any]:
        """Retrieve information about a running container."""
        try:
            cont = self.cli.containers.get(docker_id)
        except Exception as e:
            raise ZoeException(str(e))
        return self._container_summary(cont)

    def terminate_container(self, docker_id: str, delete=False) -> None:
        """
        Terminate a container.

        :param docker_id: The container to terminate
        :type docker_id: str
        :param delete: If True, also delete the container files
        :type delete: bool
        :return: None
        """
        try:
            cont = self.cli.containers.get(docker_id)
        except docker.errors.NotFound:
            return

        cont.stop(timeout=5)
        if delete:
            try:
                cont.remove(force=True)
            except docker.errors.APIError as e:
                log.warning(str(e))

    def event_listener(self, callback: Callable[[str], bool]) -> None:
        """An infinite loop that listens for events from Swarm."""
        event_gen = self.cli.events(decode=True)
        while True:
            try:
                event = next(event_gen)
            except requests.exceptions.RequestException:
                log.warning('Docker closed event connection, retrying...')
                event_gen = self.cli.events(decode=True)
                continue

            try:
                res = callback(event)
            except Exception:
                log.exception('Uncaught exception in swarm event callback')
                log.warning('event was: {}'.format(event))
                continue
            if not res:
                break

    def list(self, only_label=None) -> List[dict]:
        """
        List running or defined containers.

        :param only_label: filter containers with only a certain label
        :return: a list of containers
        """
        try:
            ret = self.cli.containers.list(all=True)
        except docker.errors.APIError as ex:
            raise ZoeException(str(ex))
        except requests.exceptions.RequestException as ex:
            raise ZoeException(str(ex))
        if only_label is None:
            only_label = {}
        conts = []
        for cont_info in ret:
            match = True
            for key, value in only_label.items():
                if key not in cont_info.attrs['Config']['Labels']:
                    match = False
                    break
                if cont_info.attrs['Config']['Labels'][key] != value:
                    match = False
                    break
            if match:
                conts.append(self._container_summary(cont_info))

        return conts

    def stats(self, docker_id: str, stream: bool):
        """Retrieves container stats based on resource usage."""
        try:
            cont = self.cli.containers.get(docker_id)
        except docker.errors.NotFound:
            raise ZoeException('Container not found')
        except docker.errors.APIError as e:
            raise ZoeException('Docker API error: {}'.format(e))

        try:
            return cont.stats(stream=stream)
        except docker.errors.APIError as e:
            raise ZoeException('Docker API error: {}'.format(e))
        except requests.exceptions.ReadTimeout:
            raise ZoeException('Read timeout')
        except ValueError:
            raise ZoeException('Docker API decoding error')

    def logs(self, docker_id: str, stream: bool, follow=None):
        """
        Retrieves the logs of the selected container.

        :param docker_id:
        :param stream:
        :param follow:
        :return:
        """
        try:
            cont = self.cli.containers.get(docker_id)
        except (docker.errors.NotFound, docker.errors.APIError):
            return None

        try:
            return cont.logs(stdout=True, stderr=True, follow=follow, stream=stream, timestamps=True, tail='all')
        except docker.errors.APIError:
            return None

    def list_images(self):
        """Retrieve the list of images available on this node."""
        try:
            return self.cli.images.list()
        except (docker.errors.NotFound, docker.errors.APIError):
            return []

    def pull_image(self, image_name):
        """Pulls an image in the docker engine."""
        try:
            self.cli.images.pull(image_name)
        except docker.errors.APIError as e:
            log.error('Cannot download image {}: {}'.format(image_name, e))
            raise ZoeException('Cannot download image {}: {}'.format(image_name, e))

    def update(self, docker_id, cpu_quota=None, mem_reservation=None, mem_limit=None):
        """Update the resource reservation for a container."""
        kwargs = {}
        if cpu_quota is not None:
            kwargs['cpu_quota'] = cpu_quota
        if mem_reservation is not None:
            kwargs['mem_reservation'] = mem_reservation
        if mem_limit is not None:
            kwargs['mem_limit'] = mem_limit

        try:
            cont = self.cli.containers.get(docker_id)
        except (docker.errors.NotFound, docker.errors.APIError):
            return

        try:
            cont.update(**kwargs)
        except docker.errors.APIError:
            pass
