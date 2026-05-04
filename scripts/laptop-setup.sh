#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

info()  { echo -e "${GREEN}[atlas]${NC} $*"; }
error() { echo -e "${RED}[atlas]${NC} $*"; exit 1; }

# ── Dependency checks ────────────────────────────────────────────────
command -v uv   >/dev/null 2>&1 || error "uv is not installed. Install it: curl -LsSf https://astral.sh/uv/install.sh | sh"
command -v node >/dev/null 2>&1 || error "node is not installed. Install Node.js 20+."
command -v pnpm >/dev/null 2>&1 || error "pnpm is not installed. Install it: npm install -g pnpm"

info "All dependencies found."

# ── Python dependencies ──────────────────────────────────────────────
info "Installing Python dependencies with uv..."
uv sync

# ── Create config directory ──────────────────────────────────────────
info "Creating ~/.atlas directory..."
mkdir -p ~/.atlas

# ── Database migrations ──────────────────────────────────────────────
info "Running database migrations..."
uv run alembic upgrade head

# ── Pre-commit hooks ─────────────────────────────────────────────────
info "Installing pre-commit hooks..."
uv run pre-commit install

# ── Web dependencies ─────────────────────────────────────────────────
info "Installing web dependencies..."
cd apps/web && pnpm install

# ── Done ─────────────────────────────────────────────────────────────
echo ""
info "Atlas development environment is ready."
info "Run 'make dev' to start the API and web servers."
