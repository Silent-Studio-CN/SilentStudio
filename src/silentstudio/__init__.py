import subprocess
import sys

__version__ = "0.1.5"
__author__ = "SilentStudio"
__description__ = "SilentStudio CLI - 让开发者体验更好一点"

def ensure_requests():
    """确保 requests 已安装，没有则自动安装"""
    try:
        import requests
        return True
    except ImportError:
        print("📦 检测到 requests 未安装，正在自动安装...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "requests", "-q"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ requests 已自动安装")
                return True
            else:
                print(f"❌ 自动安装失败: {result.stderr}")
                print("   请手动执行: pip install requests")
                return False
        except Exception as e:
            print(f"❌ 自动安装失败: {e}")
            print("   请手动执行: pip install requests")
            return False

# 自动检测并安装
ensure_requests()

# 延迟导入 requests，确保已安装
import requests