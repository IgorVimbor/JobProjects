# Настройки settings для продакшена

from .base import *


DEBUG = False
ALLOWED_HOSTS = [
    '192.168.0.191', # IP в локальной сети завода
    'localhost',
    '127.0.0.1'
]

# Добавляем WhiteNoise в MIDDLEWARE (после SecurityMiddleware!)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # <-- Вот эта строка
] + MIDDLEWARE[1:]  # Сохраняем остальные middleware

# Настройки WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Для продакшена
CSRF_TRUSTED_ORIGINS = ['http://192.168.0.191:8000', 'http://localhost:8000']
# Это необходимо для безопасной обработки AJAX-запросов.
# Django использует CSRF-защиту, и эта настройка указывает, каким источникам можно доверять.

# Дополнительные настройки безопасности
CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'  # Кастомный вид при ошибке
CSRF_USE_SESSIONS = False  # Хранить токен в куках (стандартное поведение)

# Настройки кук для работы по HTTP в локальной сети
CSRF_COOKIE_SECURE = False    # Разрешить передачу CSRF-куки по HTTP
SESSION_COOKIE_SECURE = False  # Разрешить сессионные куки по HTTP
CSRF_COOKIE_HTTPONLY = False  # Разрешить JavaScript доступ к куке (для AJAX)


# Запуск в продакшене:
# python manage.py runserver 0.0.0.0:8000 --settings=reclamationhub.settings.production
