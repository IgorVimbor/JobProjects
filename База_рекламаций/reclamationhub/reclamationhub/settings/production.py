# Настройки settings для продакшена

from .base import *


DEBUG = False
ALLOWED_HOSTS = ["192.168.1.100"]  # ваш IP в локальной сети


# Запуск в продакшене:
# python manage.py runserver 0.0.0.0:8000 --settings=reclamationhub.settings.production
