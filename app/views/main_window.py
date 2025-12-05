import asyncio
import importlib
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QGroupBox, QFormLayout, QComboBox, QPushButton,
    QTextEdit, QProgressBar, QMessageBox
)
from PySide6.QtCore import QThread, Signal, Slot

from app.views.account_view import AccountView
from app.controllers import account_controller


class AsyncWorker(QThread):
    """
    A worker thread to run asyncio tasks without blocking the UI.
    """
    log_received = Signal(str)
    task_finished = Signal()

    def __init__(self, publisher_module_name, account, task_data):
        super().__init__()
        self.publisher_module_name = publisher_module_name
        self.account = account
        self.task_data = task_data

    def run(self):
        try:
            publisher_module = importlib.import_module(self.publisher_module_name)
            asyncio.run(publisher_module.publish(self.account, self.task_data, self.log_received.emit))
        except Exception as e:
            self.log_received.emit(f"发生严重错误: {e}")
        finally:
            self.task_finished.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python 多平台发布助手")
        self.setGeometry(100, 100, 1200, 700)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Add tabs
        self.setup_publisher_tab()
        self.setup_account_tab()
        self.setup_settings_tab()

    def setup_publisher_tab(self):
        publisher_widget = QWidget()
        layout = QVBoxLayout(publisher_widget)

        # Top: Task selection
        selection_group = QGroupBox("任务配置")
        form_layout = QFormLayout(selection_group)
        self.platform_selector = QComboBox()
        self.account_selector = QComboBox()
        
        form_layout.addRow("选择平台:", self.platform_selector)
        form_layout.addRow("选择账号:", self.account_selector)
        
        # Bottom: Logging and execution
        control_group = QGroupBox("执行与日志")
        control_layout = QVBoxLayout(control_group)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Indeterminate
        self.progress_bar.hide()
        self.start_button = QPushButton("开始发布")

        control_layout.addWidget(self.log_output)
        control_layout.addWidget(self.progress_bar)
        control_layout.addWidget(self.start_button)

        layout.addWidget(selection_group)
        layout.addWidget(control_group)
        
        self.tabs.addTab(publisher_widget, "自动化发布")

        # Connect signals
        self.platform_selector.currentTextChanged.connect(self.update_account_selector)
        self.start_button.clicked.connect(self.start_publishing_task)
        
        self.load_platforms()

    def setup_account_tab(self):
        account_widget = AccountView()
        self.tabs.addTab(account_widget, "账号管理")
        # Refresh publisher tab when accounts might have changed
        self.tabs.currentChanged.connect(self.on_tab_changed)

    def setup_settings_tab(self):
        settings_widget = QWidget()
        # Add settings components here later
        self.tabs.addTab(settings_widget, "设置")

    def load_platforms(self):
        self.platform_selector.clear()
        # In a real app, you might scan the `publishers` directory
        # For now, we'll hardcode it.
        self.platform_selector.addItem("xiaohongshu")
        # self.platform_selector.addItem("temu") # Example for another platform

    def update_account_selector(self, platform):
        self.account_selector.clear()
        if not platform:
            return
        
        accounts = account_controller.get_all_accounts()
        for acc in accounts:
            if acc.platform.lower() == platform.lower():
                self.account_selector.addItem(f"{acc.username} ({acc.remark})", userData=acc.id)

    @Slot(str)
    def append_log(self, message):
        self.log_output.append(message)

    @Slot()
    def on_task_finished(self):
        self.start_button.setEnabled(True)
        self.progress_bar.hide()
        QMessageBox.information(self, "完成", "发布任务已结束。")

    def start_publishing_task(self):
        platform = self.platform_selector.currentText()
        account_id = self.account_selector.currentData()

        if not platform or account_id is None:
            QMessageBox.warning(self, "错误", "请选择平台和账号。")
            return

        account = account_controller.get_account_by_id(account_id)
        if not account:
            QMessageBox.critical(self, "错误", "找不到所选账号。")
            return

        # Placeholder for task data. In a real app, you'd have a UI to collect this.
        task_data = {"content": "这是通过UI触发的自动化内容。"}
        
        publisher_module_name = f"publishers.{platform}_publisher"

        self.log_output.clear()
        self.start_button.setEnabled(False)
        self.progress_bar.show()

        # Run the asyncio task in a separate thread
        self.worker = AsyncWorker(publisher_module_name, account, task_data)
        self.worker.log_received.connect(self.append_log)
        self.worker.task_finished.connect(self.on_task_finished)
        self.worker.start()

    def on_tab_changed(self, index):
        # When switching to the publisher tab, refresh the accounts
        if self.tabs.tabText(index) == "自动化发布":
            self.update_account_selector(self.platform_selector.currentText())

    def closeEvent(self, event):
        # Ensure worker thread is properly terminated
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        event.accept()


