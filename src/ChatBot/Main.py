"""

Setup:
    pip install anthropic python-dotenv
    export ANTHROPIC_API_KEY=sk-ant-...      (or put it in a .env file)
    python3 ServerHTTP.py 8000 &             (start the remote server first)
    python3 chatbot_main.py
"""

import os
import sys
from pathlib import Path
from config import STDIO_SERVERS, HTTP_SERVERS, MODEL, SYSTEM_PROMPT

import anthropic

from MCP_Client import MCPManager
from Logger import LOG_FILE

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional; the env var may already be set

BASE_DIR = Path(__file__).resolve().parent


def process_turn(client_llm, manager, messages) -> None:
    """One conversation turn, looping while the model keeps requesting tools."""
    while True:
        response = client_llm.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=manager.anthropic_tools(),
        )
        # Store the assistant turn exactly as returned (context, requirement 2)
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            for block in response.content:
                if block.type == "text":
                    print(f"\nBot: {block.text}\n")
            return

        tool_results = []
        for block in response.content:
            if block.type == "text" and block.text.strip():
                print(f"\nBot (thinking): {block.text}")
            if block.type == "tool_use":
                print(f"[tool] {block.name}({json.dumps(block.input, ensure_ascii=False)})")
                result_text = manager.call_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_text,
                })
        # Tool results go back as a *user* message (Anthropic API convention)
        messages.append({"role": "user", "content": tool_results})


def show_log(n: int = 20) -> None:
    path = Path(LOG_FILE)
    if not path.exists():
        print("(no MCP interactions logged yet)")
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    print(f"--- last {min(n, len(lines))} MCP interactions ---")
    for line in lines[-n:]:
        print(line)
    print("---")


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY (env var or .env file) before running.")

    client_llm = anthropic.Anthropic()
    manager = MCPManager()

    print("Connecting to MCP servers...")
    for name, command in STDIO_SERVERS.items():
        manager.connect_stdio(name, command)
    for name, url in HTTP_SERVERS.items():
        manager.connect_http(name, url)
    print(f"Ready. {len(manager.tools_mcp)} tools available: "
          f"{', '.join(t['name'] for t in manager.tools_mcp)}")
    print("Commands: /log (show MCP log), /exit\n")

    messages = []  # session context lives here (requirement 2)
    try:
        while True:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("/exit", "exit", "salir"):
                break
            if user_input.lower() == "/log":
                show_log()
                continue
            messages.append({"role": "user", "content": user_input})
            process_turn(client_llm, manager, messages)
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        manager.close_all()
        print("\nBye.")


import json  # used in process_turn for pretty-printing tool inputs

main()
