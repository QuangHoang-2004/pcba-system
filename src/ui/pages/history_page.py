from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QDateEdit, QDialog, QAbstractItemView, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QFont
from src.ui.utils.style_utils import apply_shadow
from src.services.local_storage import StorageService
from src.services.config_manager import ConfigManager
import csv

# ── Style constants ────────────────────────────────────────────────────────────
_CARD = "QFrame{background:#fff;border:1px solid #E2E8F0;border-radius:14px;}"
_SEC  = "color:#1E293B;font-size:14px;font-weight:700;background:transparent;border:none;"
_LBL  = "color:#64748B;font-size:12px;background:transparent;border:none;"
_SEP  = "background:#F1F5F9;border:none;"

_BTN_BLUE  = ("QPushButton{background:#3B82F6;color:#fff;border:none;border-radius:8px;"
              "font-weight:700;font-size:12px;padding:0 16px;"
              "min-height:32px;max-height:32px;}"
              "QPushButton:hover{background:#2563EB;}")
_BTN_GRAY  = ("QPushButton{background:#F1F5F9;color:#475569;border:1.5px solid #E2E8F0;"
              "border-radius:8px;font-weight:600;font-size:12px;padding:0 14px;"
              "min-height:32px;max-height:32px;}"
              "QPushButton:hover{background:#E2E8F0;color:#0F172A;}")
_BTN_RED   = ("QPushButton{background:#FEF2F2;color:#DC2626;border:1.5px solid #FECACA;"
              "border-radius:8px;font-weight:600;font-size:12px;padding:0 14px;"
              "min-height:32px;max-height:32px;}"
              "QPushButton:hover{background:#FECACA;}")
_BTN_INFO  = ("QPushButton{background:#EFF6FF;color:#2563EB;border:1.5px solid #BFDBFE;"
              "border-radius:8px;font-weight:700;font-size:12px;padding:0 10px;"
              "min-height:28px;max-height:28px;}"
              "QPushButton:hover{background:#DBEAFE;}")

_COMBO = ("QComboBox{background:#F8FAFC;border:1.5px solid #E2E8F0;border-radius:8px;"
          "padding:0 10px;font-size:12px;color:#1E293B;"
          "min-height:32px;max-height:32px;}"
          "QComboBox:focus{border-color:#3B82F6;}"
          "QComboBox QAbstractItemView{background:#fff;border:1px solid #E2E8F0;"
          "selection-background-color:#EFF6FF;selection-color:#1E293B;}"
          "QComboBox::drop-down{border:none;width:20px;padding-right:4px;}"
          "QComboBox::down-arrow{border-left:5px solid transparent;border-right:5px solid transparent;"
          "border-top:6px solid #94A3B8;width:0;height:0;margin-right:6px;}")
_DATE  = ("QDateEdit{background:#F8FAFC;border:1.5px solid #E2E8F0;border-radius:8px;"
          "padding:0 8px;font-size:12px;color:#1E293B;"
          "min-height:32px;max-height:32px;}"
          "QDateEdit:focus{border-color:#3B82F6;}"
          "QDateEdit::drop-down{border:none;width:20px;}"
          "QDateEdit::down-arrow{border-left:5px solid transparent;border-right:5px solid transparent;"
          "border-top:6px solid #94A3B8;width:0;height:0;margin-right:4px;}")

_TBL = ("QTableWidget{background:#fff;border:none;font-size:13px;color:#334155;"
        "alternate-background-color:#F8FAFC;selection-background-color:#EFF6FF;"
        "selection-color:#1E293B;}"
        "QHeaderView::section{background:#F8FAFC;color:#64748B;font-weight:700;"
        "font-size:12px;padding:7px 6px;border:none;border-bottom:2px solid #E2E8F0;}"
        "QTableWidget::item{padding:4px;border:none;}")


# ── Helper: card container ─────────────────────────────────────────────────────
def _make_card(title="", with_sep=True):
    f = QFrame(); f.setStyleSheet(_CARD)
    apply_shadow(f, blur_radius=16, y_offset=4, alpha=20)
    v = QVBoxLayout(f); v.setContentsMargins(14, 12, 14, 14); v.setSpacing(8)
    if title:
        t = QLabel(title); t.setStyleSheet(_SEC); v.addWidget(t)
        if with_sep:
            sep = QFrame(); sep.setFixedHeight(1); sep.setStyleSheet(_SEP); v.addWidget(sep)
    return f, v


def clear_layout(layout):
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                clear_layout(item.layout())

# ── Detail dialog ──────────────────────────────────────────────────────────────
class DetectDetailDialog(QDialog):
    def __init__(self, rec: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Chi tiết – {rec['board']}  {rec['date']} {rec['time']}")
        self.setMinimumSize(820, 540)
        self.setStyleSheet("QDialog{background:#F1F5F9;} QLabel{background:transparent;border:none;}"
                           "QWidget{font-family:'Segoe UI',sans-serif;}")
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14); root.setSpacing(10)

        # Header strip
        hdr = QFrame()
        hdr.setStyleSheet("QFrame{background:#1E293B;border-radius:12px;}")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(16, 10, 16, 10)
        brd_lbl = QLabel(rec["board"])
        brd_lbl.setStyleSheet("color:#F8FAFC;font-size:15px;font-weight:800;background:transparent;border:none;")
        hl.addWidget(brd_lbl)
        dt_lbl = QLabel(f"{rec['date']}   {rec['time']}")
        dt_lbl.setStyleSheet("color:#94A3B8;font-size:12px;background:transparent;border:none;")
        hl.addStretch(); hl.addWidget(dt_lbl)
        ok = rec["status"] == "OK"
        badge = QLabel("ĐẠT CHUẨN" if ok else "CÓ LỖI")
        badge.setStyleSheet(
            f"background:{'rgba(22,163,74,.2)' if ok else 'rgba(220,38,38,.2)'};"
            f"color:{'#4ADE80' if ok else '#F87171'};"
            f"border:1px solid {'rgba(74,222,128,.4)' if ok else 'rgba(248,113,113,.4)'};"
            f"border-radius:8px;font-size:12px;font-weight:700;padding:4px 12px;")
        hl.addWidget(badge)
        root.addWidget(hdr)

        # Body
        body = QHBoxLayout(); body.setSpacing(10)

        # Left: image
        img_card, img_v = _make_card("🖼  Ảnh phát hiện")
        img_ph = QLabel("[ DETECTED IMAGE ]")
        img_ph.setAlignment(Qt.AlignCenter)
        img_ph.setMinimumHeight(200)
        img_ph.setStyleSheet("QLabel{background:#0F172A;border-radius:10px;color:#475569;"
                             "font-size:12px;font-weight:600;letter-spacing:1px;}")
        
        # Load real captured image if available
        import os
        from PySide6.QtGui import QPixmap
        from src.ui.utils.aspect_ratio import AspectRatioContainer
        rec_id = rec.get("id")
        img_path = f"data/captures/{rec_id}.jpg"
        if rec_id and os.path.exists(img_path):
            pixmap = QPixmap(img_path)
            if not pixmap.isNull():
                img_ph.setPixmap(pixmap)
                img_ph.setScaledContents(True)
        
        img_container = AspectRatioContainer(img_ph, ratio=1.0, margin=0)
        img_v.addWidget(img_container, stretch=1)

        # mini stats 3-col grid
        sg = QHBoxLayout(); sg.setSpacing(8)
        for label, val, clr in [("Tổng mẫu",str(rec["total"]),"#3B82F6"),
                                  ("Phát hiện",str(rec["detected"]),"#10B981"),
                                  ("Lỗi",str(rec["defect"]),"#EF4444")]:
            mini = QFrame()
            mini.setStyleSheet(f"QFrame{{background:{clr}18;border:1px solid {clr}55;border-radius:8px;}}")
            ml = QVBoxLayout(mini); ml.setContentsMargins(10,6,10,6); ml.setSpacing(0)
            ml.addWidget(QLabel(label, styleSheet=f"color:{clr};font-size:10px;font-weight:700;background:transparent;border:none;"))
            num = QLabel(val)
            font = num.font()
            font.setPointSize(18)
            font.setBold(True)
            num.setFont(font)
            num.setStyleSheet(f"color:{clr};background:transparent;border:none;")
            ml.addWidget(num)
            sg.addWidget(mini)
        img_v.addLayout(sg)
        body.addWidget(img_card, stretch=5)

        # Right
        right = QVBoxLayout(); right.setSpacing(10)

        # Component table
        tc, tv = _make_card("Thống kê linh kiện")
        tbl = QTableWidget(len(rec["components"]), 3)
        tbl.setHorizontalHeaderLabels(["Linh kiện","Mẫu","Phát hiện"])
        tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tbl.setSelectionMode(QAbstractItemView.NoSelection)
        tbl.verticalHeader().setVisible(False); tbl.setShowGrid(False)
        tbl.setAlternatingRowColors(True)
        tbl.setStyleSheet(_TBL)
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        tbl.verticalHeader().setDefaultSectionSize(30)
        for i, (nm, tot, det) in enumerate(rec["components"]):
            for j, v2 in enumerate([nm, str(tot), str(det)]):
                it = QTableWidgetItem(v2); it.setTextAlignment(Qt.AlignCenter)
                if j == 2 and det < tot:
                    it.setForeground(QColor("#DC2626"))
                    font = it.font()
                    font.setPointSize(10)
                    font.setBold(True)
                    it.setFont(font)
                tbl.setItem(i, j, it)
        tv.addWidget(tbl)
        right.addWidget(tc, stretch=3)

        # Defect list
        dc, dv = _make_card("Danh sách lỗi")
        n_def = len(rec["defects"])
        tag = QLabel(f"{n_def} lỗi" if n_def else "Không có lỗi")
        tag.setStyleSheet(
            f"QLabel{{background:{'#FEF2F2' if n_def else '#F0FDF4'};"
            f"color:{'#DC2626' if n_def else '#16A34A'};"
            f"border:1px solid {'#FECACA' if n_def else '#BBF7D0'};"
            f"border-radius:6px;font-size:11px;font-weight:700;padding:2px 8px;}}")
        for dfct in rec["defects"]:
            rw = QHBoxLayout(); rw.setSpacing(8)
            dot = QLabel("●"); dot.setFixedWidth(16)
            dot.setStyleSheet("color:#EF4444;font-size:13px;background:transparent;border:none;")
            txt = QLabel(dfct)
            txt.setStyleSheet("color:#1E293B;font-size:13px;background:transparent;border:none;")
            txt.setWordWrap(True)
            rw.addWidget(dot); rw.addWidget(txt)
            dv.addLayout(rw)
        if not rec["defects"]:
            ok_l = QLabel("Tất cả linh kiện đạt chuẩn")
            ok_l.setStyleSheet("color:#16A34A;font-size:13px;font-weight:600;background:transparent;border:none;")
            dv.addWidget(ok_l)
        dv.addStretch()
        right.addWidget(dc, stretch=2)

        body.addLayout(right, stretch=4)
        root.addLayout(body)

        close_btn = QPushButton("✕  Đóng")
        close_btn.setStyleSheet(_BTN_GRAY); close_btn.setFixedWidth(110)
        close_btn.clicked.connect(self.close)
        root.addWidget(close_btn, alignment=Qt.AlignRight)


# ── History page ───────────────────────────────────────────────────────────────
class HistoryPage(QWidget):
    def __init__(self):
        super().__init__()
        self.storage = StorageService()
        self.config_manager = ConfigManager()
        self.filtered_data = []
        
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(10)

        # ── Filter bar ────────────────────────────────────────────────────
        fb = QFrame(); fb.setStyleSheet(_CARD)
        apply_shadow(fb, blur_radius=12, y_offset=3, alpha=18)
        fb.setFixedHeight(56)
        fl = QHBoxLayout(fb); fl.setContentsMargins(14, 0, 14, 0); fl.setSpacing(8)
        fl.setAlignment(Qt.AlignVCenter)

        def _lbl(t):
            w = QLabel(t)
            w.setStyleSheet(_LBL)
            w.setFixedHeight(32)
            w.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            return w

        def _combo(items):
            w = QComboBox()
            w.addItems(items)
            w.setFixedHeight(32)
            w.setStyleSheet(_COMBO)
            return w

        fl.addWidget(_lbl("Từ:"))
        self.d_from = QDateEdit(QDate(2026, 5, 18))
        self.d_from.setCalendarPopup(True); self.d_from.setFixedHeight(32)
        self.d_from.setStyleSheet(_DATE); fl.addWidget(self.d_from)

        fl.addWidget(_lbl("đến"))
        self.d_to = QDateEdit(QDate.currentDate())
        self.d_to.setCalendarPopup(True); self.d_to.setFixedHeight(32)
        self.d_to.setStyleSheet(_DATE); fl.addWidget(self.d_to)

        fl.addWidget(_lbl("Board:"))
        self.cbo_board = QComboBox()
        self.cbo_board.setFixedHeight(32)
        self.cbo_board.setStyleSheet(_COMBO)
        fl.addWidget(self.cbo_board)
        self._update_board_combo()

        fl.addWidget(_lbl("Trạng thái:"))
        self.cbo_status = _combo(["Tất cả","OK","DEFECT"])
        fl.addWidget(self.cbo_status)

        b_filter = QPushButton("Lọc"); b_filter.setStyleSheet(_BTN_BLUE); b_filter.setFixedHeight(32)
        fl.addWidget(b_filter)
        b_export = QPushButton("CSV"); b_export.setStyleSheet(_BTN_GRAY); b_export.setFixedHeight(32)
        fl.addWidget(b_export)
        fl.addStretch()
        b_clear = QPushButton("Xóa lọc"); b_clear.setStyleSheet(_BTN_RED); b_clear.setFixedHeight(32)
        fl.addWidget(b_clear)
        root.addWidget(fb)

        # ── Body ──────────────────────────────────────────────────────────
        body = QHBoxLayout(); body.setSpacing(10)

        # ── Left column: stat cards + chart ───────────────────────────────
        self.left_layout = QVBoxLayout(); self.left_layout.setSpacing(10)
        
        self.stats_widget = QWidget()
        self.stats_layout = QVBoxLayout(self.stats_widget)
        self.stats_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.addWidget(self.stats_widget)
        
        self.chart_widget = QWidget()
        self.chart_layout = QVBoxLayout(self.chart_widget)
        self.chart_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.addWidget(self.chart_widget, stretch=1)
        
        body.addLayout(self.left_layout, stretch=3)

        # ── Right column: log table ────────────────────────────────────────
        tc, self.tv = _make_card("Nhật ký phát hiện")
        self.tbl = QTableWidget()
        
        hdrs = ["Ngày","Giờ","Loại board","Tổng","Phát hiện","Lỗi","Trạng thái",""]
        self.tbl.setColumnCount(len(hdrs))
        self.tbl.setHorizontalHeaderLabels(hdrs)
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setShowGrid(False)
        self.tbl.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tbl.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tbl.setStyleSheet(_TBL + """
            QScrollBar:vertical { background:transparent; width:8px; margin:0; }
            QScrollBar::handle:vertical { background:#CBD5E1; min-height:30px; border-radius:4px; }
            QScrollBar::handle:vertical:hover { background:#94A3B8; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background:none; }
        """)
        h = self.tbl.horizontalHeader()
        for i in range(7): h.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        h.setSectionResizeMode(7, QHeaderView.Fixed)
        self.tbl.setColumnWidth(7, 100)
        self.tbl.verticalHeader().setDefaultSectionSize(38)
        
        self.tv.addWidget(self.tbl)
        body.addWidget(tc, stretch=7)
        root.addLayout(body)
        
        # Connect signals
        b_filter.clicked.connect(self._apply_filter)
        b_clear.clicked.connect(self._clear_filter)
        b_export.clicked.connect(self._export_csv)
        
        # Initial render
        self._apply_filter()

    def _update_board_combo(self):
        self.config_manager.load()
        boards = self.config_manager.get("boards", [])
        board_ids = ["Tất cả"] + [b.get("board_id") for b in boards if b.get("board_id")]
        
        current_text = self.cbo_board.currentText()
        self.cbo_board.clear()
        self.cbo_board.addItems(board_ids)
        idx = self.cbo_board.findText(current_text)
        if idx >= 0:
            self.cbo_board.setCurrentIndex(idx)

    def _apply_filter(self):
        self._update_board_combo()
        date_start = self.d_from.date().toString("yyyy-MM-dd")
        date_end = self.d_to.date().toString("yyyy-MM-dd")
        board = self.cbo_board.currentText()
        status = self.cbo_status.currentText()
        
        self.filtered_data = []
        records = self.storage.get_records()
        for row in records:
            if not (date_start <= row["date"] <= date_end):
                continue
            if board != "Tất cả" and row["board"] != board:
                continue
            if status != "Tất cả" and row["status"] != status:
                continue
            self.filtered_data.append(row)
            
        self._render_stats()
        self._render_chart()
        self._render_table()

    def _clear_filter(self):
        self.d_from.setDate(QDate(2026, 5, 18))
        self.d_to.setDate(QDate.currentDate())
        self.cbo_board.setCurrentIndex(0)
        self.cbo_status.setCurrentIndex(0)
        self._apply_filter()

    def _export_csv(self):
        if not self.filtered_data:
            QMessageBox.warning(self, "Trống", "Không có dữ liệu để xuất!")
            return
            
        path, _ = QFileDialog.getSaveFileName(self, "Lưu file CSV", "history_export.csv", "CSV Files (*.csv)")
        if not path:
            return
            
        try:
            with open(path, mode='w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Ngày", "Giờ", "Loại board", "Tổng", "Phát hiện", "Lỗi", "Trạng thái", "Danh sách lỗi"])
                for row in self.filtered_data:
                    defects_str = "; ".join(row["defects"])
                    writer.writerow([
                        row["date"], row["time"], row["board"],
                        row["total"], row["detected"], row["defect"],
                        row["status"], defects_str
                    ])
            QMessageBox.information(self, "Thành công", f"Đã xuất dữ liệu ra file:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu file: {str(e)}")

    def _render_stats(self):
        clear_layout(self.stats_layout)
        total = len(self.filtered_data)
        ok_cnt = sum(1 for r in self.filtered_data if r["status"] == "OK")
        df_cnt = total - ok_cnt

        for title, val, bg, fg in [
            ("TỔNG KIỂM TRA", str(total),  "#EFF6FF", "#2563EB"),
            ("ĐẠT CHUẨN",     str(ok_cnt), "#F0FDF4", "#16A34A"),
            ("CÓ LỖI",        str(df_cnt), "#FFF1F2", "#DC2626"),
        ]:
            c = QFrame()
            c.setStyleSheet(f"QFrame{{background:{bg};border:1px solid {fg}40;border-radius:12px;}}")
            c.setFixedHeight(66)
            apply_shadow(c, blur_radius=12, alpha=16)
            cl = QHBoxLayout(c); cl.setContentsMargins(14, 0, 14, 0)
            tl = QLabel(title)
            tl.setStyleSheet(f"color:{fg};font-size:12px;font-weight:700;background:transparent;border:none;letter-spacing:1px;")
            vl = QLabel(val)
            vl.setStyleSheet(f"color:{fg};font-size:28px;font-weight:800;background:transparent;border:none;")
            cl.addWidget(tl); cl.addStretch(); cl.addWidget(vl)
            self.stats_layout.addWidget(c)

    def _render_chart(self):
        clear_layout(self.chart_layout)
        bc, bv = _make_card("Tỷ lệ đạt chuẩn")
        
        # Load boards dynamically
        self.config_manager.load()
        boards = self.config_manager.get("boards", [])
        configured_board_ids = [b.get("board_id") for b in boards if b.get("board_id")]
        
        # Also include any boards present in filtered_data to ensure historical data is shown
        historical_board_ids = list(set(r["board"] for r in self.filtered_data if r.get("board")))
        
        # Combine boards dynamically preserving config order first
        board_ids = []
        for bid in configured_board_ids:
            if bid not in board_ids:
                board_ids.append(bid)
        for bid in historical_board_ids:
            if bid not in board_ids:
                board_ids.append(bid)
                
        colors_palette = ["#3B82F6", "#8B5CF6", "#10B981", "#F59E0B", "#EF4444", "#EC4899", "#06B6D4", "#6366F1"]
        
        for idx, brd in enumerate(board_ids):
            clr = colors_palette[idx % len(colors_palette)]
            rows = [r for r in self.filtered_data if r["board"] == brd]
            ok_b = sum(1 for r in rows if r["status"] == "OK")
            n    = len(rows)
            pct  = int(ok_b / n * 100) if n else 0

            br = QHBoxLayout(); br.setSpacing(8)
            bl = QLabel(brd); bl.setFixedWidth(72)
            bl.setStyleSheet(_LBL + "font-size:12px;")

            track = QFrame(); track.setFixedHeight(10)
            track.setStyleSheet("QFrame{background:#F1F5F9;border-radius:5px;border:none;}")
            tl2 = QHBoxLayout(track); tl2.setContentsMargins(0,0,0,0)
            fill = QFrame(); fill.setFixedHeight(10)
            fill.setStyleSheet(f"QFrame{{background:{clr};border-radius:5px;border:none;}}")
            fill.setFixedWidth(max(10, pct * 2))
            tl2.addWidget(fill); tl2.addStretch()

            pl = QLabel(f"{pct}%"); pl.setFixedWidth(38)
            pl.setStyleSheet(f"color:{clr};font-size:12px;font-weight:700;background:transparent;border:none;")
            br.addWidget(bl); br.addWidget(track, stretch=1); br.addWidget(pl)
            bv.addLayout(br)

        bv.addStretch()
        self.chart_layout.addWidget(bc)

    def _render_table(self):
        self.tbl.setRowCount(len(self.filtered_data))
        for ri, rec in enumerate(self.filtered_data):
            for ci, val in enumerate([rec["date"],rec["time"],rec["board"],
                                       str(rec["total"]),str(rec["detected"]),
                                       str(rec["defect"]),rec["status"]]):
                it = QTableWidgetItem(val); it.setTextAlignment(Qt.AlignCenter)
                if ci == 6:
                    ok = val == "OK"
                    it.setForeground(QColor("#16A34A" if ok else "#DC2626"))
                    font = it.font()
                    font.setPointSize(10)
                    font.setBold(True)
                    it.setFont(font)
                self.tbl.setItem(ri, ci, it)

            btn = QPushButton("Chi tiết"); btn.setStyleSheet(_BTN_INFO)
            btn.setFixedHeight(28)
            btn.clicked.connect(lambda _, r=rec: DetectDetailDialog(r, self).exec())
            self.tbl.setCellWidget(ri, 7, btn)
