"""解决方案管理器 - 从文件夹读取解决方案"""
import os
import markdown

from config import SCRIPT_CACHE_DIR


class SolutionManager:
    """管理错误解决方案的获取和显示"""

    def __init__(self, scripts_dir: str = None):
        self._scripts_dir = scripts_dir or SCRIPT_CACHE_DIR
        self._cache: dict = {}  # 缓存已加载的解决方案

    def fetch_solution(self, error_code: str) -> str:
        """
        获取指定错误编号的解决方案

        :param error_code: 错误编号，如 "E001"
        :return: Markdown格式的解决方案内容
        """
        # 检查缓存
        if error_code in self._cache:
            return self._cache[error_code]

        # 从文件夹读取 solution.md
        solution_path = os.path.join(self._scripts_dir, error_code, "solution.md")
        if not os.path.exists(solution_path):
            raise FileNotFoundError(f"解决方案不存在: {solution_path}")

        with open(solution_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self._cache[error_code] = content
        return content

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

    def get_solution_html(self, error_code: str) -> str:
        """
        获取解决方案并转换为HTML

        :param error_code: 错误编号
        :return: HTML格式的解决方案
        """
        md_content = self.fetch_solution(error_code)
        return self.render_solution(md_content)

    def clear_cache(self):
        """清除解决方案缓存"""
        self._cache.clear()
