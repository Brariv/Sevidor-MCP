# Chatbot con MCP — Farmacia (FAQ de productos)

Proyecto 1 de Redes (CC3067, UVG). Implementa el ciclo completo del protocolo
**MCP (Model Context Protocol)** sobre **JSON-RPC 2.0 escrito a mano**, sin usar el
SDK oficial:

- un **servidor MCP propio** que expone las FAQ de productos farmacéuticos,
  con dos transportes (stdio local y HTTP remoto);
- un **host/chatbot** que conecta el LLM (Claude) con uno o varios servidores MCP,
  mantiene el contexto de la conversación y registra cada mensaje del protocolo;
- una **UI web** (React + Vite) que simula la tienda con un widget de chat.

---

## Arquitectura

```
   Navegador (UI React)
        │  POST /api/chat        (nginx lo reenvía a /chat)
        ▼
   Chatbot host  (FastAPI · src/ChatBot/)
        │                        ├─── Anthropic API  (Claude, tool use)
        │  JSON-RPC 2.0          │
        ├──── HTTP  ─────────────► Servidor MCP remoto  (Cloud Run)
        └──── stdio ─────────────► Servidor MCP local   (src/Server.py)
                                   + filesystem / git (servidores oficiales)
```

El host traduce entre los dos formatos: MCP usa `inputSchema`, la API de Anthropic usa
`input_schema` (ver `MCPManager.anthropic_tools()`). Cada mensaje JSON-RPC que entra o
sale queda registrado en `src/logs/mcp_interactions.log`.

| Pieza | Código | Puerto | Transporte |
|-------|--------|--------|------------|
| Servidor MCP local | `src/Server.py` | — | stdio (una línea JSON por mensaje) |
| Servidor MCP remoto | `src/Server/ServerHTTP.py` | 8000 (local) / `$PORT` | HTTP `POST /mcp` |
| Chatbot (API web) | `src/ChatBot/WebAPI.py` | 8500 | HTTP REST |
| Chatbot (consola) | `src/ChatBot/Main.py` | — | CLI |
| UI | `UI/` | 5173 (dev) / 8080 (Docker) | HTTP |

El servidor remoto ya está desplegado:
`https://farmacia-mcp-247170717560.us-central1.run.app/mcp`

---

## Estructura del repositorio

```
src/
  Server.py               Loop stdio: lee una línea, responde una línea
  Json_RPC_Plumbing.py    Envelopes JSON-RPC y códigos de error estándar
  MethodHandlers.py       initialize · tools/list · tools/call · notificaciones
  Tools.py                Registro de tools (JSON Schema) generado desde MARCAS
  QandA.py                Lógica de negocio: búsqueda difusa sobre la FAQ
  DataLoader.py           Lee el Excel (una hoja por marca, encabezados variables)
  Server/ServerHTTP.py    Mismo servidor, transporte HTTP (para Cloud Run)
  ChatBot/
    Config.py             Servidores MCP a conectar, modelo, system prompt
    MCP_Client.py         Clientes stdio y HTTP + MCPManager (routing de tools)
    Main.py               Chatbot de consola
    WebAPI.py             Chatbot como API HTTP para la UI
    Logger.py             Log de interacciones MCP
  logs/                   mcp_interactions.log
  data/                   Excel de FAQs
UI/                       Tienda + widget de chat (React 19 + Vite)
docs/arquitectura.drawio  Diagrama de arquitectura y tabla de componentes (draw.io)
captura/                  sslkeys.log y .pcap para Wireshark (no se versiona)
test/TestClient.py        Cliente MCP mínimo para probar el servidor local
Examples/                 Servidor de clima de referencia (ejemplo del curso)
```

---

## Herramientas MCP expuestas

Se generan automáticamente a partir del diccionario `MARCAS` en `src/Tools.py`:

| Tool | Argumentos | Qué hace |
|------|-----------|----------|
| `consultar_faq_producto` | `marca` | Lista todas las preguntas disponibles de un producto |
| `get_faq_<producto>` | `pregunta` | Búsqueda difusa (rapidfuzz, `token_set_ratio`); devuelve hasta 5 candidatos con score |
| `get_faq_<producto>_exacta` | `pregunta` | Coincidencia cercana con difflib; devuelve una sola respuesta |

Productos: `maxicrez`, `diabelife`, `colonditox`, `geriaking_vital`, `perenterol`, `calmiderm`.

El texto de las respuestas sale de `data/FAQ_Redes_Sociales_Marcas.xlsx`, que tiene una
hoja por marca. `DataLoader.py` busca sola la fila de encabezados, así que el logo y el
título de arriba no rompen la carga.

---

## Configuración

```bash
cp .env.example .env
```

y llena las dos variables:

```
ANTHROPIC_API_KEY = sk-ant-...
ANTHROPIC_WORKSPACE_ID = ...
```

`.env` está en `.gitignore` — no lo subas.

Para cambiar entre servidor local y remoto, edita `USAR_REMOTO` en `src/ChatBot/Config.py`:

```python
USAR_REMOTO = True    # True  -> HTTP contra Cloud Run
                      # False -> stdio local + filesystem + git
```

---

## Correr con Docker (recomendado)

El servidor MCP ya corre en Cloud Run, así que Docker levanta solo las otras dos piezas:

| Servicio | Imagen | Puerto host | Qué hace |
|----------|--------|-------------|----------|
| `chatbot` | `Dockerfile.chatbot` (FastAPI) | 8500 | Host MCP + Anthropic API |
| `ui` | `UI/Dockerfile` (Vite + nginx) | 8080 | Tienda + widget; `/api/*` va a `chatbot:8500` |

```bash
docker compose up --build
```

Abre <http://localhost:8080>. El widget llama a `/api/chat` en el mismo origen (sin CORS);
el chatbot también queda expuesto directo en <http://localhost:8500/tools>.

El log MCP se monta en `src/logs/mcp_interactions.log` del host, así que
`GET http://localhost:8500/log` y el archivo muestran lo mismo.

Para detener: `docker compose down`.

### Captura de tráfico TLS (Wireshark)

El contenedor `chatbot` corre con `SSLKEYLOGFILE=/app/captura/sslkeys.log`, montado en
`captura/sslkeys.log` del host. Ahí caen las llaves de sesión de **todo** el TLS que abre
el host: el servidor MCP remoto en Cloud Run y `api.anthropic.com`.

Funciona sin tocar el código porque las dos rutas de red terminan en
`ssl.create_default_context()`, que lee la variable sola: `MCP_Client.py` usa `urllib`
y el SDK de Anthropic usa `httpx`.

1. Levanta todo y manda un mensaje desde el widget. El archivo aparece solo:

   ```bash
   docker compose up --build
   wc -l captura/sslkeys.log        # debe crecer con cada conexión nueva
   ```

2. Captura. En macOS y Windows, Docker Desktop corre dentro de una VM, así que Wireshark
   en tu máquina **no ve** la interfaz del contenedor; hay que capturar desde adentro
   (la imagen ya trae `tcpdump`):

   ```bash
   docker compose exec chatbot tcpdump -i any -w /app/captura/mcp.pcap 'tcp port 443'
   ```

   Ctrl-C para parar. El `.pcap` queda en `captura/`.

3. En Wireshark: **Preferences → Protocols → TLS → (Pre)-Master-Secret log filename** →
   apunta a `captura/sslkeys.log`. Abre `captura/mcp.pcap` y filtra con
   `http` o `frame contains "jsonrpc"`; los mensajes JSON-RPC se ven en claro.

Notas:

- Solo se descifran las sesiones abiertas **después** de arrancar el contenedor con la
  variable puesta; las anteriores no tienen llave.
- El tráfico UI ↔ chatbot (puertos 8080 y 8500) es HTTP plano, se ve sin necesidad de llaves.
- `captura/` está en `.gitignore`. Borra `sslkeys.log` al terminar: con ese archivo
  cualquiera puede descifrar esas sesiones.
- Para desactivarlo, agrega una línea vacía `SSLKEYLOGFILE=` en tu `.env`.

---

## Correr sin Docker

### Dependencias

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install fastapi "uvicorn[standard]"     # solo si vas a usar la API web
```

### Servidor MCP local (stdio)

```bash
cd src && python Server.py
```

Habla JSON-RPC por stdin/stdout; normalmente no se corre a mano, lo lanza el host.
Para probarlo directo:

```bash
python test/TestClient.py
```

### Servidor MCP remoto (HTTP)

```bash
cd src/Server && python ServerHTTP.py 8000
curl -X POST http://localhost:8000/mcp \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

### Chatbot en consola

```bash
cd src/ChatBot && python Main.py
```

Comandos dentro del chat: `/log` (últimas interacciones MCP), `/exit`.

### Chatbot como API web

```bash
cd src && python -m uvicorn ChatBot.WebAPI:app --port 8500 --reload
```

| Endpoint | Qué hace |
|----------|----------|
| `POST /chat` | `{ session_id, mensaje }` → `{ respuesta, tools_usadas }` |
| `GET /tools` | Tools cargadas y de qué servidor viene cada una |
| `GET /log?n=50` | Últimas n líneas del log MCP |
| `DELETE /sesion/{id}` | Borra el contexto de una conversación |

El contexto vive en memoria por `session_id`, así que reiniciar el proceso lo borra.
`ALLOWED_ORIGINS` se puede sobrescribir con una variable de entorno (lista separada
por comas); por defecto permite `localhost:5173`.

### UI

```bash
cd UI
npm install
npm run dev            # http://localhost:5173
```

Apunta el widget al backend con `UI/.env`:

```
VITE_CHAT_API_URL=http://localhost:8500/chat
```

(En Docker esta variable se ignora: la imagen la fija en `/api/chat`.)

---

## Detalles del protocolo

Métodos implementados: `initialize`, `tools/list`, `tools/call`, `ping` (solo HTTP)
y la notificación `notifications/initialized`. Versión del protocolo: `2025-06-18`.

Códigos de error JSON-RPC usados:

| Código | Cuándo |
|--------|--------|
| `-32700` | JSON inválido |
| `-32600` | Falta `"jsonrpc": "2.0"` |
| `-32601` | Método o tool que no existe |
| `-32602` | Argumentos faltantes o inválidos |
| `-32603` | La tool tronó al ejecutarse |

Dos reglas que importan en la implementación:

- Las **notificaciones no llevan `id` y nunca se responden** (en HTTP se contesta `202`
  con body vacío).
- En stdio, **los logs van a stderr**: escribir en stdout corrompe el stream del protocolo.

---

## Despliegue en Cloud Run

`src/Dockerfile` empaqueta el servidor MCP remoto (lee el puerto de `$PORT`):

```bash
cd src
gcloud run deploy farmacia-mcp --source . --region us-central1 --allow-unauthenticated
```

Luego actualiza la URL en `HTTP_SERVERS` dentro de `src/ChatBot/Config.py`.

---

## Pendientes conocidos

- En `src/Tools.py`, la llave `get_faq_geriaking_vital` está repetida tres veces en
  `MARCAS`; gana la última (`"geriaking_vital"`), pero la hoja del Excel se llama
  `Geriaking Vital`, así que esa tool responde "No hay preguntas frecuentes registradas".
- `calmiderm` está en `MARCAS` pero no tiene hoja en el Excel, con el mismo resultado.
- `tools/invoke.json` y `files/` son versiones viejas que ya no se usan.
