"""解决方案管理器 - 解决方案拉取（支持本地/远程模式）"""
import os
import requests
import markdown

from config import (
    LOCAL_MODE,
    LOCAL_SOLUTION_BASE,
    REMOTE_SOLUTION_BASE
)


class SolutionManager:
    """管理错误解决方案的拉取和显示"""

    def __init__(self):
        self._cache: dict = {}  # 缓存已拉取的解决方案

    def fetch_solution(self, error_code: str, timeout: int = 10) -> str:
        """
        获取指定错误编号的解决方案

        :param error_code: 错误编号，如 "E001"
        :param timeout: 请求超时时间（远程模式）
        :return: Markdown格式的解决方案内容
        """
        # 检查缓存
        if error_code in self._cache:
            return self._cache[error_code]

        if LOCAL_MODE:
            content = self._fetch_local_solution(error_code)
        else:
            content = self._fetch_remote_solution(error_code, timeout)

        self._cache[error_code] = content
        return content

    def _fetch_local_solution(self, error_code: str) -> str:
        """从本地examples目录读取解决方案"""
        file_path = os.path.join(LOCAL_SOLUTION_BASE, f"{error_code}.md")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"解决方案不存在: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _fetch_remote_solution(self, error_code: str, timeout: int) -> str:
        """从远程拉取解决方案"""
        url = f"{REMOTE_SOLUTION_BASE}{error_code}.md"
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text

    def render_solution(self, md_content: str) -> str:
        """
        将Markdown内容转换为HTML用于显示

        :param md_content: Markdown格式内容
        :return: HTML格式内容
        """
        html = markdown.markdown(
            md_content,
            extensions=['fenced_code', 'tables', 'nl2br']
        )
        # 添加基础样式
        styled_html = f"""
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
            code {{ background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
            pre {{ background-color: #f4f4f4; padding: 12px; border-radius: 6px; overflow-x: auto; }}
            h1, h2, h3 {{ color: #333; }}
            a {{ color: #0066cc; }}
        </style>
        {html}
        """
        return styled_html

    def get_solution_html(self, error_code: str, timeout: int = 10) -> str:
        """
        获取解决方案并转换为HTML

        :param error_code: 错误编号
        :param timeout: 请求超时时间
        :return: HTML格式的解决方案
        """
        md_content = self.fetch_solution(error_code, timeout)
        return self.render_solution(md_content)

    def clear_cache(self):
        """清除解决方案缓存"""
        self._cache.clear()
