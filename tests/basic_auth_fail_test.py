import requests
import json
import time
import unittest

from config import ZOE_API_URI, ZOE_AUTH

class ZoeRestTestSuccess(unittest.TestCase):

    uri = ZOE_API_URI
    auth = ZOE_AUTH
    wrong_auth = ('test', '123')
    id = '-1'
    
    def tearDown(self):
        time.sleep(3)

    def test_1_userinfo(self):
        print('Test userinfo api endpoint')
        r = requests.get(self.__class__.uri + 'userinfo', auth=self.__class__.wrong_auth)
        self.assertEqual(r.status_code, 401)

    def test_3_execution_details(self):
        print('Test execution details api endpoint')
        r = requests.get(self.__class__.uri + 'execution/' + self.__class__.id, auth=self.__class__.auth)
        self.assertEqual(r.status_code, 404)

    def test_4_terminate_execution(self):
        print('Test terminate no execution api endpoint')
        r = requests.delete(self.__class__.uri + 'execution/' + self.__class__.id, auth=self.__class__.auth)
        self.assertEqual(r.status_code, 404)

    def test_6_delete_execution(self):
        print('Test delete execution api endpoint')
        r = requests.delete(self.__class__.uri + 'execution/delete/' + self.__class__.id, auth=self.__class__.auth)
        self.assertEqual(r.status_code, 404)       
    
    def test_2_start_failed_execution(self):
        print('Test fail submit execution api endpoint')
        
        r = requests.post(self.__class__.uri + 'execution', auth=self.__class__.auth, json={"application": "data", "name": "requests"})
        self.assertEqual(r.status_code, 400)

if __name__ == '__main__':
        unittest.main()
