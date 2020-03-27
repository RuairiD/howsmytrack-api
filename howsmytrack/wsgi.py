"""
WSGI config for howsmytrack project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from howsmytrack.jobs import start_scheduler

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'howsmytrack.settings')

application = get_wsgi_application()

start_scheduler()
