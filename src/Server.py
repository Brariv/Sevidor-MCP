# ---------------------------------------------------------------------------
# Main loop: one JSON-RPC message per line on stdin
# ---------------------------------------------------------------------------


import json
import sys
from Json_RPC_Plumbing import send_error, PARSE_ERROR, INVALID_REQUEST, log
from MethodHandlers import handle_message

def main() -> None:
    log("FAQ MCP server (manual JSON-RPC) started.")
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

main()