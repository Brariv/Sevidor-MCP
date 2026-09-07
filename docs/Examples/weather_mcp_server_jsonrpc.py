#!/usr/bin/env python3
"""
Weather MCP Server - manual JSON-RPC 2.0 implementation (no MCP SDK).

Transport: stdio.
- Reads one JSON-RPC message per line from stdin.
- Writes one JSON-RPC message per line to stdout.
- Never prints anything else to stdout (logs go to stderr).

Reproduces the two tools from the official MCP weather quickstart example
(get_alerts, get_forecast) but hand-rolling the protocol layer, since the
assignment forbids using MCP SDKs/libraries (e.g. the official `mcp` package
or FastMCP).
"""

import sys
import json
import urllib.request

# ---------------------------------------------------------------------------
# Business logic (equivalent to what the SDK example wraps with @mcp.tool())
# ---------------------------------------------------------------------------

NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-mcp-manual/1.0"


def _nws_request(url: str) -> dict | None:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/geo+json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        log(f"NWS request failed: {e}")
        return None


def get_alerts(state: str) -> str:
    """Get active weather alerts for a US state (two-letter code, e.g. CA)."""
    url = f"{NWS_API_BASE}/alerts/active/area/{state.upper()}"
    data = _nws_request(url)
    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."
    if not data["features"]:
        return "No active alerts for this state."

    alerts = []
    for feature in data["features"]:
        props = feature["properties"]
        alerts.append(
            f"Event: {props.get('event', 'Unknown')}\n"
            f"Area: {props.get('areaDesc', 'Unknown')}\n"
            f"Severity: {props.get('severity', 'Unknown')}\n"
            f"Description: {props.get('description', 'No description')}"
        )
    return "\n---\n".join(alerts)


def get_forecast(latitude: float, longitude: float) -> str:
    """Get the weather forecast for a given latitude/longitude."""
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = _nws_request(points_url)
    if not points_data:
        return "Unable to fetch forecast data for this location."

    forecast_url = points_data["properties"]["forecast"]
    forecast_data = _nws_request(forecast_url)
    if not forecast_data:
        return "Unable to fetch detailed forecast."

    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:
        forecasts.append(
            f"{period['name']}:\n"
            f"Temperature: {period['temperature']}°{period['temperatureUnit']}\n"
            f"Wind: {period['windSpeed']} {period['windDirection']}\n"
            f"Forecast: {period['detailedForecast']}"
        )
    return "\n---\n".join(forecasts)


# ---------------------------------------------------------------------------
# Tool registry: JSON Schema definitions exposed via tools/list
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "get_alerts",
        "description": "Get active weather alerts for a US state",
        "inputSchema": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "string",
                    "description": "Two-letter US state code, e.g. CA, NY",
                }
            },
            "required": ["state"],
        },
    },
    {
        "name": "get_forecast",
        "description": "Get the weather forecast for a location",
        "inputSchema": {
            "type": "object",
            "properties": {
                "latitude": {"type": "number"},
                "longitude": {"type": "number"},
            },
            "required": ["latitude", "longitude"],
        },
    },
]


def call_tool(name: str, arguments: dict) -> str:
    if name == "get_alerts":
        return get_alerts(arguments["state"])
    if name == "get_forecast":
        return get_forecast(arguments["latitude"], arguments["longitude"])
    raise ValueError(f"Unknown tool: {name}")


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 plumbing
# ---------------------------------------------------------------------------

# Standard JSON-RPC error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


def log(msg: str) -> None:
    """Debug logging MUST go to stderr, never to stdout (that would corrupt
    the protocol stream)."""
    print(msg, file=sys.stderr, flush=True)


def send(message: dict) -> None:
    """Write a single JSON-RPC message as one line of UTF-8 JSON to stdout."""
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def send_result(msg_id, result) -> None:
    send({"jsonrpc": "2.0", "id": msg_id, "result": result})


def send_error(msg_id, code: int, message: str, data=None) -> None:
    error = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    send({"jsonrpc": "2.0", "id": msg_id, "error": error})


# ---------------------------------------------------------------------------
# Method handlers
# ---------------------------------------------------------------------------

SERVER_INFO = {"name": "weather-mcp-manual", "version": "1.0.0"}
PROTOCOL_VERSION = "2025-06-18"


def handle_initialize(msg_id, params):
    send_result(
        msg_id,
        {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        },
    )


def handle_tools_list(msg_id, params):
    send_result(msg_id, {"tools": TOOLS})


def handle_tools_call(msg_id, params):
    name = params.get("name")
    arguments = params.get("arguments", {})
    try:
        text_result = call_tool(name, arguments)
    except KeyError as e:
        send_error(msg_id, INVALID_PARAMS, f"Missing argument: {e}")
        return
    except ValueError as e:
        send_error(msg_id, METHOD_NOT_FOUND, str(e))
        return
    except Exception as e:
        send_error(msg_id, INTERNAL_ERROR, f"Tool execution failed: {e}")
        return

    send_result(
        msg_id,
        {"content": [{"type": "text", "text": text_result}], "isError": False},
    )


# Requests (expect a response). Notifications (no "id") are handled separately.
REQUEST_HANDLERS = {
    "initialize": handle_initialize,
    "tools/list": handle_tools_list,
    "tools/call": handle_tools_call,
}


def handle_message(message: dict) -> None:
    msg_id = message.get("id")
    method = message.get("method")
    params = message.get("params", {}) or {}

    # Notification: no "id" field -> no response is sent, ever.
    if msg_id is None:
        if method == "notifications/initialized":
            log("Client finished initialization.")
        else:
            log(f"Ignoring unknown notification: {method}")
        return

    handler = REQUEST_HANDLERS.get(method)
    if handler is None:
        send_error(msg_id, METHOD_NOT_FOUND, f"Method not found: {method}")
        return

    handler(msg_id, params)


# ---------------------------------------------------------------------------
# Main loop: one JSON-RPC message per line on stdin
# ---------------------------------------------------------------------------

def main() -> None:
    log("Weather MCP server (manual JSON-RPC) started.")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            send_error(None, PARSE_ERROR, "Invalid JSON was received.")
            continue

        if message.get("jsonrpc") != "2.0":
            send_error(message.get("id"), INVALID_REQUEST, "Invalid JSON-RPC version.")
            continue

        handle_message(message)


if __name__ == "__main__":
    main()
