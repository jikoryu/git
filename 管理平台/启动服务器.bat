@echo off
chcp 65001 >nul
title 价格追踪工具 - 本地服务器

echo.
echo   ╔══════════════════════════════════════╗
echo   ║    📉 商品价格走势查询工具          ║
echo   ╚══════════════════════════════════════╝
echo.
echo   启动本地服务器...
echo   访问地址: http://localhost:8888
echo.
echo   按 Ctrl+C 停止服务器
echo   ─────────────────────────────────────
echo.

cd /d "%~dp0"
python -m http.server 8888
pause
