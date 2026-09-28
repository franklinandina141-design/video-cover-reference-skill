"""Offline contract tests; no provider credentials or paid requests are used."""
import base64
import http.server
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/generate_with_references.py"
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aF6sAAAAASUVORK5CYII=")


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_POST(self):
        self.server.requests.append((self.path, self.headers.get("Authorization"),
            json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
        self.send_response(self.server.status)
        self.end_headers()
        if self.server.status != 200:
            self.wfile.write(b"private-provider-diagnostic offline-test-key")
            return
        item = {"type": "image_generation_call", "status": "completed",
                "result": base64.b64encode(PNG).decode()}
        event = {"type": "response.completed", "response": {"output": [item]}}
        self.wfile.write(b"data: " + json.dumps(event).encode() + b"\n\ndata: [DONE]\n\n")


class GenerateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.photo = self.root / "person.png"
        self.style = self.root / "style.png"
        self.photo.write_bytes(PNG)
        self.style.write_bytes(PNG)
        self.output = self.root / "cover.png"
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.requests = []
        self.server.status = 200
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith("IMAGE_") and k != "OPENAI_API_KEY"}
        self.env.update(IMAGE_API_KEY="offline-test-key",
                        IMAGE_API_BASE_URL=f"http://127.0.0.1:{self.server.server_port}/v1",
                        IMAGE_HOST_MODEL="test-host", IMAGE_MODEL="test-image")

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def run_helper(self):
        return subprocess.run([sys.executable, str(SCRIPT), "--prompt", "准确标题",
                               "--input-image", str(self.photo), "--input-image", str(self.style),
                               "--output", str(self.output)], env=self.env,
                              text=True, capture_output=True, timeout=10)

    def test_two_real_image_inputs_and_png_output(self):
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.output.read_bytes(), PNG)
        path, auth, payload = self.server.requests[0]
        self.assertEqual(path, "/v1/responses")
        self.assertEqual(auth, "Bearer offline-test-key")
        self.assertEqual(payload["model"], "test-host")
        self.assertEqual(payload["tools"][0]["model"], "test-image")
        self.assertEqual(payload["tools"][0]["quality"], "high")
        content = payload["input"][0]["content"]
        self.assertEqual(content[0]["text"], "准确标题")
        self.assertEqual(len(content), 3)
        for item in content[1:]:
            self.assertEqual(base64.b64decode(item["image_url"].split(",", 1)[1]), PNG)

    def test_missing_configuration_fails_before_network(self):
        self.env.pop("IMAGE_HOST_MODEL")
        result = self.run_helper()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("IMAGE_HOST_MODEL", result.stderr)
        self.assertEqual(self.server.requests, [])

    def test_existing_output_is_not_overwritten(self):
        self.output.write_bytes(b"keep existing work")
        result = self.run_helper()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.output.read_bytes(), b"keep existing work")
        self.assertEqual(self.server.requests, [])

    def test_http_error_is_redacted_and_not_retried(self):
        self.server.status = 524
        result = self.run_helper()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("HTTP 524", result.stderr)
        self.assertNotIn("private-provider-diagnostic", result.stderr)
        self.assertNotIn("offline-test-key", result.stderr)
        self.assertEqual(len(self.server.requests), 1)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
