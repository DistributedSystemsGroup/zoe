import requests
import json
import time
import unittest

class ZoeRestTestSuccess(unittest.TestCase):

    uri = 'http://192.168.12.2:5100/api/0.6/'
    id = ''
    s = None

    def tearDown(self):
        time.sleep(3)
    
    def test_0_login(self):
        print('Test login api endpoint')
        s = requests.Session()
        r = s.get(self.__class__.uri + 'login', auth=('admin','admin'))

        self.assertEqual(r.status_code, 200)

        self.assertGreater(len(s.cookies.items()), 0)

        self.__class__.s = s

    def test_1_info(self):
        print('Test info api endpoint')

        s = self.__class__.s

        r = s.get(self.__class__.uri + 'info')
        
        self.assertEqual(r.status_code, 200)

    def test_2_userinfo(self):
        print('Test userinfo api endpoint')

        s = self.__class__.s

        r = s.get(self.__class__.uri + 'userinfo')

        self.assertEqual(r.status_code, 200)

    def test_4_execution_details(self):
        print('Test execution details api endpoint')
        s = self.__class__.s
        r = s.get(self.__class__.uri + 'execution/' + self.__class__.id)
        self.assertEqual(r.status_code, 200)

    def test_4_service_details(self):
        print('Test service details api aendpoint')
        s = self.__class__.s
        r = s.get(self.__class__.uri + 'execution/' + self.__class__.id)
        sid = r.json()["services"][0]
        r = s.get(self.__class__.uri + 'service/' + str(sid))
        self.assertEqual(r.status_code, 200)

    def test_5_terminate_execution(self):
        print('Test terminate execution api endpoint')
        s = self.__class__.s
        r = s.delete(self.__class__.uri + 'execution/' + self.__class__.id)
        self.assertEqual(r.status_code, 204)

    def test_6_list_all_executions(self):
        print('Test list all executions api endpoint')
        s = self.__class__.s
        r = s.get(self.__class__.uri + 'execution')
        self.assertEqual(r.status_code, 200)

    def test_7_delete_execution(self):
        print('Test delete execution api endpoint')
        s = self.__class__.s
        r = s.delete(self.__class__.uri + 'execution/delete/' + self.__class__.id)
        self.assertEqual(r.status_code, 204)
        

    def test_3_start_execution(self):
        print('Test start execution api endpoint')
        
        data = []

        with open('tf.json', encoding='utf-8') as data_file:
            data = json.loads(data_file.read())
        
        s = self.__class__.s

        r = s.post(self.__class__.uri + 'execution', json={"application": data, "name": "requests"})
        self.assertEqual(r.status_code, 201)
        self.__class__.id = str(r.json()['execution_id'])

if __name__ == '__main__':
        unittest.main()
