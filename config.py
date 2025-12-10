"""MaaDoctor 配置文件"""
import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ============ 模式切换 ============
# True: 本地开发模式（不校验，直接使用本地脚本）
# False: 远程模式（必须联网校验SHA，强制同步）
LOCAL_MODE = True

# ============ 远程GitHub配置 ============
GITHUB_OWNER = "your-username"
GITHUB_REPO_NAME = "maadoctor-scripts"
GITHUB_BRANCH = "main"

# GitHub Raw 文件下载地址
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO_NAME}/{GITHUB_BRANCH}"

# GitHub API 地址（用于获取文件SHA）
GITHUB_API_BASE = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO_NAME}"
GITHUB_TREE_API = f"{GITHUB_API_BASE}/git/trees/{GITHUB_BRANCH}?recursive=1"

# ============ 本地目录配置 ============
# 脚本目录 - 每个错误一个文件夹 (E001/, E002/, ...)
SCRIPT_CACHE_DIR = os.path.join(BASE_DIR, "scripts")

# SHA清单文件 - 记录已下载文件的SHA
SHA_MANIFEST_FILE = os.path.join(SCRIPT_CACHE_DIR, "sha_manifest.json")

# 临时目录 - 用于解压日志
TEMP_DIR = os.path.join(BASE_DIR, "temp")

# 确保目录存在
os.makedirs(SCRIPT_CACHE_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
