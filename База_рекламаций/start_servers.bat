@echo off
:: Устанавливаем кодировку UTF-8 для корректного отображения русских символов
chcp 65001 > nul
title Сервер Django
echo        ========================================
echo             Запуск серверов Django + Nginx
echo        ========================================

echo.
echo        Запуск Django сервера...
:: Переходим в папку проекта и активируем виртуальное окружение
cd /d "E:\MyRepositories\JobProjects\База_рекламаций"
call r-hub_venv\Scripts\activate
cd reclamationhub
:: Запускаем сервер Django в режиме продакшен в отдельном минимизированном окне
start /min "Django" cmd /k "python manage.py runserver 127.0.0.1:8000 --settings=reclamationhub.settings.production"

timeout /t 3 /nobreak > nul

echo.
:: Запускаем прокси-сервер Nginx
echo        Запуск Nginx...
cd /d "C:\nginx-1.28.0"
start "" ".\nginx.exe"

echo.
:: Выводим информационное сообщение о запуске серверов
timeout /t 2 /nobreak > nul
echo        Серверы запущены!
timeout /t 3 /nobreak > nul
:: Закрываем окно
exit