#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
打包脚本 - 将项目打包成可执行文件

使用方法:
    python scripts/build.py
    
输出:
    dist/datasource-test-tool.exe (Windows)
    dist/datasource-test-tool (Linux/Mac)
"""
import subprocess
import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def check_dependencies():
    """检查依赖"""
    print("🔍 检查依赖...")
    
    try:
        import PyInstaller
        print("  ✓ PyInstaller 已安装")
    except ImportError:
        print("  ✗ PyInstaller 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # 检查其他依赖
    requirements = PROJECT_ROOT / "requirements.txt"
    if requirements.exists():
        print("  📦 安装项目依赖...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements)], check=True)


def clean_build():
    """清理构建目录"""
    print("🧹 清理构建目录...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        dir_path = PROJECT_ROOT / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  ✓ 已删除: {dir_name}")
    
    # 删除 .spec 文件
    for spec_file in PROJECT_ROOT.glob("*.spec"):
        if spec_file.name != "build.spec":
            spec_file.unlink()
            print(f"  ✓ 已删除: {spec_file.name}")


def build_exe():
    """构建可执行文件"""
    print("\n📦 开始打包...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=datasource-test-tool",
        "--onefile",
        "--windowed",  # GUI 模式
        "--add-data=config;config",  # Windows 用分号
        "--add-data=README.md;.",
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=yaml",
        "--hidden-import=requests",
        "--hidden-import=pytest",
        "--hidden-import=colorlog",
        "--hidden-import=sqlparse",
        "--hidden-import=pandas",
        "--exclude-module=matplotlib",
        "--exclude-module=IPython",
        "--exclude-module=jupyter",
        "run.py"
    ]
    
    # Linux/Mac 使用冒号
    if sys.platform != "win32":
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--name=datasource-test-tool",
            "--onefile",
            "--windowed",
            "--add-data=config:config",
            "--add-data=README.md:.",
            "--hidden-import=tkinter",
            "--hidden-import=tkinter.ttk",
            "--hidden-import=yaml",
            "--hidden-import=requests",
            "--hidden-import=pytest",
            "--hidden-import=colorlog",
            "--hidden-import=sqlparse",
            "--hidden-import=pandas",
            "--exclude-module=matplotlib",
            "--exclude-module=IPython",
            "--exclude-module=jupyter",
            "run.py"
        ]
    
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    
    if result.returncode == 0:
        print("\n✅ 打包成功!")
        
        # 显示输出文件
        dist_dir = PROJECT_ROOT / "dist"
        if dist_dir.exists():
            print("\n📁 输出文件:")
            for f in dist_dir.iterdir():
                size = f.stat().st_size / 1024 / 1024
                print(f"  {f.name} ({size:.1f} MB)")
    else:
        print("\n❌ 打包失败!")
        sys.exit(1)


def create_portable():
    """创建便携版（包含配置目录）"""
    print("\n📦 创建便携版...")
    
    dist_dir = PROJECT_ROOT / "dist"
    portable_dir = dist_dir / "datasource-test-tool-portable"
    
    # 创建目录
    portable_dir.mkdir(parents=True, exist_ok=True)
    
    # 复制可执行文件
    exe_name = "datasource-test-tool.exe" if sys.platform == "win32" else "datasource-test-tool"
    exe_src = dist_dir / exe_name
    exe_dst = portable_dir / exe_name
    
    if exe_src.exists():
        shutil.copy2(exe_src, exe_dst)
        print(f"  ✓ 复制: {exe_name}")
    
    # 复制配置目录
    config_src = PROJECT_ROOT / "config"
    config_dst = portable_dir / "config"
    
    if config_src.exists():
        shutil.copytree(config_src, config_dst, dirs_exist_ok=True)
        print("  ✓ 复制: config/")
    
    # 复制启动脚本
    if sys.platform == "win32":
        shutil.copy2(PROJECT_ROOT / "start.bat", portable_dir / "start.bat")
        print("  ✓ 复制: start.bat")
    else:
        shutil.copy2(PROJECT_ROOT / "start.sh", portable_dir / "start.sh")
        print("  ✓ 复制: start.sh")
    
    # 复制 README
    shutil.copy2(PROJECT_ROOT / "README.md", portable_dir / "README.md")
    print("  ✓ 复制: README.md")
    
    print(f"\n✅ 便携版创建完成: {portable_dir}")


def main():
    """主函数"""
    print("=" * 50)
    print("  数据源接口自动化测试工具 - 打包脚本")
    print("=" * 50)
    
    # 检查依赖
    check_dependencies()
    
    # 清理
    clean_build()
    
    # 构建
    build_exe()
    
    # 创建便携版
    create_portable()
    
    print("\n" + "=" * 50)
    print("  打包完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()