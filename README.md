# MaaDoctor

一个带GUI的日志分析工具，支持动态拉取远程Python分析脚本，本地执行分析ZIP格式的日志压缩包，并提供错误解决方案。

## 功能特性

- **ZIP日志解压**：选择ZIP日志包，自动解压到临时目录
- **动态脚本拉取**：从GitHub仓库或本地目录加载分析脚本
- **批量分析**：一键执行所有分析脚本，合并结果
- **错误编号系统**：每个问题有唯一编号（如E001、E002）
- **独立解决方案**：每个错误对应独立的Markdown解决方案文件
- **本地/远程模式**：支持本地测试和远程GitHub两种模式

## 安装

```bash
cd maadoctor
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 使用方法

1. 点击"选择ZIP日志包"选择要分析的日志文件
2. 点击"开始分析"执行所有分析脚本
3. 查看左侧"检测到的问题"列表
4. 点击"获取解决方案"查看对应问题的解决方法

## 配置

编辑 `config.py` 切换本地/远程模式：

```python
# 本地测试模式（从scripts目录读取）
LOCAL_MODE = True

# 远程模式（从GitHub拉取）
LOCAL_MODE = False
GITHUB_REPO = "your-username/maadoctor-scripts"
```

## 项目结构

```
maadoctor/
├── main.py                 # 程序入口
├── config.py               # 配置文件
├── requirements.txt        # 依赖
├── gui/
│   ├── app.py              # PyQt6主窗口
│   └── widgets.py          # 自定义组件
├── core/
│   ├── log_handler.py      # ZIP解压处理
│   ├── script_manager.py   # 脚本拉取管理
│   ├── solution_manager.py # 解决方案管理
│   └── executor.py         # 脚本执行器
├── scripts/                # 分析脚本目录
│   ├── E001/               # ADB连接失败
│   │   ├── check.py        # 检测脚本
│   │   └── solution.md     # 解决方案
│   ├── E002/               # 截图失败
│   │   ├── check.py
│   │   └── solution.md
│   └── E003/               # 识别超时
│       ├── check.py
│       └── solution.md
└── temp/                   # 临时解压目录
```

## 编写分析脚本

每个错误对应一个文件夹，包含 `check.py` 和 `solution.md` 两个文件。

### check.py 示例

```python
"""E001: ADB连接失败 - 检测脚本"""
import os
import re

# 脚本元信息
ERROR_CODE = "E001"
ERROR_TITLE = "ADB连接失败"
ERROR_DESC = "检测ADB连接相关问题"

# 检测模式（正则表达式列表）
PATTERNS = [
    r'adb.*connect.*fail',
    r'cannot connect to',
    r'connection refused',
]

# 目标日志文件（可选，None表示检查所有日志）
TARGET_LOGS = None  # 例如: ["asst.log", "gui.log"]


def check(log_dir: str) -> dict | None:
    """
    检查日志目录中是否包含此错误

    :param log_dir: 日志目录路径
    :return: 错误信息字典，如果未检测到则返回None
    """
    for filename, content in iter_log_files(log_dir):
        for pattern in PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return {
                    "code": ERROR_CODE,
                    "title": ERROR_TITLE,
                    "detail": f"在 {filename} 中检测到ADB连接错误",
                    "has_solution": True
                }
    return None


def iter_log_files(log_dir: str):
    """遍历日志文件"""
    for root, dirs, files in os.walk(log_dir):
        for filename in files:
            if TARGET_LOGS and filename not in TARGET_LOGS:
                continue
            if not (filename.endswith('.log') or filename.endswith('.txt')):
                continue
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    yield filename, f.read()
            except Exception:
                continue
```

## 远程仓库结构

如果使用远程模式，GitHub仓库结构应为：

```
your-repo/
└── scripts/
    ├── E001/
    │   ├── check.py
    │   └── solution.md
    ├── E002/
    │   ├── check.py
    │   └── solution.md
    └── ...
```

## 依赖

- Python 3.10+
- PyQt6
- requests
- markdown

## AI Prompt for Writing check.py

Use the following prompt to instruct AI assistants to write check.py scripts:

```
You are writing a log analysis check script for MaaDoctor. Create a check.py file that detects a specific error pattern in log files.

Requirements:
1. Define these module-level constants:
   - ERROR_CODE: string like "E001", "E002", etc. (unique identifier)
   - ERROR_TITLE: short Chinese title describing the error
   - ERROR_DESC: brief Chinese description of what this script detects
   - PATTERNS: list of regex patterns to match in log content
   - TARGET_LOGS: list of target log filenames to check, or None for all logs
     Example: ["asst.log", "gui.log"] or None

2. Implement the check() function:
   - Input: log_dir (str) - path to the directory containing extracted log files
   - Output: dict or None
   - Return None if no error pattern is detected
   - Return a dict with these keys if error is detected:
     {
       "code": ERROR_CODE,
       "title": ERROR_TITLE,
       "detail": "在 {filename} 中检测到XXX (Chinese)",
       "has_solution": True
     }

3. Implement iter_log_files() helper to iterate through log files
4. Use re.search() with re.IGNORECASE for pattern matching
5. Only use Python standard library (re, os, json, etc.)
6. Keep the script simple and focused on one specific error type

Example structure:
"""EXXX: 错误标题 - 检测脚本"""
import os
import re

ERROR_CODE = "EXXX"
ERROR_TITLE = "错误标题"
ERROR_DESC = "检测XXX相关问题"

PATTERNS = [
    r'pattern1.*here',
    r'another.*pattern',
]

TARGET_LOGS = None  # or ["asst.log", "specific.log"]

def check(log_dir: str) -> dict | None:
    for filename, content in iter_log_files(log_dir):
        for pattern in PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return {
                    "code": ERROR_CODE,
                    "title": ERROR_TITLE,
                    "detail": f"在 {filename} 中检测到问题",
                    "has_solution": True
                }
    return None

def iter_log_files(log_dir: str):
    for root, dirs, files in os.walk(log_dir):
        for filename in files:
            if TARGET_LOGS and filename not in TARGET_LOGS:
                continue
            if not (filename.endswith('.log') or filename.endswith('.txt')):
                continue
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    yield filename, f.read()
            except Exception:
                continue
```

## License

MIT
