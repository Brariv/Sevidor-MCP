import json
import sys
from datetime import datetime
from .Config import LOG_FILE

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def log_mcp(server: str, direction: str, payload: dict) -> None:
    """Registra un mensaje JSON-RPC. direction: '-->' o '<--'."""
    line = (
        f"[{datetime.now().isoformat(timespec='seconds')}] "
        f"[{server}] {direction} {json.dumps(payload, ensure_ascii=False)}"
    )
    print(line, file=sys.stderr)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def log_llm(role: str, content: str) -> None:
    """Opcional: registrar también los turnos con el LLM."""
    ...


def read_log(n: int = 20) -> list[str]:
    """Últimas n líneas, para el comando /log del chatbot."""
    if not LOG_FILE.exists():
        return []
    return LOG_FILE.read_text(encoding="utf-8").splitlines()[-n:]