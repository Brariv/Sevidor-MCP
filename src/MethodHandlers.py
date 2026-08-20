# ---------------------------------------------------------------------------
# Method handlers
# ---------------------------------------------------------------------------

import sys
from Json_RPC_Plumbing import send_result, send_error, INVALID_PARAMS, METHOD_NOT_FOUND, INTERNAL_ERROR, log
from QandA import call_tool
from Tools import TOOLS

SERVER_INFO = {"name": "faq-mcp-manual", "version": "1.0.0"}
PROTOCOL_VERSION = "2025-06-18"

class ToolNotFound(Exception):
    """Raised when a tool is not found."""
    pass

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
    except ToolNotFound as e:
        send_error(msg_id, METHOD_NOT_FOUND, str(e))      # -32601
    except ValueError as e:
        send_error(msg_id, INVALID_PARAMS, str(e))        # -32602
    except Exception as e:
        send_error(msg_id, INTERNAL_ERROR, f"Tool execution failed: {e}")  # -32603

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

