import asyncio
import importlib
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QGroupBox, QFormLayout, QComboBox, QPushButton,
    QTextEdit, QProgressBar, QMessageBox, QFileDialog, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QLineEdit
)
from PySide6.QtCore import Qt, Signal, Slot, QThread

from app.views.account_view import AccountView
from app.views.publication_view import PublicationView
from app.controllers import account_controller, publication_controller


class AsyncWorker(QThread):
    """
    A worker thread to run a queue of asyncio tasks and log the results.
    """
    log_received = Signal(str)
    task_finished = Signal(bool)  # Pass overall success status

    def __init__(self, jobs, task_data):
        super().__init__()
        self.jobs = jobs
        self.task_data = task_data

    def run(self):
        overall_success = True
        total_jobs = len(self.jobs)
        for i, job in enumerate(self.jobs):
            account = job['account']
            platform = job['platform']
            publisher_module_name = f"publishers.{platform}_publisher"
            
            self.log_received.emit(f"--- 开始任务 {i+1}/{total_jobs}: 平台='{platform}', 账号='{account.username}' ---")
            
            success = False
            try:
                publisher_module = importlib.import_module(publisher_module_name)
                asyncio.run(publisher_module.publish(account, self.task_data, self.log_received.emit))
                
                success = True
                publication_controller.add_publication_record(
                    account_id=account.id,
                    title=self.task_data["title"],
                    description=self.task_data["description"],
                    media_paths=self.task_data["media_paths"],
                    status="success"
                )
                self.log_received.emit("发布成功，已存入数据库。")
            except Exception as e:
                overall_success = False
                self.log_received.emit(f"发生严重错误: {e}")
                publication_controller.add_publication_record(
                    account_id=account.id,
                    title=self.task_data["title"],
                    description=self.task_data["description"],
                    media_paths=self.task_data["media_paths"],
                    status="failed"
                )
                self.log_received.emit("发布失败，已存入数据库。")
            
            self.log_received.emit(f"--- 任务 {i+1}/{total_jobs} 结束 ---")
        
        self.task_finished.emit(overall_success)


class MainWindow(QMainWindow):
    # ... (init and other setup methods remain the same)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("多平台发布助手")
        self.setGeometry(100, 100, 1200, 700)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Add tabs
        self.setup_publisher_tab()
        self.setup_account_tab()
        self.setup_publication_history_tab()
        self.setup_settings_tab()

    def setup_publisher_tab(self):
        publisher_widget = QWidget()
        layout = QVBoxLayout(publisher_widget)

        # Top: Task selection using a Tree Widget
        selection_group = QGroupBox("任务配置: 选择要发布的平台和账号")
        tree_layout = QVBoxLayout(selection_group)
        self.platform_tree = QTreeWidget()
        self.platform_tree.setHeaderLabel("平台 / 账号")
        tree_layout.addWidget(self.platform_tree)
        
        # Middle: Content to be published
        content_group = QGroupBox("发布内容")
        content_layout = QFormLayout(content_group)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("输入笔记标题...")

        self.post_type_selector = QComboBox()
        self.post_type_selector.addItems(["图文笔记", "视频笔记"])
        
        self.file_path_input = QLineEdit()
        self.file_path_input.setReadOnly(True)
        self.select_files_button = QPushButton("选择文件")
        
        file_selection_layout = QHBoxLayout()
        file_selection_layout.addWidget(self.file_path_input)
        file_selection_layout.addWidget(self.select_files_button)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("输入笔记内容...")

        content_layout.addRow("标题:", self.title_input)
        content_layout.addRow("内容类型:", self.post_type_selector)
        content_layout.addRow("选择媒体:", file_selection_layout)
        content_layout.addRow("笔记内容:", self.description_input)

        # Bottom: Logging and execution
        control_group = QGroupBox("执行与日志")
        control_layout = QVBoxLayout(control_group)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Indeterminate
        self.progress_bar.hide()
        self.start_button = QPushButton("开始批量发布")

        control_layout.addWidget(self.log_output)
        control_layout.addWidget(self.progress_bar)
        control_layout.addWidget(self.start_button)

        layout.addWidget(selection_group)
        layout.addWidget(content_group)
        layout.addWidget(control_group)
        
        self.tabs.addTab(publisher_widget, "自动化发布")

        # Connect signals
        self.select_files_button.clicked.connect(self.open_file_dialog)
        self.start_button.clicked.connect(self.start_publishing_task)
        self.platform_tree.itemChanged.connect(self.handle_tree_item_change)
        
        self.load_platform_tree()

    def setup_account_tab(self):
        self.account_view = AccountView()
        self.tabs.addTab(self.account_view, "账号管理")

    def setup_publication_history_tab(self):
        self.publication_view = PublicationView()
        self.tabs.addTab(self.publication_view, "发布记录")

    def setup_settings_tab(self):
        settings_widget = QWidget()
        self.tabs.addTab(settings_widget, "设置")
        self.tabs.currentChanged.connect(self.on_tab_changed)

    def load_platform_tree(self):
        self.platform_tree.clear()
        accounts = account_controller.get_all_accounts()
        
        platforms = {} # Group accounts by platform
        for acc in accounts:
            if acc.platform not in platforms:
                platforms[acc.platform] = []
            platforms[acc.platform].append(acc)

        for platform_name, acc_list in platforms.items():
            platform_item = QTreeWidgetItem(self.platform_tree, [platform_name])
            platform_item.setFlags(platform_item.flags() | Qt.ItemIsUserCheckable)
            platform_item.setCheckState(0, Qt.Unchecked)
            
            for acc in acc_list:
                acc_item = QTreeWidgetItem(platform_item, [f"{acc.username} ({acc.remark})"])
                acc_item.setFlags(acc_item.flags() | Qt.ItemIsUserCheckable)
                acc_item.setCheckState(0, Qt.Unchecked)
                acc_item.setData(0, Qt.UserRole, acc.id) # Store account ID

    def handle_tree_item_change(self, item, column):
        self.platform_tree.blockSignals(True)
        if item.childCount() > 0:
            for i in range(item.childCount()):
                item.child(i).setCheckState(0, item.checkState(0))
        elif item.parent():
            if item.checkState(0) == Qt.Checked:
                item.parent().setCheckState(0, Qt.Checked)
            else:
                all_unchecked = True
                parent = item.parent()
                for i in range(parent.childCount()):
                    if parent.child(i).checkState(0) == Qt.Checked:
                        all_unchecked = False
                        break
                if all_unchecked:
                    parent.setCheckState(0, Qt.Unchecked)
        self.platform_tree.blockSignals(False)

    def open_file_dialog(self):
        post_type = self.post_type_selector.currentText()
        if post_type == "图文笔记":
            files, _ = QFileDialog.getOpenFileNames(self, "选择图片", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.webp)")
            if files:
                self.file_path_input.setText(";".join(files))
        elif post_type == "视频笔记":
            file, _ = QFileDialog.getOpenFileName(self, "选择视频", "", "Video Files (*.mp4 *.avi *.mov)")
            if file:
                self.file_path_input.setText(file)

    @Slot(str)
    def append_log(self, message):
        self.log_output.append(message)

    @Slot(bool)
    def on_task_finished(self, success):
        self.start_button.setEnabled(True)
        self.progress_bar.hide()
        if success:
            QMessageBox.information(self, "完成", "所有发布任务已执行完毕。")
        else:
            QMessageBox.warning(self, "失败", "部分或全部任务遇到错误，请查看日志。")

    def start_publishing_task(self):
        # 1. Collect jobs from the tree
        jobs = []
        root = self.platform_tree.invisibleRootItem()
        for i in range(root.childCount()):
            platform_item = root.child(i)
            platform_name = platform_item.text(0)
            for j in range(platform_item.childCount()):
                account_item = platform_item.child(j)
                if account_item.checkState(0) == Qt.Checked:
                    account_id = account_item.data(0, Qt.UserRole)
                    account = account_controller.get_account_by_id(account_id)
                    if account:
                        jobs.append({'account': account, 'platform': platform_name})

        # 2. Validate inputs
        title = self.title_input.text()
        media_paths_str = self.file_path_input.text()
        description = self.description_input.toPlainText()

        if not jobs:
            QMessageBox.warning(self, "错误", "请至少选择一个要发布的账号。")
            return
        
        if not all([title, media_paths_str, description]):
            QMessageBox.warning(self, "错误", "请填写所有发布内容：标题、媒体文件和笔记内容。")
            return

        # 3. Structure common task data
        post_type = self.post_type_selector.currentText()
        task_data = {
            "title": title,
            "post_type": "image" if post_type == "图文笔记" else "video",
            "media_paths": media_paths_str.split(";") if post_type == "图文笔记" else [media_paths_str],
            "description": description
        }
        
        # 4. Start the worker
        self.log_output.clear()
        self.start_button.setEnabled(False)
        self.progress_bar.show()

        self.worker = AsyncWorker(jobs, task_data)
        self.worker.log_received.connect(self.append_log)
        self.worker.task_finished.connect(self.on_task_finished)
        self.worker.start()

    def on_tab_changed(self, index):
        tab_text = self.tabs.tabText(index)
        if tab_text == "自动化发布":
            self.load_platform_tree()
        elif tab_text == "发布记录":
            self.publication_view.refresh()
        elif tab_text == "账号管理":
            self.account_view.model.select()

    def closeEvent(self, event):
        # Ensure worker thread is properly terminated
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        event.accept()


