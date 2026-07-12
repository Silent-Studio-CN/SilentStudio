import locale
import subprocess
import sys
from typing import Optional, Tuple


def detect_language() -> str:
    """检测系统语言"""
    try:
        lang = locale.getdefaultlocale()[0]
        if lang:
            if lang.startswith("zh"):
                return "zh-CN"
            elif lang.startswith("en"):
                return "en-US"
    except Exception:
        pass
    return "en-US"


def get_system_language(config_lang: str = "auto") -> str:
    """获取最终使用的语言"""
    if config_lang == "auto":
        return detect_language()
    return config_lang


def run_pip_command(args: list, scope: str = "user") -> Tuple[bool, str, str]:
    """执行 pip 命令"""
    cmd = [sys.executable, "-m", "pip"]
    if scope == "user":
        cmd.append("--user")
    cmd.extend(args)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        success = result.returncode == 0
        return success, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def get_pip_packages() -> list:
    """获取所有已安装的 pip 包"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        if result.returncode == 0:
            import json
            return json.loads(result.stdout)
        return []
    except Exception:
        return []


def get_package_version(pkg_name: str) -> Optional[str]:
    """获取指定包的版本号"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", pkg_name],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.startswith("Version:"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return None


def check_package_installed(pkg_name: str) -> bool:
    """检查包是否已安装"""
    return get_package_version(pkg_name) is not None