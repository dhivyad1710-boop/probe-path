"""Local server for safe testing:  python tools/test_server.py   (port 9000)
Paths: /ok /redirect /unauthorized /forbidden /error /slow  (anything else = 404)"""
import time
from http.server import BaseHTTPRequestHandler, HTTPServer


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        p = self.path
        if p == "/slow":
            time.sleep(30)
        code = {"/ok": 200, "/redirect": 302, "/unauthorized": 401,
                "/forbidden": 403, "/error": 500, "/slow": 200}.get(p, 404)
        self.send_response(code)
        if code == 302:
            self.send_header("Location", "/ok")
        self.end_headers()
        self.wfile.write(f"ProbePath test server: {code}\n".encode())


if __name__ == "__main__":
    print("Test server on http://localhost:9000")
    HTTPServer(("0.0.0.0", 9000), H).serve_forever()
