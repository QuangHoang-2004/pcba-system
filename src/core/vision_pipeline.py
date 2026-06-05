from src.services.config_manager import ConfigManager
from src.core.inference_engine import EngineFactory

class VisionPipeline:
    def __init__(self):
        # Initialize Config Manager
        self.config = ConfigManager()
        
        # Load active board settings
        active_board_id = self.config.get("active_board_id", "")
        boards = self.config.get("boards", [])
        
        # Find active board profile
        self.active_profile = next((b for b in boards if b.get("board_id") == active_board_id), None)
        
        if self.active_profile:
            runtime = self.config.get("runtime", "onnxruntime")
            board_id = self.active_profile.get("board_id", "default")
            
            if runtime == "onnxruntime":
                model_path = f"models/raspberry/{board_id}.onnx"
            else:
                model_path = f"models/jetson/{board_id}.engine"
            
            print(f"[VisionPipeline] Khởi tạo AI Engine với runtime: {runtime}")
            # Instantiate correct engine using the Factory
            self.engine = EngineFactory.create_engine(runtime, model_path)
        else:
            self.engine = None
            print("[VisionPipeline] Không tìm thấy cấu hình bo mạch đang kích hoạt.")

    def start(self):
        # Start the processing loop
        pass

    def stop(self):
        # Stop the processing loop
        pass
