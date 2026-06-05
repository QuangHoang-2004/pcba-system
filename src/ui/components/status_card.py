from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from src.ui.utils.style_utils import apply_shadow

class StatusCard(QFrame):
    def __init__(self, title, count, type="good"):
        super().__init__()
        self.setObjectName("statusCard")
        self.setMinimumHeight(60)
        
        # Good/Defect styling
        if type == "good":
            bg_color = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(22, 163, 74, 0.4), stop:1 rgba(21, 128, 61, 0.2))"
            border_color = "rgba(74, 222, 128, 0.5)"
            text_color = "#16A34A"
            shadow_color = "#16A34A"
        else:
            bg_color = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(220, 38, 38, 0.4), stop:1 rgba(185, 28, 28, 0.2))"
            border_color = "rgba(248, 113, 113, 0.5)"
            text_color = "#DC2626"
            shadow_color = "#DC2626"

        self.setStyleSheet(f"""
            QFrame#statusCard {{
                background: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
        """)
        apply_shadow(self, blur_radius=20, color_hex=shadow_color, alpha=40)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignCenter)

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(f"color: {text_color}; font-size: 11px; font-weight: bold; background: transparent; border: none;")

        self.count_label = QLabel(str(count))
        self.count_label.setAlignment(Qt.AlignCenter)
        self.count_label.setStyleSheet(f"color: {text_color}; font-size: 18px; font-weight: 800; background: transparent; border: none;")

        layout.addWidget(self.title_label)
        layout.addWidget(self.count_label)

    def update_value(self, count):
        self.count_label.setText(str(count))

    def update_type(self, type="good"):
        if type == "good":
            bg_color = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(22, 163, 74, 0.4), stop:1 rgba(21, 128, 61, 0.2))"
            border_color = "rgba(74, 222, 128, 0.5)"
            text_color = "#16A34A"
        else:
            bg_color = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(220, 38, 38, 0.4), stop:1 rgba(185, 28, 28, 0.2))"
            border_color = "rgba(248, 113, 113, 0.5)"
            text_color = "#DC2626"
            
        self.setStyleSheet(f"""
            QFrame#statusCard {{
                background: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
        """)
        self.title_label.setStyleSheet(f"color: {text_color}; font-size: 11px; font-weight: bold; background: transparent; border: none;")
        self.count_label.setStyleSheet(f"color: {text_color}; font-size: 18px; font-weight: 800; background: transparent; border: none;")
