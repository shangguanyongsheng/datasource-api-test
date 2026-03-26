#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据源接口自动化测试工具 - 命令行入口

Usage:
    # 运行 GUI
    python run.py --gui
    
    # 运行测试
    python run.py --test
    
    # 运行指定类型测试
    python run.py --test --markers basic,pagination
    
    # 生成测试用例
    python run.py --generate --widget-id 123
    
    # 添加 SQL 配置
    python run.py --add-sql "INSERT INTO ..."
"""
import argparse
import sys
import subprocess
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def detect_encoding(file_path: str) -> str:
    """检测文件编码，支持 GBK 等 Windows 编码和 UTF-8 BOM"""
    # 先检查 BOM
    try:
        with open(file_path, 'rb') as f:
            bom = f.read(3)
            if bom == b'\xef\xbb\xbf':
                return 'utf-8-sig'
    except:
        pass
    
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read()
            return encoding
        except UnicodeDecodeError:
            continue
    return 'utf-8'


def run_gui():
    """启动 GUI 界面"""
    try:
        from gui.main_window import main
        main()
    except ImportError as e:
        print(f"❌ GUI 启动失败: {e}")
        print("💡 提示: 请确保已安装 tkinter")
        sys.exit(1)


def run_tests(markers=None, widget_id=None, output="reports/html/report.html"):
    """运行测试
    
    Args:
        markers: 测试标记列表
        widget_id: 指定数据源ID
        output: 报告输出路径
    """
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_dynamic.py",
        "-v",
        f"--html={output}",
        "--self-contained-html",
        "-p", "no:warnings"
    ]
    
    if markers:
        marker_expr = " or ".join(markers)
        cmd.extend(["-m", marker_expr])
    
    print(f"🚀 执行命令: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    
    if result.returncode == 0:
        print(f"\n✅ 测试完成！报告: {output}")
    else:
        print(f"\n⚠️ 测试完成，部分用例失败")
    
    return result.returncode


def generate_cases(widget_id):
    """生成测试用例
    
    Args:
        widget_id: 数据源ID
    """
    from utils.sql_parser import SQLParser, DataSourceConfig
    from utils.case_generator import TestCaseGenerator
    
    sql_file = PROJECT_ROOT / "config" / "sql_input" / f"datasource_{widget_id}.sql"
    
    if not sql_file.exists():
        print(f"❌ SQL 配置文件不存在: {sql_file}")
        return
    
    parser = SQLParser()
    fields = parser.parse_sql_file(str(sql_file))
    config = DataSourceConfig(fields)
    generator = TestCaseGenerator(config)
    
    cases = generator.generate_all_cases()
    
    print(f"\n📋 数据源 {widget_id} 测试用例列表:")
    print("-" * 60)
    
    for case in cases:
        print(f"  {case['case_id']}: {case['name']}")
    
    print("-" * 60)
    print(f"共 {len(cases)} 个测试用例")


def add_sql_config(widget_id, sql_content, name=""):
    """添加 SQL 配置
    
    Args:
        widget_id: 数据源ID
        sql_content: SQL 内容
        name: 数据源名称
    """
    sql_dir = PROJECT_ROOT / "config" / "sql_input"
    sql_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = sql_dir / f"datasource_{widget_id}.sql"
    
    full_content = f"-- 数据源ID: {widget_id}\n"
    if name:
        full_content += f"-- 数据源名称: {name}\n"
    full_content += f"\n{sql_content}"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(full_content)
    
    print(f"✅ SQL 配置已保存: {file_path}")


def list_datasources():
    """列出所有数据源"""
    sql_dir = PROJECT_ROOT / "config" / "sql_input"
    
    if not sql_dir.exists():
        print("📁 暂无数据源配置")
        return
    
    print("\n📁 已配置的数据源:")
    print("-" * 40)
    
    for sql_file in sorted(sql_dir.glob("*.sql")):
        # 读取名称
        try:
            encoding = detect_encoding(str(sql_file))
            with open(sql_file, 'r', encoding=encoding) as f:
                first_lines = [f.readline() for _ in range(3)]
            
            name = ""
            for line in first_lines:
                if '数据源名称' in line:
                    name = line.split(':', 1)[-1].strip().lstrip('- ')
                    break
            
            print(f"  {sql_file.stem:15} {name}")
        except:
            print(f"  {sql_file.stem}")
    
    print("-" * 40)


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="数据源接口自动化测试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --gui                    启动 GUI 界面
  %(prog)s --test                   运行所有测试
  %(prog)s --test -m basic,pagination  运行指定类型测试
  %(prog)s --generate -w 123        生成数据源 123 的测试用例
  %(prog)s --list                   列出所有数据源
        """
    )
    
    # 主要操作
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--gui", "-g", action="store_true", help="启动 GUI 界面")
    group.add_argument("--test", "-t", action="store_true", help="运行测试")
    group.add_argument("--generate", action="store_true", help="生成测试用例")
    group.add_argument("--list", "-l", action="store_true", help="列出数据源")
    group.add_argument("--add-sql", metavar="SQL", help="添加 SQL 配置")
    
    # 测试选项
    parser.add_argument("--markers", "-m", help="测试标记 (逗号分隔): basic,combine,pagination,no_pagination,boundary")
    parser.add_argument("--widget-id", "-w", type=int, help="数据源ID")
    parser.add_argument("--name", "-n", help="数据源名称")
    parser.add_argument("--output", "-o", default="reports/html/report.html", help="报告输出路径")
    
    args = parser.parse_args()
    
    # 默认启动 GUI
    if not any([args.gui, args.test, args.generate, args.list, args.add_sql]):
        args.gui = True
    
    if args.gui:
        run_gui()
    
    elif args.test:
        markers = args.markers.split(",") if args.markers else None
        sys.exit(run_tests(markers=markers, widget_id=args.widget_id, output=args.output))
    
    elif args.generate:
        if not args.widget_id:
            print("❌ 请指定数据源ID: --widget-id")
            sys.exit(1)
        generate_cases(args.widget_id)
    
    elif args.list:
        list_datasources()
    
    elif args.add_sql:
        if not args.widget_id:
            print("❌ 请指定数据源ID: --widget-id")
            sys.exit(1)
        add_sql_config(args.widget_id, args.add_sql, args.name or "")


if __name__ == "__main__":
    main()