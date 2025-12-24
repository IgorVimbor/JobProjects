"""Настройки Django для рабочего режима"""

from .base import *


DEBUG = False
ALLOWED_HOSTS = [
    "192.168.0.191",  # IP в локальной сети завода
    "localhost",
    "127.0.0.1",
    "0.0.0.0",  # для запуска 0.0.0.0:8000 (домашнего тестирования)
]

# ----------------- Настройки по варианту 1 urls.py (только Django) --------------------------
# Убрать (закоментировать настройки WhiteNoise)

# ----------------- Настройки по варианту 2 urls.py (Django + WhiteNoise) --------------------
# # Добавляем WhiteNoise в MIDDLEWARE для отображения статики (WhiteNoise для статики, Django для медиа)
# MIDDLEWARE = [
#     "django.middleware.security.SecurityMiddleware",
#     "whitenoise.middleware.WhiteNoiseMiddleware",  # после SecurityMiddleware!
# ] + MIDDLEWARE[1:]

# # Настройки WhiteNoise
# STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
# # STORAGES = {  # новый синтаксис для WhiteNoise 6.x
# #     "staticfiles": {
# #         "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
# #     },
# # }

# ----------------- Настройки по варианту 3 urls.py (Django + Nginx) --------------------------
# Убрать (закоментировать настройки WhiteNoise)

# Настройки для работы HTTP / HTTPS
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "http")  # для HTTP
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # для HTTPS

# CSRF для работы HTTP / HTTPS
# Django использует CSRF-защиту, и эта настройка указывает, каким источникам можно доверять.
# Для продакшена без порта 8000
CSRF_TRUSTED_ORIGINS = [  # CSRF для HTTP
    "http://192.168.0.191",
    "http://localhost",
    "http://127.0.0.1",
]

# CSRF_TRUSTED_ORIGINS = [ # CSRF для HTTPS
#     "https://192.168.0.191",
#     "https://localhost",
#     "https://bza-otk",
# ]

# Дополнительные настройки поведения CSRF защиты
CSRF_FAILURE_VIEW = "django.views.csrf.csrf_failure"  # Кастомный вид при ошибке
CSRF_USE_SESSIONS = False  # Хранить токен в куках (стандартное поведение)

# Настройки кук по HTTP в локальной сети
CSRF_COOKIE_SECURE = False  # CSRF-куки по HTTP
SESSION_COOKIE_SECURE = False  # Сессионные куки по HTTP
CSRF_COOKIE_HTTPONLY = False  # Разрешить JavaScript доступ к куке (для AJAX)

# # Настройки кук для HTTPS
# CSRF_COOKIE_SECURE = True  # CSRF-куки только по HTTPS
# SESSION_COOKIE_SECURE = True  # Сессионные куки только по HTTPS
# CSRF_COOKIE_HTTPONLY = False  # Разрешить JavaScript доступ к куке (для AJAX)

# # Дополнительные настройки безопасности для HTTPS
# SECURE_SSL_REDIRECT = False  # Nginx делает редирект
