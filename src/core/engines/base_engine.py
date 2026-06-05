class BaseEngine:
    """
    Abstract base class for inference engines.
    All specific hardware engines (ONNX, TensorRT) must inherit from this class.
    """
    def __init__(self, model_path: str):
        self.model_path = model_path
        self._load_model()

    def _load_model(self):
        """Implement model loading logic here."""
        raise NotImplementedError("Bắt buộc phải cài đặt logic nạp mô hình.")

    def infer(self, image):
        """
        Run inference on the provided image.
        :param image: Input image (e.g., numpy array from cv2)
        :return: Detection results (bounding boxes, classes, confidences)
        """
        raise NotImplementedError("Bắt buộc phải cài đặt logic suy luận.")
