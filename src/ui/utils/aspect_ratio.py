from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QSize

class AspectRatioContainer(QWidget):
    def __init__(self, child_widget, ratio=4/3, margin=0):
        super().__init__()
        self.child_widget = child_widget
        self.ratio = ratio
        self.margin = margin
        self.bottom_widget = None
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(margin, margin, margin, margin)
        self.layout.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(child_widget)

    def minimumSizeHint(self):
        return QSize(100, 100)

    def add_bottom_widget(self, widget):
        self.bottom_widget = widget
        self.layout.addWidget(widget)

    def resizeEvent(self, event):
        w = event.size().width() - (self.margin * 2)
        h = event.size().height() - (self.margin * 2)
        
        if self.bottom_widget:
            h -= (self.bottom_widget.sizeHint().height() + self.layout.spacing())
        
        if w > 0 and h > 0:
            target_w = w
            target_h = int(w / self.ratio)
            
            if target_h > h:
                target_h = h
                target_w = int(h * self.ratio)
                
            self.child_widget.setFixedSize(target_w, target_h)
            
        super().resizeEvent(event)
