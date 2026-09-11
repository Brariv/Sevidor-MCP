#!/usr/bin/env bash
# Despliega el chatbot host (FastAPI) en Cloud Run, junto al servidor MCP.
#
#   ./deploy-chatbot.sh
#
# Requiere: gcloud autenticado, Docker corriendo, y las variables del .env.
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-farmacia-chatbot}"
REPO="${REPO:-apps}"                    # repositorio de Artifact Registry
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${SERVICE}:latest"

# Origen(es) permitidos por CORS. Si la UI llama vía el rewrite de Vercel
# (/api/... -> Cloud Run) el navegador ve mismo origen y esto casi no se usa,
# pero no estorba tenerlo.
ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-https://${SERVICE}.vercel.app,http://localhost:5173}"

[ -f .env ] || { echo "Falta .env con ANTHROPIC_API_KEY y ANTHROPIC_WORKSPACE_ID"; exit 1; }

# Se parsea igual que python-dotenv: tolera `CLAVE = "valor"` con espacios y comillas,
# que es como está el .env y que `source` de bash no sabe leer.
eval "$(python3 - <<'PY'
import re, shlex
for linea in open('.env', encoding='utf-8'):
    linea = linea.strip()
    if not linea or linea.startswith('#') or '=' not in linea:
        continue
    clave, valor = linea.split('=', 1)
    clave, valor = clave.strip(), valor.strip()
    if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
        valor = valor[1:-1]
    if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', clave):
        print(f'export {clave}={shlex.quote(valor)}')
PY
)"

: "${ANTHROPIC_API_KEY:?falta ANTHROPIC_API_KEY en .env}"
: "${ANTHROPIC_WORKSPACE_ID:?falta ANTHROPIC_WORKSPACE_ID en .env}"

echo "==> Proyecto: $PROJECT_ID   Región: $REGION"
echo "==> Imagen:   $IMAGE"

# Crea el repositorio de Artifact Registry la primera vez (si ya existe, no pasa nada)
gcloud artifacts repositories create "$REPO" \
  --repository-format=docker --location="$REGION" \
  --description="Imágenes del proyecto MCP" 2>/dev/null || true
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# --platform linux/amd64 es obligatorio desde una Mac con chip Apple:
# Cloud Run no corre imágenes arm64.
echo "==> Construyendo (linux/amd64)..."
docker build --platform linux/amd64 -f Dockerfile.chatbot -t "$IMAGE" .

echo "==> Subiendo imagen..."
docker push "$IMAGE"

echo "==> Desplegando en Cloud Run..."
gcloud run deploy "$SERVICE" \
  --image "$IMAGE" \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars "^@^ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}@ANTHROPIC_WORKSPACE_ID=${ANTHROPIC_WORKSPACE_ID}@ALLOWED_ORIGINS=${ALLOWED_ORIGINS}"

echo
echo "==> Listo. URL del chatbot:"
gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)'
echo "Ponla en UI/vercel.json (rewrite de /api) y vuelve a desplegar la UI."
