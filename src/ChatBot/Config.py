from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent   # raíz del proyecto

USAR_REMOTO = True   # False = local (stdio), True = remoto (HTTP)

if USAR_REMOTO:
    STDIO_SERVERS = {}
    HTTP_SERVERS = {'farmacia-remota': 'https://farmacia-mcp-247170717560.us-central1.run.app/mcp'}
else:
    STDIO_SERVERS = {
        "farmacia":   [sys.executable, str(BASE_DIR / "Server.py")],
        "filesystem": ["npx", "-y", "@modelcontextprotocol/server-filesystem",
                       str(BASE_DIR / "demo")],
        "git":        ["uvx", "mcp-server-git", "--repository", str(BASE_DIR / "demo")],
    }
    HTTP_SERVERS = {}
# Servidores MCP locales (subproceso, transporte stdio)
# STDIO_SERVERS = {
#     "farmacia":   [sys.executable, str(BASE_DIR / "Server.py")],
#     "filesystem": ["npx", "-y", "@modelcontextprotocol/server-filesystem",
#                    str(BASE_DIR / "demo")],
#     "git":        ["uvx", "mcp-server-git", "--repository", str(BASE_DIR / "demo")],
# }

# # Servidores MCP remotos (HTTP)
# HTTP_SERVERS = {'farmacia-remota': 'https://farmacia-mcp-247170717560.us-central1.run.app/mcp'}

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 500

SYSTEM_PROMPT = (
    "Eres el asistente de redes sociales de una marca de productos farmacéuticos. "
    "Usa las herramientas MCP para consultar la información oficial de productos. "
    "Nunca inventes dosis ni interacciones: si la información no está en la FAQ, "
    "recomienda consultar con un farmacéutico."
)

LOG_FILE = BASE_DIR / "logs" / "mcp_interactions.log"