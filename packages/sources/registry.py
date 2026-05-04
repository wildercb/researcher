from __future__ import annotations

_REGISTRY: dict[str, type] = {}


def register_source(cls: type) -> type:
    """Decorator to register a source plugin.

    Usage:
        @register_source
        class ArxivSource:
            name = "arxiv"
            cadence = "0 */6 * * *"
            ...
    """
    name = getattr(cls, "name", None)
    if not name:
        raise ValueError(f"Source class {cls.__name__} must define a 'name' attribute")
    _REGISTRY[name] = cls
    return cls


def get_source(name: str) -> type:
    if name not in _REGISTRY:
        raise KeyError(f"Unknown source: {name}. Available: {list(_REGISTRY.keys())}")
    return _REGISTRY[name]


def list_sources() -> list[str]:
    return list(_REGISTRY.keys())


def get_all_sources() -> dict[str, type]:
    return dict(_REGISTRY)
