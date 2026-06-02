#!/usr/bin/env bash
# scripts/check-env.sh — проверка что .env заполнен на минимум
set -euo pipefail

cd "$(dirname "$0")/.."
[[ -f .env ]] || { echo "FATAL: .env not found"; exit 1; }
# shellcheck disable=SC1091
set -a; source .env; set +a

REQUIRED=(
  ANTHROPIC_API_KEY
  TG_BOT_TOKEN_CHIEF TG_BOT_TOKEN_DESIGNER TG_BOT_TOKEN_CTO TG_BOT_TOKEN_DEV TG_BOT_TOKEN_RESEARCH
  TG_GROUP_ID TG_ALLOWED_USERS
  DATABASE_URL DB_PASSWORD
  GITHUB_TOKEN GITHUB_USER PRODUCT_REPO
)

MISSING=()
for v in "${REQUIRED[@]}"; do
  val="${!v:-}"
  if [[ -z "${val}" ]]; then
    MISSING+=("$v")
  fi
done

if (( ${#MISSING[@]} > 0 )); then
  echo "FATAL: missing required env vars:"
  printf '  - %s\n' "${MISSING[@]}"
  exit 2
fi

echo "✅ .env looks complete (${#REQUIRED[@]} required vars set)"
