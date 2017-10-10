# Copyright (c) 2017, Daniele Venzano
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

"""Unit tests"""

import pytest

from zoe_master.backends.docker import api_client
from zoe_master.backends.docker.config import DockerHostConfig
from zoe_master.exceptions import ZoeException


class MockDocker:
    """A mock object for the official docker client."""
    def __init__(self):
        self.containers = MockContainerModel()

    def info(self):
        """The info method."""
        return {
            "ID": "7TRN:IPZB:QYBB:VPBQ:UMPP:KARE:6ZNR:XE6T:7EWV:PKF4:ZOJD:TPYS",
            "Containers": 14,
            "ContainersRunning": 3,
            "ContainersPaused": 1,
            "ContainersStopped": 10,
            "Images": 508,
            "Driver": "overlay2",
            "DriverStatus": [
                [
                    "Backing Filesystem",
                    "extfs"
                ],
                [
                    "Supports d_type",
                    "true"
                ],
                [
                    "Native Overlay Diff",
                    "true"
                ]
            ],
            "DockerRootDir": "/var/lib/docker",
            "SystemStatus": [],
            "Plugins": {
                "Volume": [
                    "local"
                ],
                "Network": [
                    "bridge",
                    "host",
                    "ipvlan",
                    "macvlan",
                    "null",
                    "overlay"
                ],
                "Authorization": [
                    "img-authz-plugin",
                    "hbm"
                ],
                "Log": [
                    "awslogs",
                    "fluentd",
                    "gcplogs",
                    "gelf",
                    "journald",
                    "json-file",
                    "logentries",
                    "splunk",
                    "syslog"
                ]
            },
            "MemoryLimit": True,
            "SwapLimit": True,
            "KernelMemory": True,
            "CpuCfsPeriod": True,
            "CpuCfsQuota": True,
            "CPUShares": True,
            "CPUSet": True,
            "OomKillDisable": True,
            "IPv4Forwarding": True,
            "BridgeNfIptables": True,
            "BridgeNfIp6tables": True,
            "Debug": False,
            "NFd": 64,
            "NGoroutines": 174,
            "SystemTime": "2017-08-08T20:28:29.06202363Z",
            "LoggingDriver": "string",
            "CgroupDriver": "cgroupfs",
            "NEventsListener": 30,
            "KernelVersion": "4.9.38-moby",
            "OperatingSystem": "Alpine Linux v3.5",
            "OSType": "linux",
            "Architecture": "x86_64",
            "NCPU": 4,
            "MemTotal": 2095882240,
            "IndexServerAddress": "https://index.docker.io/v1/",
            "RegistryConfig": {
                "InsecureRegistryCIDRs": [
                    "::1/128",
                    "127.0.0.0/8"
                ],
                "IndexConfigs": {
                    "127.0.0.1:5000": {
                        "Name": "127.0.0.1:5000",
                        "Mirrors": [],
                        "Secure": False,
                        "Official": False
                    },
                    "[2001:db8:a0b:12f0::1]:80": {
                        "Name": "[2001:db8:a0b:12f0::1]:80",
                        "Mirrors": [],
                        "Secure": False,
                        "Official": False
                    },
                    "docker.io": {
                        "Name": "docker.io",
                        "Mirrors": [
                            "https://hub-mirror.corp.example.com:5000/"
                        ],
                        "Secure": True,
                        "Official": True
                    }
                },
                "Mirrors": []
            },
            "GenericResources": [],
            "HttpProxy": "http://user:pass@proxy.corp.example.com:8080",
            "HttpsProxy": "https://user:pass@proxy.corp.example.com:4443",
            "NoProxy": "*.local, 169.254/16",
            "Name": "node5.corp.example.com",
            "Labels": [
                "storage=ssd",
                "production"
            ],
            "ExperimentalBuild": False,
            "ServerVersion": "17.06.0-ce",
            "ClusterStore": "consul://consul.corp.example.com:8600/some/path",
            "ClusterAdvertise": "node5.corp.example.com:8000",
            "Runtimes": {
                "runc": {
                    "path": "docker-runc"
                }
            },
            "DefaultRuntime": "runc",
            "Swarm": {},
            "LiveRestoreEnabled": False,
            "Isolation": "default",
            "InitBinary": "docker-init"
        }


class MockContainerModel:
    """A mock object fot the docker container model."""
    def get(self, docker_id):
        """The get method"""
        return MockContainer(docker_id)


class MockContainer:
    """A mock container object"""
    def __init__(self, docker_id):
        self.id = docker_id
        self.name = 'mock-container'
        self.attrs = {
            "AppArmorProfile": "",
            "Args": [
                "-c",
                "exit 9"
            ],
            "Config": {
                "AttachStderr": True,
                "AttachStdin": False,
                "AttachStdout": True,
                "Cmd": [
                    "/bin/sh",
                    "-c",
                    "exit 9"
                ],
                "Domainname": "",
                "Env": [
                    "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
                ],
                "Hostname": "ba033ac44011",
                "Image": "ubuntu",
                "Labels": {
                    "com.example.vendor": "Acme",
                    "com.example.license": "GPL",
                    "com.example.version": "1.0"
                },
                "MacAddress": "",
                "NetworkDisabled": False,
                "OpenStdin": False,
                "StdinOnce": False,
                "Tty": False,
                "User": "",
                "Volumes": {
                    "/volumes/data": {}
                },
                "WorkingDir": "",
                "StopSignal": "SIGTERM",
                "StopTimeout": 10
            },
            "Created": "2015-01-06T15:47:31.485331387Z",
            "Driver": "devicemapper",
            "HostConfig": {
                "MaximumIOps": 0,
                "MaximumIOBps": 0,
                "BlkioWeight": 0,
                "BlkioWeightDevice": [
                    {}
                ],
                "BlkioDeviceReadBps": [
                    {}
                ],
                "BlkioDeviceWriteBps": [
                    {}
                ],
                "BlkioDeviceReadIOps": [
                    {}
                ],
                "BlkioDeviceWriteIOps": [
                    {}
                ],
                "ContainerIDFile": "",
                "CpusetCpus": "",
                "CpusetMems": "",
                "CpuPercent": 0,
                "CpuQuota": 100000,
                "CpuPeriod": 100000,
                "CpuRealtimePeriod": 1000000,
                "CpuRealtimeRuntime": 10000,
                "Devices": [],
                "IpcMode": "",
                "LxcConf": [],
                "Memory": 0,
                "MemorySwap": 0,
                "MemoryReservation": 0,
                "KernelMemory": 0,
                "OomKillDisable": False,
                "OomScoreAdj": 500,
                "NetworkMode": "bridge",
                "PidMode": "",
                "PortBindings": {},
                "Privileged": False,
                "ReadonlyRootfs": False,
                "PublishAllPorts": False,
                "RestartPolicy": {
                    "MaximumRetryCount": 2,
                    "Name": "on-failure"
                },
                "LogConfig": {
                    "Type": "json-file"
                },
                "Sysctls": {
                    "net.ipv4.ip_forward": "1"
                },
                "Ulimits": [
                    {}
                ],
                "VolumeDriver": "",
                "ShmSize": 67108864
            },
            "HostnamePath": "/var/lib/docker/containers/ba033ac4401106a3b513bc9d639eee123ad78ca3616b921167cd74b20e25ed39/hostname",
            "HostsPath": "/var/lib/docker/containers/ba033ac4401106a3b513bc9d639eee123ad78ca3616b921167cd74b20e25ed39/hosts",
            "LogPath": "/var/lib/docker/containers/1eb5fabf5a03807136561b3c00adcd2992b535d624d5e18b6cdc6a6844d9767b/1eb5fabf5a03807136561b3c00adcd2992b535d624d5e18b6cdc6a6844d9767b-json.log",
            "Id": "ba033ac4401106a3b513bc9d639eee123ad78ca3616b921167cd74b20e25ed39",
            "Image": "04c5d3b7b0656168630d3ba35d8889bd0e9caafcaeb3004d2bfbc47e7c5d35d2",
            "MountLabel": "",
            "Name": "/boring_euclid",
            "NetworkSettings": {
                "Bridge": "",
                "SandboxID": "",
                "HairpinMode": False,
                "LinkLocalIPv6Address": "",
                "LinkLocalIPv6PrefixLen": 0,
                "SandboxKey": "",
                "EndpointID": "",
                "Gateway": "",
                "GlobalIPv6Address": "",
                "GlobalIPv6PrefixLen": 0,
                "IPAddress": "",
                "IPPrefixLen": 0,
                "IPv6Gateway": "",
                "MacAddress": "",
                "Networks": {
                    "bridge": {
                        "NetworkID": "7ea29fc1412292a2d7bba362f9253545fecdfa8ce9a6e37dd10ba8bee7129812",
                        "EndpointID": "7587b82f0dada3656fda26588aee72630c6fab1536d36e394b2bfbcf898c971d",
                        "Gateway": "172.17.0.1",
                        "IPAddress": "172.17.0.2",
                        "IPPrefixLen": 16,
                        "IPv6Gateway": "",
                        "GlobalIPv6Address": "",
                        "GlobalIPv6PrefixLen": 0,
                        "MacAddress": "02:42:ac:12:00:02"
                    }
                }
            },
            "Path": "/bin/sh",
            "ProcessLabel": "",
            "ResolvConfPath": "/var/lib/docker/containers/ba033ac4401106a3b513bc9d639eee123ad78ca3616b921167cd74b20e25ed39/resolv.conf",
            "RestartCount": 1,
            "State": {
                "Error": "",
                "ExitCode": 9,
                "FinishedAt": "2015-01-06T15:47:32.080254511Z",
                "OOMKilled": False,
                "Dead": False,
                "Paused": False,
                "Pid": 0,
                "Restarting": False,
                "Running": True,
                "StartedAt": "2015-01-06T15:47:32.072697474Z",
                "Status": "running"
            },
            "Mounts": [
                {
                    "Name": "fac362...80535",
                    "Source": "/data",
                    "Destination": "/data",
                    "Driver": "local",
                    "Mode": "ro,Z",
                    "RW": False,
                    "Propagation": ""
                }
            ]
        }
        self.status = 'running'

    def stop(self, timeout=5):
        """Stop method"""
        return

    def remove(self, force=False):
        """Remove method"""
        return


class TestDockerEngineApiClient:
    """Docker low-level wrapper testing."""

    @pytest.fixture
    def docker_client(self):
        """The mock Docker client object."""
        return MockDocker()

    def test_init_fail(self):
        """Test that initialization fails with a bad address."""
        dhc = DockerHostConfig()
        dhc.name = 'test'
        dhc.address = '999.999.999.999:9999'
        with pytest.raises(ZoeException):
            api_client.DockerClient(dhc)

    def test_info(self, docker_client):
        """Test that the info method works."""
        dhc = DockerHostConfig()
        dhc.name = 'test'
        mock_client = docker_client
        cli = api_client.DockerClient(dhc, mock_client)
        assert cli.info() is not None

    def test_inspect_container(self, docker_client):
        """Test the inspect container parsing logic."""
        dhc = DockerHostConfig()
        dhc.name = 'test'
        mock_client = docker_client
        cli = api_client.DockerClient(dhc, mock_client)
        assert cli.inspect_container('test') is not None

    def test_terminate_container(self, docker_client):
        """Test the terminate container method."""
        dhc = DockerHostConfig()
        dhc.name = 'test'
        mock_client = docker_client
        cli = api_client.DockerClient(dhc, mock_client)
        cli.terminate_container('test')
        cli.terminate_container('test', delete=True)
