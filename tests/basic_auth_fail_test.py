"""Test script for unsuccessful basic authentication."""

import time
import sys
import unittest

import requests

ZOE_API_URI = 'http://192.168.12.2:5100/api/0.7/'
ZOE_AUTH = ('admin', 'admin')


class ZoeRestTestSuccess(unittest.TestCase):
    """Test case class."""

    uri = ZOE_API_URI
    auth = ZOE_AUTH
    wrong_auth = ('test', '123')
    id = '-1'

    def tearDown(self):
        """Test end."""
        time.sleep(3)

    def test_1_userinfo(self):
        """Test userinfo api endpoint."""
        print('Test userinfo api endpoint')
        req = requests.get(self.__class__.uri + 'userinfo', auth=self.__class__.wrong_auth)
        self.assertEqual(req.status_code, 401)

    def test_3_execution_details(self):
        """Test execution details api endpoint."""
        print('Test execution details api endpoint')
        req = requests.get(self.__class__.uri + 'execution/' + self.__class__.id, auth=self.__class__.auth)
        self.assertEqual(req.status_code, 404)

    def test_4_terminate_execution(self):
        """Test terminate no execution api endpoint."""
        print('Test terminate no execution api endpoint')
        req = requests.delete(self.__class__.uri + 'execution/' + self.__class__.id, auth=self.__class__.auth)
        self.assertEqual(req.status_code, 404)

    def test_6_delete_execution(self):
        """Test delete execution api endpoint."""
        print('Test delete execution api endpoint')
        req = requests.delete(self.__class__.uri + 'execution/delete/' + self.__class__.id, auth=self.__class__.auth)
        self.assertEqual(req.status_code, 404)

    def test_2_start_failed_execution(self):
        """Test fail submit execution api endpoint."""
        print('Test fail submit execution api endpoint')

        req = requests.post(self.__class__.uri + 'execution', auth=self.__class__.auth, json={"application": "data", "name": "requests"})
        self.assertEqual(req.status_code, 400)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        API_SERVER = sys.argv.pop()
        ZoeRestTestSuccess.uri = 'http://' + API_SERVER + '/api/0.7/'
    unittest.main()
