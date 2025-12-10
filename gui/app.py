"""主窗口"""
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog,
    QTextEdit, QStatusBar, QMessageBox, QProgressBar,
    QSplitter, QGroupBox,
    QDialog, QFormLayout, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from config import SCRIPT_CACHE_DIR
from core.log_handler import LogHandler
from core.script_manager import ScriptManager, ScriptSyncError
from core.solution_manager import SolutionManager
from core.executor import ScriptExecutor, AnalysisResult, ErrorInfo
from gui.widgets import ErrorListWidget, SolutionDialog

from core.ai import AIAnalyzer, AIConfig

class AnalysisWorker(QThread):
    """分析线程"""
    progress_update = pyqtSignal(str)  # 状态消息
    finished = pyqtSignal(object)  # AnalysisResult
    error = pyqtSignal(str)

    def __init__(self, script_manager: ScriptManager, executor: ScriptExecutor, log_dir: str):
        super().__init__()
        self.script_manager = script_manager
        self.executor = executor
        self.log_dir = log_dir

    def run(self):
        try:
            # 1. 确保脚本已同步（远程模式会校验SHA）
            self.progress_update.emit("正在同步脚本...")
            self.script_manager.ensure_synced()

            # 2. 执行分析
            self.progress_update.emit("正在分析日志...")
            result = self.executor.run_analysis(SCRIPT_CACHE_DIR, self.log_dir)

            self.finished.emit(result)

        except ScriptSyncError as e:
            self.error.emit(f"脚本同步失败: {e}")
        except Exception as e:
            self.error.emit(str(e))

class AIAnalysisWorker(QThread):
    """AI分析线程"""
    progress_update = pyqtSignal(str)
    finished = pyqtSignal(object)  # AnalysisResult
    error = pyqtSignal(str)

    def __init__(self, ai_analyzer: AIAnalyzer, log_dir: str):
        super().__init__()
        self.ai_analyzer = ai_analyzer
        self.log_dir = log_dir

    def run(self):
        try:
            self.progress_update.emit("正在执行AI分析...")
            result = self.ai_analyzer.analyze_with_ai(self.log_dir)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class ConfigDialog(QDialog):
    """AI配置对话框"""
    def __init__(self, ai_config: AIConfig, parent=None):
        super().__init__(parent)
        self.ai_config = ai_config
        self.setWindowTitle("AI配置")
        self.setMinimumWidth(400)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.api_url_edit = QLineEdit()
        self.api_url_edit.setText(self.ai_config.api_url)
        self.api_url_edit.setPlaceholderText("https://api.deepseek.com/")
        form_layout.addRow("API URL:", self.api_url_edit)
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setText(self.ai_config.api_key)
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("sk-...")
        form_layout.addRow("API Key:", self.api_key_edit)
        
        self.model_edit = QLineEdit()
        self.model_edit.setText(self.ai_config.model)
        self.model_edit.setPlaceholderText("deepseek-chat")
        form_layout.addRow("模型:", self.model_edit)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
    
    def get_config(self) -> AIConfig:
        """获取配置"""
        return AIConfig(
            api_url=self.api_url_edit.text().strip() or "https://api.deepseek.com/",
            api_key=self.api_key_edit.text().strip(),
            model=self.model_edit.text().strip() or "deepseek-chat"
        )

class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MaaDoctor - 日志分析工具")
        self.setMinimumSize(900, 600)

        # 初始化核心组件
        self.log_handler = LogHandler()
        self.script_manager = ScriptManager()
        self.solution_manager = SolutionManager()
        self.executor = ScriptExecutor()
        
        self.ai_config = AIConfig()
        self.ai_analyzer = AIAnalyzer(self.ai_config)
        self.use_ai_analysis = False

        # 状态
        self._current_zip_path = None
        self._current_log_dir = None
        self._worker = None

        self._setup_ui()
        self._setup_statusbar()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # 顶部：文件选择和执行
        top_group = QGroupBox("日志分析")
        top_layout = QHBoxLayout(top_group)

        self.file_label = QLabel("未选择文件")
        self.file_label.setStyleSheet("color: #666;")
        top_layout.addWidget(self.file_label, 1)

        self.select_btn = QPushButton("选择ZIP日志包")
        self.select_btn.clicked.connect(self._on_select_file)
        top_layout.addWidget(self.select_btn)

        self.run_btn = QPushButton("开始分析")
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #218838; }
            QPushButton:disabled { background-color: #ccc; }
        """)
        self.run_btn.clicked.connect(self._on_run_analysis)
        self.run_btn.setEnabled(False)
        top_layout.addWidget(self.run_btn)
        
        # 新增：AI分析按钮
        self.ai_run_btn = QPushButton("开始AI分析")
        self.ai_run_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #0056b3; }
            QPushButton:disabled { background-color: #ccc; }
        """)
        self.ai_run_btn.clicked.connect(self._on_run_ai_analysis)
        self.ai_run_btn.setEnabled(False)
        top_layout.addWidget(self.ai_run_btn)
        
        self.ai_config_btn = QPushButton("AI配置")
        self.ai_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #5a6268; }
        """)
        self.ai_config_btn.clicked.connect(self._on_open_config)
        top_layout.addWidget(self.ai_config_btn)

        main_layout.addWidget(top_group)

        # 进度条
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setTextVisible(True)
        self.progress.setRange(0, 0)  # 不确定进度
        main_layout.addWidget(self.progress)

        # 下部：结果显示（使用分割器）
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：错误列表
        error_group = QGroupBox("检测到的问题")
        error_layout = QVBoxLayout(error_group)
        self.error_list = ErrorListWidget()
        self.error_list.solution_requested.connect(self._on_solution_requested)
        error_layout.addWidget(self.error_list)
        splitter.addWidget(error_group)

        # 右侧：摘要
        summary_group = QGroupBox("分析摘要")
        summary_layout = QVBoxLayout(summary_group)
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        summary_layout.addWidget(self.summary_text)
        splitter.addWidget(summary_group)

        splitter.setSizes([500, 400])
        main_layout.addWidget(splitter, 1)

    def _setup_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("就绪 - 请选择ZIP日志包")
    
    def _on_open_config(self):
        """打开AI配置对话框"""
        dialog = ConfigDialog(self.ai_config, self)
        if dialog.exec():
            new_config = dialog.get_config()
            self.ai_config = new_config
            self.ai_analyzer.update_config(new_config)
            
            QMessageBox.information(self, "成功", "AI配置已保存")

    def _on_select_file(self):
        """选择ZIP文件"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择日志压缩包", "",
            "ZIP文件 (*.zip);;所有文件 (*)"
        )
        if path:
            self._current_zip_path = path
            self.file_label.setText(os.path.basename(path))
            self.file_label.setStyleSheet("color: #000; font-weight: bold;")
            self.statusbar.showMessage(f"已选择: {path}")

            # 解压文件
            try:
                self._current_log_dir = self.log_handler.extract_zip(path)
                self.statusbar.showMessage(f"已解压，可以开始分析")
                self.run_btn.setEnabled(True)
                self.ai_run_btn.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"解压失败: {e}")
                self.run_btn.setEnabled(False)

    def _on_run_analysis(self):
        """执行分析"""
        if not self._current_log_dir:
            QMessageBox.warning(self, "警告", "请先选择日志文件")
            return

        # 禁用按钮，显示进度
        self.run_btn.setEnabled(False)
        self.select_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.error_list.clear_errors()
        self.summary_text.clear()

        self.statusbar.showMessage("正在分析...")

        # 启动后台线程
        self._worker = AnalysisWorker(
            self.script_manager,
            self.executor,
            self._current_log_dir
        )
        self._worker.progress_update.connect(self._on_progress_update)
        self._worker.finished.connect(self._on_analysis_finished)
        self._worker.error.connect(self._on_analysis_error)
        self._worker.start()
    
    def _on_run_ai_analysis(self):
        """执行AI分析"""
        if not self._current_log_dir:
            QMessageBox.warning(self, "警告", "请先选择日志文件")
            return
        
        # 检查AI是否配置
        if not self.ai_analyzer.is_configured():
            QMessageBox.warning(self, "警告", 
                "请先配置AI API。\n\n"
                "请在菜单中选择：工具 -> AI配置\n"
                "填写API URL和API Key"
            )
            return

        # 禁用按钮，显示进度
        self.run_btn.setEnabled(False)
        self.ai_run_btn.setEnabled(False)
        self.select_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.error_list.clear_errors()
        self.summary_text.clear()

        self.statusbar.showMessage("正在执行AI分析...")

        # 启动AI分析线程
        self._worker = AIAnalysisWorker(
            self.ai_analyzer,
            self._current_log_dir
        )
        self._worker.progress_update.connect(self._on_progress_update)
        self._worker.finished.connect(self._on_analysis_finished)
        self._worker.error.connect(self._on_analysis_error)
        self._worker.start()

    def _on_progress_update(self, message: str):
        """更新进度"""
        self.progress.setFormat(message)
        self.statusbar.showMessage(message)

    def _on_analysis_finished(self, result: AnalysisResult):
        """分析完成"""
        self.progress.setVisible(False)
        self.run_btn.setEnabled(True)
        self.ai_run_btn.setEnabled(True)
        self.select_btn.setEnabled(True)

        # 显示错误列表
        errors_dict = [
            e.to_dict() if isinstance(e, ErrorInfo) else e
            for e in result.errors
        ]
        self.error_list.set_errors(errors_dict)

        # 显示摘要
        self.summary_text.setText(result.summary)

        # 状态栏
        if result.success:
            self.statusbar.showMessage("分析完成 - 未发现问题")
        else:
            self.statusbar.showMessage(f"分析完成 - 发现 {len(result.errors)} 个问题")

    def _on_analysis_error(self, error_msg: str):
        """分析出错"""
        self.progress.setVisible(False)
        self.run_btn.setEnabled(True)
        self.ai_run_btn.setEnabled(True)
        self.select_btn.setEnabled(True)
        QMessageBox.critical(self, "分析错误", error_msg)
        self.statusbar.showMessage("分析失败")

    def _on_solution_requested(self, error_code: str):
        """请求解决方案"""
        self.statusbar.showMessage(f"正在获取 {error_code} 的解决方案...")

        try:
            html = self.solution_manager.get_solution_html(error_code)
            dialog = SolutionDialog(error_code, html, self)
            dialog.show()
            self.statusbar.showMessage("就绪")
        except Exception as e:
            QMessageBox.warning(self, "警告", f"获取解决方案失败: {e}")
            self.statusbar.showMessage("获取解决方案失败")

    def closeEvent(self, event):
        """关闭时清理"""
        self.log_handler.cleanup_all()
        super().closeEvent(event)
