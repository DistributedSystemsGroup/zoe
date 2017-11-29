"""Test script for successful basic authentication."""

import subprocess
import time
import json
import sys
import os

import pytest
import requests

ZOE_API_URI = 'http://127.0.0.1:5100/api/0.7/'
ZOE_AUTH = ('admin', 'admin')
TIMEOUT = 5

ARGS = [
    '--debug',
    '--deployment-name', 'integration_test',
    '--dbuser', 'zoeuser',
    '--dbhost', 'postgres',
    '--dbport', '5432',
    '--dbname', 'zoe',
    '--dbpass', 'zoepass',
    '--master-url', 'tcp://localhost:4850',
    '--auth-type', 'text',
    '--listen-port', '5100',
    '--workspace-base-path', '/tmp',
    '--workspace-deployment-path', 'integration_test',
    '--auth-file', 'zoepass.csv',
    '--backend', 'DockerEngine',
    '--backend-docker-config-file', 'tests/sample_docker.conf',
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


class TestZoeRest:
    """Test case class."""

    id = None

    def test_info(self, zoe_api_process):
        """Test info api endpoint."""
        print('Test info api endpoint')
        req = requests.get(ZOE_API_URI + 'info', timeout=TIMEOUT)
        assert req.status_code == 200

    def test_userinfo(self, zoe_api_process):
        """Test userinfo api endpoint."""
        print('Test userinfo api endpoint')
        req = requests.get(ZOE_API_URI + 'userinfo', auth=ZOE_AUTH, timeout=TIMEOUT)
        assert req.status_code == 200

    def test_list_all_executions(self, zoe_api_process):
        """Test list all executions api endpoint."""
        print('Test list all executions api endpoint')
        req = requests.get(ZOE_API_URI + 'execution', auth=ZOE_AUTH, timeout=TIMEOUT)
        assert req.status_code == 200

#    def test_7_delete_execution(self):
#        """Test delete execution api endpoint."""
#        print('Test delete execution api endpoint')
#       req = requests.delete(self.__class__.uri + 'execution/delete/' + self.__class__.id, auth=self.__class__.auth)
#        if req.status_code != 204:
#            print('error message: {}'.format(req.json()['message']))
#        self.assertEqual(req.status_code, 204)

    def test_start_stop_execution(self, zoe_api_process, zoe_master_process):
        """Test start execution api endpoint."""
        print('Test start execution api endpoint')

        with open('tests/zapp.json', encoding='utf-8') as data_file:
            data = json.loads(data_file.read())

        req = requests.post(ZOE_API_URI + 'execution', auth=ZOE_AUTH, json={"application": data, "name": "requests"}, timeout=TIMEOUT)
        assert req.status_code == 201
        exec_id = str(req.json()['execution_id'])
        print('execution ID is {}'.format(exec_id))

        print('Test execution details api endpoint')
        while True:
            req = requests.get(ZOE_API_URI + 'execution/' + exec_id, auth=ZOE_AUTH, timeout=TIMEOUT)
            assert req.status_code == 200
            if req.json()['status'] == 'running':
                break
            elif req.json()['status'] == 'error':
                print(req.json()['error_message'])
                assert False
            print('Waiting for ZApp to start (status is {})...'.format(req.json()['status']))
            time.sleep(1)

        print('Test service details api endpoint')
        req = requests.get(ZOE_API_URI + 'execution/' + exec_id, auth=ZOE_AUTH, timeout=TIMEOUT)
        sid = req.json()["services"][0]
        req = requests.get(ZOE_API_URI + 'service/' + str(sid), auth=ZOE_AUTH, timeout=TIMEOUT)
        assert req.status_code == 200

        print('Test terminate execution api endpoint')
        req = requests.delete(ZOE_API_URI + 'execution/' + exec_id, auth=ZOE_AUTH, timeout=TIMEOUT)
        assert req.status_code == 204

    def test_zapp_validate(self, zoe_api_process):
        """Test ZApp validation endpoint"""
        print("Test ZApp validation endpoint")
        with open('tests/zapp.json', encoding='utf-8') as data_file:
            data = json.loads(data_file.read())

        req = requests.post(ZOE_API_URI + 'zapp_validate', json={"application": data}, timeout=TIMEOUT)
        assert req.status_code == 200

    def test_zapp_validate_fail(self, zoe_api_process):
        """Test ZApp validation endpoint"""
        print("Test ZApp validation endpoint")
        with open('tests/zapp.json', encoding='utf-8') as data_file:
            data = json.loads(data_file.read())

        del data['version']
        req = requests.post(ZOE_API_URI + 'zapp_validate', json={"application": data}, timeout=TIMEOUT)
        assert req.status_code == 400
