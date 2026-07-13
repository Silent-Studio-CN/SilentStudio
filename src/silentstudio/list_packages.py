import argparse
from typing import Dict, Any

from .config import load_installed
from .utils import get_pip_packages
from .utils import get_system_language


def format_package_list(show_all: bool = False) -> str:
    """格式化包列表"""
    lang = get_system_language()
    
    # 获取所有包
    all_pkgs = get_pip_packages()
    
    # 获取 SilentStudio 安装的记录
    installed_data = load_installed()
    silent_names = {pkg["name"] for pkg in installed_data.get("installed", [])}
    
    # 分类
    silent_pkgs = []
    other_pkgs = []
    for pkg in all_pkgs:
        name = pkg.get("name", "")
        if name in silent_names:
            silent_pkgs.append(pkg)
        else:
            other_pkgs.append(pkg)
    
    # 排序
    silent_pkgs.sort(key=lambda x: x.get("name", ""))
    other_pkgs.sort(key=lambda x: x.get("name", ""))
    
    # 构建输出
    lines = []
    
    if lang == "zh-CN":
        lines.append(f"📦 已安装 Python 库 (共 {len(all_pkgs)} 个)")
        lines.append("")
        
        if silent_pkgs:
            lines.append(f"✦ SilentStudio 安装 ({len(silent_pkgs)} 个):")
            for i, pkg in enumerate(silent_pkgs):
                name = pkg.get("name", "")
                version = pkg.get("version", "未知")
                lines.append(f"  {name}  v{version}")
        
        if silent_pkgs and other_pkgs:
            lines.append("")
        
        if other_pkgs:
            lines.append(f"📚 其他库 ({len(other_pkgs)} 个):")
            if show_all:
                display = other_pkgs
            else:
                display = other_pkgs[:10]
                if len(other_pkgs) > 10:
                    lines.append(f"  (显示前 10 个，共 {len(other_pkgs)} 个，使用 -a 查看全部)")
            
            for pkg in display:
                name = pkg.get("name", "")
                version = pkg.get("version", "未知")
                lines.append(f"  {name}  v{version}")
            
            if not show_all and len(other_pkgs) > 10:
                lines.append(f"  ... 还有 {len(other_pkgs) - 10} 个")
    
    else:
        lines.append(f"📦 Installed Python Packages (total: {len(all_pkgs)})")
        lines.append("")
        
        if silent_pkgs:
            lines.append(f"✦ Installed via SilentStudio ({len(silent_pkgs)}):")
            for i, pkg in enumerate(silent_pkgs):
                name = pkg.get("name", "")
                version = pkg.get("version", "unknown")
                lines.append(f"  {name}  v{version}")
        
        if silent_pkgs and other_pkgs:
            lines.append("")
        
        if other_pkgs:
            lines.append(f"📚 Other packages ({len(other_pkgs)}):")
            if show_all:
                display = other_pkgs
            else:
                display = other_pkgs[:10]
                if len(other_pkgs) > 10:
                    lines.append(f"  (showing first 10 of {len(other_pkgs)}, use -a to show all)")
            
            for pkg in display:
                name = pkg.get("name", "")
                version = pkg.get("version", "unknown")
                lines.append(f"  {name}  v{version}")
            
            if not show_all and len(other_pkgs) > 10:
                lines.append(f"  ... and {len(other_pkgs) - 10} more")
    
    return "\n".join(lines)


def handle_list_packages(show_all: bool = False) -> int:
    """处理 list 命令"""
    try:
        print(format_package_list(show_all))
        return 0
    except Exception as e:
        lang = get_system_language()
        msg_zh = f"❌ 获取包列表失败: {e}"
        msg_en = f"❌ Failed to get package list: {e}"
        print(msg_zh if lang == "zh-CN" else msg_en)
        return 1