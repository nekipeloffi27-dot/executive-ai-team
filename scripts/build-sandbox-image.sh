#!/usr/bin/env bash
# scripts/build-sandbox-image.sh
set -euo pipefail

cd "$(dirname "$0")/.."

# Загружаем proxy URL из .env если есть
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  set -a; source .env; set +a
fi

PROXY="${ANTHROPIC_PROXY_URL:-}"
echo "Building sandbox image (proxy: ${PROXY:-none})"

docker build \
  -t executive-ai-team-dev-sandbox:latest \
  --build-arg "ANTHROPIC_PROXY_URL=${PROXY}" \
  -f agents/dev/sandbox/Dockerfile \
  agents/dev/sandbox/

echo "Done. Image: executive-ai-team-dev-sandbox:latest"
docker images | grep executive-ai-team-dev-sandbox
