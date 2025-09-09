@echo off
echo ========================================
echo       Остановка серверов
echo ========================================

echo Остановка Nginx...
cd /d "C:\nginx-1.28.0"
.\nginx.exe -s stop

echo Nginx остановлен!
echo ВНИМАНИЕ: Остановите сервер Django нажав Ctrl+C в его окне
pause