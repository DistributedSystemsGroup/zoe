"""Test script for successful cookie authentication."""

import json
import time
import sys
import unittest

import requests

ZOE_API_URI = 'http://192.168.12.2:5100/api/0.7/'
ZOE_AUTH = ('admin', 'admin')


class ZoeRestTestSuccess(unittest.TestCase):
    """Test case class."""

    uri = ZOE_API_URI
    id = ''
    session = None

    def tearDown(self):
        """Test end."""
        time.sleep(3)

    def test_0_login(self):
        """Test login api endpoint."""
        print('Test login api endpoint')
        session = requests.Session()
        req = session.get(self.__class__.uri + 'login', auth=ZOE_AUTH)

        self.assertEqual(req.status_code, 200)

        self.assertGreater(len(session.cookies.items()), 0)

        self.__class__.session = session

    def test_1_info(self):
        """Test info api endpoint."""
        print('Test info api endpoint')

        session = self.__class__.session

        req = session.get(self.__class__.uri + 'info')

        self.assertEqual(req.status_code, 200)

    def test_2_userinfo(self):
        """Test userinfo api endpoint."""
        print('Test userinfo api endpoint')

        session = self.__class__.session

        req = session.get(self.__class__.uri + 'userinfo')

        self.assertEqual(req.status_code, 200)

    def test_4_execution_details(self):
        """Test execution details api endpoint."""
        print('Test execution details api endpoint')
        session = self.__class__.session
        req = session.get(self.__class__.uri + 'execution/' + self.__class__.id)
        self.assertEqual(req.status_code, 200)

    def test_4_service_details(self):
        """Test service details api endpoint."""
        print('Test service details api endpoint')
        session = self.__class__.session
        req = session.get(self.__class__.uri + 'execution/' + self.__class__.id)
        sid = req.json()["services"][0]
        req = session.get(self.__class__.uri + 'service/' + str(sid))
        self.assertEqual(req.status_code, 200)

    def test_5_terminate_execution(self):
        """Test terminate execution api endpoint."""
        print('Test terminate execution api endpoint')
        session = self.__class__.session
        req = session.delete(self.__class__.uri + 'execution/' + self.__class__.id)
        self.assertEqual(req.status_code, 204)

    def test_6_list_all_executions(self):
        """Test list all executions api endpoint."""
        print('Test list all executions api endpoint')
        session = self.__class__.session
        req = session.get(self.__class__.uri + 'execution')
        self.assertEqual(req.status_code, 200)

    def test_7_delete_execution(self):
        """Test delete execution api endpoint."""
        print('Test delete execution api endpoint')
        session = self.__class__.session
        req = session.delete(self.__class__.uri + 'execution/delete/' + self.__class__.id)
        self.assertEqual(req.status_code, 204)

    def test_3_start_execution(self):
        """Test start execution api endpoint."""
        print('Test start execution api endpoint')

        with open('zapp.json', encoding='utf-8') as data_file:
            data = json.loads(data_file.read())

        session = self.__class__.session

        req = session.post(self.__class__.uri + 'execution', json={"application": data, "name": "requests"})
        self.assertEqual(req.status_code, 201)
        self.__class__.id = str(req.json()['execution_id'])

if __name__ == '__main__':
    if len(sys.argv) > 1:
        API_SERVER = sys.argv.pop()
        ZoeRestTestSuccess.uri = 'http://' + API_SERVER + '/api/0.7/'

    unittest.main()
