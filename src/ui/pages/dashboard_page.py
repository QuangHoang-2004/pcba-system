import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap

from src.ui.components.camera_widget import CameraWidget
from src.ui.components.control_panel import ControlPanel
from src.ui.components.component_table import ComponentTable
from src.ui.components.status_card import StatusCard
from src.ui.utils.style_utils import apply_shadow
from src.ui.utils.aspect_ratio import AspectRatioContainer
from src.services.local_storage import StorageService
from src.services.config_manager import ConfigManager
from src.hardware.camera_worker import CameraWorker
from src.utils.colors import get_label_color


def load_labels(labels_path):
    import os
    if not os.path.exists(labels_path):
        return ["capacitor", "diode", "resistor", "transistor"]
    try:
        with open(labels_path, "r", encoding="utf-8") as f:
            content = f.read()
            local_vars = {}
            exec(content, {}, local_vars)
            return local_vars.get("class_names", ["capacitor", "diode", "resistor", "transistor"])
    except Exception as e:
        print(f"Error loading labels: {e}")
        return ["capacitor", "diode", "resistor", "transistor"]

class ResultPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid rgba(0, 0, 0, 0.05);
                border-radius: 16px;
            }
        """)
        apply_shadow(self, blur_radius=20, y_offset=6, alpha=30)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = QLabel("Kết quả kiểm tra")
        title.setStyleSheet("color: #1E293B; font-weight: bold; font-size: 15px; border: none; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        
        self.status = StatusCard("BOARD STATUS", "N/A", type="good")
        
        layout.addWidget(title)
        layout.addWidget(self.status)

    def update_data(self, status):
        self.status.update_value(status)
        self.status.update_type("good" if status == "OK" else "defect")

class RecentDetectPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid rgba(0, 0, 0, 0.05);
                border-radius: 16px;
            }
        """)
        apply_shadow(self, blur_radius=20, y_offset=6, alpha=30)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = QLabel("Ảnh lỗi gần nhất")
        title.setStyleSheet("color: #1E293B; font-weight: bold; font-size: 15px; border: none; background: transparent;")
        title.setAlignment(Qt.AlignCenter)

        self.image_placeholder = QLabel("[ IMAGE CROP ]")
        self.image_placeholder.setAlignment(Qt.AlignCenter)
        self.image_placeholder.setMinimumSize(200, 200)
        self.image_placeholder.setStyleSheet("""
            QLabel {
                background-color: #F1F5F9;
                border: 1px dashed rgba(0, 0, 0, 0.15);
                border-radius: 8px;
                color: #64748B;
                font-weight: bold;
                letter-spacing: 1px;
            }
        """)

        self.time_label = QLabel("N/A")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("color: #64748B; font-size: 12px; border: none; background: transparent;")

        self.image_container = AspectRatioContainer(self.image_placeholder, ratio=1.0, margin=0)

        layout.addWidget(title, stretch=0)
        layout.addWidget(self.image_container, stretch=1)
        layout.addWidget(self.time_label, stretch=0)

    def update_data(self, time_str, image_path=None):
        self.time_label.setText(time_str)
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                self.image_placeholder.setPixmap(pixmap)
                self.image_placeholder.setScaledContents(True)
            else:
                self.image_placeholder.setPixmap(QPixmap())
                self.image_placeholder.setText("[ IMAGE CROP ]")
                self.image_placeholder.setScaledContents(False)
        else:
            self.image_placeholder.setPixmap(QPixmap())
            self.image_placeholder.setText("[ IMAGE CROP ]")
            self.image_placeholder.setScaledContents(False)

class DashboardPage(QWidget):
    detection_state_changed = Signal(bool)

    def __init__(self, serial_worker=None):
        super().__init__()
        self.setStyleSheet("background: transparent;")
        self.config_manager = ConfigManager()
        self.storage = StorageService()
        self.is_running = False
        
        self.serial_worker = serial_worker
        self.serial_connected = False
        if self.serial_worker:
            self.serial_worker.board_detected.connect(self._on_serial_board_detected)
            self.serial_worker.connection_status.connect(self._on_serial_status_changed)
            
        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(self._simulate_detection)
        
        # Load Labels and ONNX Inference Engine
        labels_path = "models/raspberry/labels.txt"
        self.labels = load_labels(labels_path)
        
        from src.core.engines.onnx_engine import ONNXEngine
        model_path = "models/raspberry/yolo26n.onnx"
        if os.path.exists(model_path):
            try:
                self.onnx_engine = ONNXEngine(model_path)
                print(f"[DashboardPage] Loaded ONNX Engine with model: {model_path}")
            except Exception as e:
                self.onnx_engine = None
                print(f"[DashboardPage] Failed to load ONNX Engine: {e}")
        else:
            self.onnx_engine = None
            print(f"[DashboardPage] Model file not found at: {model_path}")

        center_layout = QHBoxLayout(self)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(8)

        # --- LEFT PANEL ---
        left_layout = QVBoxLayout()
        left_layout.setSpacing(8)

        self.camera_widget = CameraWidget()
        
        # Initialize and start Camera Worker Thread
        self.camera_worker = CameraWorker(self)
        self.camera_worker.frame_ready.connect(self.camera_widget.update_frame)
        self.camera_worker.start()
        
        self.camera_container = AspectRatioContainer(
            self.camera_widget,
            ratio=1.0
        )
        left_layout.addWidget(self.camera_container, stretch=5)

        self.control_panel = ControlPanel()
        self.control_panel.btn_start.clicked.connect(self._start_detection)
        self.control_panel.btn_stop.clicked.connect(self._stop_detection)
        left_layout.addWidget(self.control_panel, stretch=1)

        # --- RIGHT PANEL ---
        right_layout = QVBoxLayout()
        right_layout.setSpacing(8)

        top_right_layout = QHBoxLayout()
        top_right_layout.setSpacing(8)

        self.recent_detect = RecentDetectPanel()
        self.table_widget = ComponentTable()

        top_right_layout.addWidget(self.recent_detect, stretch=5)
        top_right_layout.addWidget(self.table_widget, stretch=5)

        right_layout.addLayout(top_right_layout, stretch=5)

        bottom_right_layout = QHBoxLayout()
        bottom_right_layout.setSpacing(8)

        self.result_panel = ResultPanel()
        bottom_right_layout.addWidget(self.result_panel, stretch=2)

        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(8)
        self.card_good = StatusCard("TOTAL GOOD", 0, type="good")
        self.card_defect = StatusCard("TOTAL DEFECT", 0, type="defect")
        stats_layout.addWidget(self.card_good)
        stats_layout.addWidget(self.card_defect)

        stats_container = QWidget()
        stats_container.setLayout(stats_layout)
        bottom_right_layout.addWidget(stats_container, stretch=1)

        right_layout.addLayout(bottom_right_layout, stretch=2)

        center_layout.addLayout(left_layout, stretch=5)
        center_layout.addLayout(right_layout, stretch=6)

        self.refresh_dashboard()

    def _on_serial_status_changed(self, connected, port_name):
        self.serial_connected = connected

    def _on_serial_board_detected(self):
        if not self.is_running:
            return
        print("[DashboardPage] Board trigger received from ESP32. Running detection...")
        is_ok = self._execute_detection()
        if self.serial_worker:
            self.serial_worker.send_cmd("RESULT_OK\n" if is_ok else "RESULT_NG\n")

    def _start_detection(self):
        self.is_running = True
        self.control_panel.set_running_state(True)
        self.detection_state_changed.emit(True)
        
        # Load active profile and default confidence
        self.config_manager.load()
        active_board_id = self.config_manager.get("active_board_id", "")
        boards = self.config_manager.get("boards", [])
        profile = next((b for b in boards if b.get("board_id") == active_board_id), None)
        default_conf = self.config_manager.get("default_confidence", 0.5)
        
        # Configure CameraWorker for real-time inference
        if self.onnx_engine is not None and profile is not None:
            self.camera_worker.set_detection_params(self.onnx_engine, self.labels, profile, default_conf)
            self.camera_worker.set_detect_enabled(True)
            self.camera_widget.model_label.setText("YOLO: RUNNING")
            self.camera_widget.model_label.setStyleSheet("""
                color: #4ADE80;
                background-color: rgba(74, 222, 128, 0.1);
                padding: 4px 10px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            """)
        
        if self.serial_connected and self.serial_worker:
            self.serial_worker.send_cmd("START\n")
            print("[DashboardPage] Sent START to ESP32. Waiting for hardware triggers...")
        else:
            self.sim_timer.start(5000)  # Simulate detection every 5 seconds
            print("[DashboardPage] ESP32 disconnected. Falling back to simulation mode (5s interval).")

    def _stop_detection(self):
        self.is_running = False
        self.control_panel.set_running_state(False)
        self.detection_state_changed.emit(False)
        
        self.camera_worker.set_detect_enabled(False)
        self.camera_widget.model_label.setText("YOLO: READY")
        self.camera_widget.model_label.setStyleSheet("""
            color: #38BDF8;
            background-color: rgba(56, 189, 248, 0.1);
            padding: 4px 10px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 12px;
        """)
        
        if self.serial_connected and self.serial_worker:
            self.serial_worker.send_cmd("STOP\n")
            print("[DashboardPage] Sent STOP to ESP32.")
        
        self.sim_timer.stop()

    def _simulate_detection(self):
        self._execute_detection()

    def _execute_detection(self) -> bool:
        from datetime import datetime
        import cv2
        self.config_manager.load()
        active_board_id = self.config_manager.get("active_board_id", "")
        boards = self.config_manager.get("boards", [])
        profile = next((b for b in boards if b.get("board_id") == active_board_id), None)
        if not profile:
            return True

        components = []
        defects = []
        status = "OK"
        total = 0
        detected = 0

        # Get actual frame from camera worker
        cv_img = self.camera_worker.get_last_frame()

        if self.onnx_engine is None:
            print("[DashboardPage] ONNX Engine is not loaded. Cannot run detection.")
            return False

        if cv_img is None:
            print("[DashboardPage] No frame available from camera. Cannot run detection.")
            return False

        # 1. Letterbox to 640x640 with padding (BGR theme color (42, 23, 15)) to prevent distortion
        h, w = cv_img.shape[:2]
        r = min(640 / h, 640 / w)
        new_w, new_h = int(w * r), int(h * r)
        if (w, h) != (new_w, new_h):
            img_resized = cv2.resize(cv_img, (new_w, new_h))
        else:
            img_resized = cv_img.copy()
        
        top = (640 - new_h) // 2
        bottom = 640 - new_h - top
        left = (640 - new_w) // 2
        right = 640 - new_w - left
        cv_img_padded = cv2.copyMakeBorder(img_resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(42, 23, 15))
        
        # 2. Run actual inference using the model on the padded image
        detections = self.onnx_engine.infer(cv_img_padded)
        
        # 3. Match detections to board profile requirements
        for comp in profile.get("components", []):
            name = comp.get("name", "component").lower()
            req = comp.get("required_count", 1)
            min_conf = comp.get("min_confidence", self.config_manager.get("default_confidence", 0.5))
            
            try:
                cls_idx = self.labels.index(name)
            except ValueError:
                cls_idx = -1
            
            det = 0
            if cls_idx != -1:
                for det_box in detections:
                    x1, y1, x2, y2, conf, cls_id = det_box
                    if cls_id == cls_idx and conf >= min_conf:
                        det += 1
            
            total += req
            detected += det
            components.append([name, req, det])
            
            if det < req:
                status = "DEFECT"
                defects.append(f"Thiếu {name} ({req - det} chiếc)")
            elif det > req:
                status = "DEFECT"
                defects.append(f"Dư {name} ({det - req} chiếc)")
        
        # 4. Draw bounding boxes on the 640x640 padded image
        for det_box in detections:
            x1, y1, x2, y2, conf, cls_id = det_box
            if 0 <= cls_id < len(self.labels):
                name = self.labels[cls_id]
            else:
                name = "unknown"
            
            # Find matching component configuration to use correct confidence threshold
            comp_cfg = next((c for c in profile.get("components", []) if c.get("name", "").lower() == name.lower()), None)
            min_conf = comp_cfg.get("min_confidence", self.config_manager.get("default_confidence", 0.5)) if comp_cfg else self.config_manager.get("default_confidence", 0.5)
            
            if conf >= min_conf:
                color = get_label_color(name)
                # Draw bounding box and text label in dynamic component color
                cv2.rectangle(cv_img_padded, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                label = f"{name} {conf:.2f}"
                cv2.putText(cv_img_padded, label, (int(x1), int(y1) - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1, cv2.LINE_AA)
        
        defect_count = sum(abs(req - det) for name, req, det in components)
        record = {
            "board": active_board_id,
            "status": status,
            "total": total,
            "detected": detected,
            "defect": defect_count,
            "defects": defects,
            "components": components
        }
        rec_id = self.storage.save_record(record)
        
        filename = f"{rec_id}.jpg"
        self.storage.save_image(cv_img_padded, filename)

        self.refresh_dashboard()
        return status == "OK"

    def refresh_dashboard(self):
        self.config_manager.load()  # Always get latest config from disk
        active_board_id = self.config_manager.get("active_board_id", "")
        
        # Filter SQLite data for the active board
        board_history = self.storage.get_records(active_board_id)
        
        # Update Stats
        total_ok = sum(1 for r in board_history if r["status"] == "OK")
        total_defect = sum(1 for r in board_history if r["status"] == "DEFECT")
        self.card_good.update_value(total_ok)
        self.card_defect.update_value(total_defect)
        
        # Update latest record overall
        latest_record = board_history[0] if board_history else None
        
        # Update Component Table
        self.table_widget.update_data(latest_record)
        
        # Update Result Panel
        if latest_record:
            self.result_panel.update_data(latest_record["status"])
        else:
            self.result_panel.update_data("N/A")
            
        # Update Recent Defect Image
        latest_defect = next((r for r in board_history if r["status"] == "DEFECT"), None)
        if latest_defect:
            img_path = os.path.join(self.storage.capture_dir, f"{latest_defect['id']}.jpg")
            self.recent_detect.update_data(f"{latest_defect['date']} {latest_defect['time']}", img_path)
        else:
            self.recent_detect.update_data("Chưa có lỗi nào", None)
