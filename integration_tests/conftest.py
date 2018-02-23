import os
import subprocess
import sys
import time

import pytest

ARGS = [
    '--debug',
    '--deployment-name', 'integration_test',
    '--dbuser', 'zoeuser',
    '--dbhost', 'postgres',
    '--dbport', '5432',
    '--dbname', 'zoe',
    '--dbpass', 'zoepass',
    '--master-url', 'tcp://localhost:4850',
    '--listen-port', '5100',
    '--workspace-base-path', '/tmp',
    '--workspace-deployment-path', 'integration_test',
    '--auth-file', 'zoepass.csv',
    '--backend', 'DockerEngine',
    '--backend-docker-config-file', 'integration_tests/sample_docker.conf',
    '--zapp-shop-path', 'contrib/zapp-shop-sample'
]


@pytest.fixture(scope="session")
def zoe_api_process(request):
    """Fixture that starts the Zoe API process."""
    proc = subprocess.Popen(["python", "zoe-api.py"] + ARGS, stderr=sys.stderr, stdout=sys.stdout)
    request.addfinalizer(proc.terminate)
    time.sleep(2)


@pytest.fixture(scope="session")
def zoe_master_process(request):
    """Fixture that starts the Zoe Master process."""
    os.mkdir('/tmp/integration_test')
    proc = subprocess.Popen(["python", "zoe-master.py"] + ARGS, stderr=sys.stderr, stdout=sys.stdout)
    request.addfinalizer(proc.terminate)
    time.sleep(4)
