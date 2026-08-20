# ---------------------------------------------------------------------------
# JSON-RPC 2.0 plumbing
# ---------------------------------------------------------------------------

import sys
import json

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