"""Fake exporter for the SLO demo.

Emits http_requests_total{service, code} for each configured service at a fixed
request rate. The share of 5xx responses per service is configurable at start
through environment variables and at runtime through HTTP:

    curl -X POST 'http://localhost:8000/error-rate?service=reservations&value=0.2'
    curl http://localhost:8000/error-rate
"""

import json
import os
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

SERVICES = [name.strip() for name in os.environ.get("SERVICES", "reservations,licensing").split(",") if name.strip()]
REQUESTS_PER_SECOND = float(os.environ.get("REQUESTS_PER_SECOND", "50"))
DEFAULT_ERROR_RATE = float(os.environ.get("ERROR_RATE", "0.0005"))
PORT = int(os.environ.get("PORT", "8000"))
SUCCESS_CODES = ["200", "201", "204"]
ERROR_CODES = ["500", "502", "503"]

lock = threading.Lock()
error_rates = {
    service: float(os.environ.get(f"ERROR_RATE_{service.upper()}", DEFAULT_ERROR_RATE)) for service in SERVICES
}
request_counts = {(service, code): 0 for service in SERVICES for code in SUCCESS_CODES + ERROR_CODES}


def parse_error_rate(raw_value):
    value = float(raw_value)
    if not 0.0 <= value <= 1.0:
        raise ValueError("error rate must be between 0 and 1")
    return value


def generate_traffic():
    while True:
        with lock:
            for service in SERVICES:
                for _ in range(int(REQUESTS_PER_SECOND)):
                    if random.random() < error_rates[service]:
                        code = random.choice(ERROR_CODES)
                    else:
                        code = random.choice(SUCCESS_CODES)
                    request_counts[(service, code)] += 1
        time.sleep(1)


def render_metrics():
    lines = [
        "# HELP http_requests_total Total HTTP requests handled, by service and status code.",
        "# TYPE http_requests_total counter",
    ]
    with lock:
        for (service, code), count in sorted(request_counts.items()):
            lines.append(f'http_requests_total{{service="{service}",code="{code}"}} {count}')
    return "\n".join(lines) + "\n"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/metrics":
            self.respond(200, render_metrics(), "text/plain; version=0.0.4")
        elif path == "/error-rate":
            with lock:
                self.respond_json(200, error_rates)
        else:
            self.respond_json(404, {"error": "not found"})

    def do_POST(self):
        url = urlparse(self.path)
        if url.path != "/error-rate":
            self.respond_json(404, {"error": "not found"})
            return
        query = parse_qs(url.query)
        service = query.get("service", [None])[0]
        raw_value = query.get("value", [None])[0]
        if raw_value is None:
            self.respond_json(400, {"error": "value is required"})
            return
        try:
            value = parse_error_rate(raw_value)
        except ValueError:
            self.respond_json(400, {"error": "value must be a number between 0 and 1"})
            return
        targets = SERVICES if service is None else [service]
        if any(target not in SERVICES for target in targets):
            self.respond_json(400, {"error": f"unknown service, expected one of {SERVICES}"})
            return
        with lock:
            for target in targets:
                error_rates[target] = value
            self.respond_json(200, error_rates)

    def respond_json(self, status, payload):
        self.respond(status, json.dumps(payload) + "\n", "application/json")

    def respond(self, status, body, content_type):
        encoded = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    threading.Thread(target=generate_traffic, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
