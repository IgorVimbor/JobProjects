# Настройки settings для разработки

from .base import *


DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
INTERNAL_IPS = ["127.0.0.1"]


# Запуск при разработке:
# python manage.py runserver --settings=reclamationhub.settings.development
