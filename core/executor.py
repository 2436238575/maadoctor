"""脚本执行器 - 动态加载和执行分析脚本"""
import os
import sys
import importlib.util
from typing import Dict, Any, List
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

    def load_script(self, script_path: str, module_name: str = None) -> Any:
        """
        动态加载Python脚本模块

        :param script_path: 脚本文件路径
        :param module_name: 模块名称（可选）
        :return: 加载的模块对象
        """
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"脚本文件不存在: {script_path}")

        if module_name is None:
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

    def load_all_scripts(self, scripts_dir: str) -> List[Any]:
        """
        加载目录下所有 E*/check.py 脚本

        :param scripts_dir: 脚本目录路径
        :return: 加载的模块列表
        """
        modules = []
        if not os.path.exists(scripts_dir):
            return modules

        for folder_name in sorted(os.listdir(scripts_dir)):
            if folder_name.startswith('E') and folder_name[1:].isdigit():
                check_path = os.path.join(scripts_dir, folder_name, "check.py")
                if os.path.exists(check_path):
                    try:
                        module = self.load_script(check_path, f"check_{folder_name}")
                        modules.append(module)
                    except Exception as e:
                        print(f"加载脚本失败 {folder_name}/check.py: {e}")
        return modules

    def run_analysis(self, scripts_dir: str, log_dir: str) -> AnalysisResult:
        """
        执行所有分析脚本

        :param scripts_dir: 脚本目录路径
        :param log_dir: 日志目录路径
        :return: 分析结果
        """
        errors = []
        summary_parts = []

        # 查找日志文件
        log_files = []
        for root, dirs, files in os.walk(log_dir):
            for f in files:
                if f.endswith('.log') or f.endswith('.txt'):
                    log_files.append(os.path.join(root, f))

        if not log_files:
            return AnalysisResult(
                success=False,
                errors=[ErrorInfo(
                    code="E000",
                    title="未找到日志文件",
                    detail=f"在 {log_dir} 中未找到 .log 或 .txt 文件",
                    has_solution=False
                )],
                summary="未找到可分析的日志文件"
            )

        summary_parts.append(f"找到 {len(log_files)} 个日志文件")

        # 加载所有脚本
        modules = self.load_all_scripts(scripts_dir)
        if not modules:
            return AnalysisResult(
                success=False,
                errors=[ErrorInfo(
                    code="E000",
                    title="未找到分析脚本",
                    detail=f"在 {scripts_dir} 中未找到分析脚本",
                    has_solution=False
                )],
                summary="未找到分析脚本"
            )

        # 对每个脚本执行检查，传入log_dir让脚本自己决定读取哪些文件
        seen_codes = set()
        for module in modules:
            if hasattr(module, 'check'):
                try:
                    result = module.check(log_dir)
                    if result and result.get("code") not in seen_codes:
                        seen_codes.add(result["code"])
                        errors.append(ErrorInfo.from_dict(result))
                except Exception as e:
                    print(f"执行脚本检查失败: {e}")

        # 生成摘要
        if errors:
            summary_parts.append(f"发现 {len(errors)} 个问题")
            success = False
        else:
            summary_parts.append("未发现明显问题")
            success = True

        return AnalysisResult(
            success=success,
            errors=errors,
            summary="，".join(summary_parts)
        )

    def get_script_info(self, module: Any) -> Dict[str, str]:
        """
        获取脚本的元信息

        :param module: 已加载的脚本模块
        :return: 包含code, title, description的字典
        """
        return {
            "code": getattr(module, 'ERROR_CODE', ''),
            "title": getattr(module, 'ERROR_TITLE', '未命名'),
            "description": getattr(module, 'ERROR_DESC', '无描述')
        }
