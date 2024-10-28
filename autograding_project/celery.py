from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograding_project.settings')

app = Celery('autograding_project')

# Configure Celery to use settings from Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# app.conf.broker_url = 'redis://localhost:6380/0'


# Autodiscover tasks from all installed apps
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
