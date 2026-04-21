# HTTP -> ZMQ bridge for the WASD GUI.
# POST /command with {"cmd": "W"|"A"|"S"|"D"|"STOP"} -> ZMQ PUSH to motor_loop.

import argparse
import json
import zmq
from http.server import BaseHTTPRequestHandler, HTTPServer


parser = argparse.ArgumentParser(description="HTTP -> ZMQ bridge for the Pacbot GUI")
parser.add_argument("--pi", default="tcp://localhost:5556",
                    help="ZMQ address of motor_loop (default tcp://localhost:5556)")
parser.add_argument("--port", type=int, default=8000,
                    help="HTTP port to listen on (default 8000)")
args = parser.parse_args()

ctx = zmq.Context()
push = ctx.socket(zmq.PUSH)
push.connect(args.pi)


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path != "/command":
            self.send_response(404)
            self._cors()
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        cmd = body.get("cmd", "STOP")
        push.send_string(cmd)
        print(f"-> {cmd}")
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def log_message(self, *_):
        pass  # quiet default access log


print(f"HTTP bridge on :{args.port} -> ZMQ {args.pi}")
try:
    HTTPServer(("0.0.0.0", args.port), Handler).serve_forever()
except KeyboardInterrupt:
    print("\nShutting down bridge...")
finally:
    push.close()
    ctx.term()
