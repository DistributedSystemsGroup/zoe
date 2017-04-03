import requests
import json
import time
import unittest

from test_config import ZOE_API_URI, ZOE_AUTH

class ZoeRestTestSuccess(unittest.TestCase):

    uri = ZOE_API_URI
    auth = ZOE_AUTH
    id = ''

    def tearDown(self):
        time.sleep(3)

    def test_0_info(self):
        print('Test info api endpoint')
        r = requests.get(self.__class__.uri + 'info')
        self.assertEqual(r.status_code, 200)

    def test_1_userinfo(self):
        print('Test userinfo api endpoint')
        r = requests.get(self.__class__.uri + 'userinfo', auth=self.__class__.auth)
        self.assertEqual(r.status_code, 200)

    def test_3_execution_details(self):
        print('Test execution details api endpoint')
        r = requests.get(self.__class__.uri + 'execution/' + self.__class__.id, auth=self.__class__.auth)
        self.assertEqual(r.status_code, 200)

    def test_4_service_details(self):
        print('Test service details api aendpoint')
        r = requests.get(self.__class__.uri + 'execution/' + self.__class__.id, auth=self.__class__.auth)
        sid = r.json()["services"][0]
        r = requests.get(self.__class__.uri + 'service/' + str(sid), auth=self.__class__.auth)
        self.assertEqual(r.status_code, 200)

    def test_5_terminate_execution(self):
        print('Test terminate execution api endpoint')
        r = requests.delete(self.__class__.uri + 'execution/' + self.__class__.id, auth=self.__class__.auth)
        self.assertEqual(r.status_code, 204)

    def test_6_list_all_executions(self):
        print('Test list all executions api endpoint')
        r = requests.get(self.__class__.uri + 'execution', auth=self.__class__.auth)
        self.assertEqual(r.status_code, 200)

    def test_7_delete_execution(self):
        print('Test delete execution api endpoint')
        r = requests.delete(self.__class__.uri + 'execution/delete/' + self.__class__.id, auth=self.__class__.auth)
        self.assertEqual(r.status_code, 204)
        
    def test_2_start_execution(self):
        print('Test start execution api endpoint')
        
        data = []

        with open('zapp.json', encoding='utf-8') as data_file:
            data = json.loads(data_file.read())
        
        r = requests.post(self.__class__.uri + 'execution', auth=self.__class__.auth, json={"application": data, "name": "requests"})
        self.assertEqual(r.status_code, 201)
        self.__class__.id = str(r.json()['execution_id'])

if __name__ == '__main__':
        unittest.main()
