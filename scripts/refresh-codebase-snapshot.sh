#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
# shellcheck disable=SC1091
[[ -f .env ]] && set -a && source .env && set +a

: "${PRODUCT_REPO:?PRODUCT_REPO required (org/name)}"
: "${GITHUB_TOKEN:?GITHUB_TOKEN required}"
: "${CODEBASE_SNAPSHOT_DIR:?CODEBASE_SNAPSHOT_DIR required}"

SNAPSHOT="${CODEBASE_SNAPSHOT_DIR}"
mkdir -p "${SNAPSHOT}"

if [[ -d "${SNAPSHOT}/.git" ]]; then
  cd "${SNAPSHOT}"
  git fetch --depth 50 origin main
  git reset --hard origin/main
  echo "[snapshot] Refreshed at $(date)"
else
  git clone --depth 50 "https://x-access-token:${GITHUB_TOKEN}@github.com/${PRODUCT_REPO}.git" "${SNAPSHOT}"
  echo "[snapshot] Cloned at $(date)"
fi
