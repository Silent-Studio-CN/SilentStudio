import sys
import json
import subprocess
import threading
from pathlib import Path
from typing import Dict, Optional, List

import requests

from PySide6.QtCore import Qt, QTimer, Signal, QObject, Slot
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QFrame,
    QMessageBox, QDialog, QGridLayout, QComboBox,
    QHeaderView, QTableWidget, QTableWidgetItem,
    QListWidget, QListWidgetItem, QStackedWidget
)

from qfluentwidgets import (
    FluentWindow, FluentIcon, NavigationItemPosition,
    setTheme, Theme, setThemeColor,
    PrimaryPushButton, PushButton, LineEdit, ComboBox,
    SwitchButton, SpinBox,
    InfoBar, InfoBarPosition,
    BodyLabel, CaptionLabel, StrongBodyLabel,
    SubtitleLabel, TitleLabel, CardWidget,
    SmoothScrollArea, TransparentToolButton,
    IndeterminateProgressRing, ProgressRing,
    ToolTipFilter, TableWidget, ListWidget,
    HorizontalSeparator, VerticalSeparator
)


# ===================== CLI 调用器 =====================
class CLICaller:
    """调用 silentstudio CLI 命令"""
    
    @staticmethod
    def run_command(args: list) -> tuple:
        """执行 CLI 命令"""
        cmd = [sys.executable, "-m", "silentstudio"] + args
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
    
    @staticmethod
    def get_version() -> str:
        """获取版本号"""
        success, stdout, _ = CLICaller.run_command(["-v"])
        if success:
            return stdout.strip()
        return "0.0.0"
    
    @staticmethod
    def install_package(name: str) -> tuple:
        """安装包 - 调用 silentstudio install <name>"""
        return CLICaller.run_command(["install", name])
    
    @staticmethod
    def uninstall_package(name: str) -> tuple:
        """卸载包 - 调用 pip uninstall"""
        return CLICaller.run_command(["pip", "uninstall", name, "-y"])
    
    @staticmethod
    def update_package(name: str) -> tuple:
        """更新包 - 调用 pip install --upgrade"""
        return CLICaller.run_command(["pip", "install", "--upgrade", name])
    
    @staticmethod
    def list_packages(show_all: bool = False) -> tuple:
        """列出已安装的包 - 调用 silentstudio install list"""
        args = ["install", "list"]
        if show_all:
            args.append("-a")
        return CLICaller.run_command(args)
    
    @staticmethod
    def detect_region() -> str:
        """检测用户所在地区，返回 'CN' 或 'OTHER'"""
        try:
            resp = requests.get('http://ip-api.com/json/', timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('status') == 'success':
                    country_code = data.get('countryCode', '')
                    if country_code == 'CN':
                        return 'CN'
                    else:
                        return 'OTHER'
        except Exception as e:
            print(f"⚠️ IP 检测失败: {e}")
        # 默认返回 OTHER（使用官方源）
        return 'OTHER'
    
    @staticmethod
    def get_index_packages() -> Dict[str, dict]:
        """获取 SilentStudio 索引包（根据 IP 自动选择源）"""
        result = {}
        
        # 检测地区
        region = CLICaller.detect_region()
        print(f"📍 检测到地区: {region}")
        
        if region == 'CN':
            # 国内使用镜像
            index_urls = [
                "https://gh-proxy.com/https://raw.githubusercontent.com/Silent-Studio-CN/index/main/index.jsonl",
                "https://ghproxy.net/https://raw.githubusercontent.com/Silent-Studio-CN/index/main/index.jsonl",
            ]
        else:
            # 国外使用官方源
            index_urls = [
                "https://raw.githubusercontent.com/Silent-Studio-CN/index/main/index.jsonl",
            ]
        
        # 如果用户配置了自定义 URL，优先使用
        try:
            from .config import load_config
            config = load_config()
            configured_url = config.get("index_url", "")
            if configured_url:
                index_urls.insert(0, configured_url)
        except:
            pass
        
        for url in index_urls:
            try:
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    for line in resp.text.splitlines():
                        if line.strip():
                            try:
                                data = json.loads(line)
                                name = data.get("name", "")
                                if name:
                                    result[name] = data
                            except:
                                continue
                    if result:
                        print(f"✅ 索引加载成功: {url}")
                        return result
            except Exception as e:
                print(f"⚠️ 索引加载失败: {url} - {e}")
                continue
        
        print("⚠️ 所有索引源均失败，仅显示已安装的包")
        return result
    
    @staticmethod
    def get_package_info_from_pypi(pkg_name: str) -> dict:
        """从 PyPI API 获取包详细信息"""
        try:
            import requests
            url = f"https://pypi.org/pypi/{pkg_name}/json"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                info = data.get("info", {})
                return {
                    "author": info.get("author", ""),
                    "license": info.get("license", ""),
                    "homepage": info.get("home_page", ""),
                    "description": info.get("summary", ""),
                    "version": info.get("version", ""),
                    "size": info.get("size", 0),
                }
        except:
            pass
        return {}
    
    @staticmethod
    def get_package_install_path(pkg_name: str) -> str:
        """获取包的安装路径（通过 pip show）"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", pkg_name],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if line.startswith("Location:"):
                        return line.split(":", 1)[1].strip()
        except:
            pass
        return ""
    
    @staticmethod
    def get_installed_packages() -> Dict[str, dict]:
        """获取所有已安装的包（通过 pip list）"""
        result = {}
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=json"],
                capture_output=True, text=True
            )
            if proc.returncode == 0:
                data = json.loads(proc.stdout)
                for pkg in data:
                    name = pkg.get("name", "")
                    if name:
                        result[name] = {"version": pkg.get("version", "")}
        except:
            pass
        return result
    
    @staticmethod
    def get_package_size(pkg_name: str) -> int:
        """获取包的大小（通过 pip show 获取）"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", pkg_name],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if line.startswith("Size:"):
                        try:
                            return int(line.split(":", 1)[1].strip())
                        except:
                            return 0
        except:
            pass
        return 0


# ===================== 语言管理器 =====================
class LanguageManager(QObject):
    language_changed = Signal()
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if LanguageManager._initialized:
            return
        super().__init__()
        LanguageManager._initialized = True
        self._init()

    def _init(self):
        self.lang_dir = Path(__file__).parent / "lang"
        self.current_lang = "zh-CN"
        self.strings = {}
        self.load_language(self.current_lang)
    
    def load_language(self, lang_code: str):
        self.current_lang = lang_code
        lang_file = self.lang_dir / f"{lang_code}.lang"
        
        if not lang_file.exists():
            lang_file = self.lang_dir / "zh-CN.lang"
        
        self.strings = {}
        try:
            with open(lang_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        self.strings[key.strip()] = value.strip()
        except Exception as e:
            print(f"加载语言文件失败: {e}")
        
        self.language_changed.emit()
    
    def get(self, key: str, *args, **kwargs) -> str:
        """获取翻译字符串，兼容多种调用方式"""
        text = self.strings.get(key)
        
        if text is None:
            if args:
                default = args[0]
            else:
                default = kwargs.get("default", key)
            text = default
        
        if kwargs:
            format_kwargs = {k: v for k, v in kwargs.items() if k != "default"}
            if format_kwargs:
                try:
                    return text.format(**format_kwargs)
                except:
                    return text
        
        return text


# ===================== 设置管理器 =====================
class SettingsManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        self.config_file = Path.home() / ".silentstudio" / "config.json"
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config = self._load()
    
    def _load(self) -> dict:
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return self._default()
    
    def _default(self) -> dict:
        return {
            "language": "zh-CN",
            "pypi_mirror": "https://pypi.org/simple",
            "index_url": "",
            "auto_check_update": True,
            "auto_install_update": False,
            "check_interval_hours": 6,
            "theme_color": "#89b4fa"
        }
    
    def get(self, key: str, default=None):
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        self.config[key] = value
        self._save()
    
    def _save(self):
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)


# ===================== 包数据 =====================
class PackageInfo:
    def __init__(self, name: str):
        self.name = name
        self.version = ""
        self.latest_version = ""
        self.description = ""
        self.is_installed = False
        self.is_updatable = False
        self.author = ""
        self.homepage = ""
        self.license = ""
        self.installed_path = ""
        self.size = 0


# ===================== 安装进度对话框 =====================
class InstallProgressDialog(QDialog):
    def __init__(self, pkg_name: str, parent=None, action: str = "install"):
        super().__init__(parent)
        self.pkg_name = pkg_name
        self.action = action
        self.lang = LanguageManager()
        self.setWindowTitle(self.lang.get("install_dialog_title", default="安装 {name}", name=pkg_name))
        self.setFixedSize(520, 400)
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                border-radius: 12px;
                border: 1px solid #45475a;
            }
            QLabel {
                color: #cdd6f4;
            }
            QTextEdit {
                background-color: #11111b;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                font-family: "Cascadia Code", "Consolas", monospace;
                font-size: 12px;
                padding: 8px;
            }
            QPushButton {
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton#close_btn {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
            }
            QPushButton#close_btn:hover {
                background-color: #6c7086;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)
        
        # 标题栏
        title_layout = QHBoxLayout()
        title_layout.setSpacing(12)
        
        self.spinner = IndeterminateProgressRing()
        self.spinner.setFixedSize(32, 32)
        title_layout.addWidget(self.spinner)
        
        self.title_label = SubtitleLabel(self.lang.get("installing", default="正在安装 {name}...", name=self.pkg_name))
        self.title_label.setStyleSheet("color: #89b4fa;")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        
        close_btn = TransparentToolButton()
        close_btn.setIcon(FluentIcon.CLOSE)
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)
        
        main_layout.addLayout(title_layout)
        
        # 进度环
        self.progress = ProgressRing()
        self.progress.setFixedSize(60, 60)
        self.progress.setValue(0)
        
        progress_layout = QHBoxLayout()
        progress_layout.addStretch()
        progress_layout.addWidget(self.progress)
        progress_layout.addStretch()
        main_layout.addLayout(progress_layout)
        
        # 输出
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumHeight(160)
        self.output.setMinimumHeight(100)
        main_layout.addWidget(self.output)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.close_btn = QPushButton(self.lang.get("close_btn", default="关闭"))
        self.close_btn.setObjectName("close_btn")
        self.close_btn.setEnabled(False)
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(btn_layout)
    
    def append_output(self, text: str):
        self.output.append(text)
        self.output.moveCursor(self.output.textCursor().End)
        
        if "成功" in text or "✅" in text or "successfully" in text:
            self.progress.setValue(100)
        elif "失败" in text or "❌" in text or "failed" in text:
            self.progress.setValue(0)
        elif self.progress.value() < 90:
            self.progress.setValue(self.progress.value() + 5)
    
    def set_success(self):
        self.spinner.hide()
        self.title_label.setText(self.lang.get("install_success", default="✅ {name} 安装完成", name=self.pkg_name))
        self.title_label.setStyleSheet("color: #a6e3a1;")
        self.close_btn.setEnabled(True)
        self.progress.setValue(100)
    
    def set_error(self, error: str):
        self.spinner.hide()
        self.title_label.setText(self.lang.get("install_failed", default="❌ 安装失败"))
        self.title_label.setStyleSheet("color: #f38ba8;")
        self.append_output(f"\n{self.lang.get('error_prefix', default='错误')}: {error}")
        self.close_btn.setEnabled(True)
        self.progress.setValue(0)


# ===================== 包列表项（类似 Windows 设置） =====================
class PackageListItem(QWidget):
    install_clicked = Signal(str)
    uninstall_clicked = Signal(str)
    update_clicked = Signal(str)
    detail_clicked = Signal(str)
    
    def __init__(self, pkg: PackageInfo, parent=None):
        super().__init__(parent)
        self.pkg = pkg
        self.lang = LanguageManager()
        self.setup_ui()
        self.setToolTip("双击查看详情")
    
    def setup_ui(self):
        self.setStyleSheet("""
            PackageListItem {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 8px 12px;
            }
            PackageListItem:hover {
                background-color: #45475a;
                border: 1px solid #89b4fa;
            }
            QLabel#name {
                color: #cdd6f4;
                font-size: 14px;
                font-weight: bold;
            }
            QLabel#version {
                color: #6c7086;
                font-size: 12px;
            }
            QLabel#size {
                color: #6c7086;
                font-size: 11px;
            }
            QLabel#desc {
                color: #a6adc8;
                font-size: 12px;
            }
        """)
        
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 8, 12, 8)
        
        # 左侧：信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        # 第一行：名称 + 版本 + 状态
        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        
        name_label = QLabel(self.pkg.name)
        name_label.setObjectName("name")
        name_row.addWidget(name_label)
        
        version_label = QLabel(f"v{self.pkg.version}" if self.pkg.version else "")
        version_label.setObjectName("version")
        name_row.addWidget(version_label)
        
        # 状态标签
        if self.pkg.is_installed:
            if self.pkg.is_updatable:
                status = "⬆️ 可更新"
                color = "#f9e2af"
            else:
                status = "✓ 已安装"
                color = "#a6e3a1"
        else:
            status = "✗ 未安装"
            color = "#6c7086"
        
        status_label = QLabel(status)
        status_label.setStyleSheet(
            f"background-color: {color}; color: #1e1e2e; "
            f"padding: 1px 10px; border-radius: 10px; font-size: 11px; font-weight: bold;"
        )
        name_row.addWidget(status_label)
        name_row.addStretch()
        info_layout.addLayout(name_row)
        
        # 第二行：描述 + 大小
        desc_row = QHBoxLayout()
        desc_label = QLabel(self.pkg.description or "暂无描述")
        desc_label.setObjectName("desc")
        desc_label.setWordWrap(True)
        desc_row.addWidget(desc_label)
        
        if self.pkg.is_installed and self.pkg.size > 0:
            size_label = QLabel(f"📦 {self.pkg.size/1024:.1f} KB")
            size_label.setObjectName("size")
            desc_row.addWidget(size_label)
        
        desc_row.addStretch()
        info_layout.addLayout(desc_row)
        
        main_layout.addLayout(info_layout, 1)
        
        # 右侧：操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        if self.pkg.is_installed:
            if self.pkg.is_updatable:
                update_btn = PushButton("更新")
                update_btn.setStyleSheet("""
                    background-color: #f9e2af;
                    color: #1e1e2e;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 14px;
                    font-size: 12px;
                """)
                update_btn.clicked.connect(lambda: self.update_clicked.emit(self.pkg.name))
                btn_layout.addWidget(update_btn)
            
            uninstall_btn = PushButton("卸载")
            uninstall_btn.setStyleSheet("""
                background-color: #f38ba8;
                color: #1e1e2e;
                border: none;
                border-radius: 4px;
                padding: 4px 14px;
                font-size: 12px;
            """)
            uninstall_btn.clicked.connect(lambda: self.uninstall_clicked.emit(self.pkg.name))
            btn_layout.addWidget(uninstall_btn)
        else:
            install_btn = PrimaryPushButton("安装")
            install_btn.setStyleSheet("""
                border: none;
                border-radius: 4px;
                padding: 4px 18px;
                font-size: 12px;
            """)
            install_btn.clicked.connect(lambda: self.install_clicked.emit(self.pkg.name))
            btn_layout.addWidget(install_btn)
        
        detail_btn = TransparentToolButton()
        detail_btn.setIcon(FluentIcon.INFO)
        detail_btn.setToolTip("查看详情")
        detail_btn.clicked.connect(lambda: self.detail_clicked.emit(self.pkg.name))
        btn_layout.addWidget(detail_btn)
        
        main_layout.addLayout(btn_layout)
    
    def mouseDoubleClickEvent(self, event):
        self.detail_clicked.emit(self.pkg.name)


# ===================== 包详情对话框 =====================
class PackageDetailDialog(QDialog):
    def __init__(self, pkg: PackageInfo, parent=None):
        super().__init__(parent)
        self.pkg = pkg
        self.lang = LanguageManager()
        self.setWindowTitle(self.lang.get("detail_title", default="{name} - 详情", name=pkg.name))
        self.setFixedSize(520, 420)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                border-radius: 12px;
                border: 1px solid #45475a;
            }
            QLabel {
                color: #cdd6f4;
            }
            QLabel#value {
                color: #a6adc8;
            }
            QLabel#label {
                color: #6c7086;
                font-weight: bold;
            }
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                border-radius: 6px;
                padding: 8px 18px;
            }
            QPushButton:hover {
                background-color: #6c7086;
            }
            QPushButton#primary {
                background-color: #89b4fa;
                color: #1e1e2e;
            }
            QPushButton#primary:hover {
                background-color: #74c7ec;
            }
            QFrame#line {
                background-color: #45475a;
                border: none;
                max-height: 1px;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(24, 20, 24, 20)
        
        # 标题栏
        title_layout = QHBoxLayout()
        title = TitleLabel(f"📦 {self.pkg.name}")
        title.setStyleSheet("color: #89b4fa;")
        title_layout.addWidget(title)
        
        version = CaptionLabel(f"v{self.pkg.version}" if self.pkg.version else self.lang.get("not_installed", default="未安装"))
        version.setStyleSheet("color: #6c7086;")
        title_layout.addWidget(version)
        title_layout.addStretch()
        
        close_btn = TransparentToolButton()
        close_btn.setIcon(FluentIcon.CLOSE)
        close_btn.clicked.connect(self.accept)
        title_layout.addWidget(close_btn)
        
        main_layout.addLayout(title_layout)
        
        # 状态
        if self.pkg.is_installed:
            if self.pkg.is_updatable:
                status_text = self.lang.get("updatable", default="⬆️ 可更新") + f" ({self.lang.get('detail_latest_version', default='最新版本')}: {self.pkg.latest_version})"
            else:
                status_text = self.lang.get("installed", default="✓ 已安装")
        else:
            status_text = self.lang.get("not_installed", default="✗ 未安装")
        status_label = BodyLabel(f"{self.lang.get('detail_status', default='状态')}: {status_text}")
        status_label.setStyleSheet("font-size: 14px;")
        main_layout.addWidget(status_label)
        
        # 分割线
        line = QFrame()
        line.setObjectName("line")
        main_layout.addWidget(line)
        
        # 信息
        fields = [
            (self.lang.get("detail_description", default="描述"), self.pkg.description or self.lang.get("detail_none", default="无")),
            (self.lang.get("detail_author", default="作者"), self.pkg.author or self.lang.get("detail_unknown", default="未知")),
            (self.lang.get("detail_license", default="许可证"), self.pkg.license or self.lang.get("detail_unknown", default="未知")),
            (self.lang.get("detail_homepage", default="主页"), self.pkg.homepage or self.lang.get("detail_none", default="无")),
            (self.lang.get("detail_installed_path", default="安装路径"), self.pkg.installed_path or self.lang.get("detail_not_installed", default="未安装")),
            ("大小", f"{self.pkg.size/1024:.2f} KB" if self.pkg.size > 0 else "未知"),
        ]
        
        for label, value in fields:
            row = QHBoxLayout()
            label_w = CaptionLabel(label + ":")
            label_w.setObjectName("label")
            label_w.setFixedWidth(70)
            row.addWidget(label_w)
            
            value_w = BodyLabel(value)
            value_w.setObjectName("value")
            value_w.setWordWrap(True)
            row.addWidget(value_w)
            main_layout.addLayout(row)
        
        main_layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QPushButton(self.lang.get("close_btn", default="关闭"))
        close_btn.setObjectName("primary")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        main_layout.addLayout(btn_layout)


# ===================== 包管理界面 =====================
class PackageInterface(QWidget):
    packages_loaded = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("packageInterface")
        self.parent_window = parent
        self.settings = SettingsManager()
        self.lang = LanguageManager()
        self.packages: List[PackageInfo] = []
        self.filtered_packages: List[PackageInfo] = []
        self.loading = False
        self.sort_mode = "name_asc"
        
        self.setup_ui()
        self.lang.language_changed.connect(self.on_language_changed)

        self.packages_loaded.connect(self.on_packages_loaded)
        print("🔗 信号已连接")
    
    def on_language_changed(self):
        self.title_label.setText(self.lang.get("nav_packages", default="包管理"))
        self.refresh_btn.setText("🔄 " + self.lang.get("ready", default="就绪"))
        self.search_input.setPlaceholderText(self.lang.get("search_placeholder", default="🔍 搜索包名..."))
        self.status_label.setText(self.lang.get("ready", default="就绪"))
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(30, 20, 30, 20)
        
        # ===== 标题行 =====
        title_layout = QHBoxLayout()
        self.title_label = TitleLabel("📦 " + self.lang.get("nav_packages", default="包管理"))
        self.title_label.setStyleSheet("color: #89b4fa;")
        title_layout.addWidget(self.title_label)
        
        count_label = CaptionLabel("")
        count_label.setStyleSheet("color: #6c7086;")
        self.count_label = count_label
        title_layout.addWidget(count_label)
        title_layout.addStretch()
        
        self.refresh_btn = PrimaryPushButton("🔄 " + self.lang.get("ready", default="就绪"))
        self.refresh_btn.clicked.connect(self.start_loading_packages)
        title_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(title_layout)
        
        # ===== 工具栏 =====
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(12)
        
        # 搜索框
        self.search_input = LineEdit()
        self.search_input.setPlaceholderText(self.lang.get("search_placeholder", default="🔍 搜索包名..."))
        self.search_input.setFixedHeight(32)
        self.search_input.textChanged.connect(self.filter_packages)
        toolbar_layout.addWidget(self.search_input, 1)
        
        # 排序下拉
        toolbar_layout.addWidget(BodyLabel("排序:"))
        self.sort_combo = ComboBox()
        self.sort_combo.addItems(["名称 A-Z", "名称 Z-A", "大小 小-大", "大小 大-小"])
        self.sort_combo.setFixedWidth(140)
        self.sort_combo.setFixedHeight(32)
        self.sort_combo.currentIndexChanged.connect(self.apply_sort)
        toolbar_layout.addWidget(self.sort_combo)
        
        layout.addLayout(toolbar_layout)
        
        # ===== 分割线 =====
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #45475a; border: none; max-height: 1px;")
        layout.addWidget(line)
        
        # ===== 包列表 =====
        self.scroll = SmoothScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            SmoothScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setSpacing(6)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.addStretch()
        
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)
        
        # ===== 状态 =====
        self.status_label = BodyLabel(self.lang.get("ready", default="就绪"))
        self.status_label.setStyleSheet("color: #6c7086;")
        layout.addWidget(self.status_label)
    
    def start_loading_packages(self):
        if self.loading:
            return
        
        self.loading = True
        self.status_label.setText(self.lang.get("status_loading_packages", default="正在加载包列表..."))
        self.clear_items()
        
        # 用线程，不要直接调用
        threading.Thread(target=self.load_packages_thread, daemon=True).start()
    
    def clear_items(self):
        """清除所有项目（保留 stretch）"""
        while self.container_layout.count() > 1:
            widget = self.container_layout.itemAt(0).widget()
            if widget:
                widget.deleteLater()
            else:
                break
    
    def load_packages_thread(self):
        """直接加载包列表（主线程执行）"""
        installed = CLICaller.get_installed_packages()
        print(f"📦 已安装包数量: {len(installed)}")
        index = CLICaller.get_index_packages()
        print(f"📦 索引包数量: {len(index)}")
        
        all_names = set(installed.keys()) | set(index.keys())
        print(f"📦 合并后包数量: {len(all_names)}")
        total = len(all_names)
        
        if total == 0:
            self.status_label.setText(self.lang.get("no_packages", default="没有找到任何包"))
            self.loading = False
            return
        
        packages = []
        for name in sorted(all_names):
            pkg = PackageInfo(name)
            
            if name in installed:
                pkg.version = installed[name].get("version", "")
                pkg.is_installed = True
                pkg.installed_path = CLICaller.get_package_install_path(name)
                pkg.size = CLICaller.get_package_size(name)
            
            if name in index:
                info = index[name]
                lang_code = self.settings.get("language", "zh-CN")
                pkg.description = info.get("description", {}).get(lang_code, info.get("description", {}).get("zh-CN", ""))
                pkg.latest_version = info.get("latest_version", "")
                if pkg.is_installed and pkg.latest_version and pkg.version != pkg.latest_version:
                    pkg.is_updatable = True
            
            if pkg.is_installed or name in index:
                pypi_info = CLICaller.get_package_info_from_pypi(name)
                pkg.author = pypi_info.get("author", "")
                pkg.license = pypi_info.get("license", "")
                pkg.homepage = pypi_info.get("homepage", "")
                if not pkg.description:
                    pkg.description = pypi_info.get("description", "")
                if pkg.size == 0:
                    pkg.size = pypi_info.get("size", 0)
            
            self.packages.append(pkg)
        
        print(f"✅ 加载完成，共 {len(self.packages)} 个包")
        
        # 关键：用 QTimer 回到主线程渲染
        QTimer.singleShot(0, lambda p=packages: self.do_render(p))


    def do_render(self, packages):
        """主线程渲染"""
        print(f"✅ do_render 被调用，包数量: {len(packages)}")
        self.packages = packages
        self.filtered_packages = self.packages.copy()
    
        while self.container_layout.count() > 1:
            widget = self.container_layout.itemAt(0).widget()
            if widget:
                widget.deleteLater()
            else:
                break
    
        self.apply_sort()
        self.update_count()
        self.status_label.setText(self.lang.get("status_loaded", default="已加载 {total} 个包", total=len(self.packages)))
        self.loading = False

    def on_packages_loaded(self, packages):
        """主线程中处理加载完成的包（保留但不用）"""
        print(f"✅ on_packages_loaded 被调用，包数量: {len(packages)}")
        self.packages = packages
        self.filtered_packages = self.packages.copy()
        
        while self.container_layout.count() > 1:
            widget = self.container_layout.itemAt(0).widget()
            if widget:
                widget.deleteLater()
            else:
                break
        
        self.apply_sort()
        self.update_count()
        self.status_label.setText(self.lang.get("status_loaded", default="已加载 {total} 个包", total=len(self.packages)))
        self.loading = False
    
    def apply_sort(self):
        sort_index = self.sort_combo.currentIndex()
        
        if sort_index == 0:
            self.filtered_packages.sort(key=lambda x: x.name.lower())
        elif sort_index == 1:
            self.filtered_packages.sort(key=lambda x: x.name.lower(), reverse=True)
        elif sort_index == 2:
            self.filtered_packages.sort(key=lambda x: x.size)
        elif sort_index == 3:
            self.filtered_packages.sort(key=lambda x: x.size, reverse=True)
        
        self.display_packages()
    
    def display_packages(self):
        self.clear_items()
        
        for pkg in self.filtered_packages:
            item = PackageListItem(pkg, self)
            item.install_clicked.connect(self.install_package)
            item.uninstall_clicked.connect(self.uninstall_package)
            item.update_clicked.connect(self.update_package)
            item.detail_clicked.connect(self.show_detail)
            self.container_layout.insertWidget(self.container_layout.count() - 1, item)
        
        self.update_count()
    
    def filter_packages(self, text: str):
        text = text.lower().strip()
        if not text:
            self.filtered_packages = self.packages.copy()
        else:
            self.filtered_packages = [p for p in self.packages if text in p.name.lower() or text in p.description.lower()]
        
        self.apply_sort()
    
    def update_count(self):
        total = len(self.packages)
        shown = len(self.filtered_packages)
        if total == shown:
            self.count_label.setText(f"共 {total} 个包")
        else:
            self.count_label.setText(f"显示 {shown}/{total} 个包")
    
    def install_package(self, name: str):
        dialog = InstallProgressDialog(name, self)
        dialog.show()
        threading.Thread(target=self._install_thread, args=(name, dialog), daemon=True).start()
    
    def _install_thread(self, name: str, dialog: InstallProgressDialog):
        try:
            QTimer.singleShot(0, lambda: dialog.append_output("📡 " + dialog.lang.get("querying_index", default="正在查询 SilentStudio 索引...")))
            QTimer.singleShot(0, lambda: dialog.append_output("📦 " + dialog.lang.get("installing_pkg", default="正在安装 {name}...", name=name)))
        
            success, stdout, stderr = CLICaller.install_package(name)
        
            if stdout:
                for line in stdout.splitlines():
                    QTimer.singleShot(0, lambda l=line: dialog.append_output(l))
        
            if success:
                QTimer.singleShot(0, dialog.set_success)
                QTimer.singleShot(0, self.start_loading_packages)
            else:
                QTimer.singleShot(0, lambda: dialog.set_error(stderr or "安装失败"))
        except Exception as e:
            QTimer.singleShot(0, lambda: dialog.set_error(str(e)))
    
    def uninstall_package(self, name: str):
        reply = QMessageBox.question(
            self, 
            self.lang.get("confirm_uninstall_title", default="确认卸载"),
            self.lang.get("confirm_uninstall_msg", default="确定要卸载 {name} 吗？", name=name),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._run_action(f"pip uninstall {name} -y", self.lang.get("uninstall_btn", default="卸载"))
    
    def update_package(self, name: str):
        reply = QMessageBox.question(
            self,
            self.lang.get("confirm_update_title", default="确认更新"),
            self.lang.get("confirm_update_msg", default="确定要更新 {name} 吗？", name=name),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._run_action(f"pip install --upgrade {name}", self.lang.get("update_btn", default="更新"))
    
    def _run_action(self, cmd: str, action: str):
        self.status_label.setText(self.lang.get("status_refreshing", default="正在 {action}...", action=action))
        threading.Thread(target=self._run_action_thread, args=(cmd, action), daemon=True).start()
    
    def _run_action_thread(self, cmd: str, action: str):
        try:
            args = cmd.split()
            proc = subprocess.run(args, capture_output=True, text=True)
            QTimer.singleShot(0, lambda: self._action_done(action, proc.returncode == 0))
        except Exception as e:
            QTimer.singleShot(0, lambda: self._action_done(action, False, str(e)))
    
    def _action_done(self, action: str, success: bool, error: str = ""):
        if success:
            self.status_label.setText(self.lang.get("action_complete", default="✅ {action} 完成", action=action))
            InfoBar.success(
                title=self.lang.get("action_complete", default="✅ {action} 完成", action=action),
                content=self.lang.get("action_success_content", default="{action} 成功！", action=action),
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000
            )
            self.start_loading_packages()
        else:
            self.status_label.setText(self.lang.get("action_failed", default="❌ {action} 失败", action=action))
            InfoBar.error(
                title=self.lang.get("action_failed", default="❌ {action} 失败", action=action),
                content=self.lang.get("action_failed_content", default="{action} 失败: {error}", action=action, error=error),
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )
    
    def show_detail(self, name: str):
        for pkg in self.packages:
            if pkg.name == name:
                dialog = PackageDetailDialog(pkg, self)
                dialog.exec()
                break


# ===================== 主页界面 =====================
class HomeInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("homeInterface")
        self.parent_window = parent
        self.lang = LanguageManager()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(16)
        
        # 标题
        home_title = TitleLabel("🏠 主页")
        home_title.setStyleSheet("color: #89b4fa; font-size: 28px;")
        layout.addWidget(home_title)
        
        # 版本信息
        version = CLICaller.get_version()
        welcome = BodyLabel(f"SilentStudio v{version}\n\n快速开始：")
        welcome.setStyleSheet("color: #a6adc8; font-size: 14px;")
        layout.addWidget(welcome)
        
        # 快捷按钮
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(12)
        
        install_btn = PrimaryPushButton("📦 安装包")
        install_btn.clicked.connect(lambda: self.parent_window.switchTo(self.parent_window.package_interface))
        quick_layout.addWidget(install_btn)
        
        list_btn = PushButton("📋 查看所有包")
        list_btn.clicked.connect(lambda: self.parent_window.switchTo(self.parent_window.package_interface))
        quick_layout.addWidget(list_btn)
        
        layout.addLayout(quick_layout)
        layout.addStretch()


# ===================== 设置界面 =====================
class SettingsInterface(QWidget):
    settings_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsInterface")
        self.settings = SettingsManager()
        self.lang = LanguageManager()
        self.setup_ui()
        self.load_settings()
        self.lang.language_changed.connect(self.on_language_changed)
    
    def on_language_changed(self):
        self.title_label.setText(self.lang.get("settings_title", default="⚙️ 设置"))
        self.save_btn.setText(self.lang.get("settings_save_btn", default="💾 保存设置"))
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 30, 40, 30)
        
        self.title_label = TitleLabel(self.lang.get("settings_title", default="⚙️ 设置"))
        self.title_label.setStyleSheet("color: #89b4fa;")
        layout.addWidget(self.title_label)
        
        card = CardWidget()
        card.setBorderRadius(10)
        card.setStyleSheet("""
            CardWidget {
                background-color: #313244;
                border: 1px solid #45475a;
            }
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(24, 20, 24, 20)
        
        # 语言
        lang_layout = QHBoxLayout()
        self.lang_label = BodyLabel(self.lang.get("settings_language", default="🌐 界面语言"))
        lang_layout.addWidget(self.lang_label)
        lang_layout.addStretch()
        self.lang_combo = ComboBox()
        self.lang_combo.addItems(["zh-CN", "en-US", "auto"])
        self.lang_combo.setFixedWidth(120)
        lang_layout.addWidget(self.lang_combo)
        card_layout.addLayout(lang_layout)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #45475a; border: none; max-height: 1px;")
        card_layout.addWidget(line)
        
        # 镜像源
        mirror_layout = QHBoxLayout()
        self.mirror_label = BodyLabel(self.lang.get("settings_mirror", default="📦 PyPI 镜像源"))
        mirror_layout.addWidget(self.mirror_label)
        mirror_layout.addStretch()
        self.mirror_input = LineEdit()
        self.mirror_input.setPlaceholderText(self.lang.get("settings_mirror_placeholder", default="https://pypi.org/simple"))
        self.mirror_input.setFixedWidth(300)
        mirror_layout.addWidget(self.mirror_input)
        card_layout.addLayout(mirror_layout)
        
        card_layout.addWidget(line)
        
        # 自动更新检查
        check_layout = QHBoxLayout()
        self.auto_check_label = BodyLabel(self.lang.get("settings_auto_check", default="🔄 自动检查更新"))
        check_layout.addWidget(self.auto_check_label)
        check_layout.addStretch()
        self.auto_check_switch = SwitchButton()
        check_layout.addWidget(self.auto_check_switch)
        card_layout.addLayout(check_layout)
        
        card_layout.addWidget(line)
        
        # 自动安装更新
        install_layout = QHBoxLayout()
        self.auto_install_label = BodyLabel(self.lang.get("settings_auto_install", default="📥 自动安装更新"))
        install_layout.addWidget(self.auto_install_label)
        install_layout.addStretch()
        self.auto_install_switch = SwitchButton()
        install_layout.addWidget(self.auto_install_switch)
        card_layout.addLayout(install_layout)
        
        card_layout.addWidget(line)
        
        # 检查间隔
        interval_layout = QHBoxLayout()
        self.interval_label = BodyLabel(self.lang.get("settings_check_interval", default="⏱ 检查间隔"))
        interval_layout.addWidget(self.interval_label)
        interval_layout.addStretch()
        self.interval_spin = SpinBox()
        self.interval_spin.setRange(1, 24)
        self.interval_spin.setValue(6)
        interval_layout.addWidget(self.interval_spin)
        self.interval_hours_label = BodyLabel(self.lang.get("settings_hours", default="小时"))
        interval_layout.addWidget(self.interval_hours_label)
        card_layout.addLayout(interval_layout)
        
        layout.addWidget(card)
        layout.addStretch()
        
        self.save_btn = PrimaryPushButton(self.lang.get("settings_save_btn", default="💾 保存设置"))
        self.save_btn.setFixedWidth(140)
        self.save_btn.clicked.connect(self.save_settings)
        layout.addWidget(self.save_btn, alignment=Qt.AlignRight)
    
    def load_settings(self):
        self.lang_combo.setCurrentText(self.settings.get("language", "zh-CN"))
        self.mirror_input.setText(self.settings.get("pypi_mirror", ""))
        self.auto_check_switch.setChecked(self.settings.get("auto_check_update", True))
        self.auto_install_switch.setChecked(self.settings.get("auto_install_update", False))
        self.interval_spin.setValue(self.settings.get("check_interval_hours", 6))
    
    def save_settings(self):
        new_lang = self.lang_combo.currentText()
        self.settings.set("language", new_lang)
        self.settings.set("pypi_mirror", self.mirror_input.text())
        self.settings.set("auto_check_update", self.auto_check_switch.isChecked())
        self.settings.set("auto_install_update", self.auto_install_switch.isChecked())
        self.settings.set("check_interval_hours", self.interval_spin.value())
        
        lang_manager = LanguageManager()
        actual_lang = new_lang if new_lang != "auto" else "zh-CN"
        lang_manager.load_language(actual_lang)
        
        self.settings_changed.emit()
        
        InfoBar.success(
            title=self.lang.get("settings_saved_title", default="设置已保存"),
            content=self.lang.get("settings_saved_content", default="设置已保存成功！"),
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
            duration=1500
        )
        
        QTimer.singleShot(800, self.restart_window)
    
    def restart_window(self):
        main_window = self.window()
        if main_window and isinstance(main_window, SilentStudioWindow):
            geometry = main_window.saveGeometry()
            new_window = SilentStudioWindow()
            new_window.restoreGeometry(geometry)
            new_window.show()
            main_window.close()


# ===================== 主窗口 =====================
class SilentStudioWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.settings = SettingsManager()
        self.lang = LanguageManager()
        
        version = CLICaller.get_version()
        self.setWindowTitle(f"SilentStudio - v{version}")
        self.setMinimumSize(1100, 750)
        
        setTheme(Theme.DARK)
        setThemeColor(self.settings.get("theme_color", "#89b4fa"))
        
        self.init_navigation()
        QTimer.singleShot(100, self.package_interface.start_loading_packages)
    
    def init_navigation(self):
        # ===== 主页 =====
        self.home_interface = HomeInterface(self)
        self.addSubInterface(self.home_interface, FluentIcon.HOME, self.lang.get("nav_home", default="主页"))
        
        # ===== 包管理 =====
        self.package_interface = PackageInterface(self)
        self.addSubInterface(
            self.package_interface,
            FluentIcon.LIBRARY,
            self.lang.get("nav_packages", default="包管理")
        )
        
        # ===== 设置 =====
        self.settings_interface = SettingsInterface(self)
        self.addSubInterface(
            self.settings_interface,
            FluentIcon.SETTING,
            self.lang.get("nav_settings", default="设置"),
            position=NavigationItemPosition.BOTTOM
        )
    
    def switchTo(self, interface: QWidget):
        """切换到指定界面"""
        if hasattr(self, 'stackedWidget'):
            self.stackedWidget.setCurrentWidget(interface)
        else:
            for i in range(self.stackedWidget.count()):
                if self.stackedWidget.widget(i) == interface:
                    self.stackedWidget.setCurrentIndex(i)
                    break


def main():
    app = QApplication(sys.argv)
    window = SilentStudioWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()