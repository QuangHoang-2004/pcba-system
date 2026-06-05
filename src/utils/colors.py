def get_label_color(name: str) -> tuple:
    """Return a BGR color tuple based on the label name for OpenCV drawing."""
    name_lower = name.strip().lower()
    
    # BGR format: (Blue, Green, Red)
    COLOR_MAP = {
        "capacitor": (248, 189, 56),   # Sky Blue / Cyan (RGB: 56, 189, 248)
        "diode": (11, 158, 245),       # Amber / Yellow (RGB: 245, 158, 11)
        "resistor": (46, 204, 113),     # Emerald Green (RGB: 113, 204, 46)
        "transistor": (153, 72, 236),  # Pink / Magenta (RGB: 236, 72, 153)
    }
    
    return COLOR_MAP.get(name_lower, (46, 204, 113))  # Fallback to emerald green
