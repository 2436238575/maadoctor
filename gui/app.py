"""主窗口"""
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog,
    QTextEdit, QStatusBar, QMessageBox, QProgressBar,
    QSplitter, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from core.log_handler import LogHandler
from core.script_manager import ScriptManager
from core.solution_manager import SolutionManager
from core.executor import ScriptExecutor, AnalysisResult, ErrorInfo
from gui.widgets import ErrorListWidget, SolutionDialog


class BatchAnalysisWorker(QThread):
    """批量分析线程 - 执行所有脚本"""
    progress_update = pyqtSignal(int, int, str)  # current, total, script_name
    finished = pyqtSignal(object)  # 合并后的AnalysisResult
    error = pyqtSignal(str)

    def __init__(self, script_manager: ScriptManager, executor: ScriptExecutor, log_dir: str):
        super().__init__()
        self.script_manager = script_manager
        self.executor = executor
        self.log_dir = log_dir

    def run(self):
        try:
            # 获取所有脚本
            script_list = self.script_manager.fetch_script_list()
            if not script_list:
                self.error.emit("没有可用的分析脚本")
                return

            all_errors = []
            all_summaries = []
            total = len(script_list)

            for i, script_info in enumerate(script_list):
                self.progress_update.emit(i + 1, total, script_info.name)

                try:
                    # 下载/复制脚本
                    script_path = self.script_manager.get_script_path(script_info)
                    # 执行分析
                    result = self.executor.run_analysis(script_path, self.log_dir)

                    # 收集结果
                    all_errors.extend(result.errors)
                    if result.summary:
                        all_summaries.append(f"【{script_info.name}】\n{result.summary}")

                except Exception as e:
                    all_summaries.append(f"【{script_info.name}】执行失败: {e}")

            # 去重错误（按code）
            seen_codes = set()
            unique_errors = []
            for err in all_errors:
                code = err.code if isinstance(err, ErrorInfo) else err.get("code", "")
                if code and code not in seen_codes:
                    seen_codes.add(code)
                    unique_errors.append(err)

            # 合并结果
            merged_result = AnalysisResult(
                success=len(unique_errors) == 0,
                errors=unique_errors,
                summary="\n\n".join(all_summaries) if all_summaries else "分析完成，未发现问题"
            )

            self.finished.emit(merged_result)

        except Exception as e:
            self.error.emit(str(e))


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

        main_layout.addWidget(top_group)

        # 进度条
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setTextVisible(True)
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
            except Exception as e:
                QMessageBox.critical(self, "错误", f"解压失败: {e}")
                self.run_btn.setEnabled(False)

    def _on_run_analysis(self):
        """执行所有脚本分析"""
        if not self._current_log_dir:
            QMessageBox.warning(self, "警告", "请先选择日志文件")
            return

        # 禁用按钮，显示进度
        self.run_btn.setEnabled(False)
        self.select_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.error_list.clear_errors()
        self.summary_text.clear()

        self.statusbar.showMessage("正在分析...")

        # 启动后台线程
        self._worker = BatchAnalysisWorker(
            self.script_manager,
            self.executor,
            self._current_log_dir
        )
        self._worker.progress_update.connect(self._on_progress_update)
        self._worker.finished.connect(self._on_analysis_finished)
        self._worker.error.connect(self._on_analysis_error)
        self._worker.start()

    def _on_progress_update(self, current: int, total: int, script_name: str):
        """更新进度"""
        percent = int(current / total * 100)
        self.progress.setValue(percent)
        self.progress.setFormat(f"正在执行: {script_name} ({current}/{total})")
        self.statusbar.showMessage(f"正在执行: {script_name}")

    def _on_analysis_finished(self, result: AnalysisResult):
        """分析完成"""
        self.progress.setVisible(False)
        self.run_btn.setEnabled(True)
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
