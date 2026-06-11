@echo off
chcp 65001 >nul
title Link Safe — 链接安全检测

cd /d "%~dp0backend"

echo.
echo   ╔══════════════════════════════════╗
echo   ║   🛡  Link Safe — 链接安全检测  ║
echo   ╚══════════════════════════════════╝
echo.
echo   安装依赖...
pip install -q -r requirements.txt 2>nul
echo.
echo   启动服务: http://localhost:8000
echo   按 Ctrl+C 停止
echo   ─────────────────────────────────
start http://localhost:8000
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
