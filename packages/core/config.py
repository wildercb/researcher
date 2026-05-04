from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

from packages.core.types import AtlasMode


class Settings(BaseSettings):
    model_config = {"env_prefix": "ATLAS_", "env_file": ".env", "extra": "ignore"}

    mode: AtlasMode = AtlasMode.LAPTOP
    host: str = "0.0.0.0"
    port: int = 8765
    debug: bool = False

    # Database
    database_url: str = ""
    data_dir: Path = Path.home() / ".atlas"

    # LLM
    daily_cost_cap_usd: float = 5.0

    # Config paths
    config_dir: Path = Path("config")

    @property
    def effective_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if self.mode == AtlasMode.VPS:
            return "postgresql+asyncpg://atlas:atlas@localhost:5432/atlas"
        db_path = self.data_dir / "atlas.db"
        return f"sqlite+aiosqlite:///{db_path}"

    @property
    def is_sqlite(self) -> bool:
        return self.effective_database_url.startswith("sqlite")

    @property
    def seeds_path(self) -> Path:
        return self.config_dir / "seeds.yaml"

    @property
    def sources_path(self) -> Path:
        return self.config_dir / "sources.yaml"

    @property
    def models_path(self) -> Path:
        return self.config_dir / "models.yaml"

    @property
    def interest_path(self) -> Path:
        return self.config_dir / "interest.yaml"


@lru_cache
def get_settings() -> Settings:
    return Settings()
