# Copyright (c) 2015, Daniele Venzano
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


def openmpi_worker_service(counter, workspace_volume, worker_memory):
    """
    :type counter: int
    :type workspace_volume: dict
    :type worker_memory: int
    :rtype: dict
    """
    service = {
        'name': "mpiworker{}".format(counter),
        'docker_image': '192.168.45.252:5000/zoerepo/openmpi-worker',
        'monitor': False,
        'required_resources': {"memory": worker_memory},
        'ports': [],
        'environment': [],
        'volumes': [],
        'command': ''
    }
    service['volumes'].append([workspace_volume['host_path'], workspace_volume['cont_path'], workspace_volume['readonly']])
    return service


def openmpi_mpirun_service(workspace_volume, mpirun_commandline, worker_memory):
    """
    :type mpirun_commandline: str
    :type workspace_volume: dict
    :type worker_memory: int
    :rtype: dict
    """
    service = {
        'name': "mpirun",
        'docker_image': '192.168.45.252:5000/zoerepo/openmpi-worker',
        'monitor': True,
        'required_resources': {"memory": worker_memory},
        'ports': [],
        'environment': [],
        'volumes': [],
        'command': mpirun_commandline
    }
    service['volumes'].append([workspace_volume['host_path'], workspace_volume['cont_path'], workspace_volume['readonly']])
    return service


empty = {
    'host_path': 'CHANGEME',  # the path containing what to copy
    'cont_path': 'CHANGEME',  # the file or directory to copy from or to host_path
    'readonly': False
}


def openmpi_app(name='openmpi-test', workspace_volume=empty, mpirun_commandline='', worker_count=4, worker_memory=(1024 ** 3)):
    """
    :type name: str
    :type workspace_volume: dict
    :type mpirun_commandline: str
    :type worker_count: int
    :type worker_memory: int
    :rtype: dict
    """
    app = {
        'name': name,
        'version': 1,
        'will_end': True,
        'priority': 512,
        'requires_binary': True,
        'services': []
    }
    for i in range(worker_count):
        proc = openmpi_worker_service(i, workspace_volume, worker_memory)
        app['services'].append(proc)
    proc = openmpi_mpirun_service(workspace_volume, mpirun_commandline, worker_memory)
    app['services'].append(proc)
    return app
