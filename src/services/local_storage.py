import os
import sqlite3
import json
import uuid
from datetime import datetime, timedelta

class StorageService:
    RETENTION_DAYS = 7  # Số ngày lưu trữ tối đa do lập trình viên quy định sẵn

    def __init__(self, db_path: str = "data/database/pcba_local.db", capture_dir: str = "data/captures"):
        self.db_path = db_path
        self.capture_dir = capture_dir
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.capture_dir, exist_ok=True)
        
        # Initialize SQLite Database
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.create_tables()
        self.prune_old_records()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inspections (
                id TEXT PRIMARY KEY,
                board_id TEXT,
                date TEXT,
                time TEXT,
                status TEXT,
                total INTEGER,
                detected INTEGER,
                defect INTEGER,
                defects_json TEXT,
                components_json TEXT
            )
        """)
        self.conn.commit()

    def prune_old_records(self):
        """
        Deletes database records and their associated images that are older than RETENTION_DAYS.
        """
        try:
            threshold_date = (datetime.now() - timedelta(days=self.RETENTION_DAYS)).strftime("%Y-%m-%d")
            cursor = self.conn.cursor()
            
            # 1. Select IDs of records to delete
            cursor.execute("SELECT id FROM inspections WHERE date < ?", (threshold_date,))
            old_ids = [row[0] for row in cursor.fetchall()]
            
            # 2. Delete corresponding image files
            for rec_id in old_ids:
                img_path = os.path.join(self.capture_dir, f"{rec_id}.jpg")
                if os.path.exists(img_path):
                    try:
                        os.remove(img_path)
                    except Exception:
                        pass
            
            # 3. Delete database records
            cursor.execute("DELETE FROM inspections WHERE date < ?", (threshold_date,))
            self.conn.commit()
            
            if old_ids:
                print(f"[StorageService] Pruned {len(old_ids)} records and images older than {self.RETENTION_DAYS} days (threshold: {threshold_date}).")
        except Exception as e:
            print(f"[StorageService] Failed to prune old records: {e}")

    def save_record(self, record: dict) -> str:
        """
        Saves an inspection record into the local SQLite database.
        record schema:
        {
            "board": str,
            "status": str (OK / DEFECT),
            "total": int,
            "detected": int,
            "defect": int,
            "defects": list of str,
            "components": list of (name, required_count, detected_count)
        }
        """
        rec_id = str(uuid.uuid4())
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        board_id = record.get("board", "default")
        status = record.get("status", "OK")
        total = record.get("total", 0)
        detected = record.get("detected", 0)
        defect = record.get("defect", 0)
        defects_json = json.dumps(record.get("defects", []))
        
        # Components can be a list of lists/tuples: [ (name, required, detected), ... ]
        components_json = json.dumps(record.get("components", []))

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO inspections (id, board_id, date, time, status, total, detected, defect, defects_json, components_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (rec_id, board_id, date_str, time_str, status, total, detected, defect, defects_json, components_json))
        self.conn.commit()
        return rec_id

    def get_records(self, board_id: str = None) -> list:
        """
        Retrieves all records, optionally filtered by board_id.
        Returns a list of dicts formatted like the mock data.
        """
        cursor = self.conn.cursor()
        if board_id:
            cursor.execute("""
                SELECT id, board_id, date, time, status, total, detected, defect, defects_json, components_json 
                FROM inspections 
                WHERE board_id = ? 
                ORDER BY date DESC, time DESC
            """, (board_id,))
        else:
            cursor.execute("""
                SELECT id, board_id, date, time, status, total, detected, defect, defects_json, components_json 
                FROM inspections 
                ORDER BY date DESC, time DESC
            """)
        
        rows = cursor.fetchall()
        records = []
        for r in rows:
            try:
                defects = json.loads(r[8])
            except Exception:
                defects = []
            
            try:
                components = json.loads(r[9])
            except Exception:
                components = []

            records.append({
                "id": r[0],
                "board": r[1],
                "date": r[2],
                "time": r[3],
                "status": r[4],
                "total": r[5],
                "detected": r[6],
                "defect": r[7],
                "defects": defects,
                "components": components
            })
        return records

    def save_image(self, image_data, filename: str) -> str:
        """
        Saves a captured image (as numpy array or bytes) to the disk inside data/captures/.
        For mock simulation, we can just write a dummy text or placeholder file if image_data is mock, 
        or use cv2 if it's an image.
        """
        full_path = os.path.join(self.capture_dir, filename)
        if isinstance(image_data, bytes):
            with open(full_path, "wb") as f:
                f.write(image_data)
        elif hasattr(image_data, "save"): # PIL Image
            image_data.save(full_path)
        else:
            # Try OpenCV save if cv2 is imported, else write mock file
            try:
                import cv2
                cv2.imwrite(full_path, image_data)
            except Exception:
                # Fallback mock text file if it's not a real image
                with open(full_path, "w") as f:
                    f.write("mock image data")
        return full_path
