import os
import sqlite3

DB_PATH = "data/database/pcba_local.db"
CAPTURE_DIR = "data/captures"

def clean():
    print("=== DỌN DẸP DỮ LIỆU LỊCH SỬ ===")
    
    # 1. Xóa các tệp ảnh trong thư mục captures
    deleted_images = 0
    if os.path.exists(CAPTURE_DIR):
        for filename in os.listdir(CAPTURE_DIR):
            file_path = os.path.join(CAPTURE_DIR, filename)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    deleted_images += 1
                except Exception as e:
                    print(f"Không thể xóa ảnh {filename}: {e}")
    print(f"-> Đã xóa {deleted_images} tệp ảnh trong thư mục captures.")

    # 2. Xóa dữ liệu trong database
    deleted_rows = 0
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Đếm số dòng trước khi xóa
            cursor.execute("SELECT COUNT(*) FROM inspections")
            deleted_rows = cursor.fetchone()[0]
            
            # Xóa toàn bộ dữ liệu
            cursor.execute("DELETE FROM inspections")
            conn.commit()
            conn.close()
            print(f"-> Đã xóa {deleted_rows} bản ghi lịch sử trong database.")
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                print("\n[LỖI] Database đang bị khóa!")
                print("Vui lòng TẮT ứng dụng PCBA Edge AI đang chạy và thử lại.")
                return
            else:
                print(f"\n[LỖI] Lỗi kết nối database: {e}")
                return
        except Exception as e:
            print(f"\n[LỖI] Đã xảy ra lỗi khi xóa database: {e}")
            return
    else:
        print("-> Không tìm thấy tệp database.")

    print("\n=== HOÀN THÀNH ===")
    print("Dữ liệu lịch sử đã được dọn sạch hoàn toàn.")

if __name__ == "__main__":
    clean()
