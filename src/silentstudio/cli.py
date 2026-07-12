#!/usr/bin/env python3
import argparse
import sys
from typing import Optional

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
SilentStudio CLI v{__version__} - 让开发者体验更好一点
主页: https://github.com/Silent-Studio-CN/SilentStudioCLI

用法:
  silentstudio                          显示此帮助信息
  silentstudio -v, --version            显示版本号
  silentstudio -w, --window            启动 GUI 界面
  silentstudio new <name> -l <lang>    创建新项目
  silentstudio new <name> --lang <lang>创建新项目
  silentstudio <pkg_name>              查询并安装生态库
  silentstudio install list            列出已安装的库

示例:
  silentstudio new my-app -l java
  silentstudio slimemold
  silentstudio install list
  silentstudio -w

更多信息: https://github.com/Silent-Studio-CN/SilentStudioCLI
""")
    else:
        print(f"""
SilentStudio CLI v{__version__} - Making developer experience better
Home: https://github.com/Silent-Studio-CN/SilentStudioCLI

Usage:
  silentstudio                          Show this help
  silentstudio -v, --version            Show version
  silentstudio -w, --window            Launch GUI
  silentstudio new <name> -l <lang>    Create new project
  silentstudio new <name> --lang <lang> Create new project
  silentstudio <pkg_name>              Query and install package
  silentstudio install list            List installed packages

Examples:
  silentstudio new my-app -l java
  silentstudio slimemold
  silentstudio install list
  silentstudio -w

More info: https://github.com/Silent-Studio-CN/SilentStudioCLI
""")


def main():
    """主入口"""
    lang = get_system_language()
    
    # 检查是否有参数
    if len(sys.argv) == 1:
        show_help(lang)
        return 0
    
    # 解析参数
    parser = argparse.ArgumentParser(
        prog="silentstudio",
        description="SilentStudio CLI - 让开发者体验更好一点" if lang == "zh-CN" else "SilentStudio CLI - Making developer experience better",
        add_help=False  # 自定义帮助
    )
    
    # 全局选项
    parser.add_argument("-v", "--version", action="store_true", help="显示版本号")
    parser.add_argument("-w", "--window", action="store_true", help="启动 GUI 界面")
    parser.add_argument("-h", "--help", action="store_true", help="显示帮助信息")
    
    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # new 子命令
    new_parser = subparsers.add_parser("new", help="创建新项目", add_help=False)
    new_parser.add_argument("name", help="项目名称")
    new_parser.add_argument("-l", "--lang", dest="language", required=True, help="编程语言 (java/python/go)")
    
    # install list 子命令
    install_parser = subparsers.add_parser("install", help="安装相关", add_help=False)
    install_subparsers = install_parser.add_subparsers(dest="install_cmd", help="安装子命令")
    list_parser = install_subparsers.add_parser("list", help="列出已安装的库", add_help=False)
    
    # 解析已知参数，忽略未知（处理 silentstudio <pkg_name>）
    args, unknown = parser.parse_known_args()
    
    # 处理 -h/--help
    if args.help or (len(sys.argv) >= 2 and sys.argv[1] in ("-h", "--help")):
        show_help(lang)
        return 0
    
    # 处理 -v/--version
    if args.version:
        print(f"SilentStudio CLI v{__version__}")
        return 0
    
    # 处理 -w/--window
    if args.window:
        try:
            from .window import main as gui_main
            gui_main()
            return 0
        except ImportError:
            if lang == "zh-CN":
                print("❌ GUI 组件未安装，请执行: pip install silentstudio[window]")
            else:
                print("❌ GUI component not installed, please run: pip install silentstudio[window]")
            return 1
    
    # 处理子命令
    if args.command == "new":
        return handle_new(args.name, args.language)
    
    if args.command == "install":
        if args.install_cmd == "list":
            return handle_list_packages()
        else:
            if lang == "zh-CN":
                print("❌ 未知的 install 子命令，请使用: silentstudio install list")
            else:
                print("❌ Unknown install subcommand, use: silentstudio install list")
            return 1
    
    # 处理 silentstudio <pkg_name> (安装)
    if len(sys.argv) >= 2:
        pkg_name = sys.argv[1]
        # 排除命令本身
        if pkg_name not in ("new", "install", "-v", "--version", "-w", "--window", "-h", "--help"):
            return handle_install(pkg_name, lang)
    
    # 默认显示帮助
    show_help(lang)
    return 0


if __name__ == "__main__":
    sys.exit(main())