from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QTextEdit, QStackedWidget
)
from PySide6.QtCore import Qt

from src.ui.components.header_widget import HeaderWidget, TabBarWidget
from src.ui.pages.dashboard_page import DashboardPage
from src.ui.pages.config_page import ConfigPage
from src.ui.pages.history_page import HistoryPage
from src.hardware.serial_worker import SerialWorker

class PCBADashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI PCBA Inspection System")
        self.setMinimumSize(1024, 600)
        self.resize(1024, 600)
        self.setObjectName("mainDashboard")

        # Global Style
        self.setStyleSheet("""
            QWidget#mainDashboard {
                background-color: #F1F5F9;
            }
            QWidget {
                font-family: 'Inter', 'Segoe UI', sans-serif;
                color: #0F172A;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1;
                min-height: 30px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover { background: #94A3B8; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """)

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Initialize SerialWorker running in background
        self.serial_worker = SerialWorker(self)
        self.serial_worker.connection_status.connect(self._on_serial_connection_status)
        self.serial_worker.start()

        # 1. Header & Tabs
        self.header = HeaderWidget()
        main_layout.addWidget(self.header)
        self.tab_bar = TabBarWidget()
        main_layout.addWidget(self.tab_bar)

        # 2. Stacked pages
        self.stack = QStackedWidget()

        # ── Page 0: Dashboard ──────────────────────────────────────────────
        self.dashboard_page = DashboardPage(self.serial_worker)
        self.stack.addWidget(self.dashboard_page)   # index 0

        # ── Page 1: Cấu hình ──────────────────────────────────────────────
        self.config_page = ConfigPage()
        self.stack.addWidget(self.config_page)  # index 1

        # ── Page 2: Lịch sử ───────────────────────────────────────────────
        self.history_page = HistoryPage()
        self.stack.addWidget(self.history_page) # index 2

        # ── Page 3: Cài đặt (placeholder) ─────────────────────────────────
        settings_placeholder = QWidget()
        ph_lay = QVBoxLayout(settings_placeholder)
        ph_label = QLabel("🛠 Trang Cài đặt (đang phát triển)")
        ph_label.setAlignment(Qt.AlignCenter)
        ph_label.setStyleSheet("color: #94A3B8; font-size: 20px; font-weight: bold;")
        ph_lay.addWidget(ph_label)
        self.stack.addWidget(settings_placeholder) # index 3

        main_layout.addWidget(self.stack)

        # Connect tab bar signal
        self.tab_bar.tab_changed.connect(self._on_tab_changed)

        # Connect detection state
        self.dashboard_page.detection_state_changed.connect(self._on_detection_state_changed)

    def _on_serial_connection_status(self, connected, port_name):
        self.header.set_esp_connected(connected, port_name)

    def _on_tab_changed(self, index):
        if index == 0:
            self.dashboard_page.refresh_dashboard()
        self.stack.setCurrentIndex(index)

    def _on_detection_state_changed(self, is_running):
        # Disable Config and Settings tab while running
        self.tab_bar.set_tab_enabled(1, not is_running)
        self.tab_bar.set_tab_enabled(3, not is_running)

    def closeEvent(self, event):
        self.serial_worker.stop()
        if hasattr(self, 'dashboard_page') and hasattr(self.dashboard_page, 'camera_worker'):
            self.dashboard_page.camera_worker.stop()
        if hasattr(self, 'header') and hasattr(self.header, 'internet_worker'):
            self.header.internet_worker.stop()
        event.accept()