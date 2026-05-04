#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

info()  { echo -e "${GREEN}[atlas]${NC} $*"; }
error() { echo -e "${RED}[atlas]${NC} $*"; exit 1; }

# ── Dependency checks ────────────────────────────────────────────────
command -v docker >/dev/null 2>&1 || error "docker is not installed."
docker compose version >/dev/null 2>&1 || error "docker compose plugin is not installed."

# ── Environment checks ──────────────────────────────────────────────
[ -z "${DOMAIN:-}" ] && error "DOMAIN env var is required. Usage: make vps-deploy DOMAIN=example.com EMAIL=you@example.com"
[ -z "${EMAIL:-}"  ] && error "EMAIL env var is required. Usage: make vps-deploy DOMAIN=example.com EMAIL=you@example.com"

export DOMAIN
export EMAIL

info "Deploying Atlas to ${DOMAIN}..."

# ── Build and start services ─────────────────────────────────────────
docker compose -f infra/docker-compose.yml up -d --build

info "Deployment complete."
info "Atlas is running at https://${DOMAIN}"
