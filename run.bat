@echo off
chcp 65001 >nul
title TheBoringEnglish 桌面客户端
cd /d "%~dp0"

echo 正在启动 TheBoringEnglish 客户端...
python -m src.main
if %errorlevel% neq 0 (
    echo.
    echo 启动出现异常，请确认已安装依赖: pip install -r requirements.txt
    pause
)
