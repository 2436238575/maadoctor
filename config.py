"""MaaDoctor 配置文件"""
import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ============ 模式切换 ============
# True: 本地测试模式（从examples目录读取）
# False: 远程模式（从GitHub拉取）
LOCAL_MODE = True

# ============ 本地测试配置 ============
LOCAL_EXAMPLES_DIR = os.path.join(BASE_DIR, "examples")
LOCAL_SCRIPT_INDEX = os.path.join(LOCAL_EXAMPLES_DIR, "scripts", "index.json")
LOCAL_SCRIPT_BASE = os.path.join(LOCAL_EXAMPLES_DIR, "scripts")
LOCAL_SOLUTION_BASE = os.path.join(LOCAL_EXAMPLES_DIR, "solutions")

# ============ 远程GitHub配置 ============
GITHUB_REPO = "your-username/maadoctor-scripts"
GITHUB_BRANCH = "main"
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}"

REMOTE_SCRIPT_INDEX = f"{GITHUB_RAW_BASE}/scripts/index.json"
REMOTE_SCRIPT_BASE = f"{GITHUB_RAW_BASE}/scripts/"
REMOTE_SOLUTION_BASE = f"{GITHUB_RAW_BASE}/solutions/"

# ============ 本地缓存配置 ============
SCRIPT_CACHE_DIR = os.path.join(BASE_DIR, "scripts")
TEMP_DIR = os.path.join(BASE_DIR, "temp")

# 确保目录存在
os.makedirs(SCRIPT_CACHE_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
