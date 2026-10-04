@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在启动 PVZH 关卡自定义工具...
python main.py
if errorlevel 1 (
    echo.
    echo 启动失败。请确认已安装 Python，并执行: pip install -r requirements.txt
    pause
    exit /b 1
)
pause
