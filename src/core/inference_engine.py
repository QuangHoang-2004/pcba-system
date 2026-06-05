class EngineFactory:
    """
    Factory class to instantiate the correct Inference Engine 
    based on the configuration runtime parameter.
    """
    @staticmethod
    def create_engine(runtime: str, model_path: str):
        if runtime == "onnxruntime":
            from .engines.onnx_engine import ONNXEngine
            return ONNXEngine(model_path)
            
        elif runtime == "tensorrt":
            from .engines.tensorrt_engine import TensorRTEngine
            return TensorRTEngine(model_path)
            
        else:
            raise ValueError(f"Runtime '{runtime}' không được hỗ trợ! Vui lòng chọn 'onnxruntime' hoặc 'tensorrt'.")
