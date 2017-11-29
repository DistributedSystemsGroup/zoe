# Copyright (c) 2017, Jordan Kuhn
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

"""Fixture for mock configuration used in tests."""

from argparse import Namespace

import pytest


@pytest.fixture(scope="session")
def zoe_configuration():
    """Mock Zoe configuration."""
    zoe_api_args = Namespace()
    zoe_api_args.debug = True
    zoe_api_args.deployment_name = 'integration_test'
    zoe_api_args.dbhost = 'postgres'
    zoe_api_args.dbport = 5432
    zoe_api_args.dbuser = 'zoeuser'
    zoe_api_args.dbpass = 'zoepass'
    zoe_api_args.dbname = 'zoe'
    zoe_api_args.api_listen_uri = 'tcp://*:4850'
    zoe_api_args.kairosdb_enable = False
    zoe_api_args.workspace_base_path = '/tmp'
    zoe_api_args.workspace_deployment_path = zoe_api_args.workspace_base_path
    zoe_api_args.overlay_network_name = 'zoe'
    zoe_api_args.gelf_listener = 0
    zoe_api_args.listen_address = '0.0.0.0'
    zoe_api_args.listen_port = 5100
    zoe_api_args.master_url = 'tcp://127.0.0.1:4850'
    zoe_api_args.cookie_secret = 'changeme'
    zoe_api_args.auth_type = 'text'
    zoe_api_args.auth_file = 'zoepass.csv'
    zoe_api_args.scheduler_class = 'ZoeElasticScheduler'
    zoe_api_args.scheduler_policy = 'FIFO'
    zoe_api_args.backend = 'DockerEngine'
    zoe_api_args.backend_docker_config_file = 'integration_tests/sample_docker.conf'
    zoe_api_args.zapp_shop_path = 'contrib/zapp-shop-sample'
    zoe_api_args.log_file = 'stderr'
    zoe_api_args.max_core_limit = 1
    zoe_api_args.max_memory_limit = 2
    zoe_api_args.no_user_edit_limits_web = False
    zoe_api_args.additional_volumes = ''
    return zoe_api_args
