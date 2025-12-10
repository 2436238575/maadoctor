"""脚本执行器 - 动态加载和执行分析脚本"""
import os
import sys
import importlib.util
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ErrorInfo:
    """错误信息"""
    code: str
    title: str
    detail: str = ""
    has_solution: bool = True

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "title": self.title,
            "detail": self.detail,
            "has_solution": self.has_solution
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ErrorInfo":
        return cls(
            code=data.get("code", ""),
            title=data.get("title", ""),
            detail=data.get("detail", ""),
            has_solution=data.get("has_solution", True)
        )


@dataclass
class AnalysisResult:
    """分析结果"""
    success: bool
    errors: list = field(default_factory=list)
    summary: str = ""
    raw_data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "errors": [e.to_dict() if isinstance(e, ErrorInfo) else e for e in self.errors],
            "summary": self.summary,
            "raw_data": self.raw_data
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AnalysisResult":
        errors = [
            ErrorInfo.from_dict(e) if isinstance(e, dict) else e
            for e in data.get("errors", [])
        ]
        return cls(
            success=data.get("success", False),
            errors=errors,
            summary=data.get("summary", ""),
            raw_data=data.get("raw_data", {})
        )


class ScriptExecutor:
    """动态加载和执行分析脚本"""

    def __init__(self):
        self._loaded_modules: Dict[str, Any] = {}

    def load_script(self, script_path: str) -> Any:
        """
        动态加载Python脚本模块

        :param script_path: 脚本文件路径
        :return: 加载的模块对象
        :raises: FileNotFoundError, ImportError
        """
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"脚本文件不存在: {script_path}")

        # 生成模块名
        module_name = os.path.splitext(os.path.basename(script_path))[0]

        # 如果已加载，先卸载
        if module_name in self._loaded_modules:
            del self._loaded_modules[module_name]
            if module_name in sys.modules:
                del sys.modules[module_name]

        # 动态加载模块
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"无法加载脚本: {script_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        self._loaded_modules[module_name] = module
        return module

    def execute(self, module: Any, log_dir: str) -> AnalysisResult:
        """
        执行分析脚本

        :param module: 已加载的脚本模块
        :param log_dir: 日志目录路径
        :return: 分析结果
        :raises: AttributeError 如果脚本没有analyze函数
        """
        if not hasattr(module, 'analyze'):
            raise AttributeError(f"脚本缺少 analyze 函数")

        # 调用分析函数
        result = module.analyze(log_dir)

        # 转换结果
        if isinstance(result, dict):
            return AnalysisResult.from_dict(result)
        elif isinstance(result, AnalysisResult):
            return result
        else:
            return AnalysisResult(
                success=False,
                summary=f"脚本返回了无效的结果类型: {type(result)}"
            )

    def get_script_info(self, module: Any) -> Dict[str, str]:
        """
        获取脚本的元信息

        :param module: 已加载的脚本模块
        :return: 包含name和description的字典
        """
        return {
            "name": getattr(module, 'SCRIPT_NAME', '未命名脚本'),
            "description": getattr(module, 'SCRIPT_DESC', '无描述')
        }

    def run_analysis(self, script_path: str, log_dir: str) -> AnalysisResult:
        """
        一站式执行分析：加载脚本并执行

        :param script_path: 脚本文件路径
        :param log_dir: 日志目录路径
        :return: 分析结果
        """
        module = self.load_script(script_path)
        return self.execute(module, log_dir)
