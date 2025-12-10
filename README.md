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


def check(content: str) -> dict | None:
    """
    检查日志内容是否包含此错误

    :param content: 日志文件内容
    :return: 错误信息字典，如果未检测到则返回None
    """
    for pattern in PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return {
                "code": ERROR_CODE,
                "title": ERROR_TITLE,
                "detail": "检测到ADB连接错误",
                "has_solution": True
            }
    return None
```

### solution.md 示例

```markdown
# E001: ADB连接失败

## 问题描述
MAA无法通过ADB连接到模拟器或设备。

## 解决方案

### 方案一：检查模拟器状态
1. 确保模拟器已完全启动
2. 确认ADB调试已开启

### 方案二：重启ADB服务
\`\`\`bash
adb kill-server
adb start-server
\`\`\`
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

## License

MIT
