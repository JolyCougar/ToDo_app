import os
from celery import Celery

"""Подключение Celery"""

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'toDo_app.settings')

app = Celery('toDo_app')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
