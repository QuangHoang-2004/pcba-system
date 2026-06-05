from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QLineEdit, QSpinBox, QDoubleSpinBox,
    QComboBox, QFileDialog, QScrollArea, QListWidget, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox, QCheckBox, QInputDialog
)
from PySide6.QtCore import Qt
from src.ui.utils.style_utils import apply_shadow
from src.services.config_manager import ConfigManager
import copy

# ─── Design tokens ────────────────────────────────────────────────────────────
BG_CARD = "#FFFFFF"
BORDER  = "rgba(0,0,0,0.06)"
RADIUS  = "12px"

STYLE_CARD = f"QFrame {{ background: {BG_CARD}; border: 1px solid {BORDER}; border-radius: {RADIUS}; }}"
STYLE_INPUT = """
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
        background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 6px;
        padding: 4px 8px; font-size: 13px; color: #1E293B; min-height: 28px;
    }
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border-color: #3B82F6; background: #FFFFFF; }
    QComboBox::drop-down { border: none; width: 24px; }
    QComboBox::down-arrow { image: none; }
    QComboBox QAbstractItemView {
        background: #FFFFFF; color: #1E293B;
        selection-background-color: #EFF6FF; selection-color: #2563EB;
        outline: none; border: 1px solid #E2E8F0; border-radius: 6px;
    }
    QComboBox QListView { background-color: #FFFFFF; }
    QComboBox QListView::item { background-color: #FFFFFF; color: #1E293B; padding: 4px; }
    QComboBox QListView::item:selected { background-color: #EFF6FF; color: #2563EB; }
    QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button { width: 18px; }
"""
STYLE_BTN_PRIMARY = """
    QPushButton {
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #3B82F6, stop:1 #2563EB);
        color: white; border: none; border-radius: 6px; font-weight: 700; font-size: 12px; padding: 6px 16px;
    }
    QPushButton:hover { background: #2563EB; }
"""
STYLE_BTN_SECONDARY = """
    QPushButton {
        background: #F1F5F9; color: #475569; border: 1px solid #E2E8F0; border-radius: 6px;
        font-weight: 600; font-size: 12px; padding: 6px 16px;
    }
    QPushButton:hover { background: #E2E8F0; color: #0F172A; }
"""
STYLE_BTN_DANGER = """
    QPushButton {
        background: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; border-radius: 6px;
        font-weight: 600; font-size: 12px; padding: 6px 16px;
    }
    QPushButton:hover { background: #FECACA; color: #991B1B; }
"""
STYLE_LABEL   = "color:#475569; font-size:12px; font-weight:600; background:transparent; border:none;"
STYLE_SECTION = "color:#0F172A; font-size:15px; font-weight:700; background:transparent; border:none; margin-bottom:8px;"
STYLE_SIDEBAR = """
    QListWidget { background: #FFFFFF; border: 1px solid rgba(0,0,0,0.06); border-radius: 12px; outline: none; padding: 8px; }
    QListWidget::item { color: #475569; font-size: 13px; font-weight: 600; padding: 10px 12px; border-radius: 6px; margin-bottom: 4px; }
    QListWidget::item:hover { background: #F1F5F9; color: #1E293B; }
    QListWidget::item:selected { background: #EFF6FF; color: #2563EB; font-weight: 700; }
"""
STYLE_TABLE = """
    QTableWidget { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 12px; color: #334155; }
    QHeaderView::section { background: #F8FAFC; color: #64748B; font-weight: bold; font-size: 12px; padding: 6px; border: none; border-bottom: 1px solid #E2E8F0; }
    QTableWidget::item { padding: 4px; }
"""

def _form_row(label_text: str, widget: QWidget, inner: QVBoxLayout):
    row = QHBoxLayout()
    lbl = QLabel(label_text)
    lbl.setFixedWidth(140)
    lbl.setStyleSheet(STYLE_LABEL)
    row.addWidget(lbl)
    row.addWidget(widget)
    row.addStretch()
    inner.addLayout(row)


class SystemConfigPage(QWidget):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.current_config = self.config_manager.get_full_config()
        self.boards = []
        self.active_board_id = ""  # The board the system will run
        self.edit_board_id = ""    # The board currently being edited in Board Management
        self.is_loading = True
        
        self.setStyleSheet(STYLE_INPUT)
        
        root = QHBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(12)
        
        # 1. SIDEBAR
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet(STYLE_SIDEBAR)
        apply_shadow(self.sidebar, blur_radius=12, y_offset=4, alpha=15)
        self.sidebar.addItems([
            "🖥️ Profile Board", 
            "📦 Quản lý Board mạch"
        ])
        self.sidebar.currentRowChanged.connect(self.stack_change_page)
        root.addWidget(self.sidebar)
        
        # 2. MAIN CONTENT
        main_area = QVBoxLayout()
        main_area.setContentsMargins(0, 0, 0, 0)
        main_area.setSpacing(12)
        
        self.stack = QStackedWidget()
        self.stack.addWidget(self._create_active_board_page())
        self.stack.addWidget(self._create_board_management_page())
        main_area.addWidget(self.stack)
        # 3. FOOTER
        footer = QFrame()
        footer.setStyleSheet("background: #FFFFFF; border: 1px solid rgba(0,0,0,0.06); border-radius: 12px;")
        apply_shadow(footer, blur_radius=12, y_offset=4, alpha=15)
        footer_lay = QHBoxLayout(footer)
        footer_lay.setContentsMargins(12, 10, 12, 10)
        
        btn_reload = QPushButton("Tải lại cấu hình")
        btn_reload.setStyleSheet(STYLE_BTN_SECONDARY)
        btn_reload.clicked.connect(self.load_config_from_json)
        
        btn_save = QPushButton("💾 Lưu cấu hình")
        btn_save.setStyleSheet(STYLE_BTN_PRIMARY)
        btn_save.clicked.connect(self.save_config_to_json)
        
        footer_lay.addStretch()
        footer_lay.addWidget(btn_reload)
        footer_lay.addWidget(btn_save)
        
        main_area.addWidget(footer)
        root.addLayout(main_area)
        
        self.load_config_from_json()

    def stack_change_page(self, index):
        # Save memory of the currently edited board before switching
        if not self.is_loading:
            self._save_board_edit_to_memory()
        self.stack.setCurrentIndex(index)
        if index == 1:  # Board management tab
            self._load_board_edit_ui()

    def _create_scroll_card(self, title):
        card = QFrame()
        card.setStyleSheet(STYLE_CARD)
        apply_shadow(card, blur_radius=12, y_offset=4, alpha=15)
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(16, 16, 16, 16)
        lbl = QLabel(title); lbl.setStyleSheet(STYLE_SECTION)
        vbox.addWidget(lbl)
        sep = QFrame(); sep.setFixedHeight(1); sep.setStyleSheet("background: #E2E8F0; border: none; margin-bottom: 8px;")
        vbox.addWidget(sep)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame); scroll.setStyleSheet("background: transparent;")
        content = QWidget(); content.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(content); lay.setContentsMargins(0,0,0,0); lay.setSpacing(10)
        scroll.setWidget(content)
        vbox.addWidget(scroll)
        return card, lay

    # --- PAGES ---
    def _create_active_board_page(self):
        card, lay = self._create_scroll_card("🖥️ Chọn Mạch Chạy Dây Chuyền")
        
        lbl_info = QLabel("Chọn loại mạch (Profile) hệ thống sẽ sử dụng để phát hiện và kiểm tra linh kiện.")
        lbl_info.setStyleSheet("color: #64748B; font-size: 13px; margin-bottom: 10px;")
        lay.addWidget(lbl_info)
        
        self.ui_active_board_sel = QComboBox()
        self.ui_active_board_sel.currentIndexChanged.connect(self._on_active_board_changed)
        _form_row("Mạch đang chọn:", self.ui_active_board_sel, lay)
        
        # Readonly summary
        self.ui_active_name = QLineEdit(); self.ui_active_name.setReadOnly(True); self.ui_active_name.setStyleSheet("background:#F1F5F9;")
        self.ui_active_comps = QLineEdit(); self.ui_active_comps.setReadOnly(True); self.ui_active_comps.setStyleSheet("background:#F1F5F9;")
        _form_row("Tên mạch:", self.ui_active_name, lay)
        _form_row("Tổng linh kiện:", self.ui_active_comps, lay)
        
        lay.addStretch()
        return card



    def _create_board_management_page(self):
        card, lay = self._create_scroll_card("📦 Quản lý Board mạch & Linh kiện")
        
        # Select board to edit
        sel_row = QHBoxLayout()
        sel_row.addWidget(QLabel("Chọn mạch để sửa:", styleSheet=STYLE_LABEL, fixedWidth=140))
        self.ui_edit_board_sel = QComboBox()
        self.ui_edit_board_sel.currentIndexChanged.connect(self._on_edit_board_selected)
        sel_row.addWidget(self.ui_edit_board_sel)
        
        btn_add = QPushButton("+ Thêm"); btn_add.setStyleSheet(STYLE_BTN_SECONDARY)
        btn_add.clicked.connect(self._add_board)
        btn_del = QPushButton("- Xóa"); btn_del.setStyleSheet(STYLE_BTN_DANGER)
        btn_del.clicked.connect(self._del_board)
        sel_row.addWidget(btn_add)
        sel_row.addWidget(btn_del)
        sel_row.addStretch()
        lay.addLayout(sel_row)
        
        sep = QFrame(); sep.setFixedHeight(1); sep.setStyleSheet("background: #E2E8F0; border: none; margin: 10px 0;")
        lay.addWidget(sep)
        
        # Details
        self.ui_board_id = QLineEdit(); self.ui_board_id.setReadOnly(True); self.ui_board_id.setStyleSheet("background:#F1F5F9;")
        self.ui_board_name = QLineEdit()
        _form_row("Mã board (ID):", self.ui_board_id, lay)
        _form_row("Tên board:", self.ui_board_name, lay)
        
        # Components table
        lbl_comp = QLabel("Danh sách linh kiện yêu cầu:"); lbl_comp.setStyleSheet(STYLE_LABEL)
        lay.addWidget(lbl_comp)
        
        self.tbl_comp = QTableWidget(0, 2)
        self.tbl_comp.setHorizontalHeaderLabels(["Tên linh kiện", "SL Yêu cầu"])
        self.tbl_comp.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl_comp.setStyleSheet(STYLE_TABLE)
        self.tbl_comp.setMinimumHeight(200)
        lay.addWidget(self.tbl_comp)
        
        btn_row = QHBoxLayout()
        btn_add_comp = QPushButton("+ Thêm linh kiện"); btn_add_comp.setStyleSheet(STYLE_BTN_SECONDARY)
        btn_add_comp.clicked.connect(lambda: self.tbl_comp.insertRow(self.tbl_comp.rowCount()))
        btn_del_comp = QPushButton("- Xóa dòng chọn"); btn_del_comp.setStyleSheet(STYLE_BTN_DANGER)
        btn_del_comp.clicked.connect(lambda: self.tbl_comp.removeRow(self.tbl_comp.currentRow()))
        btn_row.addWidget(btn_add_comp); btn_row.addWidget(btn_del_comp); btn_row.addStretch()
        lay.addLayout(btn_row)
        
        return card






    # --- LOGIC ---
    def _add_board(self):
        name, ok = QInputDialog.getText(self, "Thêm Board", "Nhập ID (Mã board, vd: board_v3):")
        if ok and name.strip():
            new_id = name.strip()
            if any(b.get("board_id") == new_id for b in self.boards):
                QMessageBox.warning(self, "Lỗi", "Board ID đã tồn tại!")
                return
            
            self._save_board_edit_to_memory() 
            self.boards.append({
                "board_id": new_id,
                "board_name": "New Board",
                "components": []
            })
            self._refresh_combos()
            self.ui_edit_board_sel.setCurrentText(new_id)

    def _del_board(self):
        if len(self.boards) <= 1:
            QMessageBox.warning(self, "Lỗi", "Phải có ít nhất 1 Board trong hệ thống!")
            return
        rep = QMessageBox.question(self, "Xóa Board", f"Bạn muốn xóa board {self.edit_board_id}?")
        if rep == QMessageBox.Yes:
            self.boards = [b for b in self.boards if b.get("board_id") != self.edit_board_id]
            self.edit_board_id = self.boards[0]["board_id"]
            if self.active_board_id not in [b["board_id"] for b in self.boards]:
                self.active_board_id = self.boards[0]["board_id"]
            self._refresh_combos()

    def _refresh_combos(self):
        self.is_loading = True
        
        self.ui_active_board_sel.clear()
        self.ui_edit_board_sel.clear()
        
        for b in self.boards:
            self.ui_active_board_sel.addItem(b.get("board_id"))
            self.ui_edit_board_sel.addItem(b.get("board_id"))
            
        # Set indices
        idx_act = self.ui_active_board_sel.findText(self.active_board_id)
        if idx_act >= 0: self.ui_active_board_sel.setCurrentIndex(idx_act)
            
        idx_edit = self.ui_edit_board_sel.findText(self.edit_board_id)
        if idx_edit >= 0: self.ui_edit_board_sel.setCurrentIndex(idx_edit)
        
        self.is_loading = False
        self._on_active_board_changed()
        self._load_board_edit_ui()

    def _on_active_board_changed(self):
        if self.is_loading: return
        self.active_board_id = self.ui_active_board_sel.currentText()
        b = next((x for x in self.boards if x.get("board_id") == self.active_board_id), None)
        if b:
            self.ui_active_name.setText(b.get("board_name", ""))
            c = b.get("components", [])
            self.ui_active_comps.setText(f"{len(c)} loại linh kiện")

    def _on_edit_board_selected(self, idx):
        if self.is_loading or idx < 0: return
        self._save_board_edit_to_memory()
        self.edit_board_id = self.ui_edit_board_sel.currentText()
        self._load_board_edit_ui()

    def _get_edit_board_dict(self):
        return next((x for x in self.boards if x.get("board_id") == self.edit_board_id), None)

    def _load_board_edit_ui(self):
        b = self._get_edit_board_dict()
        if b:
            self.is_loading = True
            self.ui_board_id.setText(b.get("board_id", ""))
            self.ui_board_name.setText(b.get("board_name", ""))
            
            comps = b.get("components", [])
            self.tbl_comp.setRowCount(0)
            for c in comps:
                r = self.tbl_comp.rowCount()
                self.tbl_comp.insertRow(r)
                self.tbl_comp.setItem(r, 0, QTableWidgetItem(c.get("name", "")))
                self.tbl_comp.setItem(r, 1, QTableWidgetItem(str(c.get("required_count", 0))))
            self.is_loading = False

    def _save_board_edit_to_memory(self):
        b = self._get_edit_board_dict()
        if b and not self.is_loading:
            b["board_name"] = self.ui_board_name.text()
            comps = []
            for r in range(self.tbl_comp.rowCount()):
                n = self.tbl_comp.item(r, 0).text() if self.tbl_comp.item(r, 0) else ""
                c = self.tbl_comp.item(r, 1).text() if self.tbl_comp.item(r, 1) else "0"
                try: cv = int(c)
                except: cv = 0
                if n.strip():
                    comps.append({"name": n.strip(), "required_count": cv})
            b["components"] = comps

    def load_config_from_json(self):
        self.is_loading = True
        cfg = self.config_manager.get_full_config()
        self.current_config = copy.deepcopy(cfg)
        
        self.boards = copy.deepcopy(cfg.get("boards", []))
        for b in self.boards:
            for comp in b.get("components", []):
                comp.pop("min_confidence", None)
        if not self.boards:
            self.boards = [{"board_id": "default", "board_name": "Default Board", "model_path": "", "components": []}]
            
        self.active_board_id = cfg.get("active_board_id", self.boards[0]["board_id"])
        self.edit_board_id = self.active_board_id
        
        self._refresh_combos()
        self.is_loading = False

    def save_config_to_json(self):
        self._save_board_edit_to_memory()
        
        cfg = copy.deepcopy(self.current_config)
        cfg["active_board_id"] = self.active_board_id
        cfg["boards"] = copy.deepcopy(self.boards)
        
        self.config_manager.set_full_config(cfg)
        self.current_config = cfg
        QMessageBox.information(self, "Lưu thành công", "Đã lưu cấu hình hệ thống!")



    def get_current_config(self):
        return self.current_config

ConfigPage = SystemConfigPage
