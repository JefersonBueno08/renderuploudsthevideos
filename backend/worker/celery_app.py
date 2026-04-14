from __future__ import annotations

from celery import Celery

from backend.app.settings import settings

celery_app = Celery(
    "youtube_news_automation",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "backend.worker.tasks.pipeline",
    ],
)

celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
)

