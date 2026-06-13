from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt, QRect, QRectF
from PySide6.QtGui import QPainter, QImage, QPainterPath
from src.ui.utils.style_utils import apply_shadow

class CameraWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("cameraFrame")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.current_frame = None
        
        # HUD Style frame with glowing border
        self.setStyleSheet("""
            QFrame#cameraFrame {
                background-color: #000000;
                border: 1px solid #E2E8F0;
                border-radius: 16px;
            }
        """)
        apply_shadow(self, blur_radius=20, y_offset=8, alpha=40)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        # Top Info Bar
        top_info_layout = QHBoxLayout()
        
        self.model_label = QLabel("YOLO: READY")
        self.model_label.setStyleSheet("""
            color: #38BDF8;
            background-color: rgba(56, 189, 248, 0.1);
            padding: 4px 10px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 12px;
        """)

        top_info_layout.addStretch()
        top_info_layout.addWidget(self.model_label)

        layout.addLayout(top_info_layout)
        layout.addStretch()

        # Center Overlay
        self.camera_overlay = QLabel("CAMERA REALTIME")
        self.camera_overlay.setAlignment(Qt.AlignCenter)
        self.camera_overlay.setStyleSheet("""
            color: rgba(255, 255, 255, 0.1);
            font-size: 28px;
            font-weight: 800;
            letter-spacing: 2px;
            background: transparent;
        """)
        layout.addWidget(self.camera_overlay)

        layout.addStretch()

    def update_frame(self, q_img: QImage):
        self.current_frame = q_img
        if self.camera_overlay.isVisible():
            self.camera_overlay.hide()
        self.update()

    def set_fps(self, fps_text: str):
        self.fps_label.setText(fps_text)

    def paintEvent(self, event):
        # 1. Draw parent style sheet elements (background, border, rounded corners)
        super().paintEvent(event)
        
        if self.current_frame:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            
            # 2. Clip the painter path to sit inside the 16px rounded border (subtract 1px for border outline)
            clip_rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
            path = QPainterPath()
            path.addRoundedRect(clip_rect, 15, 15)
            painter.setClipPath(path)
            
            # 3. Calculate target geometry with Aspect Ratio scaling
            rect = self.contentsRect()
            img_size = self.current_frame.size()
            scaled_size = img_size.scaled(rect.size(), Qt.KeepAspectRatio)
            
            x = rect.x() + (rect.width() - scaled_size.width()) // 2
            y = rect.y() + (rect.height() - scaled_size.height()) // 2
            
            # 4. Draw the image (it will be beautifully clipped inside the rounded borders)
            painter.drawImage(QRect(x, y, scaled_size.width(), scaled_size.height()), self.current_frame)
