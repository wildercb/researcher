from pathlib import Path

from packages.core.config import Settings
from packages.core.types import AtlasMode


def test_default_mode():
    s = Settings(data_dir=Path("/tmp/atlas-test"))
    assert s.mode == AtlasMode.LAPTOP


def test_vps_mode():
    s = Settings(mode="vps", data_dir=Path("/tmp/atlas-test"))
    assert s.mode == AtlasMode.VPS


def test_sqlite_database_url():
    s = Settings(data_dir=Path("/tmp/atlas-test"))
    assert "sqlite" in s.effective_database_url
    assert s.is_sqlite is True


def test_postgres_database_url():
    s = Settings(mode="vps", data_dir=Path("/tmp/atlas-test"))
    assert "postgresql" in s.effective_database_url
    assert s.is_sqlite is False


def test_explicit_database_url():
    s = Settings(
        database_url="sqlite+aiosqlite:///custom.db",
        data_dir=Path("/tmp/atlas-test"),
    )
    assert s.effective_database_url == "sqlite+aiosqlite:///custom.db"


def test_config_paths():
    s = Settings(config_dir=Path("config"), data_dir=Path("/tmp/atlas-test"))
    assert s.seeds_path == Path("config/seeds.yaml")
    assert s.sources_path == Path("config/sources.yaml")
    assert s.models_path == Path("config/models.yaml")
