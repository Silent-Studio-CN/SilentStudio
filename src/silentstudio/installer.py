import json
import sys
from typing import Optional, Tuple

import requests

from .config import load_config, load_installed, save_installed
from .utils import (
    run_pip_command,
    get_system_language,
    check_package_installed,
    get_package_version,
)


def fetch_index() -> list:
    """从服务器拉取索引"""
    config = load_config()
    index_url = config.get("index_url", "")
    
    try:
        resp = requests.get(index_url, timeout=10)
        if resp.status_code == 200:
            entries = []
            for line in resp.text.splitlines():
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            return entries
        return []
    except Exception:
        return []


def check_pypi(pkg_name: str) -> Tuple[bool, Optional[str]]:
    """检查 PyPI 上是否存在该包"""
    try:
        url = f"https://pypi.org/pypi/{pkg_name}/json"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            version = data.get("info", {}).get("version")
            return True, version
        return False, None
    except Exception:
        return False, None


def install_package(pkg_name: str, channel: str = "pypi") -> Tuple[bool, str]:
    """安装包"""
    config = load_config()
    scope = config.get("install_scope", "user")
    
    if channel == "pypi":
        pip_args = ["install", pkg_name]
        success, stdout, stderr = run_pip_command(pip_args, scope)
        
        if success:
            version = get_package_version(pkg_name)
            if version:
                record_installation(pkg_name, version, "pypi")
            return True, f"✅ 成功安装 {pkg_name} (版本: {version or '未知'})"
        else:
            return False, f"❌ 安装失败: {stderr or stdout}"
    
    return False, f"❌ 不支持的渠道: {channel}"


def record_installation(name: str, version: str, channel: str) -> None:
    """记录安装到 installed.json"""
    data = load_installed()
    
    # 检查是否已存在
    for pkg in data["installed"]:
        if pkg["name"] == name:
            pkg["version"] = version
            pkg["channel"] = channel
            pkg["installed_at"] = __import__("datetime").datetime.now().isoformat()
            save_installed(data)
            return
    
    # 新增
    data["installed"].append({
        "name": name,
        "version": version,
        "channel": channel,
        "installed_at": __import__("datetime").datetime.now().isoformat()
    })
    save_installed(data)


def handle_install(pkg_name: str, lang: str) -> int:
    """处理安装逻辑"""
    # 检查是否已安装
    if check_package_installed(pkg_name):
        version = get_package_version(pkg_name)
        msg_zh = f"✅ {pkg_name} 已安装 (版本: {version})"
        msg_en = f"✅ {pkg_name} is already installed (version: {version})"
        print(msg_zh if lang == "zh-CN" else msg_en)
        return 0
    
    # 1. 拉取 SilentStudio 索引
    print("📡 正在查询 SilentStudio 索引..." if lang == "zh-CN" else "📡 Querying SilentStudio index...")
    index = fetch_index()
    
    # 查找匹配
    matched = None
    for entry in index:
        if entry.get("name", "").lower() == pkg_name.lower():
            matched = entry
            break
        if entry.get("pkg_name", "").lower() == pkg_name.lower():
            matched = entry
            break
    
    if matched:
        channel = matched.get("channel", "pypi")
        pkg_name_actual = matched.get("pkg_name", pkg_name)
        
        if channel == "pypi":
            print(f"📦 从 PyPI 安装 {pkg_name_actual}..." if lang == "zh-CN" else f"📦 Installing {pkg_name_actual} from PyPI...")
            success, msg = install_package(pkg_name_actual, "pypi")
            print(msg)
            return 0 if success else 1
    
    # 2. 未在索引中找到，回退到 PyPI
    msg_zh_not_found = f"⚠️ 您搜索的 '{pkg_name}' 并未在 SilentStudio 项目列表中查询到"
    msg_en_not_found = f"⚠️ '{pkg_name}' was not found in the SilentStudio project list"
    print(msg_zh_not_found if lang == "zh-CN" else msg_en_not_found)
    
    exists, version = check_pypi(pkg_name)
    if exists:
        msg_zh_pypi = f"📦 但在官方 PyPI 上找到了同名库 (最新版本: {version})"
        msg_en_pypi = f"📦 But found the same-named package on PyPI (latest version: {version})"
        print(msg_zh_pypi if lang == "zh-CN" else msg_en_pypi)
        
        prompt_zh = "是否安装？[y/N]: "
        prompt_en = "Install? [y/N]: "
        prompt = prompt_zh if lang == "zh-CN" else prompt_en
        
        try:
            answer = input(prompt).strip().lower()
        except KeyboardInterrupt:
            print("\n❌ 已取消")
            return 1
        
        if answer in ("y", "yes", "是"):
            success, msg = install_package(pkg_name, "pypi")
            print(msg)
            return 0 if success else 1
        else:
            print("❌ 已取消安装" if lang == "zh-CN" else "❌ Installation cancelled")
            return 0
    else:
        msg_zh_not_found_all = f"❌ 未在任何源中找到 '{pkg_name}'"
        msg_en_not_found_all = f"❌ '{pkg_name}' not found in any source"
        print(msg_zh_not_found_all if lang == "zh-CN" else msg_en_not_found_all)
        return 1