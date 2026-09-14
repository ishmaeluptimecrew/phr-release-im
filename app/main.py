"""PHR API — the artifact the Release Gate is built to protect.

Public Health Research record service. Deliberately small: the point of Week 8.4
is the gate around the artifact, not the artifact itself. Standard library only,
so the image builds in seconds and runs on any Python base image.

Routes:
    GET /            landing page — gives the ZAP spider something to crawl
    GET /healthz     liveness probe — the smoke test hits this
    GET /api/records de-identified research records
    GET /api/error   deliberately raises — leaks a stack trace for ZAP to find
"""

import json
import os
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer

VERSION = os.environ.get("APP_VERSION", "1.2.4")

# Challenge 07 sets this to simulate the release that boots fine and then serves
# errors to everybody. The container starts, the port binds, `docker ps` looks
# perfect — and every request 500s. "Did it start" and "does it work" are
# different questions, and only one of them is worth gating on.
BREAK_HEALTHZ = os.environ.get("PHR_BREAK_HEALTHZ") == "1"

# Response headers sent on every request.
#
# Empty. This is what OWASP ZAP Baseline is going to complain about in
# Challenge 06 — and it is exactly the deck's point: neither Semgrep nor Trivy
# can see this, because at rest it is an empty dict and nothing more. The flaw
# only exists in the running app.
SECURITY_HEADERS = {}

RECORDS = [
    {"record_id": "phr-0001", "cohort": "respiratory-2026", "age_band": "30-39"},
    {"record_id": "phr-0002", "cohort": "respiratory-2026", "age_band": "40-49"},
    {"record_id": "phr-0003", "cohort": "cardiac-2026", "age_band": "50-59"},
]

LANDING_PAGE = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>PHR API</title></head>
<body>
  <h1>Public Health Research API</h1>
  <ul>
    <li><a href="/healthz">/healthz</a></li>
    <li><a href="/api/records">/api/records</a></li>
    <li><a href="/api/error">/api/error</a></li>
  </ul>
</body>
</html>
"""


class PHRHandler(BaseHTTPRequestHandler):
    # Do not advertise the runtime in the Server header. ZAP raises rule 10036
    # ("Server leaks version information") otherwise, and that is not the lesson
    # Challenge 06 is teaching — the missing headers are.
    server_version = "phr-api"
    sys_version = ""

    def version_string(self):
        return self.server_version

    def _respond(self, status, body, content_type):
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(payload)

    def _json(self, status, payload):
        self._respond(status, json.dumps(payload), "application/json")

    def do_GET(self):
        route = self.path.split("?", 1)[0]

        if route == "/":
            self._respond(200, LANDING_PAGE, "text/html; charset=utf-8")
        elif route == "/healthz":
            if BREAK_HEALTHZ:
                self._json(500, {"status": "degraded", "version": VERSION})
            else:
                self._json(200, {"status": "ok", "version": VERSION})
        elif route == "/api/records":
            self._json(200, {"count": len(RECORDS), "records": RECORDS})
        elif route == "/api/error":
            # The deck's "GET /api/error?x=1 returns full Python stack trace".
            # A verbose 500 is an information leak: it hands an attacker your
            # file paths, your framework, and your line numbers.
            try:
                raise RuntimeError("record lookup failed for cohort=respiratory-2026")
            except RuntimeError:
                self._respond(500, traceback.format_exc(), "text/plain; charset=utf-8")
        else:
            self._json(404, {"error": "not found", "path": route})

    def do_HEAD(self):
        # ZAP sends HEAD while spidering. Without this, BaseHTTPRequestHandler
        # answers 501 through send_error(), which bypasses _respond() and so
        # would ship a response with none of the security headers on it.
        self.do_GET()

    def log_message(self, fmt, *args):
        # One tidy line per request. Keeps the Actions log readable while ZAP
        # spiders the app.
        print("%s - %s" % (self.address_string(), fmt % args))


def main():
    port = int(os.environ.get("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), PHRHandler)
    print("phr-api %s listening on 0.0.0.0:%d" % (VERSION, port))
    server.serve_forever()


if __name__ == "__main__":
    main()
