"""API regression checks using a temporary database, without touching PostgreSQL."""

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import ClassVar, TextIO
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ApiTests(unittest.TestCase):
    directory: ClassVar[tempfile.TemporaryDirectory[str]]
    base: ClassVar[str]
    log_path: ClassVar[Path]
    log_file: ClassVar[TextIO]
    server: ClassVar[subprocess.Popen[bytes]]

    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        cls.base = f"http://127.0.0.1:{port}"
        env = dict(os.environ, DATABASE_URL=f"sqlite:///{cls.directory.name}/test.db")
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=Path(__file__).resolve().parents[1],
            env=env,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        cls.log_path = Path(cls.directory.name) / "server.log"
        cls.log_file = cls.log_path.open("w")
        cls.server = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--port", str(port)],
            cwd=Path(__file__).resolve().parents[1],
            env=env,
            stdout=cls.log_file,
            stderr=cls.log_file,
        )
        for _ in range(100):
            try:
                cls.request("GET", "/tasks")
                return
            except URLError:
                if cls.server.poll() is not None:
                    break
                time.sleep(0.1)
        cls.server.terminate()
        cls.server.wait()
        cls.log_file.close()
        cls.directory.cleanup()
        raise RuntimeError("Test server did not start")

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()
        cls.server.wait(timeout=10)
        cls.log_file.close()
        cls.directory.cleanup()

    @classmethod
    def request(cls, method, path, data=None, headers=None):
        headers = dict(headers or {})
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = Request(
            cls.base + path,
            method=method,
            headers=headers,
            data=json.dumps(data).encode() if data is not None else None,
        )
        try:
            response = urlopen(request, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            raw = response.read()
            body = None
            if raw:
                body = (
                    json.loads(raw)
                    if "application/json" in response.headers.get("Content-Type", "")
                    else raw.decode()
                )
            return response.status, body, response.headers

    def test_crud(self):
        for path, field, label in [
            ("/tasks", "title", "Task"),
            ("/categories", "name", "Category"),
        ]:
            with self.subTest(path=path):
                self.assertEqual(self.request("GET", path)[:2], (200, []))
                status, item, _ = self.request("POST", path, {field: "Проверка"})
                self.assertEqual(status, 201)
                self.assertEqual(item[field], "Проверка")
                if path == "/tasks":
                    self.assertFalse(item["completed"])
                url = path + "/" + item["id"]
                patch: dict[str, str | bool] = {field: "Изменено"}
                if path == "/tasks":
                    patch["completed"] = True
                status, updated, _ = self.request("PATCH", url, patch)
                self.assertEqual(status, 200)
                for key, value in patch.items():
                    self.assertEqual(updated[key], value)
                self.assertEqual(self.request("PATCH", url, {field: None})[1], updated)
                self.assertEqual(self.request("GET", path)[1], [updated])
                self.assertEqual(self.request("DELETE", url)[:2], (204, None))
                self.assertEqual(self.request("GET", path)[1], [])
                missing_requests: list[tuple[str, dict[str, str] | None]] = [
                    ("PATCH", {}),
                    ("DELETE", None),
                ]
                for method, data in missing_requests:
                    self.assertEqual(
                        self.request(method, url, data)[:2],
                        (404, {"detail": f"{label} not found"}),
                    )
                self.assertEqual(self.request("POST", path, {})[0], 422)

    def test_name_validation(self):
        for path, field in [("/tasks", "title"), ("/categories", "name")]:
            with self.subTest(path=path):
                for value in ["", "   ", "\t\n"]:
                    self.assertEqual(self.request("POST", path, {field: value})[0], 422)
                status, item, _ = self.request("POST", path, {field: "  Название  "})
                self.assertEqual(status, 201)
                self.assertEqual(item[field], "Название")
                url = path + "/" + item["id"]
                try:
                    for value in ["", "   ", "\t\n"]:
                        self.assertEqual(
                            self.request("PATCH", url, {field: value})[0], 422
                        )
                    status, updated, _ = self.request(
                        "PATCH", url, {field: "  Новое  "}
                    )
                    self.assertEqual(status, 200)
                    self.assertEqual(updated[field], "Новое")
                finally:
                    self.request("DELETE", url)

    def test_logging_is_connected(self):
        self.request("GET", "/logging-check-missing")
        log = self.log_path.read_text()
        self.assertIn("app.middleware", log)
        self.assertIn("GET /logging-check-missing -> 404", log)

    def test_request_numbers(self):
        first = int(self.request("GET", "/tasks")[2]["X-Request-Number"])
        responses = [
            self.request("GET", "/categories"),
            self.request("GET", "/missing"),
            self.request("POST", "/tasks", {}),
            self.request(
                "OPTIONS",
                "/tasks",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                },
            ),
        ]
        self.assertEqual([r[0] for r in responses], [200, 404, 422, 200])
        self.assertEqual(
            [int(r[2]["X-Request-Number"]) for r in responses],
            list(range(first + 1, first + 5)),
        )
        with ThreadPoolExecutor(max_workers=8) as executor:
            responses = list(
                executor.map(lambda _: self.request("GET", "/tasks"), range(16))
            )
        self.assertEqual(
            sorted(int(r[2]["X-Request-Number"]) for r in responses),
            list(range(first + 5, first + 21)),
        )

    def test_routes_and_cors(self):
        for method, data in [("GET", None), ("POST", {"book": "test"})]:
            self.assertEqual(self.request(method, "/book", data)[0], 404)
        paths = self.request("GET", "/openapi.json")[1]["paths"]
        self.assertEqual(
            set(paths),
            {"/tasks", "/tasks/{task_id}", "/categories", "/categories/{category_id}"},
        )
        for method in ["POST", "PATCH", "DELETE"]:
            status, _, headers = self.request(
                "OPTIONS",
                "/tasks",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": method,
                    "Access-Control-Request-Headers": "content-type",
                },
            )
            self.assertEqual(status, 200)
            self.assertEqual(
                headers["Access-Control-Allow-Origin"], "http://localhost:3000"
            )


if __name__ == "__main__":
    unittest.main()
