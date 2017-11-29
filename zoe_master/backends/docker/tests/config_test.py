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

from zoe_master.backends.docker import config


class TestDockerEngineBackendConfig:
    """Docker configuration parsing tests."""

    def test_new_docker_host_config(self):
        """Test the DockerHostConfig object."""
        config.DockerHostConfig()

    def test_parsing_config_file(self):
        """Test Docker backend config parsing."""
        hosts = config.DockerConfig(config_file='integration_tests/sample_docker.conf').read_config()
        assert len(hosts) == 1
