@echo off
:: Устанавливаем кодировку UTF-8 для корректного отображения русских символов
chcp 65001 > nul
title Сервер Django (Development)
echo        ========================================
echo             Запуск сервера Django (DEV)
echo        ========================================

echo.
echo        Запуск Django dev-сервера...
:: Переходим в папку проекта и активируем виртуальное окружение
cd /d "D:\MyRepositories\JobProjects\База_рекламаций"
call rhub_venv\Scripts\activate

:: 1. Явно указываем использовать настройки из файла reclamationhub\settings\development.py
set "DJANGO_SETTINGS_MODULE=reclamationhub.settings.development"

:: Переходим в папку проекта
cd reclamationhub

:: 2. Запускаем Django напрямую (без cmd /k)
start /min "Django" python manage.py runserver 127.0.0.1:8000
::start /min "Django" cmd /k "python manage.py runserver 127.0.0.1:8000"

timeout /t 3 /nobreak > nul

echo.
echo        ============================================================
echo        Django dev-сервер запущен в отдельном минимизированном окне.
echo        ============================================================
echo.
echo        Это окно закроется автоматически...
timeout /t 4 /nobreak > nul
:: Закрываем окно
exit