"""Local browser interface for the topic agent; no extra dependencies."""
import argparse
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path

from wiki_agent import ResearchError, TopicAgent, Wikipedia


class Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, source_factory=Wikipedia, **kwargs):
        self.source_factory = source_factory
        super().__init__(*args, **kwargs)

    def respond(self, status, body, content_type="application/json; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path != "/":
            self.respond(404, b'{"error":"Not found"}')
            return
        self.respond(200, Path(__file__).with_name("index.html").read_bytes(),
                     "text/html; charset=utf-8")

    def do_POST(self):
        if self.path != "/api/explain":
            self.respond(404, b'{"error":"Not found"}')
            return
        trace = []
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 8192:
                raise ValueError("Please submit a topic of up to 500 characters.")
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict) or not isinstance(payload.get("topic"), str):
                raise ValueError("A text topic is required.")
            answer = TopicAgent(self.source_factory(), trace.append).explain(payload["topic"])
            result, status = {"answer": answer, "trace": trace}, 200
        except (ValueError, UnicodeDecodeError) as exc:
            result, status = {"error": str(exc), "trace": trace}, 400
        except ResearchError as exc:
            result, status = {"error": str(exc), "trace": trace}, 502
        self.respond(status, json.dumps(result).encode())


def main():
    parser = argparse.ArgumentParser(description="Start the topic agent browser interface")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Topic interface listening on {args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
