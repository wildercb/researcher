# ── Stage 1: Python dependencies ──────────────────────────────────────
FROM python:3.12-slim AS python-deps

RUN pip install uv

WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

# ── Stage 2: Node dependencies ───────────────────────────────────────
FROM node:20-slim AS node-deps

RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /app/apps/web
COPY apps/web/package.json apps/web/pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile

# ── Stage 3: Build web (Next.js static export) ──────────────────────
FROM node-deps AS build-web

COPY apps/web/ ./
RUN pnpm build

# ── Stage 4: Runtime ─────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

RUN groupadd --gid 1000 atlas && \
    useradd --uid 1000 --gid atlas --create-home atlas

WORKDIR /app

# Copy Python virtual environment from stage 1
COPY --from=python-deps /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy built web static files from stage 3
COPY --from=build-web /app/apps/web/out /app/static

# Copy application source
COPY packages/ /app/packages/
COPY config/ /app/config/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/alembic.ini

RUN chown -R atlas:atlas /app
USER atlas

EXPOSE 8765

CMD ["uvicorn", "packages.api.app:app", "--host", "0.0.0.0", "--port", "8765"]
