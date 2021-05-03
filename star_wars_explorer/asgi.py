"""
ASGI config for star_wars_explorer project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'star_wars_explorer.settings')

application = get_asgi_application()

from django_simple_task import django_simple_task_middlware

application = django_simple_task_middlware(application)
