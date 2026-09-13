import http.server
import json
import threading
from pathlib import Path
from harpy.cph import dispatch_to_cph, write_cph_file
from harpy.models import ProblemSpec, TestCase


def test_write_cph_file(tmp_path: Path):
    sol_file = tmp_path / "solution.cpp"
    sol_file.write_text("int main() { return 0; }", encoding="utf-8")

    spec = ProblemSpec(
        title="Test Problem",
        testcases=[
            TestCase(id=1, input="1 2\n", output="3\n"),
        ],
    )

    cph_file = write_cph_file(spec, sol_file)
    assert cph_file.exists()
    assert cph_file.parent == tmp_path / ".cph"

    content = json.loads(cph_file.read_text(encoding="utf-8"))
    assert content["name"] == "Test Problem"
    assert content["srcPath"] == str(sol_file.resolve())
    assert len(content["tests"]) == 1
    assert content["tests"][0]["input"] == "1 2\n"


def test_dispatch_to_cph():
    received_payload = {}

    class MockHandler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len)
            received_payload.update(json.loads(body.decode("utf-8")))
            self.send_response(200)
            self.end_headers()

        def log_message(self, format, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), MockHandler)
    port = server.server_port
    server_thread = threading.Thread(target=server.handle_request, daemon=True)
    server_thread.start()

    spec = ProblemSpec(
        title="HTTP Test",
        testcases=[TestCase(id=1, input="abc\n", output="def\n")],
    )

    result = dispatch_to_cph(spec, ports=[port], timeout=2.0)
    server.server_close()

    assert result["success"] is True
    assert result["port"] == port
    assert received_payload["name"] == "HTTP Test"
