# ChatBot/WebAPI.py
"""
HTTP backend for the React chat widget.

Wraps the same host logic used by Main.py (LLM connection, session context,
MCP tool-use loop, interaction logging) behind two endpoints:

    POST /chat  -> { session_id, mensaje }  ->  { respuesta, tools_usadas }
    GET  /log   -> last N MCP interactions

Run from the project root (src/):
    python -m uvicorn ChatBot.WebAPI:app --port 8500
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .Config import MODEL, MAX_TOKENS, SYSTEM_PROMPT, STDIO_SERVERS, HTTP_SERVERS
from .MCP_Client import MCPManager
from .Logger import read_log

# --------------------------------------------------------------------------
# Setup (order matters: env vars first, then the clients that read them)
# --------------------------------------------------------------------------

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

if not os.environ.get("ANTHROPIC_API_KEY"):
    sys.exit("Falta ANTHROPIC_API_KEY. Revisa tu archivo .env")

client_llm = anthropic.Anthropic(
    default_headers={
        "anthropic-workspace-id": os.environ["ANTHROPIC_WORKSPACE_ID"]
    }
)
manager = MCPManager()
sesiones: dict[str, list] = {}   # session_id -> messages (session context)

ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: connect every configured MCP server once
    for name, cmd in STDIO_SERVERS.items():
        manager.connect_stdio(name, cmd)
    for name, url in HTTP_SERVERS.items():
        manager.connect_http(name, url)
    print(f"[startup] {len(manager.tools_mcp)} tools: "
          f"{', '.join(t['name'] for t in manager.tools_mcp)}")
    yield
    # shutdown: terminate MCP subprocesses
    manager.close_all()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------

class ChatRequest(BaseModel):
    session_id: str
    mensaje: str


@app.post("/chat")
def chat(req: ChatRequest):
    if not req.mensaje.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    messages = sesiones.setdefault(req.session_id, [])
    messages.append({"role": "user", "content": req.mensaje})

    tools_usadas = []
    try:
        while True:
            respuesta = client_llm.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=messages,
                tools=manager.anthropic_tools(),
            )
            messages.append({"role": "assistant", "content": respuesta.content})

            if respuesta.stop_reason != "tool_use":
                texto = "\n".join(
                    b.text for b in respuesta.content if b.type == "text"
                )
                return {"respuesta": texto, "tools_usadas": tools_usadas}

            resultados = []
            for bloque in respuesta.content:
                if bloque.type == "tool_use":
                    tools_usadas.append({
                        "nombre": bloque.name,
                        "argumentos": bloque.input,
                    })
                    resultados.append({
                        "type": "tool_result",
                        "tool_use_id": bloque.id,
                        "content": manager.call_tool(bloque.name, bloque.input),
                    })
            # Tool results go back as a *user* message (Anthropic API convention)
            messages.append({"role": "user", "content": resultados})

    except anthropic.APIError as e:
        # Roll back this turn so a failed call doesn't corrupt the history
        sesiones[req.session_id] = messages[:-1] if messages else []
        raise HTTPException(status_code=502, detail=f"Error del LLM: {e}")


@app.get("/log")
def log(n: int = 50):
    return {"lineas": read_log(n)}


@app.get("/tools")
def tools():
    """Useful for the demo: shows which tools are loaded and from which server."""
    return {
        "tools": [
            {"nombre": t["name"], "servidor": manager.tool_routing[t["name"]]}
            for t in manager.tools_mcp
        ]
    }


@app.delete("/sesion/{session_id}")
def reset_sesion(session_id: str):
    """Clears one conversation's context (handy while testing)."""
    sesiones.pop(session_id, None)
    return {"ok": True}