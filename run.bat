@echo off
rem Chay bot, crash thi tu bat lai sau 10s. Log ghi vao bot.log
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
:loop
echo [%date% %time%] start >> bot.log
python -u bot.py >> bot.log 2>&1
echo [%date% %time%] bot thoat (ma %errorlevel%), bat lai sau 10s >> bot.log
rem chay khong co console (de Ctrl+C khong giet duoc) nen dung ping thay timeout
ping -n 11 127.0.0.1 >nul
goto loop
