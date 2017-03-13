#!/usr/bin/env python3

# Copyright (c) 2016, Quang-Nhat Hoang-Xuan
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

"""Container Parameter class"""

from typing import Iterable, Callable, Dict, Any, Union

class DockerContainerParameter():
    def __init__(self):
        self.image = ''
        self.volumes = []
        self.command = ""
        self.name = ''
        self.ports = []
        self.network_name = 'bridge'
        self.gelf_address = ''
        self.restart = True
        self.hostname = ''

    def set_gelf(self, gelf_address):
        self.gelf_address = gelf_address
        
    def get_gelf(self) -> str:
        return self.gelf_address     

    def set_ports(self, ports):
        self.ports.append(ports)

    def get_ports(self) -> Iterable[str]:
        return self.ports

    def set_image(self, image) -> str:
        self.image = image

    def get_image(self) -> str:
        return self.image

    def set_volumes(self, volumes):
        self.volumes.append(volumes)

    def get_volumes(self) -> Iterable[str]:
        """Get the volumes in Docker format."""
        return self.volumes

    def set_command(self, cmd) -> str:
        """Setter for the command to run in the container."""
        self.command = cmd

    def get_command(self) -> str:
        """Getter for the command to run in the container."""
        return self.command

    def set_name(self, name) -> str:
        self.name = name

    def get_name(self) -> str:
        return self.name

    def set_hostname(self, hostname) -> str:
        self.hostname = hostname

    def get_hostname(self) -> str:
        return self.hostname

