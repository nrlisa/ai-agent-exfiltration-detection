
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import hashlib
import json

HOST = "127.0.0.1"
PORT = 8080
LOG_PATH = Path("poc-data/receiver-logs/transfers.jsonl")
MAX_BODY_SIZE = 1024 * 1024  # 1 MiB


class ReceiverHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/transfer":
            self.send_error(404, "Unknown endpoint")
            return

        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            length = -1

        if length < 0 or length > MAX_BODY_SIZE:
            self.send_error(413, "Invalid or oversized request body")
            return

        body = self.rfile.read(length)
        record = {
            "received_at": datetime.now(timezone.utc).isoformat(),
            "path": self.path,
            "bytes_received": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        }

        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(record) + "\n")

        response = json.dumps({
            "status": "accepted",
            "bytes_received": len(body),
            "sha256": record["sha256"],
        }).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

        print(json.dumps(record))

    def log_message(self, format_string, *args):
        print(f"[HTTP] {self.address_string()} - {format_string % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), ReceiverHandler)
    print(f"Receiver listening on http://{HOST}:{PORT}")
    print(f"Transfer log: {LOG_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nReceiver stopping.")
    finally:
        server.server_close()
