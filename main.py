import sys
from PySide6.QtWidgets import QApplication

from src.ui.main_window import PCBADashboard
from src.utils.logger import setup_logger

if __name__ == "__main__":
    setup_logger()
    app = QApplication(sys.argv)

    window = PCBADashboard()
    window.show()

    sys.exit(app.exec())