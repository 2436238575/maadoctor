"""日志处理器 - ZIP解压与管理"""
import os
import zipfile
import shutil
import tempfile
from typing import Optional

from config import TEMP_DIR


class LogHandler:
    """处理ZIP日志文件的解压和清理"""

    def __init__(self):
        self._current_extract_dir: Optional[str] = None

    def extract_zip(self, zip_path: str) -> str:
        """
        解压ZIP文件到临时目录

        :param zip_path: ZIP文件路径
        :return: 解压后的目录路径
        :raises: ValueError 如果文件不存在或不是有效的ZIP文件
        """
        if not os.path.exists(zip_path):
            raise ValueError(f"文件不存在: {zip_path}")

        if not zipfile.is_zipfile(zip_path):
            raise ValueError(f"不是有效的ZIP文件: {zip_path}")

        # 清理之前的解压目录
        self.cleanup()

        # 创建新的解压目录
        zip_name = os.path.splitext(os.path.basename(zip_path))[0]
        extract_dir = os.path.join(TEMP_DIR, zip_name)

        # 如果目录已存在，添加时间戳
        if os.path.exists(extract_dir):
            import time
            extract_dir = f"{extract_dir}_{int(time.time())}"

        os.makedirs(extract_dir, exist_ok=True)

        # 解压文件
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_dir)

        self._current_extract_dir = extract_dir
        return extract_dir

    def cleanup(self):
        """清理当前解压的临时目录"""
        if self._current_extract_dir and os.path.exists(self._current_extract_dir):
            shutil.rmtree(self._current_extract_dir, ignore_errors=True)
            self._current_extract_dir = None

    def get_current_dir(self) -> Optional[str]:
        """获取当前解压目录"""
        return self._current_extract_dir

    def cleanup_all(self):
        """清理所有临时文件"""
        if os.path.exists(TEMP_DIR):
            for item in os.listdir(TEMP_DIR):
                item_path = os.path.join(TEMP_DIR, item)
                if item == '.gitkeep':
                    continue
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
                else:
                    os.remove(item_path)
        self._current_extract_dir = None
