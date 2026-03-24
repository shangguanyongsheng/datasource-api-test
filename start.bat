@echo off
chcp 65001 >nul
echo ========================================
echo   数据源接口自动化测试工具
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.9+
    pause
    exit /b 1
)

REM 启动 GUI
python run.py --gui

pause