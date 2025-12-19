@echo off
:: Устанавливаем кодировку UTF-8 для корректного отображения русских символов
chcp 65001 > nul
title Сервер Django (Production)
echo        ========================================
echo          Запуск серверов Django + Nginx (PROD)
echo        ========================================

echo.
echo        Запуск Django prod-сервера...
:: Переходим в папку проекта и активируем виртуальное окружение
cd /d "E:\MyRepositories\JobProjects\База_рекламаций"
call r-hub_venv\Scripts\activate

:: 1. Явно указываем использовать настройки из файла reclamationhub\settings\production.py
set "DJANGO_SETTINGS_MODULE=reclamationhub.settings.production"

:: Переходим в папку проекта
cd reclamationhub

:: 2. Запускаем Django через production-ready WSGI сервер Waitress напрямую (без cmd /k)
:: Waitress подхватит переменную окружения
start /min "Django" waitress-serve --host=127.0.0.1 --port=8000 reclamationhub.wsgi:application
:: start /min "Django" cmd /k "waitress-serve --host=127.0.0.1 --port=8000 reclamationhub.wsgi:application"

timeout /t 3 /nobreak > nul

echo.
:: Запускаем прокси-сервер Nginx
echo        Запуск Nginx...
cd /d "C:\nginx-1.28.0"
start "" ".\nginx.exe"

echo.
:: Выводим информационное сообщение о запуске серверов
timeout /t 2 /nobreak > nul
echo        ===============================================================
echo        Серверы Nginx + Django (Waitress) запущены в режиме Production!
echo        ===============================================================
echo.
echo        Это окно закроется автоматически... ХОРОШЕГО ДНЯ! 😊
timeout /t 4 /nobreak > nul
:: Закрываем окно
exit