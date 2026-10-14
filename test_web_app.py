import json
import threading
import unittest
from functools import partial
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from test_wiki_agent import FakeSource
from web_app import Handler


class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, source_factory=FakeSource))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, payload):
        return urlopen(Request(self.base + '/api/explain', data=json.dumps(payload).encode(),
                               headers={'Content-Type': 'application/json'}), timeout=5)

    def test_interface_is_served(self):
        with urlopen(self.base, timeout=5) as response:
            self.assertIn(b'What would you like to understand?', response.read())

    def test_topic_returns_answer_and_stages(self):
        with self.request({'topic': 'software engineering'}) as response:
            data = json.load(response)
        self.assertIn('design, testing, and maintenance', data['answer'])
        self.assertTrue(data['trace'][0].startswith('THINK:'))

    def test_invalid_topic_is_reported(self):
        for payload in ({'topic': ''}, {'topic': 42}, [], {'topic': 'a' * 501}):
            with self.subTest(payload=type(payload).__name__):
                with self.assertRaises(HTTPError) as caught:
                    self.request(payload)
                self.assertEqual(caught.exception.code, 400)
                self.assertIn('error', json.load(caught.exception))


if __name__ == '__main__':
    unittest.main()
