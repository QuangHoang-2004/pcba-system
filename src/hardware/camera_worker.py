import time
import cv2
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage
from src.hardware.edge_camera import EdgeCamera
from src.utils.colors import get_label_color


class CameraWorker(QThread):
    frame_ready = Signal(QImage)
    fps_updated = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.camera = EdgeCamera()
        self.last_frame = None
        self.target_fps = 30  # Default internal frame rate
        
        # Real-time YOLO detection params
        self.onnx_engine = None
        self.labels = []
        self.active_profile = None
        self.default_confidence = 0.5
        self.detect_enabled = False

    def set_detection_params(self, onnx_engine, labels, active_profile, default_confidence):
        self.onnx_engine = onnx_engine
        self.labels = labels
        self.active_profile = active_profile
        self.default_confidence = default_confidence

    def set_detect_enabled(self, enabled: bool):
        self.detect_enabled = enabled

    def run(self):
        self.running = True
        if not self.camera.open():
            print("[CameraWorker] Failed to open camera device.")
            self.running = False
            return

        # Determine target FPS dynamically from device
        if not self.camera.is_simulated and self.camera.cap is not None:
            device_fps = self.camera.cap.get(cv2.CAP_PROP_FPS)
            if device_fps > 0:
                self.target_fps = device_fps
                print(f"[CameraWorker] Detected hardware FPS: {self.target_fps}")
            else:
                self.target_fps = None
                print("[CameraWorker] Could not detect hardware FPS. Relying on blocking read.")

        frame_count = 0
        fps_timer = time.time()
        
        while self.running:
            loop_start = time.time()
            success, frame = self.camera.read_frame()
            if success and frame is not None:
                # Save last frame (OpenCV BGR numpy array) for inspection captures
                self.last_frame = frame.copy()
                
                # 1. Always Letterbox to 640x640 with padding (BGR theme color (42, 23, 15)) to prevent distortion
                h, w = frame.shape[:2]
                r = min(640 / h, 640 / w)
                new_w, new_h = int(w * r), int(h * r)
                if (w, h) != (new_w, new_h):
                    img_resized = cv2.resize(frame, (new_w, new_h))
                else:
                    img_resized = frame.copy()
                
                top = (640 - new_h) // 2
                bottom = 640 - new_h - top
                left = (640 - new_w) // 2
                right = 640 - new_w - left
                frame_padded = cv2.copyMakeBorder(img_resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(42, 23, 15))
                
                # Check if real-time detection is enabled and engine is available
                if self.detect_enabled and self.onnx_engine is not None and self.active_profile is not None:
                    # 2. Run actual inference using the model on the padded image
                    detections = self.onnx_engine.infer(frame_padded)
                    
                    # 3. Draw bounding boxes on the 640x640 padded image
                    for det_box in detections:
                        x1, y1, x2, y2, conf, cls_id = det_box
                        if 0 <= cls_id < len(self.labels):
                            name = self.labels[cls_id]
                        else:
                            name = "unknown"
                        
                        comp_cfg = next((c for c in self.active_profile.get("components", []) if c.get("name", "").lower() == name.lower()), None)
                        min_conf = comp_cfg.get("min_confidence", self.default_confidence) if comp_cfg else self.default_confidence
                        
                        if conf >= min_conf:
                            color = get_label_color(name)
                            cv2.rectangle(frame_padded, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                            label = f"{name} {conf:.2f}"
                            cv2.putText(frame_padded, label, (int(x1), int(y1) - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1, cv2.LINE_AA)
                    
                display_frame = frame_padded
                
                # Convert BGR (OpenCV format) to RGB
                rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_frame.shape
                bytes_per_line = ch * w
                
                # Create QImage pointing to rgb_frame's memory and copy it to prevent issues
                q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.frame_ready.emit(q_img.copy())
                
                # Calculate actual FPS
                frame_count += 1
                now = time.time()
                elapsed = now - fps_timer
                if elapsed >= 1.0:
                    actual_fps = frame_count / elapsed
                    self.fps_updated.emit(f"FPS: {int(actual_fps)}")
                    frame_count = 0
                    fps_timer = now
            
            # Control frame rate dynamically depending on camera type
            if self.camera.is_simulated:
                # Simulated camera runs at 30 FPS to prevent high CPU usage
                elapsed_loop = time.time() - loop_start
                delay = max(0.001, (1.0 / 30.0) - elapsed_loop)
                time.sleep(delay)
            else:
                if self.target_fps and self.target_fps > 0:
                    # Respect native hardware FPS if reported
                    elapsed_loop = time.time() - loop_start
                    delay = max(0.001, (1.0 / self.target_fps) - elapsed_loop)
                    time.sleep(delay)
                else:
                    # Rely on cv2.VideoCapture.read() blocking, yield CPU
                    time.sleep(0.001)

        self.camera.release()

    def get_last_frame(self):
        """Returns the last successfully read frame in OpenCV BGR format."""
        return self.last_frame

    def stop(self):
        self.running = False
        self.wait()
