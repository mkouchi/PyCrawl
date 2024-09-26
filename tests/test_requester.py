import unittest
from crawler.requester import make_request

class TestRequester(unittest.TestCase):
    def test_make_request_success(self):
        url = 'https://httpbin.org/get'
        response = make_request(url)
        self.assertEqual(response.status_code, 200)

    def test_make_request_failure(self):
        url = 'https://httpbin.org/status/404'
        with self.assertRaises(Exception):
            make_request(url)

if __name__ == '__main__':
    unittest.main()
