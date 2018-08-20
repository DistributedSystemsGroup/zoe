"""Test script for unsuccessful basic authentication."""

import requests

ZOE_API_URI = 'http://127.0.0.1:5100/api/0.7/'
WRONG_AUTH = ('test', '123')
TIMEOUT = 5


class TestZoeRestAuthFails:
    """Test case class."""

    def test_user(self, zoe_api_process):
        """Test user api endpoint."""
        print('Test user api endpoint')
        req = requests.get(ZOE_API_URI + 'user', auth=WRONG_AUTH)
        assert req.status_code == 401

    def test_3_execution_details(self, zoe_api_process):
        """Test execution details api endpoint."""
        print('Test execution details api endpoint')
        req = requests.get(ZOE_API_URI + 'execution/345', auth=WRONG_AUTH)
        assert req.status_code == 401

    def test_4_terminate_execution(self, zoe_api_process):
        """Test terminate no execution api endpoint."""
        print('Test terminate no execution api endpoint')
        req = requests.delete(ZOE_API_URI + 'execution/345', auth=WRONG_AUTH)
        assert req.status_code == 401

    def test_6_delete_execution(self, zoe_api_process):
        """Test delete execution api endpoint."""
        print('Test delete execution api endpoint')
        req = requests.delete(ZOE_API_URI + 'execution/delete/234', auth=WRONG_AUTH)
        assert req.status_code == 401

    def test_2_start_failed_execution(self, zoe_api_process):
        """Test fail submit execution api endpoint."""
        print('Test fail submit execution api endpoint')

        req = requests.post(ZOE_API_URI + 'execution', auth=WRONG_AUTH, json={"application": "data", "name": "requests"})
        assert req.status_code == 401
