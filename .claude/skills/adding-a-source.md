# Adding a Source Plugin

## Key Files
- Source protocol: `packages/sources/base.py`
- Registry: `packages/sources/registry.py`
- Config: `config/sources.yaml`

## Protocol
Every source implements:
```python
class Source(Protocol):
    name: str          # e.g. "arxiv"
    cadence: str       # cron expression, e.g. "0 */6 * * *"

    async def fetch(self, since: datetime | None = None) -> AsyncIterator[SourceRawItem]: ...
    def parse(self, item: SourceRawItem) -> NormalizedItem: ...
```

## Steps

### 1. Create source file
`packages/sources/<name>.py`:
```python
from datetime import datetime
from collections.abc import AsyncIterator

import httpx

from packages.sources.base import SourceRawItem, NormalizedItem
from packages.sources.registry import register_source


@register_source
class MySource:
    name = "my_source"
    cadence = "0 */6 * * *"

    def __init__(self, config: dict):
        self.config = config

    async def fetch(self, since: datetime | None = None) -> AsyncIterator[SourceRawItem]:
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://api.example.com/items")
            for item in resp.json()["results"]:
                yield SourceRawItem(
                    source_id=item["id"],
                    fetched_at=datetime.now(),
                    payload=item,
                )

    def parse(self, item: SourceRawItem) -> NormalizedItem:
        p = item.payload
        return NormalizedItem(
            source=self.name,
            source_id=item.source_id,
            kind="paper",
            title=p["title"],
            authors=p.get("authors", []),
            url=p["url"],
            raw=p,
        )
```

### 2. Add config to `config/sources.yaml`
```yaml
my_source:
  enabled: true
  cadence: "0 */6 * * *"
```

### 3. Write tests with VCR.py fixtures
`tests/sources/test_my_source.py` with recorded cassettes.

### 4. Document rate limits in source file docstring.

### 5. Run tests
```bash
uv run pytest tests/sources/test_my_source.py
```

## Checklist
- [ ] File in `packages/sources/<name>.py`
- [ ] `@register_source` decorator
- [ ] Implements fetch + parse
- [ ] Rate limits in docstring
- [ ] Config in `config/sources.yaml`
- [ ] Tests with VCR fixtures
- [ ] `uv run pytest tests/sources/test_<name>.py` passes
