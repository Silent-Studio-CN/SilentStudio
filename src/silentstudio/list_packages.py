from typing import Dict, Any

from .config import load_installed
from .utils import get_pip_packages
from .utils import get_system_language


def format_package_list() -> str:
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
    width = 60
    
    if lang == "zh-CN":
        lines.append("╔" + "═" * width + "╗")
        lines.append("║" + " 📦 已安装 Python 库".ljust(width) + "║")
        lines.append("╠" + "═" * width + "╣")
        
        if silent_pkgs:
            lines.append(f"║  ✦ SilentStudio 安装 ({len(silent_pkgs)} 个):".ljust(width) + "║")
            for i, pkg in enumerate(silent_pkgs):
                name = pkg.get("name", "")
                version = pkg.get("version", "未知")
                prefix = "    ├─ " if i < len(silent_pkgs) - 1 else "    └─ "
                lines.append(f"║  {prefix}{name}".ljust(width - 20) + f"v{version}".rjust(20) + "║")
        
        if silent_pkgs and other_pkgs:
            lines.append("╠" + "═" * width + "╣")
        
        if other_pkgs:
            lines.append(f"║  📚 其他库 ({len(other_pkgs)} 个):".ljust(width) + "║")
            # 只显示前 20 个，避免太长
            display = other_pkgs[:20]
            for i, pkg in enumerate(display):
                name = pkg.get("name", "")
                version = pkg.get("version", "未知")
                prefix = "    ├─ " if i < len(display) - 1 else "    └─ "
                lines.append(f"║  {prefix}{name}".ljust(width - 20) + f"v{version}".rjust(20) + "║")
            
            if len(other_pkgs) > 20:
                lines.append(f"║    ... 还有 {len(other_pkgs) - 20} 个".ljust(width) + "║")
        
        lines.append("╚" + "═" * width + "╝")
    
    else:
        lines.append("╔" + "═" * width + "╗")
        lines.append("║" + " 📦 Installed Python Packages".ljust(width) + "║")
        lines.append("╠" + "═" * width + "╣")
        
        if silent_pkgs:
            lines.append(f"║  ✦ Installed via SilentStudio ({len(silent_pkgs)}):".ljust(width) + "║")
            for i, pkg in enumerate(silent_pkgs):
                name = pkg.get("name", "")
                version = pkg.get("version", "unknown")
                prefix = "    ├─ " if i < len(silent_pkgs) - 1 else "    └─ "
                lines.append(f"║  {prefix}{name}".ljust(width - 20) + f"v{version}".rjust(20) + "║")
        
        if silent_pkgs and other_pkgs:
            lines.append("╠" + "═" * width + "╣")
        
        if other_pkgs:
            lines.append(f"║  📚 Other packages ({len(other_pkgs)}):".ljust(width) + "║")
            display = other_pkgs[:20]
            for i, pkg in enumerate(display):
                name = pkg.get("name", "")
                version = pkg.get("version", "unknown")
                prefix = "    ├─ " if i < len(display) - 1 else "    └─ "
                lines.append(f"║  {prefix}{name}".ljust(width - 20) + f"v{version}".rjust(20) + "║")
            
            if len(other_pkgs) > 20:
                lines.append(f"║    ... and {len(other_pkgs) - 20} more".ljust(width) + "║")
        
        lines.append("╚" + "═" * width + "╝")
    
    return "\n".join(lines)


def handle_list_packages() -> int:
    """处理 list 命令"""
    try:
        print(format_package_list())
        return 0
    except Exception as e:
        lang = get_system_language()
        msg_zh = f"❌ 获取包列表失败: {e}"
        msg_en = f"❌ Failed to get package list: {e}"
        print(msg_zh if lang == "zh-CN" else msg_en)
        return 1