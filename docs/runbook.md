# Atlas Runbook

## Add a Source
1. Create `packages/sources/<name>.py` implementing Source protocol
2. Add config to `config/sources.yaml`
3. Write tests with VCR fixtures
4. Run: `uv run pytest tests/sources/test_<name>.py`

See: `.claude/skills/adding-a-source.md`

## Add an Agent
1. Create `packages/agents/<name>.py`
2. Create prompt in `packages/agents/prompts/<name>/v1.md`
3. Create eval dataset in `packages/eval/datasets/<name>.jsonl`
4. Add model config to `config/models.yaml`
5. Run: `uv run pytest tests/agents/test_<name>.py`

See: `.claude/skills/adding-an-agent.md`

## Swap Models
1. Edit `config/models.yaml`
2. Run: `make eval`
3. Compare scores

See: `.claude/skills/swapping-models.md`

## Run an Eval
```bash
make eval                  # all agents
uv run pytest packages/eval/ -k summarizer  # one agent
```

## Recover from Failed Pipeline
```bash
atlas pipeline retry-failed   # replay dead-letter items
```

## Deploy to VPS
```bash
make vps-deploy DOMAIN=atlas.example.com EMAIL=me@example.com
```

## Move Data Laptop -> VPS
```bash
atlas export atlas-data.json    # on laptop
scp atlas-data.json user@vps:~
ssh user@vps 'cd atlas && atlas import ~/atlas-data.json'
```

## Backup (Laptop)
```bash
cp ~/.atlas/atlas.db ~/.atlas/atlas.db.backup
```

## Backup (VPS)
```bash
docker compose -f infra/docker-compose.yml exec postgres pg_dump -U atlas atlas > backup.sql
```
