#!/usr/bin/env python3
"""
Minimal MCP test client (manual JSON-RPC, no SDK).

Launches the weather server as a subprocess and speaks JSON-RPC to it
over stdin/stdout, the same way Claude Desktop or your chatbot host would.

Usage:  python3 test_client.py
"""

import json
import subprocess
import sys
import os
from pathlib import Path

SERVER_PATH = Path(__file__).resolve().parent.parent / "src" / "Server.py"
SERVER_CMD = [sys.executable, str(SERVER_PATH)]

# SERVER_CMD = [
#     sys.executable,
#     os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "Server.py"),
# ]


class MCPClient:
    def __init__(self, cmd):
        # stderr=None lets the server's debug logs show in your terminal.
        self.proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
            text=True,
            bufsize=1,  # line buffered
        )
        self._next_id = 0

    def _send(self, message: dict) -> None:
        line = json.dumps(message)
        print(f"--> {line}")
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def request(self, method: str, params: dict | None = None) -> dict:
        self._next_id += 1
        self._send({
            "jsonrpc": "2.0",
            "id": self._next_id,
            "method": method,
            "params": params or {},
        })
        line = self.proc.stdout.readline()
        print(f"<-- {line.strip()}\n")
        return json.loads(line)

    def notify(self, method: str, params: dict | None = None) -> None:
        # Notifications have NO "id" and get NO response.
        self._send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def close(self) -> None:
        self.proc.stdin.close()
        self.proc.terminate()
        self.proc.wait(timeout=5)


def main() -> None:
    client = MCPClient(SERVER_CMD)
    try:
        # 1. Handshake
        client.request("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        })
        client.notify("notifications/initialized")

        # 2. Discover tools
        client.request("tools/list")

        # 3. Call a tool
        client.request("tools/call", {
            "name": "get_faq_maxicrez",
            "arguments": {"pregunta": "¿Cuál es el precio del frasco?"},
        })

        # 4. Find close matches
        client.request("tools/call", {
            "name": "get_faq_maxicrez",
            "arguments": {"pregunta": "¿Cuanto Cuesta?"},
        })

        # 5. Find close matches for a question that doesn't exist
        client.request("tools/call", {
            "name": "get_faq_diabelife",
            "arguments": {"pregunta": "¿Cuantas puedo tomar?"},
        })

        # 5.1 Find close matches for a question that doesn't exist
        client.request("tools/call", {
            "name": "get_faq_geriaking_vital",
            "arguments": {"pregunta": "¿Cuáles son los beneficios de las vitaminas?"},
        })

        # 6. Get a the list of questions for a specific product
        client.request("tools/call", {
            "name": "consultar_faq_producto",
            "arguments": {"marca": "maxicrez"},
        })

        # 7. Get the specific question for a specific product
        client.request("tools/call", {
            "name": "get_faq_maxicrez_exacta",
            "arguments": {"pregunta": "¿Cuál es el precio del frasco?"},
        })

        # 8. Error case: unknown tool
        client.request("tools/call", {
            "name": "does_not_exist",
            "arguments": {},
        })
    finally:
        client.close()


if __name__ == "__main__":
    main()