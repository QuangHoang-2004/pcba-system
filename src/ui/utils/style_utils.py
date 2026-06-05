from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtGui import QColor

def apply_shadow(widget, blur_radius=20, x_offset=0, y_offset=4, color_hex="#000000", alpha=80):
    """Apply a modern drop shadow to a PySide6 widget."""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur_radius)
    shadow.setXOffset(x_offset)
    shadow.setYOffset(y_offset)
    
    color = QColor(color_hex)
    color.setAlpha(alpha)
    shadow.setColor(color)
    
    widget.setGraphicsEffect(shadow)
