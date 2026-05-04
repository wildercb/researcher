# Import all source plugins so they auto-register via @register_source
from packages.sources import arxiv as _arxiv  # noqa: F401
from packages.sources import hacker_news as _hacker_news  # noqa: F401
from packages.sources import openalex as _openalex  # noqa: F401
from packages.sources import openreview as _openreview  # noqa: F401
from packages.sources import rss as _rss  # noqa: F401
from packages.sources import semantic_scholar as _semantic_scholar  # noqa: F401
from packages.sources import web_monitor as _web_monitor  # noqa: F401
