"""
Celery Tasks for LearnNova
"""

from celery import Celery  # type: ignore[import]
import os

# Create Celery app
celery_app = Celery(
    'learnnova',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Import tasks
from tasks import email_tasks, course_tasks, ai_tasks  # type: ignore[attr-defined]

__all__ = ['celery_app']
