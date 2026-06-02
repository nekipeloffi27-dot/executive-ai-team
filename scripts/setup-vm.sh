#!/usr/bin/env bash
# scripts/setup-vm.sh — bootstrap чистой Ubuntu 22.04 VM
set -euo pipefail

echo "=== Updating system ==="
sudo apt update && sudo apt upgrade -y

echo "=== Installing essentials ==="
sudo apt install -y curl git build-essential ca-certificates gnupg lsb-release

echo "=== Installing Docker ==="
if ! command -v docker &>/dev/null; then
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER"
fi

echo "=== Installing Docker Compose plugin ==="
sudo apt install -y docker-compose-plugin

echo "=== Creating workspace dirs ==="
sudo mkdir -p /var/exec-team-workspace /var/exec-team-codebase-snapshot
sudo chown -R "$USER:$USER" /var/exec-team-workspace /var/exec-team-codebase-snapshot

echo "=== Done ==="
echo "Next steps:"
echo "  1. Re-login (so 'docker' group takes effect) or run: newgrp docker"
echo "  2. Clone exec-team repo to ~/exec-team"
echo "  3. cd ~/exec-team && cp .env.example .env && edit .env"
echo "  4. ./scripts/check-env.sh"
echo "  5. ./scripts/build-sandbox-image.sh"
echo "  6. ./scripts/refresh-codebase-snapshot.sh"
echo "  7. docker compose up -d --build"
