# Edge Camera interface (GStreamer/V4L2/USB Webcam)
import cv2
import numpy as np
import time
import math

class EdgeCamera:
    def __init__(self):
        from src.services.config_manager import ConfigManager
        self.config_manager = ConfigManager()
        self.cap = None
        self.is_simulated = False
        self.sim_start_time = time.time()
        
        # Load configuration
        self.load_config()

    def load_config(self):
        cam_cfg = self.config_manager.get("camera", {})
        self.device_id = cam_cfg.get("device_id", 0)
        self.width = cam_cfg.get("width", 640)
        self.height = cam_cfg.get("height", 480)
        self.flip_mode = cam_cfg.get("flip", "none")
        self.rotate_angle = cam_cfg.get("rotate", 0)

    def open(self):
        self.load_config()  # Reload just in case config changed
        self.is_simulated = False
        
        # Attempt to open real camera
        try:
            # We can force DSHOW on Windows for faster USB camera initialization if needed
            self.cap = cv2.VideoCapture(self.device_id)
            if self.cap and self.cap.isOpened():
                # Set width and height on camera
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                print(f"[EdgeCamera] Successfully opened USB camera device {self.device_id}")
                return True
        except Exception as e:
            print(f"[EdgeCamera] Error opening physical camera: {e}")
            
        print("[EdgeCamera] Physical camera not available. Falling back to Simulated mode.")
        self.is_simulated = True
        self.sim_start_time = time.time()
        return True

    def read_frame(self):
        if self.is_simulated:
            return True, self._generate_simulated_frame()
            
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Apply transformations
                frame = self._apply_transforms(frame)
                return True, frame
            else:
                # If reading failed, generate simulated frame as fallback
                return True, self._generate_simulated_frame()
        return False, None

    def _apply_transforms(self, frame):
        # 1. Resize to target width/height if needed
        h, w = frame.shape[:2]
        if w != self.width or h != self.height:
            frame = cv2.resize(frame, (self.width, self.height))

        # 2. Flip
        if self.flip_mode == "horizontal":
            frame = cv2.flip(frame, 1)
        elif self.flip_mode == "vertical":
            frame = cv2.flip(frame, 0)
        elif self.flip_mode == "both":
            frame = cv2.flip(frame, -1)

        # 3. Rotate
        if self.rotate_angle == 90:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif self.rotate_angle == 180:
            frame = cv2.rotate(frame, cv2.ROTATE_180)
        elif self.rotate_angle == 270:
            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

        return frame

    def _generate_simulated_frame(self):
        # Create a beautiful animated mock frame representing PCBA board
        # Black background
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Draw techy grid background
        grid_size = 40
        for y in range(0, self.height, grid_size):
            cv2.line(frame, (0, y), (self.width, y), (30, 30, 30), 1)
        for x in range(0, self.width, grid_size):
            cv2.line(frame, (x, 0), (x, self.height), (30, 30, 30), 1)

        # Draw a PCBA Board Mockup inside
        pcb_w, pcb_h = int(self.width * 0.7), int(self.height * 0.6)
        pcb_x = (self.width - pcb_w) // 2
        pcb_y = (self.height - pcb_h) // 2
        cv2.rectangle(frame, (pcb_x, pcb_y), (pcb_x + pcb_w, pcb_y + pcb_h), (20, 80, 20), -1)  # Dark green PCB
        cv2.rectangle(frame, (pcb_x, pcb_y), (pcb_x + pcb_w, pcb_y + pcb_h), (40, 160, 40), 2)  # Light green border
        
        # Draw gold pins/pads on edges
        for offset in range(20, pcb_w - 20, 30):
            cv2.circle(frame, (pcb_x + offset, pcb_y + 8), 4, (0, 215, 255), -1)  # Gold circle
            cv2.circle(frame, (pcb_x + offset, pcb_y + pcb_h - 8), 4, (0, 215, 255), -1)

        # Draw components (microcontrollers, capacitors)
        # Main MCU
        mcu_w, mcu_h = 80, 80
        mcu_x = pcb_x + (pcb_w - mcu_w) // 2
        mcu_y = pcb_y + (pcb_h - mcu_h) // 2
        cv2.rectangle(frame, (mcu_x, mcu_y), (mcu_x + mcu_w, mcu_y + mcu_h), (40, 40, 40), -1)  # Dark gray MCU
        cv2.rectangle(frame, (mcu_x, mcu_y), (mcu_x + mcu_w, mcu_y + mcu_h), (120, 120, 120), 2)
        cv2.putText(frame, "MCU", (mcu_x + 15, mcu_y + 48), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Other chips
        cv2.rectangle(frame, (pcb_x + 40, pcb_y + 40), (pcb_x + 95, pcb_y + 70), (50, 50, 50), -1)
        cv2.putText(frame, "CHIP A", (pcb_x + 45, pcb_y + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        cv2.rectangle(frame, (pcb_x + pcb_w - 95, pcb_y + pcb_h - 70), (pcb_x + pcb_w - 40, pcb_y + pcb_h - 40), (50, 50, 50), -1)
        cv2.putText(frame, "CHIP B", (pcb_x + pcb_w - 90, pcb_y + pcb_h - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        # Moving scanning line (laser scan simulation)
        t = time.time() - self.sim_start_time
        scan_y = int(pcb_y + (math.sin(t * 2.5) * 0.5 + 0.5) * pcb_h)
        # Red laser line
        cv2.line(frame, (pcb_x - 10, scan_y), (pcb_x + pcb_w + 10, scan_y), (0, 0, 255), 2)
        # Glow effect
        cv2.line(frame, (pcb_x - 10, scan_y - 1), (pcb_x + pcb_w + 10, scan_y - 1), (100, 100, 255), 1)
        cv2.line(frame, (pcb_x - 10, scan_y + 1), (pcb_x + pcb_w + 10, scan_y + 1), (100, 100, 255), 1)

        # Draw HUD overlays on frame
        cv2.putText(frame, "USB WEBCAM [SIMULATED]", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Display current local timestamp
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, current_time, (15, self.height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        # Apply flip and rotate to the simulated frame as well to match user settings
        frame = self._apply_transforms(frame)
        return frame

    def release(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
            print("[EdgeCamera] Released physical camera.")
        self.cap = None
        self.is_simulated = False
