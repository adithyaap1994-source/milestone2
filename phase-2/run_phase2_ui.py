from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
PROJECT_ROOT = ROOT.parent
STATIC_UI_DIR = ROOT / "basic-ui"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from phase2_compliance.chat_service import ComplianceChatService  # noqa: E402


THREAD_STORE_PATH = ROOT / "data" / "threads.json"
SERVICE = ComplianceChatService(project_root=PROJECT_ROOT, thread_store_path=THREAD_STORE_PATH)


class Phase2UIHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, file_path: Path, content_type: str) -> None:
        if not file_path.exists() or not file_path.is_file():
            self.send_error(404, "Not Found")
            return
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_file(STATIC_UI_DIR / "index.html", "text/html; charset=utf-8")
            return
        if parsed.path == "/styles.css":
            self._send_file(STATIC_UI_DIR / "styles.css", "text/css; charset=utf-8")
            return
        if parsed.path == "/app.js":
            self._send_file(STATIC_UI_DIR / "app.js", "application/javascript; charset=utf-8")
            return
        if parsed.path == "/health":
            self._send_json({"service": "phase-2-api", "status": "ok"}, status=200)
            return
        if parsed.path.startswith("/api/thread/"):
            thread_id = parsed.path.split("/api/thread/", 1)[1].strip()
            if not thread_id:
                self._send_json({"error": "thread_id_required"}, status=400)
                return
            thread_state = SERVICE.store.get_thread(thread_id)
            self._send_json(
                {
                    "thread_id": thread_state.thread_id,
                    "messages": [
                        {
                            "thread_id": m.thread_id,
                            "role": m.role,
                            "content": m.content,
                            "intent": m.intent,
                            "policy_decision": m.policy_decision,
                            "citations": m.citations,
                        }
                        for m in thread_state.messages
                    ],
                }
            )
            return
        self.send_error(404, "Not Found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/thread":
            thread_id = str(uuid4())
            SERVICE.store.create_thread(thread_id)
            self._send_json({"thread_id": thread_id}, status=201)
            return

        if parsed.path == "/api/chat":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._send_json({"error": "invalid_content_length"}, status=400)
                return
            raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
            try:
                payload = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                self._send_json({"error": "invalid_json"}, status=400)
                return

            thread_id = (payload.get("thread_id") or "").strip()
            query = (payload.get("query") or "").strip()
            if not thread_id or not query:
                self._send_json({"error": "thread_id_and_query_required"}, status=400)
                return

            result = SERVICE.handle_user_message(thread_id=thread_id, user_query=query)
            self._send_json(result, status=200)
            return

        self.send_error(404, "Not Found")


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", 8080), Phase2UIHandler)
    print("Phase 2 API running at http://localhost:8080")
    server.serve_forever()


if __name__ == "__main__":
    main()
