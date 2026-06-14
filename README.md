# PCBA Edge AI

Hệ thống phân tích và giám sát lỗi vi mạch (PCBA) bằng AI tại biên (Edge AI). Ứng dụng cung cấp một Dashboard quản lý chuyên nghiệp, với khả năng theo dõi trạng thái dây chuyền, cấu hình hệ thống và xem chi tiết lịch sử kiểm tra. Được thiết kế tối ưu hóa để chạy trên cả **Raspberry Pi** và **NVIDIA Jetson**.

## 1. Công nghệ & Ngôn ngữ
- **Ngôn ngữ lập trình:** Python 3.x
- **Giao diện người dùng (UI):** PySide6 (Qt for Python)
- **Xử lý ảnh & AI:** OpenCV, TensorRT (cho Jetson), ONNX Runtime (cho Raspberry), YOLOv8
- **Truyền thông (IoT):** MQTT, GPIO/PLC (qua modbus/serial)

## 2. Cấu trúc thư mục dự án

```text
pcba_edge_ai/
├── main.py                 # Entry point của ứng dụng (Khởi chạy GUI)
├── requirements.txt        # Danh sách thư viện Python cần thiết (Cơ bản)
├── src/                    # Mã nguồn chính
│   ├── core/               # Chứa logic cốt lõi
│   │   ├── engines/        # Factory Pattern cho AI Engines
│   │   │   ├── base_engine.py
│   │   │   ├── onnx_engine.py      (Cho Raspberry Pi)
│   │   │   └── tensorrt_engine.py  (Cho NVIDIA Jetson)
│   │   ├── inference_engine.py     (Engine Factory)
│   │   ├── vision_pipeline.py      (Luồng xử lý hình ảnh chính)
│   │   └── defect_checker.py       (Logic kiểm tra lỗi linh kiện)
│   ├── hardware/           # Giao tiếp phần cứng (EdgeCamera, Motor, Relay)
│   ├── services/           # Dịch vụ ngầm (Config, Storage, MQTT)
│   └── ui/                 # Giao diện người dùng (PySide6)
├── data/                   # Phân bố dữ liệu sinh ra trong quá trình chạy
│   ├── boards/             # Chứa dữ liệu Profile của các bo mạch (.json)
│   ├── captures/           # Chứa hình ảnh chụp lỗi
│   ├── database/           # Cơ sở dữ liệu SQLite
│   └── reports/            # File báo cáo PDF/CSV
├── models/                 # Chứa mô hình AI phân tách theo nền tảng
│   ├── raspberry/          # Chứa file YOLOv8 dạng .onnx
│   └── jetson/             # Chứa file YOLOv8 dạng .engine (TensorRT)
├── config/                 # Các file cấu hình YAML (app, camera, hardware, model)
├── deploy/                 # Chứa các kịch bản (scripts) cài đặt cho Edge Devices
│   ├── raspberry/          # Script & requirements_pi.txt cho Raspberry
│   ├── jetson/             # Script & requirements_jetson.txt cho Jetson
│   └── systemd/            # File cấu hình service để chạy ngầm cùng OS
├── logs/                   # Log hệ thống
└── tests/                  # Kịch bản kiểm thử tự động
```

## 3. Hướng dẫn Triển khai (Deployment Setup)

Vì hệ thống hỗ trợ 2 nền tảng phần cứng khác nhau, quy trình cài đặt được chia tách rõ ràng để tránh xung đột thư viện (VD: Raspberry không cần cài gói CUDA/TensorRT nặng nề).

### A. Triển khai trên Raspberry Pi (Dùng ONNX Runtime)
Raspberry Pi sử dụng vi xử lý ARM thông thường, do đó hệ thống sử dụng `onnxruntime` để tối ưu hóa inference.
1. **Môi trường & Thư viện:**
   Vào thư mục `deploy/raspberry/` và chạy script cài đặt (hoặc cài tay bằng file `requirements_pi.txt`).
   ```bash
   pip install -r deploy/raspberry/requirements_pi.txt
   ```
2. **Cấu hình Model:**
   Đảm bảo file `config/model.yaml` (hoặc cấu hình thông qua giao diện UI) được đặt là:
   ```yaml
   runtime: onnxruntime
   ```
3. **Mô hình AI:** Đặt file model `.onnx` vào thư mục `models/raspberry/` và trỏ đường dẫn trong `data/boards/` tới file này.

### B. Triển khai trên NVIDIA Jetson (Dùng TensorRT)
Jetson có GPU mạnh mẽ, hệ thống sẽ sử dụng `ultralytics` hoặc native `tensorrt` để tận dụng tăng tốc phần cứng.
1. **Môi trường & Thư viện:**
   Cài đặt môi trường TensorRT thông qua `deploy/jetson/install.sh` hoặc cài các gói trong `requirements_jetson.txt`.
   ```bash
   pip install -r deploy/jetson/requirements_jetson.txt
   ```
2. **Cấu hình Model:**
   Đảm bảo file `config/model.yaml` được đặt là:
   ```yaml
   runtime: tensorrt
   ```
3. **Mô hình AI:** Đặt file model `.engine` (đã được export trên chính thiết bị Jetson đó) vào thư mục `models/jetson/`.

### C. Khởi chạy Ứng dụng
Sau khi setup xong môi trường, bạn luôn khởi chạy ứng dụng từ thư mục gốc:
```bash
# Trên Linux (Raspberry/Jetson)
python main.py

# Trên Windows (Dùng để Dev/Test)
./start.bat
```
*Lưu ý: Bạn có thể cài đặt file `.service` trong thư mục `deploy/systemd/` để ứng dụng tự động chạy khi máy tính nhúng bật nguồn.*

## 4. Chức năng chính
1. **Dashboard Thời Gian Thực:** Hiển thị luồng video từ camera, đếm số lượng linh kiện, số bo mạch lỗi/đạt (Pass/Fail).
2. **Quản Trị Lịch Sử:** Tra cứu lịch sử kiểm tra, xem chi tiết ảnh chụp lỗi của từng bo mạch.
3. **Quản lý Profile Đa Dạng:** Giao diện cho phép tạo và quản lý nhiều cấu hình mạch (Boards) khác nhau, lưu độc lập trong `data/boards/`.
