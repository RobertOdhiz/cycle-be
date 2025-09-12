from celery import Celery
from app.config import settings

celery_app = Celery(
    "cycle",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.worker.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Task routing
celery_app.conf.task_routes = {
    "app.worker.tasks.send_push_notification": {"queue": "notifications"},
    "app.worker.tasks.process_mpesa_webhook": {"queue": "payments"},
    "app.worker.tasks.process_payout": {"queue": "payments"},
    "app.worker.tasks.send_email": {"queue": "emails"},
    "app.worker.tasks.update_analytics": {"queue": "analytics"},
}
