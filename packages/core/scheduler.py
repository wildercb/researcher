from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from packages.core.types import AtlasMode

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from packages.core.config import Settings


class Scheduler(Protocol):
    """Dual-mode scheduler abstraction."""

    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    def add_job(
        self,
        func: Callable[..., Coroutine[Any, Any, Any]],
        cron: str,
        job_id: str,
        **kwargs: Any,
    ) -> None: ...
    def remove_job(self, job_id: str) -> None: ...


class APSchedulerBackend:
    """APScheduler backend for laptop mode."""

    def __init__(self, settings: Settings) -> None:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger

        self._settings = settings
        self._scheduler = AsyncIOScheduler()
        self._CronTrigger = CronTrigger

    async def start(self) -> None:
        self._scheduler.start()

    async def stop(self) -> None:
        self._scheduler.shutdown(wait=False)

    def add_job(
        self,
        func: Callable[..., Coroutine[Any, Any, Any]],
        cron: str,
        job_id: str,
        **kwargs: Any,
    ) -> None:
        parts = cron.split()
        trigger = self._CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4],
        )
        self._scheduler.add_job(func, trigger, id=job_id, replace_existing=True, kwargs=kwargs)

    def remove_job(self, job_id: str) -> None:
        self._scheduler.remove_job(job_id)


class PrefectBackend:
    """Prefect backend for VPS mode. Stub — wired in Phase 2."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    def add_job(
        self,
        func: Callable[..., Coroutine[Any, Any, Any]],
        cron: str,
        job_id: str,
        **kwargs: Any,
    ) -> None:
        pass

    def remove_job(self, job_id: str) -> None:
        pass


def create_scheduler(settings: Settings) -> APSchedulerBackend | PrefectBackend:
    if settings.mode == AtlasMode.LAPTOP:
        return APSchedulerBackend(settings)
    return PrefectBackend(settings)
