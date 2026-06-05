from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QTextEdit
from PySide6.QtCore import Qt
from src.ui.utils.style_utils import apply_shadow

class ControlPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("QFrame { background: transparent; border: none; }")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Buttons Row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.btn_start = QPushButton("▶ BẮT ĐẦU")
        self.btn_stop = QPushButton("■ DỪNG")
        self.btn_reset = QPushButton("↻ RESET")

        # Start Button
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border-radius: 10px;
                font-weight: 800;
                font-size: 13px;
                padding: 12px;
            }
            QPushButton:hover:!disabled { background-color: #059669; }
            QPushButton:pressed:!disabled { background-color: #047857; }
            QPushButton:disabled { background-color: #D1FAE5; color: #6EE7B7; }
        """)
        apply_shadow(self.btn_start, blur_radius=15, color_hex="#10B981", alpha=50)

        # Stop Button
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                border-radius: 10px;
                font-weight: 800;
                font-size: 13px;
                padding: 12px;
            }
            QPushButton:hover:!disabled { background-color: #DC2626; }
            QPushButton:disabled { background-color: #FEE2E2; color: #FCA5A5; }
        """)
        apply_shadow(self.btn_stop, blur_radius=15, color_hex="#EF4444", alpha=50)

        # Reset Button
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #E2E8F0;
                color: #475569;
                border-radius: 10px;
                font-weight: 800;
                font-size: 13px;
                padding: 12px;
            }
            QPushButton:hover { background-color: #CBD5E1; }
        """)

        for btn in [self.btn_start, self.btn_stop, self.btn_reset]:
            btn.setCursor(Qt.PointingHandCursor)
            btn_layout.addWidget(btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

        # Initial state
        self.set_running_state(False)

    def set_running_state(self, is_running: bool):
        self.btn_start.setEnabled(not is_running)
        self.btn_stop.setEnabled(is_running)
        
        # Update shadow based on enabled state
        if is_running:
            self.btn_start.setGraphicsEffect(None)
            apply_shadow(self.btn_stop, blur_radius=15, color_hex="#EF4444", alpha=50)
        else:
            self.btn_stop.setGraphicsEffect(None)
            apply_shadow(self.btn_start, blur_radius=15, color_hex="#10B981", alpha=50)
