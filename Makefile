.PHONY: laptop-setup vps-deploy dev test eval migrate seed-demo lint typecheck fmt clean

laptop-setup:
	scripts/laptop-setup.sh

vps-deploy:
	DOMAIN=$(DOMAIN) EMAIL=$(EMAIL) scripts/vps-deploy.sh

dev:
	uv run uvicorn apps.api.main:app --reload --port 8765 & \
	cd apps/web && pnpm dev & \
	wait

test:
	uv run pytest

eval:
	uv run pytest packages/eval

migrate:
	uv run alembic -c migrations/alembic.ini upgrade head

seed-demo:
	uv run atlas seed import config/seeds.yaml

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy .

fmt:
	uv run ruff format .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .next -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
