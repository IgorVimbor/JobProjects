"""Настройки Django для режима разработки"""

from .base import *


DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
INTERNAL_IPS = ["127.0.0.1"]

# Для разработки
CSRF_TRUSTED_ORIGINS = ["http://localhost:8000"]
# Это необходимо для безопасной обработки AJAX-запросов.
# Django использует CSRF-защиту, и эта настройка указывает, каким источникам можно доверять.
# После добавления этой строки перезапустите сервер Django.


# Запуск при разработке:
# python manage.py runserver --settings=reclamationhub.settings.development
