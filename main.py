import sys
from PySide6.QtWidgets import QApplication
from app.views.main_window import MainWindow
from app.services.database import create_db_and_tables


def main():
    """
    Main function to launch the application.
    """
    # 1. Initialize database and tables
    print("Initializing database...")
    create_db_and_tables()
    print("Database initialized.")

    # 2. Create and run the Qt application
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()