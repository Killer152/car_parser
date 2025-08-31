from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from celery.signals import setup_logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.timezone = 'UTC'
app.autodiscover_tasks()
app.conf.beat_schedule = {

}


@setup_logging.connect
def config_loggers(loglevel=None, **kwargs):
    return True


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
