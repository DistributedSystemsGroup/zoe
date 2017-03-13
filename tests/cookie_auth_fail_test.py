import requests
import json
import time
import unittest

class ZoeRestTestSuccess(unittest.TestCase):

    uri = 'http://localhost:5001/api/0.7/'
    id = '-1'
    s = None

    def tearDown(self):
        time.sleep(3)
    
    def test_0_login_fail(self):
        print('Test failed login api endpoint')
        s = requests.Session()
        r = s.get(self.__class__.uri + 'login', auth=('test','123'))

        self.assertEqual(r.status_code, 401)

    def test_1_login(self):
        print('Test login api endpoint')

        s = requests.Session()
        r = s.get(self.__class__.uri + 'login', auth=('test','1234'))

        self.assertEqual(r.status_code, 200)

        self.assertGreater(len(s.cookies.items()), 0)

        self.__class__.s = s

    def test_4_execution_details(self):
        print('Test execution details api endpoint')
        s = self.__class__.s
        r = s.get(self.__class__.uri + 'execution/' + self.__class__.id)
        self.assertEqual(r.status_code, 404)

    def test_5_terminate_execution(self):
        print('Test terminate execution api endpoint')
        s = self.__class__.s
        r = s.delete(self.__class__.uri + 'execution/' + self.__class__.id)
        self.assertEqual(r.status_code, 404)

    def test_7_delete_execution(self):
        print('Test delete execution api endpoint')
        s = self.__class__.s
        r = s.delete(self.__class__.uri + 'execution/delete/' + self.__class__.id)
        self.assertEqual(r.status_code, 404)
        

    def test_3_start_execution(self):
        print('Test start execution api endpoint')
        
        s = self.__class__.s

        r = s.post(self.__class__.uri + 'execution', json={"application": "data", "name": "requests"})
        self.assertEqual(r.status_code, 400)

if __name__ == '__main__':
        unittest.main()
