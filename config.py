"""MaaDoctor 配置文件"""
import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ============ 模式切换 ============
# True: 本地测试模式（从本地scripts目录读取）
# False: 远程模式（从GitHub拉取）
LOCAL_MODE = True

# ============ 远程GitHub配置 ============
GITHUB_REPO = "your-username/maadoctor-scripts"
GITHUB_BRANCH = "main"
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}"
REMOTE_SCRIPT_BASE = f"{GITHUB_RAW_BASE}/scripts/"

# ============ 本地目录配置 ============
# 脚本目录 - 每个错误一个Python文件 (E001.py, E002.py, ...)
SCRIPT_CACHE_DIR = os.path.join(BASE_DIR, "scripts")

# 临时目录 - 用于解压日志
TEMP_DIR = os.path.join(BASE_DIR, "temp")

# 确保目录存在
os.makedirs(SCRIPT_CACHE_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
