import json
import os
import yaml

CONFIG_DIR = "config"
DATA_DIR = "data"

APP_YML = os.path.join(CONFIG_DIR, "app.yaml")
CAMERA_YML = os.path.join(CONFIG_DIR, "camera.yaml")
MODEL_YML = os.path.join(CONFIG_DIR, "model.yaml")
HARDWARE_YML = os.path.join(CONFIG_DIR, "hardware.yaml")

# New constants for boards directory
BOARDS_DIR = os.path.join(DATA_DIR, "boards")
BOARDS_INDEX = os.path.join(BOARDS_DIR, "index.json")

class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.config = {
                "active_board_id": "power_v1",
                "boards": [],
                "camera": {},
                "conveyor": {},
                "gpio": {}
            }
            cls._instance.load()
        return cls._instance

    def load(self):
        # Load app.yaml
        if os.path.exists(APP_YML):
            try:
                with open(APP_YML, 'r', encoding='utf-8') as f:
                    app_cfg = yaml.safe_load(f) or {}
                    if "active_board_id" in app_cfg:
                        self.config["active_board_id"] = app_cfg["active_board_id"]
            except Exception:
                pass
        
        # Load camera.yaml
        if os.path.exists(CAMERA_YML):
            try:
                with open(CAMERA_YML, 'r', encoding='utf-8') as f:
                    cam_cfg = yaml.safe_load(f) or {}
                    if "camera" in cam_cfg:
                        self.config["camera"] = cam_cfg["camera"]
            except Exception:
                pass

        # Load model.yaml
        if os.path.exists(MODEL_YML):
            try:
                with open(MODEL_YML, 'r', encoding='utf-8') as f:
                    mod_cfg = yaml.safe_load(f) or {}
                    for k in ["runtime", "input_size", "default_confidence", "iou_threshold"]:
                        if k in mod_cfg:
                            self.config[k] = mod_cfg[k]
            except Exception:
                pass

        # Load hardware.yaml
        if os.path.exists(HARDWARE_YML):
            try:
                with open(HARDWARE_YML, 'r', encoding='utf-8') as f:
                    hw_cfg = yaml.safe_load(f) or {}
                    for k in ["gpio", "conveyor"]:
                        if k in hw_cfg:
                            self.config[k] = hw_cfg[k]
            except Exception:
                pass
                
        # Load boards from directory
        boards_list = []
        if os.path.exists(BOARDS_INDEX):
            try:
                with open(BOARDS_INDEX, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                    if isinstance(index_data, list):
                        for b_info in index_data:
                            b_id = b_info.get("id") if isinstance(b_info, dict) else b_info
                            b_file = os.path.join(BOARDS_DIR, f"{b_id}.json")
                            if os.path.exists(b_file):
                                with open(b_file, 'r', encoding='utf-8') as bf:
                                    boards_list.append(json.load(bf))
            except Exception:
                pass
        
        # Fallback if no index but directory exists
        if not boards_list and os.path.exists(BOARDS_DIR):
            for fname in os.listdir(BOARDS_DIR):
                if fname.endswith('.json') and fname != 'index.json':
                    try:
                        with open(os.path.join(BOARDS_DIR, fname), 'r', encoding='utf-8') as bf:
                            boards_list.append(json.load(bf))
                    except Exception:
                        pass
                        
        if boards_list:
            self.config["boards"] = boards_list
        elif os.path.exists(os.path.join(DATA_DIR, "boards.json")):
            # Fallback to old boards.json
            try:
                with open(os.path.join(DATA_DIR, "boards.json"), 'r', encoding='utf-8') as f:
                    b_data = json.load(f)
                    self.config["boards"] = b_data.get("boards", b_data) if isinstance(b_data, dict) else b_data
            except Exception:
                pass



    def save(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(BOARDS_DIR, exist_ok=True)
        
        # Save app.yaml
        app_data = {
            "active_board_id": self.config.get("active_board_id", "power_v1")
        }
        with open(APP_YML, 'w', encoding='utf-8') as f:
            yaml.dump(app_data, f, allow_unicode=True, default_flow_style=False)
            
        # Save camera.yaml
        cam_data = {
            "camera": self.config.get("camera", {})
        }
        with open(CAMERA_YML, 'w', encoding='utf-8') as f:
            yaml.dump(cam_data, f, allow_unicode=True, default_flow_style=False)
            
        # Save model.yaml
        mod_data = {
            "runtime": self.config.get("runtime", "onnxruntime"),
            "input_size": self.config.get("input_size", 320),
            "default_confidence": self.config.get("default_confidence", 0.5),
            "iou_threshold": self.config.get("iou_threshold", 0.45)
        }
        with open(MODEL_YML, 'w', encoding='utf-8') as f:
            yaml.dump(mod_data, f, allow_unicode=True, default_flow_style=False)
            
        # Save hardware.yaml
        hw_data = {}
        if "gpio" in self.config: hw_data["gpio"] = self.config["gpio"]
        if "conveyor" in self.config: hw_data["conveyor"] = self.config["conveyor"]
        if hw_data:
            with open(HARDWARE_YML, 'w', encoding='utf-8') as f:
                yaml.dump(hw_data, f, allow_unicode=True, default_flow_style=False)
                
        # Save boards to directory
        boards = self.config.get("boards", [])
        index_data = []
        
        for board in boards:
            b_id = board.get("board_id", "default")
            b_name = board.get("board_name", "")
            index_data.append({"id": b_id, "name": b_name})
            
            b_file = os.path.join(BOARDS_DIR, f"{b_id}.json")
            with open(b_file, 'w', encoding='utf-8') as f:
                json.dump(board, f, indent=4, ensure_ascii=False)
                
        # Save index.json
        with open(BOARDS_INDEX, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=4, ensure_ascii=False)
            
        # Optional: Clean up orphaned board files
        valid_files = [f"{item['id']}.json" for item in index_data] + ['index.json']
        for fname in os.listdir(BOARDS_DIR):
            if fname.endswith('.json') and fname not in valid_files:
                try:
                    os.remove(os.path.join(BOARDS_DIR, fname))
                except Exception:
                    pass

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value

    def get_full_config(self):
        return self.config.copy()
    
    def set_full_config(self, new_config):
        self.config = new_config
        self.save()


