"""Exercise the completion checker against a disposable local HTTP server."""

import contextlib
import io
import json
import os
import pathlib
import subprocess
import threading
import unittest
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import check_primes


class CheckerTests(unittest.TestCase):
    def setUp(self):
        self.mode = "complete"
        self.tasks = {}
        self.lock = threading.Lock()
        test = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def respond(self, value):
                body = json.dumps(value).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                with test.lock:
                    task_id = str(uuid.uuid4()) if test.mode != "duplicate" else str(uuid.UUID(int=1))
                    test.tasks[task_id] = {"limit": request["limit"], "polls": 0}
                self.respond({"task_id": task_id})

            def do_GET(self):
                if self.path == "/health":
                    self.respond({"status": "unhealthy" if test.mode == "unhealthy" else "healthy"})
                    return
                task_id = self.path.rsplit("/", 1)[1]
                with test.lock:
                    task = test.tasks[task_id]
                    task["polls"] += 1
                    polls = task["polls"]
                status = "processing" if polls == 1 or test.mode == "pending" else "completed"
                if test.mode == "failed":
                    status = "failed"
                self.respond({
                    "id": task_id,
                    "task_type": "prime",
                    "status": status,
                    "last_error": "handler rejected input",
                    "result": {"limit": task["limit"], "count": 26 if test.mode == "bad_result" else 25, "largest": 97},
                })

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=lambda: self.server.serve_forever(poll_interval=0.01))
        self.thread.start()
        url = f"http://127.0.0.1:{self.server.server_port}"
        self.args = check_primes.parse_args([
            "--api-url", url, "--daemon-url", url, "--limit", "100",
            "--tasks", "4", "--concurrency", "2", "--poll-interval", "0.001", "--timeout", "1",
        ])

    def tearDown(self):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()

    def run_check(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            check_primes.check(self.args)
        return output.getvalue()

    def test_all_submitted_tasks_must_complete_with_correct_results(self):
        output = self.run_check()
        self.assertIn("Verified 4 completed tasks", output)
        self.assertEqual(len(self.tasks), 4)
        self.assertTrue(all(task["polls"] == 2 for task in self.tasks.values()))

    def test_handler_failure_is_reported(self):
        self.mode = "failed"
        with self.assertRaisesRegex(check_primes.CheckError, "handler rejected input"):
            self.run_check()

    def test_wrong_result_is_reported(self):
        self.mode = "bad_result"
        with self.assertRaisesRegex(check_primes.CheckError, "incorrect prime result"):
            self.run_check()

    def test_duplicate_task_ids_are_reported(self):
        self.mode = "duplicate"
        with self.assertRaisesRegex(check_primes.CheckError, "duplicate task ID"):
            self.run_check()

    def test_unhealthy_daemon_does_not_receive_tasks(self):
        self.mode = "unhealthy"
        with self.assertRaisesRegex(check_primes.CheckError, "unhealthy"):
            self.run_check()
        self.assertEqual(self.tasks, {})

    def test_processing_tasks_do_not_pass_the_completion_check(self):
        self.mode = "pending"
        self.args.timeout = 0.1
        with self.assertRaisesRegex(check_primes.CheckError, "deadline"):
            self.run_check()

    def test_invalid_workloads_are_rejected_before_requests(self):
        for argv in (["--limit", "10000000000"], ["--limit", "1"], ["--tasks", "0"], ["--timeout", "nan"]):
            with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    check_primes.parse_args(argv)
                self.assertEqual(raised.exception.code, 2)

    def test_smoke_wrapper_checks_completion_and_propagates_failure(self):
        script = pathlib.Path(__file__).with_name("smoke-test.sh")
        env = dict(os.environ, API_URL=self.args.api_url, DAEMON_URL=self.args.daemon_url)
        for mode, expected_status in (("complete", 0), ("failed", 1)):
            with self.subTest(mode=mode):
                self.mode = mode
                result = subprocess.run([str(script), "--limit", "100", "--poll-interval", "0.001"], env=env, text=True, capture_output=True, timeout=5)
                self.assertEqual(result.returncode, expected_status, result.stdout + result.stderr)
                if mode == "complete":
                    self.assertIn("Verified 1 completed tasks", result.stdout)
                else:
                    self.assertIn("handler rejected input", result.stderr)


if __name__ == "__main__":
    unittest.main()
