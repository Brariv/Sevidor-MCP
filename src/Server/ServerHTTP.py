#!/usr/bin/env python3
"""
Pharmacy MCP Server - REMOTE version (manual JSON-RPC 2.0 over HTTP, no MCP SDK).

This file is ONLY the transport layer. All business logic (TOOLS, call_tool,
the FAQ dataframe, the fuzzy matching) is imported from Tools.py and shared
with the local stdio server - so both servers expose exactly the same tools
and behave identically, as required by the assignment.

Transport:
- POST /mcp with a JSON-RPC message in the body -> JSON-RPC response (HTTP 200)
- Notifications (no "id")                       -> HTTP 202, empty body
- Invalid JSON                                  -> HTTP 400 + error -32700
- GET /health                                   -> plain "ok" (cloud health checks)

Run locally:
    python3 ServerHTTP.py 8000

Cloud Run / containers read the port from the PORT environment variable.

Test:
    curl -X POST http://localhost:8000/mcp \
         -H "Content-Type: application/json" \
         -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
"""

import os
import sys
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Business logic shared with the local server.
# Adjust this import to match your project layout, e.g.:
#   from server.Tools import TOOLS, call_tool, ToolNotFound
# Tools.py is one directory above this file. Add that directory to the import
# path so the server also works when launched directly as `python ServerHTTP.py`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Tools import TOOLS
from QandA import call_tool, ToolNotFound

# ---------------------------------------------------------------------------
# JSON-RPC 2.0 layer (identical semantics to the stdio server)
# ---------------------------------------------------------------------------

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

SERVER_INFO = {"name": "farmacia-mcp-remote", "version": "1.0.0"}
PROTOCOL_VERSION = "2025-06-18"


def log(msg: str) -> None:
    """Logs go to stderr. Cloud Run captures stderr automatically."""
    print(msg, file=sys.stderr, flush=True)


def make_result(msg_id, result) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def make_error(msg_id, code, message) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def process_message(message: dict) -> dict | None:
    """Handle one JSON-RPC message.
    Returns the response dict, or None for notifications (never answered)."""
    msg_id = message.get("id")
    method = message.get("method")
    params = message.get("params", {}) or {}

    if message.get("jsonrpc") != "2.0":
        return make_error(msg_id, INVALID_REQUEST, "Invalid JSON-RPC version.")

    # Notification: no "id" -> no response
    if msg_id is None:
        if method == "notifications/initialized":
            log("Client finished initialization.")
        else:
            log(f"Ignoring unknown notification: {method}")
        return None

    if method == "initialize":
        return make_result(msg_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        })

    if method == "ping":
        return make_result(msg_id, {})

    if method == "tools/list":
        return make_result(msg_id, {"tools": TOOLS})

    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments", {}) or {}
        try:
            text = call_tool(name, arguments)
        except ToolNotFound as e:
            return make_error(msg_id, METHOD_NOT_FOUND, str(e))
        except ValueError as e:
            return make_error(msg_id, INVALID_PARAMS, str(e))
        except Exception as e:
            log(f"Tool execution failed: {type(e).__name__}: {e}")
            return make_error(msg_id, INTERNAL_ERROR, f"Tool execution failed: {e}")
        return make_result(msg_id, {
            "content": [{"type": "text", "text": text}],
            "isError": False,
        })

    return make_error(msg_id, METHOD_NOT_FOUND, f"Method not found: {method}")


# ---------------------------------------------------------------------------
# HTTP transport
# ---------------------------------------------------------------------------

class MCPHTTPHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"  # keep-alive: fewer TCP handshakes in Wireshark

    def do_GET(self):
        if self.path in ("/health", "/"):
            body = b"ok"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self._send_json(404, make_error(None, INVALID_REQUEST, "Use POST /mcp"))

    def do_POST(self):
        if self.path != "/mcp":
            self._send_json(404, make_error(None, INVALID_REQUEST, "Use POST /mcp"))
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            message = json.loads(body)
        except (ValueError, json.JSONDecodeError):
            self._send_json(400, make_error(None, PARSE_ERROR, "Invalid JSON was received."))
            return

        log(f"--> {json.dumps(message, ensure_ascii=False)}")
        response = process_message(message)

        if response is None:
            # Notification: acknowledge, no body
            self.send_response(202)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        log(f"<-- {json.dumps(response, ensure_ascii=False)}")
        self._send_json(200, response)

    def _send_json(self, status: int, payload: dict):
        # ensure_ascii=False keeps accents readable in Wireshark captures
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        log(f"[http] {fmt % args}")


def main():
    # Cloud Run injects PORT; fall back to argv or 8000 for local runs.
    port = int(os.environ.get("PORT") or (sys.argv[1] if len(sys.argv) > 1 else 8000))
    server = ThreadingHTTPServer(("0.0.0.0", port), MCPHTTPHandler)
    log(f"Pharmacy MCP remote server listening on http://0.0.0.0:{port}/mcp")
    log(f"Tools available: {', '.join(t['name'] for t in TOOLS)}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("Shutting down.")
        server.server_close()

main()