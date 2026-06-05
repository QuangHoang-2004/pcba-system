from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from src.ui.utils.style_utils import apply_shadow

class ComponentTable(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("tableFrame")
        self.setStyleSheet("""
            QFrame#tableFrame {
                background-color: #FFFFFF;
                border: 1px solid rgba(0, 0, 0, 0.05);
                border-radius: 16px;
            }
        """)
        apply_shadow(self, blur_radius=20, y_offset=6, alpha=30)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel("Thống kê linh kiện")
        title.setStyleSheet("color: #1E293B; font-size: 15px; font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(title)

        self.table = QTableWidget(0, 3)
        self.table.verticalHeader().setDefaultSectionSize(35)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        self.table.setHorizontalHeaderLabels(["Tên", "Mẫu", "Phát hiện"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        # Style table
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: transparent;
                border: none;
                color: #334155;
                selection-background-color: rgba(59, 130, 246, 0.3);
                selection-color: #0F172A;
                alternate-background-color: rgba(0, 0, 0, 0.02);
            }
            QHeaderView::section {
                background-color: #F1F5F9;
                color: #475569;
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 13px;
                text-transform: uppercase;
            }
            QTableWidget::item {
                padding: 5px 10px;
                border-bottom: 1px solid rgba(0, 0, 0, 0.05);
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

        # Initial clear
        self.table.setRowCount(0)
        layout.addWidget(self.table)

    def update_data(self, record):
        if not record or "components" not in record:
            self.table.setRowCount(0)
            return
            
        comps = record["components"]
        self.table.setRowCount(len(comps))
        for row, comp in enumerate(comps):
            name, expected, detected = comp
            row_data = [name, str(expected), str(detected)]
            
            for col, value in enumerate(row_data):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter if col > 0 else Qt.AlignLeft | Qt.AlignVCenter)
                
                if col == 2:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                    
                    if detected == expected:
                        item.setForeground(QColor("#16A34A")) # Green
                    else:
                        item.setForeground(QColor("#DC2626")) # Red
                        
                self.table.setItem(row, col, item)
