import socket
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont
from src.ui.utils.style_utils import apply_shadow

class InternetCheckWorker(QThread):
    status_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True

    def run(self):
        while self.running:
            connected = self.check_connection()
            self.status_changed.emit(connected)
            # Check every 10 seconds, but check exit flag frequently
            for _ in range(20):
                if not self.running:
                    break
                self.msleep(500)

    def check_connection(self):
        try:
            # Connect to Google's public DNS IP (no DNS lookup block)
            socket.setdefaulttimeout(2.0)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            return True
        except Exception:
            return False

    def stop(self):
        self.running = False
        self.wait()

class HeaderWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(65)
        self.setObjectName("headerFrame")
        
        # Premium styling with border and gradient-like dark background
        self.setStyleSheet("""
            QFrame#headerFrame {
                background-color: #FFFFFF;
                border-bottom: 1px solid rgba(0, 0, 0, 0.05);
                border-radius: 12px;
            }
        """)
        apply_shadow(self, blur_radius=15, y_offset=5, alpha=50)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)

        # Title Layout
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        
        title = QLabel("AI PCBA Inspection System")
        font = title.font()
        font.setPointSize(18)
        font.setBold(True)
        title.setFont(font)
        title.setStyleSheet("color: #0F172A; background: transparent;")
        
                
        title_layout.addWidget(title)

        # Status Badge (Internet Status)
        self.status = QLabel("● CHECKING...")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setFixedSize(140, 36)
        self.status.setStyleSheet("""
            QLabel {
                background-color: rgba(241, 245, 249, 1);
                color: #64748B;
                border: 1px solid rgba(226, 232, 240, 1);
                border-radius: 18px;
                font-weight: bold;
                font-size: 13px;
                letter-spacing: 1px;
            }
        """)

        # ESP32 Status Badge
        self.esp_status = QLabel("🔌 ESP32: DÒ TÌM...")
        self.esp_status.setAlignment(Qt.AlignCenter)
        self.esp_status.setFixedSize(180, 36)
        self.esp_status.setStyleSheet("""
            QLabel {
                background-color: rgba(239, 68, 68, 0.1);
                color: #EF4444;
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 18px;
                font-weight: bold;
                font-size: 13px;
                letter-spacing: 0.5px;
            }
        """)

        layout.addLayout(title_layout)
        layout.addStretch()
        layout.addWidget(self.esp_status)
        layout.addWidget(self.status)

        # Internet checker thread
        self.internet_worker = InternetCheckWorker(self)
        self.internet_worker.status_changed.connect(self.set_online_status)
        self.internet_worker.start()

    def set_online_status(self, online: bool):
        if online:
            self.status.setText("● ONLINE")
            self.status.setStyleSheet("""
                QLabel {
                    background-color: rgba(34, 197, 94, 0.15);
                    color: #22C55E;
                    border: 1px solid rgba(34, 197, 94, 0.3);
                    border-radius: 18px;
                    font-weight: bold;
                    font-size: 13px;
                    letter-spacing: 1px;
                }
            """)
        else:
            self.status.setText("● OFFLINE")
            self.status.setStyleSheet("""
                QLabel {
                    background-color: rgba(239, 68, 68, 0.1);
                    color: #EF4444;
                    border: 1px solid rgba(239, 68, 68, 0.3);
                    border-radius: 18px;
                    font-weight: bold;
                    font-size: 13px;
                    letter-spacing: 1px;
                }
            """)

    def set_esp_connected(self, connected: bool, port_name: str = ""):
        if connected:
            self.esp_status.setText(f"ESP32: {port_name}")
            self.esp_status.setStyleSheet("""
                QLabel {
                    background-color: rgba(34, 197, 94, 0.15);
                    color: #22C55E;
                    border: 1px solid rgba(34, 197, 94, 0.3);
                    border-radius: 18px;
                    font-weight: bold;
                    font-size: 13px;
                    letter-spacing: 0.5px;
                }
            """)
        else:
            self.esp_status.setText("ESP32: DISCONNECTED")
            self.esp_status.setStyleSheet("""
                QLabel {
                    background-color: rgba(239, 68, 68, 0.1);
                    color: #EF4444;
                    border: 1px solid rgba(239, 68, 68, 0.3);
                    border-radius: 18px;
                    font-weight: bold;
                    font-size: 13px;
                    letter-spacing: 0.5px;
                }
            """)

class TabBarWidget(QFrame):
    tab_changed = Signal(int)

    STYLE_ACTIVE = """
        QPushButton {
            background-color: #3B82F6;
            color: white;
            border-radius: 8px;
            font-weight: bold;
            font-size: 14px;
            padding: 0 20px;
            border: none;
        }
        QPushButton:hover { background-color: #2563EB; }
    """
    STYLE_INACTIVE = """
        QPushButton {
            background-color: #FFFFFF;
            color: #475569;
            border-radius: 8px;
            font-weight: bold;
            font-size: 14px;
            padding: 0 20px;
            border: 1px solid #E2E8F0;
        }
        QPushButton:hover { background-color: #F8FAFC; color: #0F172A; }
    """

    def __init__(self):
        super().__init__()
        self.setFixedHeight(50)
        self.setStyleSheet("QFrame { background-color: transparent; border: none; }")
        self._buttons = []
        self._active_idx = 0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(12)

        tab_labels = [
            "Bảng điều khiển",
            "Cấu hình",
            "Lịch sử",
            "Cài đặt",
        ]

        for idx, text in enumerate(tab_labels):
            btn = QPushButton(text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(40)
            btn.setStyleSheet(self.STYLE_ACTIVE if idx == 0 else self.STYLE_INACTIVE)
            if idx == 0:
                apply_shadow(btn, blur_radius=15, color_hex="#3B82F6", alpha=60)
            btn.clicked.connect(lambda checked, i=idx: self._on_tab_click(i))
            layout.addWidget(btn)
            self._buttons.append(btn)

        layout.addStretch()

    def _on_tab_click(self, idx: int):
        if idx == self._active_idx:
            return
        self._buttons[self._active_idx].setStyleSheet(self.STYLE_INACTIVE)
        self._buttons[self._active_idx].setGraphicsEffect(None)
        self._active_idx = idx
        self._buttons[idx].setStyleSheet(self.STYLE_ACTIVE)
        apply_shadow(self._buttons[idx], blur_radius=15, color_hex="#3B82F6", alpha=60)
        self.tab_changed.emit(idx)

    def set_tab_enabled(self, idx: int, enabled: bool):
        if 0 <= idx < len(self._buttons):
            self._buttons[idx].setEnabled(enabled)
            if not enabled:
                self._buttons[idx].setStyleSheet("color: #94A3B8; background: transparent; border: none;")
            else:
                self._buttons[idx].setStyleSheet(self.STYLE_INACTIVE if idx != self._active_idx else self.STYLE_ACTIVE)
