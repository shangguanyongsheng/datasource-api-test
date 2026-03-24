#!/bin/bash
echo "========================================"
echo "  数据源接口自动化测试工具"
echo "========================================"
echo

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python，请先安装 Python 3.9+"
    exit 1
fi

# 启动 GUI
python3 run.py --gui