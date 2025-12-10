# MaaDoctor

一个带GUI的日志分析工具，支持动态拉取远程Python分析脚本，本地执行分析ZIP格式的日志压缩包，并提供错误解决方案。

## 功能特性

- **ZIP日志解压**：选择ZIP日志包，自动解压到临时目录
- **动态脚本拉取**：从GitHub仓库或本地目录加载分析脚本
- **批量分析**：一键执行所有分析脚本，合并结果
- **错误编号系统**：每个问题有唯一编号（如E001、E002）
- **解决方案拉取**：点击按钮获取对应错误的Markdown解决方案
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
# 本地测试模式（从examples目录读取）
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
│   ├── solution_manager.py # 解决方案拉取
│   └── executor.py         # 脚本执行器
├── examples/               # 示例脚本和解决方案
│   ├── scripts/
│   │   ├── index.json
│   │   └── maa_analyzer.py
│   └── solutions/
│       ├── E001.md
│       ├── E002.md
│       └── E003.md
├── scripts/                # 脚本缓存目录
└── temp/                   # 临时解压目录
```

## 编写分析脚本

分析脚本需要实现标准接口：

```python
# 脚本元信息
SCRIPT_NAME = "示例分析脚本"
SCRIPT_DESC = "分析XXX类型的日志"

def analyze(log_dir: str) -> dict:
    """
    分析入口函数

    :param log_dir: 解压后的日志目录路径
    :return: 分析结果字典
    """
    return {
        "success": True,  # 是否成功（无错误）
        "errors": [
            {
                "code": "E001",        # 错误编号
                "title": "连接超时",    # 错误标题
                "detail": "详细信息",   # 详细描述
                "has_solution": True   # 是否有解决方案
            }
        ],
        "summary": "分析摘要"
    }
```

## 编写解决方案

解决方案使用Markdown格式，文件名为 `{错误编号}.md`：

```markdown
# E001: 错误标题

## 问题描述
描述问题...

## 解决方案
### 方案一
步骤...

### 方案二
步骤...
```

## 远程仓库结构

如果使用远程模式，GitHub仓库结构应为：

```
your-repo/
├── scripts/
│   ├── index.json      # 脚本索引
│   └── *.py            # 分析脚本
└── solutions/
    └── E001.md         # 解决方案文件
```

`scripts/index.json` 格式：

```json
{
    "scripts": [
        {
            "name": "脚本名称",
            "filename": "script.py",
            "description": "脚本描述",
            "version": "1.0"
        }
    ]
}
```

## 依赖

- Python 3.10+
- PyQt6
- requests
- markdown

## License

MIT
