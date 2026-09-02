#!/usr/bin/env python3
"""
MCP client layer for the chatbot host (manual JSON-RPC 2.0, no MCP SDK).

Two transports with the same interface:
- StdioMCPClient: launches a local server as a subprocess (stdin/stdout).
- HTTPMCPClient:  talks to a remote server via HTTP POST (one JSON-RPC
  message per request, notifications answered with 202/empty).

MCPManager coordinates several servers at once and keeps a routing table
tool_name -> server, plus a log of every MCP interaction (requirement 3).
"""

import json
import subprocess
import sys
import urllib.request
from datetime import datetime
from Logger import log_mcp



class StdioMCPClient:
    """Local MCP server launched as a subprocess (newline-delimited JSON)."""

    def __init__(self, name: str, command: list[str]):
        self.name = name
        self.proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        self._next_id = 0

    def request(self, method: str, params: dict | None = None) -> dict:
        self._next_id += 1
        message = {"jsonrpc": "2.0", "id": self._next_id,
                   "method": method, "params": params or {}}
        log_mcp(self.name, "-->", message)
        self.proc.stdin.write(json.dumps(message) + "\n")
        self.proc.stdin.flush()

        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError(f"[{self.name}] server closed the connection.")
            line = line.strip()
            if not line:
                continue
            try:
                response = json.loads(line)
            except json.JSONDecodeError:
                continue  # skip non-protocol noise
            # Skip server-initiated notifications; wait for OUR response
            if response.get("id") != self._next_id:
                continue
            log_mcp(self.name, "<--", response)
            return response

    def notify(self, method: str, params: dict | None = None) -> None:
        message = {"jsonrpc": "2.0", "method": method, "params": params or {}}
        log_mcp(self.name, "-->", message)
        self.proc.stdin.write(json.dumps(message) + "\n")
        self.proc.stdin.flush()

    def close(self) -> None:
        try:
            self.proc.stdin.close()
            self.proc.terminate()
            self.proc.wait(timeout=5)
        except Exception:
            pass


class HTTPMCPClient:
    """Remote MCP server reached via HTTP POST (JSON-RPC in the body)."""

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url  # e.g. http://localhost:8000/mcp
        self._next_id = 0

    def _post(self, message: dict) -> tuple[int, str]:
        data = json.dumps(message, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            self.url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8")

    def request(self, method: str, params: dict | None = None) -> dict:
        self._next_id += 1
        message = {"jsonrpc": "2.0", "id": self._next_id,
                   "method": method, "params": params or {}}
        log_mcp(self.name, "-->", message)
        status, body = self._post(message)
        response = json.loads(body)
        log_mcp(self.name, "<--", response)
        return response

    def notify(self, method: str, params: dict | None = None) -> None:
        message = {"jsonrpc": "2.0", "method": method, "params": params or {}}
        log_mcp(self.name, "-->", message)
        self._post(message)  # expect 202, no body

    def close(self) -> None:
        pass  # HTTP is stateless per request; nothing to tear down


class MCPManager:
    """Connects to several MCP servers and routes tool calls to the right one."""

    def __init__(self):
        self.clients: dict[str, object] = {}
        self.tool_routing: dict[str, str] = {}
        self.tools_mcp: list[dict] = []

    def connect_stdio(self, name: str, command: list[str]) -> None:
        self._handshake(name, StdioMCPClient(name, command))

    def connect_http(self, name: str, url: str) -> None:
        self._handshake(name, HTTPMCPClient(name, url))

    def _handshake(self, name: str, client) -> None:
        client.request("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "chatbot-host", "version": "1.0.0"},
        })
        client.notify("notifications/initialized")
        self.clients[name] = client

        response = client.request("tools/list")
        for tool in response.get("result", {}).get("tools", []):
            if tool["name"] in self.tool_routing:
                print(
                    f"[warn] tool '{tool['name']}' duplicated "
                    f"({self.tool_routing[tool['name']]} vs {name}); keeping first.",
                    file=sys.stderr,
                )
                continue
            self.tool_routing[tool["name"]] = name
            self.tools_mcp.append(tool)

    def anthropic_tools(self) -> list[dict]:
        """MCP tool definitions translated to the Anthropic API format.
        Key detail: MCP uses inputSchema, Anthropic uses input_schema."""
        return [{
            "name": t["name"],
            "description": t.get("description", ""),
            "input_schema": t["inputSchema"],
        } for t in self.tools_mcp]

    def call_tool(self, tool_name: str, arguments: dict) -> str:
        server = self.tool_routing.get(tool_name)
        if server is None:
            return f"[host error] Unknown tool: {tool_name}"
        response = self.clients[server].request("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })
        if "error" in response:
            err = response["error"]
            return f"[server error {err.get('code')}] {err.get('message')}"
        content = response.get("result", {}).get("content", [])
        return "\n".join(
            block.get("text", "") for block in content if block.get("type") == "text"
        ) or "(empty result)"

    def close_all(self) -> None:
        for client in self.clients.values():
            client.close()
