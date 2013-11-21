from __future__ import absolute_import

import os

from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dunya.settings')

app = Celery('dunya')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(settings.INSTALLED_APPS, related_name='jobs')

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))