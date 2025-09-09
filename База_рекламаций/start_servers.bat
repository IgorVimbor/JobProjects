@echo off
title Django + Nginx Servers
echo ========================================
echo       Запуск серверов
echo ========================================

echo Запуск Django сервера...
cd /d "E:\MyRepositories\JobProjects\База_рекламаций"
call r-hub_venv\Scripts\activate
cd reclamationhub
start /min "Django" cmd /k "python manage.py runserver 127.0.0.1:8000 --settings=reclamationhub.settings.production"

timeout /t 3 /nobreak > nul

echo Запуск Nginx...
cd /d "C:\nginx-1.28.0"
.\nginx.exe

echo Серверы запущены!
timeout /t 2 /nobreak > nul