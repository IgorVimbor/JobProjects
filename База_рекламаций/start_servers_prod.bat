@echo off
:: Устанавливаем кодировку UTF-8 для корректного отображения русских символов
chcp 65001 > nul
title Сервер Django (Production)
:: ---------------------------------------------------------------------------------------------

:: Выводим информационные сообщения
echo.
echo        ==============================================
echo          Запуск серверов Django + Nginx (Production)
echo        ==============================================
echo.
echo        Запуск Django prod-сервера ...

:: Переходим в папку проекта и активируем виртуальное окружение
cd /d "E:\MyRepositories\JobProjects\База_рекламаций"
call r-hub_venv\Scripts\activate
:: ---------------------------------------------------------------------------------------------

:: 1. Явно указываем использовать настройки из файла reclamationhub\settings\production.py
set "DJANGO_SETTINGS_MODULE=reclamationhub.settings.production"

:: Переходим в папку проекта
cd reclamationhub
:: ---------------------------------------------------------------------------------------------

:: 2. Запускаем Django через production-ready WSGI сервер Waitress напрямую (без cmd /k)
:: Waitress подхватит переменную окружения
start /min "Django" waitress-serve --host=127.0.0.1 --port=8000 reclamationhub.wsgi:application
:: start /min "Django" cmd /k "waitress-serve --host=127.0.0.1 --port=8000 reclamationhub.wsgi:application"

timeout /t 3 /nobreak > nul
:: ---------------------------------------------------------------------------------------------

:: 3. Запускаем Python-скрипт отправки письма
echo.
echo        Выполняется Python-скрипт email_send_start.py ...
echo.
python email_send_start.py

timeout /t 2 /nobreak > nul
:: ---------------------------------------------------------------------------------------------

:: 4. Запускаем прокси-сервер Nginx
echo.
echo        Запуск Nginx ...
cd /d "C:\nginx-1.28.0"
start "" ".\nginx.exe"
echo.

timeout /t 2 /nobreak > nul
:: ---------------------------------------------------------------------------------------------

:: Выводим информационное сообщение о запуске серверов
echo.
echo        =====================================================
echo         Серверы Nginx + Django (Waitress) успешно запущены!
echo        =====================================================
echo.
echo.
echo                --- ХОРОШЕГО И УДАЧНОГО ДНЯ !!! ---
echo.
echo.
timeout /t 3 /nobreak > nul
echo        ... Это окно закроется автоматически...
timeout /t 3 /nobreak > nul

:: Закрываем окно
exit
@REM pause
:: ---------------------------------------------------------------------------------------------