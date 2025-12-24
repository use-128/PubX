from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QHeaderView,
    QGroupBox, QFormLayout, QLineEdit, QPushButton, QMessageBox,
    QSplitter
)
from PySide6.QtSql import QSqlDatabase, QSqlTableModel
from PySide6.QtCore import Qt

from app.controllers import account_controller


class AccountView(QWidget):
    def __init__(self):
        super().__init__()
        self.current_account_id = None

        # Database connection for the view
        conn_name = "account_view_conn"
        if QSqlDatabase.contains(conn_name):
            self.db = QSqlDatabase.database(conn_name)
        else:
            self.db = QSqlDatabase.addDatabase("QSQLITE", conn_name)
            self.db.setDatabaseName("database.db")

        if not self.db.open():
            QMessageBox.critical(self, "Database Error", self.db.lastError().text())
            return

        self.model: QSqlTableModel | None = None

        self.setup_ui()
        self.load_accounts()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)

        # Left side: Table view
        table_group = QGroupBox("账号列表")
        table_layout = QVBoxLayout(table_group)
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_layout.addWidget(self.table_view)

        # Right side: Form for adding/editing
        form_group = QGroupBox("账号详情")
        form_layout = QFormLayout(form_group)
        self.platform_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.remark_input = QLineEdit()

        form_layout.addRow("平台:", self.platform_input)
        form_layout.addRow("用户名:", self.username_input)
        form_layout.addRow("密码:", self.password_input)
        form_layout.addRow("备注:", self.remark_input)

        # Buttons
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("新增")
        self.save_button = QPushButton("保存")
        self.delete_button = QPushButton("删除")
        self.clear_button = QPushButton("清空")
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        button_layout.addWidget(self.clear_button)

        right_layout = QVBoxLayout()
        right_layout.addWidget(form_group)
        right_layout.addLayout(button_layout)
        right_layout.addStretch()

        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        splitter.addWidget(table_group)
        splitter.addWidget(right_widget)
        splitter.setSizes([600, 400])

        main_layout.addWidget(splitter)

        # Connect signals
        self.add_button.clicked.connect(self.add_account)
        self.save_button.clicked.connect(self.save_account)
        self.delete_button.clicked.connect(self.delete_account)
        self.clear_button.clicked.connect(self.clear_form)
        # ⚠ 注意：这里不再连接 selectionModel，改到 load_accounts 里去

    def load_accounts(self):
        self.model = QSqlTableModel(self, self.db)
        self.model.setTable("account")
        self.model.select()

        # Set headers
        self.model.setHeaderData(self.model.fieldIndex("platform"), Qt.Horizontal, "平台")
        self.model.setHeaderData(self.model.fieldIndex("username"), Qt.Horizontal, "用户名")
        self.model.setHeaderData(self.model.fieldIndex("password"), Qt.Horizontal, "密码")
        self.model.setHeaderData(self.model.fieldIndex("remark"), Qt.Horizontal, "备注")

        self.table_view.setModel(self.model)
        self.table_view.hideColumn(self.model.fieldIndex("id"))  # Hide ID column

        # ✅ 这里 model 已经设置好了，再获取 selectionModel 一定不是 None
        sel_model = self.table_view.selectionModel()
        if sel_model is not None:
            sel_model.selectionChanged.connect(self.on_selection_changed)

    def on_selection_changed(self, selected, deselected):
        if not selected.indexes():
            self.current_account_id = None
            self.clear_form()
            return

        row = selected.indexes()[0].row()
        self.current_account_id = self.model.record(row).value("id")

        account = account_controller.get_account_by_id(self.current_account_id)
        if account:
            self.platform_input.setText(account.platform)
            self.username_input.setText(account.username)
            self.password_input.setText(account.password)
            self.remark_input.setText(account.remark)

    def add_account(self):
        platform = self.platform_input.text()
        username = self.username_input.text()
        password = self.password_input.text()
        remark = self.remark_input.text()

        if not all([platform, username, password]):
            QMessageBox.warning(self, "输入错误", "平台、用户名和密码不能为空。")
            return

        account_controller.add_account(platform, username, password, remark)
        self.model.select()  # Refresh table
        self.clear_form()

    def save_account(self):
        if self.current_account_id is None:
            QMessageBox.warning(self, "操作错误", "请先选择一个要编辑的账号。")
            return

        data = {
            "platform": self.platform_input.text(),
            "username": self.username_input.text(),
            "password": self.password_input.text(),
            "remark": self.remark_input.text()
        }

        if not all([data["platform"], data["username"], data["password"]]):
            QMessageBox.warning(self, "输入错误", "平台、用户名和密码不能为空。")
            return

        account_controller.update_account(self.current_account_id, data)
        self.model.select()  # Refresh table
        QMessageBox.information(self, "成功", "账号信息已更新。")

    def delete_account(self):
        if self.current_account_id is None:
            QMessageBox.warning(self, "操作错误", "请先选择一个要删除的账号。")
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除这个账号吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            account_controller.delete_account(self.current_account_id)
            self.model.select()  # Refresh table
            self.clear_form()

    def clear_form(self):
        self.current_account_id = None
        self.platform_input.clear()
        self.username_input.clear()
        self.password_input.clear()
        self.remark_input.clear()
        self.table_view.clearSelection()

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)
