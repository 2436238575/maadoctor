"""脚本管理器 - 远程脚本拉取与管理"""
import os
import json
import shutil
from typing import List, Optional

import requests

from config import (
    LOCAL_MODE,
    LOCAL_SCRIPT_INDEX,
    LOCAL_SCRIPT_BASE,
    REMOTE_SCRIPT_INDEX,
    REMOTE_SCRIPT_BASE,
    SCRIPT_CACHE_DIR
)


class ScriptInfo:
    """脚本信息"""

    def __init__(self, name: str, filename: str, description: str = "", version: str = "1.0"):
        self.name = name
        self.filename = filename
        self.description = description
        self.version = version

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "filename": self.filename,
            "description": self.description,
            "version": self.version
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScriptInfo":
        return cls(
            name=data.get("name", ""),
            filename=data.get("filename", ""),
            description=data.get("description", ""),
            version=data.get("version", "1.0")
        )


class ScriptManager:
    """管理脚本的拉取和缓存（支持本地/远程模式）"""

    def __init__(self):
        self._script_list: List[ScriptInfo] = []

    def fetch_script_list(self, timeout: int = 10) -> List[ScriptInfo]:
        """
        获取脚本列表

        :param timeout: 请求超时时间（远程模式）
        :return: 脚本信息列表
        """
        if LOCAL_MODE:
            return self._fetch_local_script_list()
        else:
            return self._fetch_remote_script_list(timeout)

    def _fetch_local_script_list(self) -> List[ScriptInfo]:
        """从本地examples目录获取脚本列表"""
        if not os.path.exists(LOCAL_SCRIPT_INDEX):
            raise FileNotFoundError(f"本地脚本索引不存在: {LOCAL_SCRIPT_INDEX}")

        with open(LOCAL_SCRIPT_INDEX, 'r', encoding='utf-8') as f:
            data = json.load(f)

        scripts = data.get("scripts", [])
        self._script_list = [ScriptInfo.from_dict(s) for s in scripts]
        return self._script_list

    def _fetch_remote_script_list(self, timeout: int) -> List[ScriptInfo]:
        """从远程获取脚本列表"""
        response = requests.get(REMOTE_SCRIPT_INDEX, timeout=timeout)
        response.raise_for_status()

        data = response.json()
        scripts = data.get("scripts", [])

        self._script_list = [ScriptInfo.from_dict(s) for s in scripts]
        return self._script_list

    def download_script(self, script_info: ScriptInfo, timeout: int = 30) -> str:
        """
        下载/复制脚本到本地缓存

        :param script_info: 脚本信息
        :param timeout: 请求超时时间（远程模式）
        :return: 本地脚本路径
        """
        if LOCAL_MODE:
            return self._copy_local_script(script_info)
        else:
            return self._download_remote_script(script_info, timeout)

    def _copy_local_script(self, script_info: ScriptInfo) -> str:
        """从本地examples复制脚本"""
        src_path = os.path.join(LOCAL_SCRIPT_BASE, script_info.filename)
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"本地脚本不存在: {src_path}")

        dst_path = os.path.join(SCRIPT_CACHE_DIR, script_info.filename)
        shutil.copy2(src_path, dst_path)
        return dst_path

    def _download_remote_script(self, script_info: ScriptInfo, timeout: int) -> str:
        """从远程下载脚本"""
        url = f"{REMOTE_SCRIPT_BASE}{script_info.filename}"
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        local_path = os.path.join(SCRIPT_CACHE_DIR, script_info.filename)
        with open(local_path, 'w', encoding='utf-8') as f:
            f.write(response.text)

        return local_path

    def get_cached_scripts(self) -> List[str]:
        """获取已缓存的脚本文件列表"""
        cached = []
        if os.path.exists(SCRIPT_CACHE_DIR):
            for filename in os.listdir(SCRIPT_CACHE_DIR):
                if filename.endswith('.py') and not filename.startswith('_'):
                    cached.append(os.path.join(SCRIPT_CACHE_DIR, filename))
        return cached

    def get_script_path(self, script_info: ScriptInfo) -> Optional[str]:
        """获取脚本的本地路径，如果不存在则下载/复制"""
        local_path = os.path.join(SCRIPT_CACHE_DIR, script_info.filename)
        if os.path.exists(local_path):
            return local_path
        return self.download_script(script_info)

    def clear_cache(self):
        """清除所有缓存的脚本"""
        if os.path.exists(SCRIPT_CACHE_DIR):
            for filename in os.listdir(SCRIPT_CACHE_DIR):
                if filename.endswith('.py'):
                    os.remove(os.path.join(SCRIPT_CACHE_DIR, filename))
