#!/usr/bin/env python3
import argparse
import sys
import os
import subprocess
import time
from typing import Optional

# 确保 requests 已安装（在导入 cli 模块时会自动检测）
from . import ensure_requests
ensure_requests()

import requests

from . import __version__
from .config import load_config
from .utils import get_system_language
from .installer import handle_install
from .list_packages import handle_list_packages
from .project_new import handle_new


def show_help(lang: str) -> None:
    """显示帮助信息"""
    if lang == "zh-CN":
        print(f"""
SilentStudio CLI v{__version__}
© SilentStudio All Rights Reserved.
https://github.com/Silent-Studio-CN/SilentStudioCLI

让开发者体验更好一点。

用法:
  silentstudio                          显示此帮助信息
  silentstudio -v, --version            显示版本号
  silentstudio --window                启动 GUI 界面（0.1.5 暂不支持）
  silentstudio new <name> -l <lang>    创建新项目
  silentstudio new <name> --lang <lang>创建新项目
  silentstudio <pkg_name>              查询并安装生态库
  silentstudio install list            列出已安装的库
  silentstudio install list -a         列出所有已安装的库
  silentstudio install <pkg_name>      安装指定包
  silentstudio uninstall <pkg_name>    卸载指定包
  silentstudio ping                    检测所有索引源的可用性
  silentstudio ls                      列出当前目录内容
  silentstudio dir                     列出当前目录内容 (Windows)
  silentstudio pwd                     显示当前工作目录

示例:
  silentstudio new my-app -l java
  silentstudio slimemold
  silentstudio install list
  silentstudio install yaml
  silentstudio uninstall requests
  silentstudio ping
  silentstudio ls

更多信息: https://github.com/Silent-Studio-CN/SilentStudioCLI
""")
    else:
        print(f"""
SilentStudio CLI v{__version__}
© SilentStudio All Rights Reserved.
https://github.com/Silent-Studio-CN/SilentStudioCLI

Making developer experience better.

Usage:
  silentstudio                          Show this help
  silentstudio -v, --version            Show version
  silentstudio --window                Launch GUI (not supported in 0.1.5)
  silentstudio new <name> -l <lang>    Create new project
  silentstudio new <name> --lang <lang> Create new project
  silentstudio <pkg_name>              Query and install package
  silentstudio install list            List installed packages
  silentstudio install list -a         List all installed packages
  silentstudio install <pkg_name>      Install package
  silentstudio uninstall <pkg_name>    Uninstall package
  silentstudio ping                    Check index source availability
  silentstudio ls                      List current directory
  silentstudio dir                     List current directory (Windows)
  silentstudio pwd                     Show current working directory

Examples:
  silentstudio new my-app -l java
  silentstudio slimemold
  silentstudio install list
  silentstudio install yaml
  silentstudio uninstall requests
  silentstudio ping
  silentstudio ls

More info: https://github.com/Silent-Studio-CN/SilentStudioCLI
""")


def handle_ping(lang: str) -> int:
    """检测所有索引源的可用性"""
    index_urls = [
        "https://raw.githubusercontent.com/Silent-Studio-CN/index/main/index.jsonl",
        "https://gh-proxy.com/https://raw.githubusercontent.com/Silent-Studio-CN/index/main/index.jsonl",
        "https://ghproxy.net/https://raw.githubusercontent.com/Silent-Studio-CN/index/main/index.jsonl",
    ]
    
    # 读取用户配置
    try:
        config = load_config()
        configured_url = config.get("index_url", "")
        if configured_url:
            index_urls.insert(0, configured_url)
    except:
        pass
    
    # 去重
    seen = set()
    unique_urls = []
    for url in index_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    
    print("📡 正在检测索引源可用性...\n")
    
    available = []
    failed = []
    
    for url in unique_urls:
        try:
            start = time.time()
            resp = requests.get(url, timeout=5)
            elapsed = (time.time() - start) * 1000  # 毫秒
            
            if resp.status_code == 200:
                print(f"✅ {url}")
                print(f"   响应时间: {elapsed:.0f}ms | 状态码: {resp.status_code}")
                available.append(url)
            else:
                print(f"❌ {url}")
                print(f"   状态码: {resp.status_code}")
                failed.append(url)
        except Exception as e:
            print(f"❌ {url}")
            print(f"   错误: {str(e)[:80]}")
            failed.append(url)
        print()
    
    print("=" * 60)
    print(f"✅ 可用: {len(available)} 个")
    for url in available:
        print(f"   {url}")
    print(f"❌ 不可用: {len(failed)} 个")
    for url in failed:
        print(f"   {url}")
    
    if available:
        print(f"\n💡 推荐使用: {available[0]}")
    else:
        print("\n❌ 没有可用的索引源")
        return 1
    
    return 0


def handle_ls(lang: str) -> int:
    """列出当前目录内容"""
    try:
        items = os.listdir(".")
        items.sort()
        
        # 分离文件和目录
        dirs = []
        files = []
        for item in items:
            if os.path.isdir(item):
                dirs.append(item)
            else:
                files.append(item)
        
        # 输出
        for d in dirs:
            print(f"📁 {d}")
        for f in files:
            size = os.path.getsize(f)
            if size > 1024 * 1024:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} B"
            print(f"📄 {f} ({size_str})")
        
        print(f"\n共 {len(items)} 项")
        return 0
    except Exception as e:
        print(f"❌ 列出目录失败: {e}")
        return 1


def handle_pwd(lang: str) -> int:
    """显示当前工作目录"""
    print(os.getcwd())
    return 0


def main():
    """主入口"""
    lang = get_system_language()
    
    # 检查是否有参数
    if len(sys.argv) == 1:
        if lang == "zh-CN":
            print(f"SilentStudio CLI v{__version__}")
            print("© SilentStudio All Rights Reserved.")
            print("https://github.com/Silent-Studio-CN/SilentStudioCLI")
            print()
            print("使用 -h 或 --help 查看完整帮助")
        else:
            print(f"SilentStudio CLI v{__version__}")
            print("© SilentStudio All Rights Reserved.")
            print("https://github.com/Silent-Studio-CN/SilentStudioCLI")
            print()
            print("Use -h or --help for full help")
        return 0
    
    # ===== 处理 -w（已弃用） =====
    if len(sys.argv) >= 2 and sys.argv[1] == "-w":
        if lang == "zh-CN":
            print("⚠️ GUI 是 0.1.5 及以前的产物，你可以安装，但它并不好用")
            print("   安装: pip install silentstudio[window]")
            print("   启用: silentstudio --window")
        else:
            print("⚠️ GUI is a product of 0.1.5 and earlier, you can install it, but it's not working well")
            print("   Install: pip install silentstudio[window]")
            print("   Enable: silentstudio --window")
        return 1
    
    # ===== 先拦截包名安装 =====
    if len(sys.argv) == 2:
        arg = sys.argv[1]
        if arg not in ("new", "install", "uninstall", "ping", "ls", "dir", "pwd", "-v", "--version", "--window", "-h", "--help"):
            return handle_install(arg, lang)
    
    # 纯帮助请求
    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        show_help(lang)
        return 0
    
    # 解析参数
    parser = argparse.ArgumentParser(
        prog="silentstudio",
        description="SilentStudio CLI - 让开发者体验更好一点" if lang == "zh-CN" else "SilentStudio CLI - Making developer experience better",
        add_help=False
    )
    
    # 全局选项
    parser.add_argument("-v", "--version", action="store_true", help="显示版本号")
    parser.add_argument("--window", action="store_true", help="启动 GUI 界面")
    parser.add_argument("-h", "--help", action="store_true", help="显示帮助信息")
    
    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # new 子命令
    new_parser = subparsers.add_parser("new", help="创建新项目", add_help=False)
    new_parser.add_argument("name", help="项目名称")
    new_parser.add_argument("-l", "--lang", dest="language", required=True, help="编程语言 (java/python/go)")
    
    # install 子命令
    install_parser = subparsers.add_parser("install", help="安装相关", add_help=False)
    install_parser.add_argument("pkg_or_list", nargs="?", help="包名或 list")
    install_parser.add_argument("-a", "--all", action="store_true", help="显示所有库（默认只显示前 10 个）")
    
    # uninstall 子命令
    uninstall_parser = subparsers.add_parser("uninstall", help="卸载包", add_help=False)
    uninstall_parser.add_argument("pkg_name", help="要卸载的包名")
    
    # ping 子命令
    ping_parser = subparsers.add_parser("ping", help="检测索引源可用性", add_help=False)
    
    # ls 子命令
    ls_parser = subparsers.add_parser("ls", help="列出当前目录内容", add_help=False)
    
    # dir 子命令
    dir_parser = subparsers.add_parser("dir", help="列出当前目录内容", add_help=False)
    
    # pwd 子命令
    pwd_parser = subparsers.add_parser("pwd", help="显示当前工作目录", add_help=False)
    
    # 解析已知参数，忽略未知
    args, unknown = parser.parse_known_args()
    
    # 处理 -v/--version
    if args.version:
        print(f"SilentStudio CLI v{__version__}")
        print("© SilentStudio All Rights Reserved.")
        print("https://github.com/Silent-Studio-CN/SilentStudioCLI")
        return 0
    
    # 处理 --window
    if args.window:
        try:
            from .window import main as gui_main
            gui_main()
            return 0
        except ImportError as e:
            if lang == "zh-CN":
                print(f"❌ GUI 启动失败: {e}")
                print("   请确保已安装: pip install silentstudio[window]")
            else:
                print(f"❌ GUI failed to start: {e}")
                print("   Please ensure you have installed: pip install silentstudio[window]")
            return 1
    
    # 处理 -h/--help（作为全局选项）
    if args.help:
        show_help(lang)
        return 0
    
    # 处理子命令
    if args.command == "new":
        return handle_new(args.name, args.language)
    
    if args.command == "install":
        if args.pkg_or_list == "list":
            return handle_list_packages(show_all=args.all)
        elif args.pkg_or_list:
            return handle_install(args.pkg_or_list, lang)
        else:
            if lang == "zh-CN":
                print("❌ 请使用: silentstudio install list 或 silentstudio install <包名>")
            else:
                print("❌ Please use: silentstudio install list or silentstudio install <package_name>")
            return 1
    
    if args.command == "uninstall":
        pkg_name = args.pkg_name
        
        # 警告核心依赖
        if pkg_name in ("requests", "colorama"):
            if lang == "zh-CN":
                print(f"⚠️ 警告: {pkg_name} 是 SilentStudio 的核心依赖")
                print("   卸载后 SilentStudio 将无法正常工作")
                print("   是否继续? (y/N): ", end="")
            else:
                print(f"⚠️ Warning: {pkg_name} is a core dependency of SilentStudio")
                print("   SilentStudio will not work properly after uninstallation")
                print("   Continue? (y/N): ", end="")
            
            confirm = input().strip().lower()
            if confirm not in ("y", "yes"):
                print("❌ 已取消")
                return 0
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", pkg_name, "-y"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                if lang == "zh-CN":
                    print(f"✅ 成功卸载 {pkg_name}")
                else:
                    print(f"✅ Successfully uninstalled {pkg_name}")
                
                # 如果卸载的是 requests，提示可能影响功能
                if pkg_name in ("requests", "colorama"):
                    if lang == "zh-CN":
                        print(f"💡 提示: 如果 SilentStudio 出现问题，请执行: pip install {pkg_name}")
                    else:
                        print(f"💡 Tip: If SilentStudio malfunctions, run: pip install {pkg_name}")
            else:
                if lang == "zh-CN":
                    print(f"❌ 卸载失败: {result.stderr}")
                else:
                    print(f"❌ Uninstall failed: {result.stderr}")
            return result.returncode
        except Exception as e:
            print(f"❌ {e}")
            return 1
    
    if args.command == "ping":
        return handle_ping(lang)
    
    if args.command == "ls" or args.command == "dir":
        return handle_ls(lang)
    
    if args.command == "pwd":
        return handle_pwd(lang)
    
    # 如果 unknown 中有包名（fallback）
    if unknown:
        pkg_name = unknown[0]
        return handle_install(pkg_name, lang)
    
    # 默认显示帮助
    show_help(lang)
    return 0


if __name__ == "__main__":
    sys.exit(main())