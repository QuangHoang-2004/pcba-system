import cv2
import numpy as np
from .base_engine import BaseEngine

class ONNXEngine(BaseEngine):
    """
    Inference Engine using ONNX Runtime.
    Optimized for Raspberry Pi and generic CPU execution.
    """
    def __init__(self, model_path: str):
        try:
            import onnxruntime
            self.ort = onnxruntime
        except ImportError:
            raise ImportError("Không tìm thấy onnxruntime. Hãy cài đặt gói onnxruntime.")
            
        super().__init__(model_path)

    def _load_model(self):
        print(f"[ONNX Engine] Loading model from {self.model_path}...")
        self.session = self.ort.InferenceSession(self.model_path)
        self.input_name = self.session.get_inputs()[0].name
        self.output_names = [o.name for o in self.session.get_outputs()]

    def infer(self, image):
        """
        Runs inference on BGR image (OpenCV numpy array).
        Returns a list of detections: [ [x1, y1, x2, y2, confidence, class_id], ... ]
        """
        if self.session is None or image is None:
            return []

        # 1. Preprocess: Resize to 640x640
        h_orig, w_orig = image.shape[:2]
        img_resized = cv2.resize(image, (640, 640))
        
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        
        # Normalize to 0.0 - 1.0 and transpose to CHW
        img_data = img_rgb.astype(np.float32) / 255.0
        img_data = np.transpose(img_data, (2, 0, 1))  # (3, 640, 640)
        img_tensor = np.expand_dims(img_data, axis=0)   # (1, 3, 640, 640)

        # 2. Run inference
        outputs = self.session.run(self.output_names, {self.input_name: img_tensor})
        
        # 3. Postprocess
        # Output shape is (1, 300, 6)
        detections = outputs[0][0] # shape (300, 6)
        
        results = []
        for det in detections:
            x1, y1, x2, y2, conf, cls_id = det
            # Filter zero/low confidence detections
            if conf > 0.1:
                results.append([float(x1), float(y1), float(x2), float(y2), float(conf), int(cls_id)])
                
        return results
