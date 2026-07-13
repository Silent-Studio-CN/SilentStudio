import locale
import subprocess
import sys
import os
from pathlib import Path
from typing import Optional, Tuple

# 支持的语言列表（内置）
BUILTIN_LANGS = {"zh-CN", "en-US"}

# 所有支持的语言（内置 + 可下载）
SUPPORTED_LANGS = {
    "zh-CN", "en-US", "ja-JP", "ru-RU", 
    "ko-KR", "fr-FR", "de-DE", "es-ES"
}


def detect_system_language() -> str:
    """检测系统语言"""
    # 临时强制中文
    return "zh-CN"


def get_lang_file_path(lang_code: str) -> Path:
    """获取语言文件路径"""
    return Path(__file__).parent / "lang" / f"{lang_code}.lang"


def ensure_language(lang_code: str) -> str:
    """确保语言可用，返回最终使用的语言代码"""
    # 1. 检查配置文件
    try:
        from .config import load_config
        config = load_config()
        config_lang = config.get("language")
        if config_lang and config_lang in SUPPORTED_LANGS:
            lang_code = config_lang
    except:
        pass
    
    # 2. 检查环境变量
    env_lang = os.environ.get("SILENTSTUDIO_LANG")
    if env_lang and env_lang in SUPPORTED_LANGS:
        lang_code = env_lang
    
    # 3. 如果没有指定，检测系统语言
    if not lang_code or lang_code == "auto":
        lang_code = detect_system_language()
    
    # 4. 如果不在支持列表中，fallback 到英文
    if lang_code not in SUPPORTED_LANGS:
        return "en-US"
    
    # 5. 检查语言文件是否存在
    lang_file = get_lang_file_path(lang_code)
    if lang_file.exists():
        return lang_code
    
    # 6. 如果是内置语言，但没有文件（理论上不会发生）
    if lang_code in BUILTIN_LANGS:
        create_default_lang_file(lang_code)
        return lang_code
    
    # 7. 尝试自动下载语言包
    if lang_code not in BUILTIN_LANGS:
        auto_install_language(lang_code)
        if get_lang_file_path(lang_code).exists():
            return lang_code
    
    # 8. 所有都失败，fallback 到英文
    return "en-US"


def auto_install_language(lang_code: str) -> bool:
    """自动下载语言包"""
    print(f"📦 正在下载 {lang_code} 语言包...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", f"silentstudio-lang-{lang_code}", "-q"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ {lang_code} 语言包安装完成")
            return True
        else:
            print(f"❌ 语言包安装失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 语言包安装失败: {e}")
        return False


def create_default_lang_file(lang_code: str) -> None:
    """创建默认语言文件（内置语言 fallback）"""
    lang_file = get_lang_file_path(lang_code)
    lang_file.parent.mkdir(parents=True, exist_ok=True)
    
    default_content = {
        "zh-CN": """# SilentStudio 中文语言文件
ready=就绪
search_placeholder=🔍 搜索包名...
""",
        "en-US": """# SilentStudio English language file
ready=Ready
search_placeholder=🔍 Search package name...
"""
    }
    
    content = default_content.get(lang_code, "")
    if content:
        with open(lang_file, "w", encoding="utf-8") as f:
            f.write(content)


def get_system_language(config_lang: str = "auto") -> str:
    """获取最终使用的语言（兼容旧接口）"""
    print(f"🔍 DEBUG: config_lang = {config_lang}")  # 加这行
    if config_lang == "auto":
        result = ensure_language("auto")
        print(f"🔍 DEBUG: result = {result}")  # 加这行
        return result
    result = ensure_language(config_lang)
    print(f"🔍 DEBUG: result = {result}")
    return result

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
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def get_package_version(pkg_name: str) -> Optional[str]:
    """获取指定包的版本号"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", pkg_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.startswith("Version:"):
                    return line.split(":", 1)[1].strip()
    except:
        pass
    return None


def check_package_installed(pkg_name: str) -> bool:
    """检查包是否已安装"""
    return get_package_version(pkg_name) is not None


def get_pip_packages() -> list:
    """获取所有已安装的 pip 包"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            import json
            return json.loads(result.stdout)
    except:
        pass
    return []