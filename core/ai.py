"""AI分析模块 - 使用OpenAI兼容API分析日志"""
import re
import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import httpx
from datetime import datetime

from core.executor import ErrorInfo, AnalysisResult


@dataclass
class AIConfig:
    """AI配置"""
    api_url: str = "https://api.deepseek.com/"
    api_key: str = ""
    model: str = "deepseek-chat"
    max_tokens: int = 2000
    temperature: float = 0.1
    timeout: int = 30


class AIAnalyzer:
    """AI日志分析器"""
    
    def __init__(self, config: Optional[AIConfig] = None):
        self.config = config or AIConfig()
        self.client = None
        self._setup_client()
    
    def _setup_client(self):
        """设置HTTP客户端"""
        if not self.config.api_url or not self.config.api_key:
            return
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        self.client = httpx.Client(
            base_url=self.config.api_url,
            headers=headers,
            timeout=self.config.timeout
        )
    
    def update_config(self, config: AIConfig):
        """更新配置"""
        self.config = config
        self._setup_client()
    
    def is_configured(self) -> bool:
        """检查是否已配置"""
        return bool(self.config.api_url and self.config.api_key and self.client)
    
    def extract_error_logs(self, log_dir: str) -> List[str]:
        """
        提取gui.log中的ERR和WRN日志
        正则表达式: ^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}\]\[(?:ERR|WRN)\]\[.*?\].*?(?=^\[|\Z)
        """
        error_logs = []
        log_pattern = re.compile(
            r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}\]\[(?:ERR|WRN)\]\[.*?\].*?(?=^\[|\Z)',
            re.MULTILINE | re.DOTALL
        )
        
        # 查找gui.log文件
        for root, dirs, files in os.walk(log_dir):
            for file in files:
                if file.lower() == 'gui.log':
                    log_path = os.path.join(root, file)
                    try:
                        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            matches = log_pattern.findall(content)
                            error_logs.extend(matches)
                    except Exception as e:
                        print(f"读取日志文件失败 {log_path}: {e}")
        
        return error_logs
    
    def analyze_with_ai(self, log_dir: str) -> AnalysisResult:
        """
        使用AI分析日志
        
        Args:
            log_dir: 日志目录路径
            
        Returns:
            AnalysisResult: 分析结果
        """
        if not self.is_configured():
            return AnalysisResult(
                success=False,
                errors=[ErrorInfo(
                    code="AI001",
                    title="AI未配置",
                    detail="请先配置API URL和API Key",
                    has_solution=True
                )],
                summary="AI分析器未配置"
            )
        
        try:
            # 1. 提取错误日志
            error_logs = self.extract_error_logs(log_dir)
            
            if not error_logs:
                return AnalysisResult(
                    success=True,
                    errors=[],
                    summary="AI分析完成 - 未发现ERR/WRN级别的日志"
                )
            
            # 2. 准备AI提示
            prompt = self._build_prompt(error_logs)
            
            # 3. 调用AI API
            ai_response = self._call_ai_api(prompt)
            
            # 4. 解析AI响应
            return self._parse_ai_response(ai_response, error_logs)
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[ErrorInfo(
                    code="AI002",
                    title="AI分析失败",
                    detail=str(e),
                    has_solution=True
                )],
                summary=f"AI分析失败: {e}"
            )
    
    def _build_prompt(self, error_logs: List[str]) -> str:
        """构建AI提示"""
        # 去重并限制数量
        unique_logs = list(set(error_logs))  # 去除完全相同的日志
        log_sample = "\n".join(unique_logs[:15])  # 最多15条去重后的日志
        log_count = len(error_logs)
        unique_count = len(unique_logs)
        
        prompt = f"""你是一个专业的日志分析专家。请分析以下MAA(MaaAssistantArknights)的日志，找出可能的问题并提供解决方案。

日志特征：
- 格式: [时间戳][级别][模块] 消息
- 关注ERR(错误)和WRN(警告)级别的日志
- 日志总数: {log_count}条，去重后: {unique_count}条

日志内容:
{log_sample}

请按照以下JSON格式返回分析结果:
{{
    "success": boolean,  // 整体是否成功
    "errors": [
        {{
            "code": string,  // 错误代码，如"AI-001"
            "title": string,  // 错误标题
            "detail": string,  // 详细描述
            "has_solution": boolean  // 是否有解决方案
        }}
    ],
    "summary": string  // 简要总结
}}

分析要求：
1. 识别重复出现的错误模式
2. 分析错误之间的关联性
3. 提供具体的解决方案建议
4. 如果问题不明显，可以返回success: true

请直接返回JSON，不要有其他文本。"""
    
        return prompt
    
    def _call_ai_api(self, prompt: str) -> str:
        """调用AI API"""
        if not self.client:
            raise ValueError("AI客户端未初始化")
        
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": "你是一个专业的日志分析专家。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }
        
        response = self.client.post("/v1/chat/completions", json=payload)
        response.raise_for_status()
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    def _parse_ai_response(self, ai_response: str, error_logs: List[str]) -> AnalysisResult:
        """解析AI响应"""
        try:
            # 尝试提取JSON
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                ai_json = json.loads(json_match.group())
            else:
                ai_json = json.loads(ai_response)
            
            # 转换为AnalysisResult
            errors = []
            if "errors" in ai_json:
                for error_dict in ai_json["errors"]:
                    errors.append(ErrorInfo.from_dict(error_dict))
            
            return AnalysisResult(
                success=ai_json.get("success", False),
                errors=errors,
                summary=ai_json.get("summary", "AI分析完成"),
                raw_data={
                    "ai_response": ai_response,
                    "error_log_count": len(error_logs),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except json.JSONDecodeError as e:
            # 如果AI没有返回有效JSON，创建一个通用的分析结果
            return AnalysisResult(
                success=False,
                errors=[ErrorInfo(
                    code="AI003",
                    title="AI响应格式错误",
                    detail=f"无法解析AI响应: {e}",
                    has_solution=True
                )],
                summary="AI分析完成但格式异常",
                raw_data={"ai_raw_response": ai_response}
            )