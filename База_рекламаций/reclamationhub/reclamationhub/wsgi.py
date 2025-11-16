"""
WSGI config for reclamationhub project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application


# Устанавливаем значение development ПО УМОЛЧАНИЮ.
# Если переменная DJANGO_SETTINGS_MODULE не задана извне, Django будет использовать настройки для разработки.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reclamationhub.settings.development")

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reclamationhub.settings.production")

application = get_wsgi_application()
