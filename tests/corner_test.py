"""Corner test."""

import json
import sys
import time
import unittest

import requests


class ZoeRestTestSuccess(unittest.TestCase):
    """Test case class."""

    uri = 'http://localhost:5001/api/0.6/'
    auth = ('test', '1234')
    id = ''

    def tearDown(self):
        """Test end."""
        time.sleep(3)

    def test_3_execution_details(self):
        """Test execution details api endpoint."""
        print('Test execution details api endpoint')
        req = requests.get(self.__class__.uri + 'execution/' + self.__class__.id, auth=self.__class__.auth)
        self.assertEqual(req.status_code, 200)

    def test_4_terminate_execution(self):
        """Test terminate no execution api endpoint."""
        print('Test terminate no execution api endpoint')
        req = requests.delete(self.__class__.uri + 'execution/' + self.__class__.id, auth=self.__class__.auth)
        self.assertEqual(req.status_code, 400)

    def test_6_delete_execution(self):
        """Test delete execution api endpoint."""
        print('Test delete execution api endpoint')
        req = requests.delete(self.__class__.uri + 'execution/delete/' + self.__class__.id, auth=self.__class__.auth)
        self.assertEqual(req.status_code, 204)

    def test_2_start_failed_execution(self):
        """Test fail submit execution api endpoint."""
        print('Test fail submit execution api endpoint')

        with open('dummy.json', encoding='utf-8') as data_file:
            data = json.loads(data_file.read())

        req = requests.post(self.__class__.uri + 'execution', auth=self.__class__.auth, json={"application": data, "name": "requests"})
        self.assertEqual(req.status_code, 201)

        self.__class__.id = str(req.json()['execution_id'])

if __name__ == '__main__':
    if len(sys.argv) > 1:
        API_SERVER = sys.argv.pop()
        ZoeRestTestSuccess.uri = 'http://' + API_SERVER + '/api/0.7/'

    unittest.main()
