# Atlas

A self-hosted research intelligence platform that calibrates from concrete seeds — papers, researchers, venues, keywords — and uses them as anchors for continuous discovery. It ingests from pluggable sources, routes all LLM calls through one abstraction, and surfaces what matters via chat, briefings, and dashboards.

## Quick Start (Laptop Mode)

```bash
# Prerequisites: uv, node, pnpm
git clone <repo> && cd atlas
make laptop-setup              # installs deps, runs migrations, creates ~/.atlas
atlas seed import config/seeds.yaml
atlas calibrate
atlas run                      # API + worker + scheduler at http://localhost:8765
```

## VPS Deploy

```bash
ssh user@my-vps
git clone <repo> && cd atlas
make vps-deploy DOMAIN=atlas.example.com EMAIL=me@example.com
```

Docker Compose: Caddy (HTTPS) + Postgres + API + Worker + Prefect.

## Architecture

```
Layer 5  UI: Chat + Briefings + Dashboards + Seeds
Layer 4  Agent Runtime: Router -> Orchestrator -> Tools
Layer 3  Knowledge Store: Vectors + Metadata + Citation Graph
Layer 2  Ingestion + Calibration: Fetch -> Dedupe -> Enrich
Layer 1  Source Plugins + Seed Importers
```

Strict layering. Lower layers know nothing about upper.

## Tech Stack

| Component      | Technology                              |
|---------------|-----------------------------------------|
| Language       | Python 3.12 (backend), TypeScript (UI)  |
| LLM Router    | LiteLLM                                 |
| Agents         | LangGraph + Pydantic AI                 |
| Database       | Postgres + pgvector (VPS) / SQLite + sqlite-vec (laptop) |
| Pipeline       | Prefect (VPS) / APScheduler (laptop)    |
| API            | FastAPI + SSE                           |
| UI             | Next.js 14 + Tailwind + shadcn/ui      |
| Testing        | pytest + hypothesis + Playwright        |

## CLI Commands

```
atlas run                          # Start the server
atlas seed paper <doi|arxiv|title> # Add a paper seed
atlas seed author <name>           # Add an author seed
atlas seed venue <name>            # Add a venue seed
atlas seed keyword <term>          # Add a keyword seed
atlas seed import <file.yaml>      # Import seeds from YAML
atlas seed export                  # Export seeds to YAML
atlas calibrate                    # Run calibration crawl
atlas sources list                 # List registered sources
atlas sources fetch <name>         # Fetch from a source
atlas pipeline run                 # Run ingestion pipeline
atlas export <path>                # Export all data
atlas import <path>                # Import data
```

## Extending

- [Adding a source](.claude/skills/adding-a-source.md)
- [Adding an agent](.claude/skills/adding-an-agent.md)
- [Swapping models](.claude/skills/swapping-models.md)

## Development

```bash
make dev         # API (uvicorn --reload) + Web (next dev)
make test        # pytest
make lint        # ruff check + format check
make typecheck   # mypy strict
make eval        # agent eval suite
make fmt         # ruff format
make migrate     # alembic upgrade head
```

## Dual Mode

Set via `ATLAS_MODE` env var:
- `laptop` (default): SQLite, APScheduler, single process
- `vps`: Postgres, Prefect, Docker Compose

Same code, same tests, same agents. `atlas export` / `atlas import` moves data between modes.

## License

MIT
