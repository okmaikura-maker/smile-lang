"""Smile Web Framework - 軽量HTTPフレームワーク"""

import json
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


class SmileApp:
    def __init__(self, name="SmileApp"):
        self.name = name
        self.routes = {}
        self.static_dir = None

    def route(self, path, methods=None):
        if methods is None:
            methods = ["GET"]
        def decorator(func):
            for method in methods:
                self.routes[(method.upper(), path)] = func
            return func
        return decorator

    def get(self, path):
        return self.route(path, ["GET"])

    def post(self, path):
        return self.route(path, ["POST"])

    def static(self, directory):
        self.static_dir = directory

    def _find_handler(self, method, path):
        handler = self.routes.get((method, path))
        if handler:
            return handler, {}
        for (m, pattern), func in self.routes.items():
            if m != method:
                continue
            regex = re.sub(r':(\w+)', r'(?P<\1>[^/]+)', pattern)
            match = re.fullmatch(regex, path)
            if match:
                return func, match.groupdict()
        return None, {}

    def run(self, host="localhost", port=8080):
        app = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self._handle("GET")

            def do_POST(self):
                self._handle("POST")

            def _handle(self, method):
                parsed = urlparse(self.path)
                path = parsed.path
                query = parse_qs(parsed.query)

                handler, params = app._find_handler(method, path)
                if handler is None and app.static_dir and method == "GET":
                    self._serve_static(path)
                    return
                if handler is None:
                    self.send_response(404)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write("404 - ページが見つかりません".encode("utf-8"))
                    return

                req = Request(self, method, path, query, params)
                res = Response(self)
                try:
                    handler(req, res)
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(f"500 - サーバーエラー: {e}".encode("utf-8"))

            def _serve_static(self, path):
                import os
                filepath = os.path.join(app.static_dir, path.lstrip("/"))
                if os.path.isfile(filepath):
                    ext = os.path.splitext(filepath)[1]
                    content_types = {
                        ".html": "text/html", ".css": "text/css",
                        ".js": "application/javascript", ".json": "application/json",
                        ".png": "image/png", ".jpg": "image/jpeg",
                        ".svg": "image/svg+xml", ".txt": "text/plain",
                    }
                    ct = content_types.get(ext, "application/octet-stream")
                    self.send_response(200)
                    self.send_header("Content-Type", f"{ct}; charset=utf-8")
                    self.end_headers()
                    with open(filepath, "rb") as f:
                        self.wfile.write(f.read())
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):
                print(f"  {args[0]}")

        server = HTTPServer((host, port), Handler)
        print(f"\n  {app.name} サーバー起動")
        print(f"  http://{host}:{port}")
        print(f"  Ctrl+C で停止\n")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nサーバー停止")
            server.server_close()


class Request:
    def __init__(self, handler, method, path, query, params):
        self.method = method
        self.path = path
        self.query = query
        self.params = params
        self._handler = handler

    def body(self):
        length = int(self._handler.headers.get("Content-Length", 0))
        if length > 0:
            return self._handler.rfile.read(length).decode("utf-8")
        return ""

    def json(self):
        return json.loads(self.body())


class Response:
    def __init__(self, handler):
        self._handler = handler
        self._sent = False

    def send(self, text, status=200, content_type="text/html; charset=utf-8"):
        if self._sent:
            return
        self._sent = True
        self._handler.send_response(status)
        self._handler.send_header("Content-Type", content_type)
        self._handler.end_headers()
        if isinstance(text, str):
            text = text.encode("utf-8")
        self._handler.wfile.write(text)

    def html(self, text, status=200):
        self.send(text, status, "text/html; charset=utf-8")

    def json(self, data, status=200):
        self.send(json.dumps(data, ensure_ascii=False), status, "application/json; charset=utf-8")

    def redirect(self, url, status=302):
        self._handler.send_response(status)
        self._handler.send_header("Location", url)
        self._handler.end_headers()
        self._sent = True


def create_app(name="SmileApp"):
    return SmileApp(name)
