import os
from pathlib import Path
from typing import Dict, Any

from .utils import get_system_language


# 项目模板
TEMPLATES: Dict[str, Dict[str, Any]] = {
    "java": {
        "description": "Java 项目",
        "dirs": ["src/main/java", "src/main/resources", "src/test/java"],
        "files": {
            "pom.xml": """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>{project_name}</artifactId>
    <version>1.0-SNAPSHOT</version>
    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
    </properties>
</project>""",
            ".gitignore": """# Java
*.class
*.jar
target/
!/.mvn/wrapper/maven-wrapper.jar
""",
            "README.md": "# {project_name}\n\nJava project created with SilentStudio."
        }
    },
    "python": {
        "description": "Python 项目",
        "dirs": ["src", "tests"],
        "files": {
            "setup.py": """from setuptools import setup, find_packages

setup(
    name="{project_name}",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
)
""",
            "README.md": "# {project_name}\n\nPython project created with SilentStudio.",
            "requirements.txt": "",
            ".gitignore": """# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
*.egg-info/
dist/
build/
"""
        }
    },
    "go": {
        "description": "Go 项目",
        "dirs": ["cmd", "internal", "pkg"],
        "files": {
            "go.mod": "module {project_name}\n\ngo 1.21",
            "main.go": """package main

import "fmt"

func main() {
    fmt.Println("Hello from {project_name}!")
}
""",
            "README.md": "# {project_name}\n\nGo project created with SilentStudio.",
            ".gitignore": """# Go
*.exe
*.test
*.out
/bin/
/dist/
/vendor/
"""
        }
    }
}


def create_project(project_name: str, language: str) -> bool:
    """创建项目"""
    lang = get_system_language()
    
    # 检查语言是否支持
    if language not in TEMPLATES:
        msg_zh = f"❌ 不支持的编程语言: {language}"
        msg_en = f"❌ Unsupported programming language: {language}"
        print(msg_zh if lang == "zh-CN" else msg_en)
        print(f"  支持的语言: {', '.join(TEMPLATES.keys())}")
        return False
    
    template = TEMPLATES[language]
    project_path = Path.cwd() / project_name
    
    # 检查目录是否已存在
    if project_path.exists():
        msg_zh = f"❌ 目录已存在: {project_path}"
        msg_en = f"❌ Directory already exists: {project_path}"
        print(msg_zh if lang == "zh-CN" else msg_en)
        return False
    
    # 创建目录
    project_path.mkdir(parents=True)
    
    # 创建子目录
    for subdir in template["dirs"]:
        (project_path / subdir).mkdir(parents=True, exist_ok=True)
    
    # 创建文件
    for filename, content in template["files"].items():
        filepath = project_path / filename
        # 替换模板变量
        content = content.format(project_name=project_name)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
    
    msg_zh = f"✅ 项目 '{project_name}' 已创建 (语言: {language})"
    msg_en = f"✅ Project '{project_name}' created (language: {language})"
    print(msg_zh if lang == "zh-CN" else msg_en)
    print(f"📁 位置: {project_path}")
    
    return True


def handle_new(project_name: str, language: str) -> int:
    """处理 new 命令"""
    if not project_name:
        lang = get_system_language()
        msg_zh = "❌ 请指定项目名称"
        msg_en = "❌ Please specify a project name"
        print(msg_zh if lang == "zh-CN" else msg_en)
        return 1
    
    if not language:
        lang = get_system_language()
        msg_zh = "❌ 请指定编程语言 (使用 -l 或 --lang)"
        msg_en = "❌ Please specify a programming language (use -l or --lang)"
        print(msg_zh if lang == "zh-CN" else msg_en)
        return 1
    
    success = create_project(project_name, language)
    return 0 if success else 1