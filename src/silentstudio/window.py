import sys
import subprocess
from pathlib import Path

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout,
        QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
        QLabel, QSplitter
    )
    from PySide6.QtCore import Qt, QProcess
    from PySide6.QtGui import QFont, QTextCursor, QIcon
except ImportError:
    print("❌ PySide6 未安装，请执行: pip install silentstudio[window]")
    sys.exit(1)


class SilentStudioGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SilentStudio - GUI 控制台")
        self.setGeometry(100, 100, 900, 650)
        
        # 设置字体
        font = QFont("Consolas", 10)
        self.setFont(font)
        
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("🔄 SilentStudio 控制台")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 输出区域
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
        """)
        self.output.append("┌" + "─" * 78 + "┐")
        self.output.append("│  SilentStudio GUI v0.1.0".ljust(79) + "│")
        self.output.append("│  输入命令并回车执行".ljust(79) + "│")
        self.output.append("└" + "─" * 78 + "┘")
        self.output.append("")
        layout.addWidget(self.output)
        
        # 输入行
        input_layout = QHBoxLayout()
        
        prompt_label = QLabel("$")
        prompt_label.setStyleSheet("color: #a6e3a1; font-weight: bold;")
        input_layout.addWidget(prompt_label)
        
        self.input = QLineEdit()
        self.input.setPlaceholderText("输入 silentstudio 命令...")
        self.input.setStyleSheet("""
            QLineEdit {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 6px;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 1px solid #89b4fa;
            }
        """)
        self.input.returnPressed.connect(self.execute_command)
        input_layout.addWidget(self.input)
        
        # 执行按钮
        self.execute_btn = QPushButton("▶ 执行")
        self.execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #74c7ec;
            }
            QPushButton:pressed {
                background-color: #6c7086;
            }
        """)
        self.execute_btn.clicked.connect(self.execute_command)
        input_layout.addWidget(self.execute_btn)
        
        # 清空按钮
        clear_btn = QPushButton("清空")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #6c7086;
            }
        """)
        clear_btn.clicked.connect(self.clear_output)
        input_layout.addWidget(clear_btn)
        
        layout.addLayout(input_layout)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
        self.statusBar().setStyleSheet("background-color: #313244; color: #cdd6f4;")
    
    def execute_command(self):
        cmd = self.input.text().strip()
        if not cmd:
            return
        
        self.input.clear()
        self.output.append(f"📌 $ {cmd}")
        
        # 特殊命令：内置帮助
        if cmd in ("exit", "quit"):
            self.output.append("👋 再见！")
            QApplication.quit()
            return
        
        if cmd in ("clear", "cls"):
            self.clear_output()
            return
        
        # 执行 silentstudio
        self.statusBar().showMessage(f"执行: {cmd}")
        self.output.append("⏳ 执行中...")
        
        # 使用 QProcess 异步执行
        self.process = QProcess()
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.finished.connect(self.handle_finished)
        
        # 拆分命令
        args = cmd.split()
        self.process.start("silentstudio", args)
    
    def handle_output(self):
        """处理命令输出"""
        data = self.process.readAllStandardOutput()
        text = data.data().decode("utf-8", errors="replace")
        # 替换最后一行"执行中..."
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()
        self.output.append(text)
        self.output.moveCursor(QTextCursor.End)
    
    def handle_finished(self, exit_code, exit_status):
        """命令执行完成"""
        status = "成功" if exit_code == 0 else f"失败 (退出码: {exit_code})"
        self.statusBar().showMessage(f"命令完成: {status}")
        
        if exit_code != 0:
            self.output.append(f"⚠️ 命令执行 {status}")
    
    def clear_output(self):
        """清空输出"""
        self.output.clear()
        self.output.append("┌" + "─" * 78 + "┐")
        self.output.append("│  输出已清空".ljust(79) + "│")
        self.output.append("└" + "─" * 78 + "┘")
        self.output.append("")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 设置暗色主题
    app.setStyleSheet("""
        QMainWindow {
            background-color: #1e1e2e;
        }
        QWidget {
            background-color: #1e1e2e;
            color: #cdd6f4;
        }
        QStatusBar {
            background-color: #313244;
            color: #cdd6f4;
        }
    """)
    
    window = SilentStudioGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()