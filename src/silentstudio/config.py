import json
import os
from pathlib import Path
from typing import Dict, Any


def get_config_dir() -> Path:
    """获取 SilentStudio 配置目录"""
    home = Path.home()
    config_dir = home / ".silentstudio"
    config_dir.mkdir(exist_ok=True)
    return config_dir


def get_config_file() -> Path:
    return get_config_dir() / "config.json"


def get_installed_file() -> Path:
    return get_config_dir() / "installed.json"


def get_cache_file() -> Path:
    return get_config_dir() / "index.cache.json"


DEFAULT_CONFIG = {
    "language": "auto",  # auto / zh-CN / en-US
    "pypi_mirror": "https://pypi.org/simple/",
    "index_url": "https://gh-proxy.com/https://raw.githubusercontent.com/Silent-Studio-CN/index/main/index.jsonl",
    "install_scope": "user",  # user / system
}


def load_config() -> Dict[str, Any]:
    """加载用户配置"""
    config_file = get_config_file()
    if not config_file.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
            # 合并默认配置（补全缺失的键）
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
            return config
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> None:
    """保存用户配置"""
    config_file = get_config_file()
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def load_installed() -> Dict[str, Any]:
    """加载安装记录"""
    installed_file = get_installed_file()
    if not installed_file.exists():
        return {"installed": []}
    
    try:
        with open(installed_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"installed": []}


def save_installed(data: Dict[str, Any]) -> None:
    """保存安装记录"""
    installed_file = get_installed_file()
    with open(installed_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_cache() -> Dict[str, Any]:
    """加载索引缓存"""
    cache_file = get_cache_file()
    if not cache_file.exists():
        return {}
    
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(data: Dict[str, Any]) -> None:
    """保存索引缓存"""
    cache_file = get_cache_file()
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)