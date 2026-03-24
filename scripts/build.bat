@echo off
chcp 65001 >nul
echo ========================================
echo   打包数据源测试工具
echo ========================================
echo.

python scripts/build.py

pause