from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QHeaderView, QMessageBox, QGroupBox
)
from PySide6.QtSql import QSqlDatabase, QSqlTableModel
from PySide6.QtCore import Qt


class PublicationView(QWidget):
    def __init__(self):
        super().__init__()
        
        # Use a dedicated connection for this model
        self.db = QSqlDatabase.addDatabase("QSQLITE", "publication_view_conn")
        self.db.setDatabaseName("database.db")
        if not self.db.open():
            QMessageBox.critical(self, "Database Error", self.db.lastError().text())
            return

        self.setup_ui()
        self.load_records()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        group_box = QGroupBox("发布历史记录")
        layout = QVBoxLayout(group_box)
        
        self.table_view = QTableView()
        self.table_view.setSortingEnabled(True)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setEditTriggers(QTableView.NoEditTriggers) # Read-only
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.table_view)
        main_layout.addWidget(group_box)

    def load_records(self):
        self.model = QSqlTableModel(self, self.db)
        self.model.setTable("publicationrecord")
        
        # Set column headers
        self.model.setHeaderData(self.model.fieldIndex("title"), Qt.Horizontal, "标题")
        self.model.setHeaderData(self.model.fieldIndex("status"), Qt.Horizontal, "状态")
        self.model.setHeaderData(self.model.fieldIndex("published_at"), Qt.Horizontal, "发布时间")
        self.model.setHeaderData(self.model.fieldIndex("account_id"), Qt.Horizontal, "账号ID")
        self.model.setHeaderData(self.model.fieldIndex("description"), Qt.Horizontal, "内容摘要")
        
        self.model.select()
        self.table_view.setModel(self.model)

        # Hide columns we don't want to see
        self.table_view.hideColumn(self.model.fieldIndex("id"))
        self.table_view.hideColumn(self.model.fieldIndex("media_paths"))

        # Sort by date by default
        self.table_view.sortByColumn(self.model.fieldIndex("published_at"), Qt.DescendingOrder)

    def refresh(self):
        """Public method to refresh the view."""
        self.model.select()

    def closeEvent(self, event):
        self.db.close()
        QSqlDatabase.removeDatabase("publication_view_conn")
        super().closeEvent(event)
