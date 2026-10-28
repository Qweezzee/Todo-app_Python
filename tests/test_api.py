"""API regression checks using a temporary database, without touching PostgreSQL."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        cls.base = f'http://127.0.0.1:{port}'
        env = dict(os.environ, DATABASE_URL=f'sqlite:///{cls.directory.name}/test.db')
        cls.server = subprocess.Popen(
            [sys.executable, '-m', 'uvicorn', 'main:app', '--port', str(port)],
            cwd=Path(__file__).resolve().parents[1], env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        for _ in range(100):
            try:
                cls.request('GET', '/tasks')
                return
            except URLError:
                if cls.server.poll() is not None:
                    break
                time.sleep(0.1)
        cls.server.terminate()
        cls.server.wait()
        cls.directory.cleanup()
        raise RuntimeError('Test server did not start')

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()
        cls.server.wait(timeout=10)
        cls.directory.cleanup()

    @classmethod
    def request(cls, method, path, data=None, headers=None):
        headers = dict(headers or {})
        if data is not None:
            headers['Content-Type'] = 'application/json'
        request = Request(cls.base + path, method=method, headers=headers,
                          data=json.dumps(data).encode() if data is not None else None)
        try:
            response = urlopen(request, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            raw = response.read()
            body = None
            if raw:
                body = json.loads(raw) if 'application/json' in response.headers.get('Content-Type', '') else raw.decode()
            return response.status, body, response.headers

    def test_crud(self):
        for path, field, label in [('/tasks', 'title', 'Task'), ('/categories', 'name', 'Category')]:
            with self.subTest(path=path):
                self.assertEqual(self.request('GET', path)[:2], (200, []))
                status, item, _ = self.request('POST', path, {field: 'Проверка'})
                self.assertEqual(status, 201)
                self.assertEqual(item[field], 'Проверка')
                if path == '/tasks':
                    self.assertFalse(item['completed'])
                url = path + '/' + item['id']
                patch = {field: 'Изменено'}
                if path == '/tasks':
                    patch['completed'] = True
                status, updated, _ = self.request('PATCH', url, patch)
                self.assertEqual(status, 200)
                for key, value in patch.items():
                    self.assertEqual(updated[key], value)
                self.assertEqual(self.request('PATCH', url, {field: None})[1], updated)
                self.assertEqual(self.request('GET', path)[1], [updated])
                self.assertEqual(self.request('DELETE', url)[:2], (204, None))
                self.assertEqual(self.request('GET', path)[1], [])
                for method, data in [('PATCH', {}), ('DELETE', None)]:
                    self.assertEqual(self.request(method, url, data)[:2],
                                     (404, {'detail': f'{label} not found'}))
                self.assertEqual(self.request('POST', path, {})[0], 422)

    def test_routes_and_cors(self):
        for method, data in [('GET', None), ('POST', {'book': 'test'})]:
            self.assertEqual(self.request(method, '/book', data)[0], 404)
        paths = self.request('GET', '/openapi.json')[1]['paths']
        self.assertEqual(set(paths), {'/tasks', '/tasks/{task_id}', '/categories', '/categories/{category_id}'})
        for method in ['POST', 'PATCH', 'DELETE']:
            status, _, headers = self.request('OPTIONS', '/tasks', headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': method,
                'Access-Control-Request-Headers': 'content-type',
            })
            self.assertEqual(status, 200)
            self.assertEqual(headers['Access-Control-Allow-Origin'], 'http://localhost:3000')


if __name__ == '__main__':
    unittest.main()
