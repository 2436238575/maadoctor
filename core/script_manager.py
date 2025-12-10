"""脚本管理器 - SHA校验与强制同步"""
import os
import json
import shutil
from datetime import datetime
from typing import Dict, List, Optional

import requests

from config import (
    LOCAL_MODE,
    GITHUB_RAW_BASE,
    GITHUB_TREE_API,
    SCRIPT_CACHE_DIR,
    SHA_MANIFEST_FILE
)


class ScriptSyncError(Exception):
    """脚本同步错误"""
    pass


class ScriptManager:
    """
    脚本管理器

    本地模式：直接使用本地脚本，不校验
    远程模式：必须联网校验SHA，有差异强制更新，否则禁止使用
    """

    def __init__(self):
        self._synced = False  # 是否已同步
        self._remote_files: Dict[str, str] = {}  # 远程文件SHA {path: sha}

    def ensure_synced(self, timeout: int = 30) -> bool:
        """
        确保脚本已同步（远程模式必须调用）

        :param timeout: 请求超时时间
        :return: 是否同步成功
        :raises: ScriptSyncError 如果远程模式下同步失败
        """
        if LOCAL_MODE:
            # 本地模式不校验
            self._synced = True
            return True

        if self._synced:
            return True

        try:
            # 1. 获取远程文件SHA
            remote_files = self._fetch_remote_sha_tree(timeout)

            # 2. 读取本地SHA清单
            local_manifest = self._load_local_manifest()

            # 3. 比较差异
            need_update = self._check_diff(remote_files, local_manifest)

            if need_update:
                # 4. 强制更新
                self._sync_all_scripts(remote_files, timeout)
                # 5. 保存新的SHA清单
                self._save_local_manifest(remote_files)

            self._synced = True
            self._remote_files = remote_files
            return True

        except requests.RequestException as e:
            raise ScriptSyncError(f"网络错误，无法校验脚本: {e}")
        except Exception as e:
            raise ScriptSyncError(f"同步失败: {e}")

    def _fetch_remote_sha_tree(self, timeout: int) -> Dict[str, str]:
        """
        从GitHub API获取远程文件SHA树

        :return: {相对路径: SHA} 字典，只包含scripts/E*下的文件
        """
        response = requests.get(GITHUB_TREE_API, timeout=timeout)
        response.raise_for_status()

        data = response.json()
        tree = data.get("tree", [])

        files = {}
        for item in tree:
            path = item.get("path", "")
            sha = item.get("sha", "")
            item_type = item.get("type", "")

            # 只关注 scripts/E*/check.py 和 scripts/E*/solution.md
            if item_type == "blob" and path.startswith("scripts/E"):
                # 提取相对路径 (去掉 scripts/ 前缀)
                rel_path = path[8:]  # len("scripts/") = 8
                if rel_path.endswith("/check.py") or rel_path.endswith("/solution.md"):
                    files[rel_path] = sha

        return files

    def _load_local_manifest(self) -> Dict[str, str]:
        """读取本地SHA清单"""
        if not os.path.exists(SHA_MANIFEST_FILE):
            return {}

        try:
            with open(SHA_MANIFEST_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("files", {})
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_local_manifest(self, files: Dict[str, str]):
        """保存本地SHA清单"""
        data = {
            "last_sync": datetime.now().isoformat(),
            "files": files
        }
        with open(SHA_MANIFEST_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _check_diff(self, remote: Dict[str, str], local: Dict[str, str]) -> bool:
        """
        检查远程和本地是否有差异

        :return: True 如果有差异需要更新
        """
        if set(remote.keys()) != set(local.keys()):
            return True

        for path, sha in remote.items():
            if local.get(path) != sha:
                return True

        return False

    def _sync_all_scripts(self, remote_files: Dict[str, str], timeout: int):
        """
        同步所有脚本文件

        :param remote_files: 远程文件SHA字典
        :param timeout: 请求超时时间
        """
        # 清理旧的E*文件夹
        self._clean_old_scripts()

        # 下载所有文件
        for rel_path in remote_files.keys():
            self._download_file(rel_path, timeout)

    def _clean_old_scripts(self):
        """清理旧的E*脚本文件夹"""
        if not os.path.exists(SCRIPT_CACHE_DIR):
            return

        for name in os.listdir(SCRIPT_CACHE_DIR):
            if name.startswith('E') and name[1:].split('/')[0].isdigit():
                path = os.path.join(SCRIPT_CACHE_DIR, name)
                if os.path.isdir(path):
                    shutil.rmtree(path)

    def _download_file(self, rel_path: str, timeout: int):
        """
        下载单个文件

        :param rel_path: 相对路径，如 "E001/check.py"
        :param timeout: 请求超时时间
        """
        url = f"{GITHUB_RAW_BASE}/scripts/{rel_path}"
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        local_path = os.path.join(SCRIPT_CACHE_DIR, rel_path)

        # 确保目录存在
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        with open(local_path, 'w', encoding='utf-8') as f:
            f.write(response.text)

    def get_script_folders(self) -> List[str]:
        """
        获取所有脚本文件夹名称

        :return: 文件夹名称列表，如 ["E001", "E002", "E003"]
        :raises: ScriptSyncError 如果远程模式下未同步
        """
        if not LOCAL_MODE and not self._synced:
            raise ScriptSyncError("远程模式下必须先调用 ensure_synced()")

        folders = []
        if os.path.exists(SCRIPT_CACHE_DIR):
            for name in sorted(os.listdir(SCRIPT_CACHE_DIR)):
                folder_path = os.path.join(SCRIPT_CACHE_DIR, name)
                if os.path.isdir(folder_path) and name.startswith('E'):
                    # 检查是否包含 check.py
                    if os.path.exists(os.path.join(folder_path, "check.py")):
                        folders.append(name)
        return folders

    def is_synced(self) -> bool:
        """检查是否已同步"""
        return LOCAL_MODE or self._synced

    def get_sync_status(self) -> dict:
        """获取同步状态信息"""
        manifest = self._load_local_manifest()
        return {
            "local_mode": LOCAL_MODE,
            "synced": self._synced,
            "last_sync": manifest.get("last_sync") if manifest else None,
            "file_count": len(manifest.get("files", {})) if manifest else 0
        }
