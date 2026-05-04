import pytest

from packages.core.config import Settings
from packages.core.scheduler import APSchedulerBackend, PrefectBackend, create_scheduler


def test_create_scheduler_laptop(settings):
    scheduler = create_scheduler(settings)
    assert isinstance(scheduler, APSchedulerBackend)


def test_create_scheduler_vps(tmp_path):
    settings = Settings(mode="vps", data_dir=tmp_path)
    scheduler = create_scheduler(settings)
    assert isinstance(scheduler, PrefectBackend)


@pytest.mark.asyncio
async def test_apscheduler_start_stop(settings):
    scheduler = APSchedulerBackend(settings)
    await scheduler.start()
    await scheduler.stop()


@pytest.mark.asyncio
async def test_apscheduler_add_job(settings):
    scheduler = APSchedulerBackend(settings)
    await scheduler.start()

    async def dummy_job():
        pass

    scheduler.add_job(dummy_job, "0 * * * *", "test-job")
    scheduler.remove_job("test-job")
    await scheduler.stop()


@pytest.mark.asyncio
async def test_prefect_backend_noop(tmp_path):
    settings = Settings(mode="vps", data_dir=tmp_path)
    scheduler = PrefectBackend(settings)
    await scheduler.start()

    async def dummy():
        pass

    scheduler.add_job(dummy, "0 * * * *", "test-job")
    scheduler.remove_job("test-job")
    await scheduler.stop()
