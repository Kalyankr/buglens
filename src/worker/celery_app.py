import os

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
# Create the Celery instance
celery_app = Celery(
    "buglens",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["src.worker.tasks"],
)

# Optimize for ML Workloads
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_persistent=True,
    worker_prefetch_multiplier=1,  # only take 1 at a time
    worker_max_tasks_per_child=10,  # Restart worker occasionally to clear GPU/RAM memory leaks
)

if __name__ == "__main__":
    celery_app.start()
