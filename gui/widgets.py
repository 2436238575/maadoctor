"""自定义GUI组件"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextBrowser, QFrame, QScrollArea, QDialog
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont


class ErrorCard(QFrame):
    """错误卡片组件"""
    solution_requested = pyqtSignal(str)  # 发送错误编号

    def __init__(self, error_code: str, title: str, detail: str = "", has_solution: bool = True):
        super().__init__()
        self.error_code = error_code
        self._setup_ui(error_code, title, detail, has_solution)

    def _setup_ui(self, code: str, title: str, detail: str, has_solution: bool):
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            ErrorCard {
                background-color: #fff3f3;
                border: 1px solid #ffcccc;
                border-radius: 6px;
                padding: 8px;
                margin: 4px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        # 标题行
        header = QHBoxLayout()
        code_label = QLabel(f"<b style='color: #cc0000;'>[{code}]</b>")
        title_label = QLabel(f"<b>{title}</b>")
        header.addWidget(code_label)
        header.addWidget(title_label)
        header.addStretch()

        if has_solution:
            btn = QPushButton("获取解决方案")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #0066cc;
                    color: white;
                    border: none;
                    padding: 4px 12px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #0055aa;
                }
            """)
            btn.clicked.connect(lambda: self.solution_requested.emit(self.error_code))
            header.addWidget(btn)

        layout.addLayout(header)

        # 详情
        if detail:
            detail_label = QLabel(detail)
            detail_label.setWordWrap(True)
            detail_label.setStyleSheet("color: #666; margin-top: 4px;")
            layout.addWidget(detail_label)


class SolutionDialog(QDialog):
    """解决方案显示窗口 - 独立弹出窗口"""

    def __init__(self, error_code: str, html_content: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"解决方案 - {error_code}")
        self.setMinimumSize(700, 500)
        self.resize(800, 600)
        # 设置为独立窗口
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMinMaxButtonsHint
        )
        self._setup_ui(error_code, html_content)

    def _setup_ui(self, error_code: str, html_content: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 标题
        title_label = QLabel(f"<h2 style='color: #333;'>📋 {error_code} 解决方案</h2>")
        layout.addWidget(title_label)

        # Markdown内容显示
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(html_content)
        browser.setStyleSheet("""
            QTextBrowser {
                background-color: #fafafa;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
            }
        """)
        layout.addWidget(browser, 1)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.setMinimumWidth(100)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)


class ErrorListWidget(QScrollArea):
    """错误列表组件"""
    solution_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWidget(self._container)

    def clear_errors(self):
        """清除所有错误卡片"""
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def add_error(self, code: str, title: str, detail: str = "", has_solution: bool = True):
        """添加错误卡片"""
        card = ErrorCard(code, title, detail, has_solution)
        card.solution_requested.connect(self.solution_requested.emit)
        self._layout.addWidget(card)

    def set_errors(self, errors: list):
        """设置错误列表"""
        self.clear_errors()
        for err in errors:
            if isinstance(err, dict):
                self.add_error(
                    err.get("code", ""),
                    err.get("title", ""),
                    err.get("detail", ""),
                    err.get("has_solution", True)
                )
