## 🎓 KHÓA LUẬN TỐT NGHIỆP

### Xây dựng hệ thống giám sát và phát hiện lỗi sản phẩm dựa trên thị giác máy tính

> **Đề tài:** Phát hiện lỗi sản phẩm (vỉ thuốc) sử dụng mô hình Deep Learning **YOLOv8-OBB** kết hợp tối ưu hóa tốc độ xử lý thời gian thực với **Intel OpenVINO™**.

Ứng dụng Desktop (PyQt5) tự động hóa quy trình kiểm tra chất lượng vỉ thuốc qua camera. Nhận diện từng viên thuốc, phân loại trạng thái (`Full`, `Partial`, `Empty`) và đưa ra kết quả **OK/NG** theo thời gian thực.

---

### 🛠 Công Nghệ Sử Dụng

| Thành phần | Công nghệ | Vai trò |
| :--- | :--- | :--- |
| **Ngôn ngữ** | Python 3.13 | Ngôn ngữ chính |
| **Giao diện** | PyQt5 | UI Desktop đa cửa sổ |
| **Mô hình AI** | YOLOv8 (OBB) | Nhận diện viên thuốc dạng xoay |
| **Tăng tốc AI** | Intel OpenVINO™ | Tối ưu inference trên CPU Intel |
| **Xử lý ảnh** | OpenCV | Camera, chỉnh sáng/bão hòa |
| **Truyền thông PLC** | python-snap7 | Giao tiếp PLC Siemens S7 |
| **Dữ liệu Local** | JSON + openpyxl | Lưu trữ + xuất Excel |
| **Dữ liệu Cloud** | gspread + google-auth | Đồng bộ Google Sheets |

---

### 📁 Cấu Trúc Thư Mục

```
KLTT/
├── .venv/               # Môi trường ảo Python
├── assets/              # Ảnh gốc + Qt Resource
├── data/                # Dữ liệu lịch sử (root)
├── docs/                # 📝 Tài liệu hướng dẫn (xem bảng bên dưới)
├── ket_qua/             # Hình ảnh thực tế (PLC, giao diện, phần cứng)
├── models/              # Model AI YOLOv8-OBB (.pt / OpenVINO)
│   └── yolov8-obb/
├── scripts/             # Script tiện ích
├── src/                 # Mã nguồn chính
│   ├── ai/              #   Lớp YOLO_Detector
│   ├── data/            #   DataManager, config, queue
│   ├── plc/             #   PLCConnector (Snap7)
│   └── ui/              #   Giao diện (finish.py, Main.py, Login.py...)
├── ui/forms/            # File thiết kế Qt Designer (.ui)
├── requirements.txt
├── run_app.bat
└── README.md
```

---

### 🔬 Nguyên Lý Hoạt Động (Tóm tắt)

```
Login → Main UI → Camera + PLC + AI chạy song song
                         │
          Auto (Sensor S0) ── hoặc ── Manual (Trigger UI)
                         │
     Đóng băng ảnh → AI phân tích → Ghi kết quả → Gửi PLC → Hạ cờ
```

- **Khởi động:** finish.py → Login (`admin` / `123`) → Main UI.
- **AI:** YOLOv8-OBB phát hiện Full / Partial / Empty.
- **Kết quả vỉ:** WAIT → MISSING → OK (xanh) / NG_L (vàng) / NG_H (đỏ).
- **PLC Auto:** Sensor S0 kích hoạt → AI chụp → ghi `PC_KetQua` + `PC_DataReady`.
- **PLC Manual:** Xác thực 2 lớp (Control Manual + công tắc vật lý) → Trigger/Continue/Cylinder.

📖 Chi tiết: [docs/QuyTrinhVanHanh.md](docs/QuyTrinhVanHanh.md)

---

### ⚙️ Hướng Dẫn Cài Đặt Nhanh

1. **Python** (3.13) + tạo môi trường ảo:
   ```bash
   python -m venv .venv && .venv\Scripts\activate
   ```
2. **Cài thư viện:**
   ```bash
   pip install -r requirements.txt
   pip install openvino          # tùy chọn, tăng tốc AI
   ```
3. **Tải model AI** từ [Google Drive](https://drive.google.com/drive/folders/1GZrhgVkqMVZgJNROqwBPujrJ1-hqv6_k?usp=sharing) → giải nén vào `models/yolov8-obb/yolov8_openvino_model/`.
4. **Chạy:**
   ```bash
   python src/ui/finish.py
   ```
   Hoặc nhấp đúp `run_app.bat`.

📖 Chi tiết có checklist: [docs/caidat.md](docs/caidat.md)

---

### 🚀 Hướng Dẫn Sử Dụng Nhanh

1. `run_app.bat` → Login `admin` / `123`.
2. Chọn camera (Webcam 1/2) → Kết nối.
3. Duyệt đường dẫn model → Tải Model.
4. Nhập IP PLC → Kết nối PLC.
5. Chế độ Auto: tự động chạy khi sensor kích hoạt.
6. Chế độ Manual: Control Manual → Trigger / Continue.
7. Xem lại dữ liệu: 📊 **Quản lý dữ liệu** → lọc, sync Google Sheets, xuất Excel.

📖 Chi tiết: [docs/huongdanUI.md](docs/huongdanUI.md)

---

### 🤖 Quản Lý Model AI

- **Duyệt** → chọn `.pt`, `.onnx` hoặc thư mục OpenVINO.
- **Tải Model** → nạp vào bộ nhận diện.
- **Khôi phục** → hủy model hiện tại.
- **Lưu ý:** Khi export từ Colab, tải `best.pt` về và chạy `model.export(format="openvino")` trên máy local để tránh lỗi tương thích.

📖 Chi tiết: [docs/tongquanOPENVION.md](docs/tongquanOPENVION.md) | [docs/export_openvino.md](docs/export_openvino.md)

---

### 📊 Quản Lý Dữ Liệu

Cửa sổ **DataViewerDialog** (nút 📊 trên UI):
- Lọc theo ngày / Model AI.
- Thống kê: Tổng, OK, NG_L, NG_H, MISSING, Yield Rate.
- **Sync Google Sheets:** đồng bộ hàng chờ lên Cloud.
- **Xuất Excel:** file `.xlsx` gộp ô ngày + tô màu kết quả.

📖 Chi tiết: [docs/DongBoGoogleSheets.md](docs/DongBoGoogleSheets.md)

---

### 🔌 Cấu Hình Truyền Thông PLC

**Bản đồ DB (Snap7):**

| DB | Chiều | Kích thước | Các biến |
| :--- | :--- | :--- | :--- |
| DB1 (DB_GET) | PC → PLC | 3 bytes | `PC_KetQua`, `PC_DataReady`, `PC_Conveyor`, `PC_Cylinder1/2` |
| DB2 (DB_PUT) | PLC → PC | 1 byte | `PLC_Auto`, `PLC_Manual`, `PLC_Running`, `PLC_TriggerReq`, `PLC_Sensor1/2` |

**Yêu cầu:** Bật **Permit access with PUT/GET** trong TIA Portal. Tắt **Optimized block access** trên DB.

📖 Chi tiết: [docs/QuyTrinhVanHanh.md](docs/QuyTrinhVanHanh.md)

---

### ⚠️ Lưu Ý Quan Trọng

1. **PUT/GET Access:** Phải bật trong TIA Portal (Protection & Security) để Snap7 kết nối được.
2. **Biên dịch UI:** Nếu sửa file `.ui` trong `ui/forms/`, chạy:
   ```bash
   pyuic5 ui/forms/Main.ui -o src/ui/Main.py
   pyuic5 ui/forms/Login.ui -o src/ui/Login.py
   pyuic5 ui/forms/data_viewer_dialog.ui -o src/ui/data_viewer_dialog_ui.py
   ```
3. **Windows + Torch:** Mã nguồn đã tích hợp tự động tìm đường dẫn DLL Torch (`torch/lib`) để tránh lỗi `c10.dll`. Luôn chạy từ `.venv`.

---

### 📚 Tài Liệu Chi Tiết (docs/)

| File | Nội dung |
| :--- | :--- |
| [docs/caidat.md](docs/caidat.md) | Cài đặt step-by-step (checklist + lỗi thường gặp) |
| [docs/huongdanUI.md](docs/huongdanUI.md) | Hướng dẫn sử dụng từng khu vực giao diện |
| [docs/QuyTrinhVanHanh.md](docs/QuyTrinhVanHanh.md) | Luồng vận hành Auto/Manual + PLC handshake |
| [docs/DongBoGoogleSheets.md](docs/DongBoGoogleSheets.md) | Cấu hình Google Sheets + xử lý hàng chờ |
| [docs/tongquanOPENVION.md](docs/tongquanOPENVION.md) | Tổng quan OpenVINO |
| [docs/export_openvino.md](docs/export_openvino.md) | Hướng dẫn export .pt → OpenVINO |
| [docs/tonghoploi.md](docs/tonghoploi.md) | Các lỗi thường gặp và cách khắc phục |

---

### 🛠 Troubleshooting Nhanh

| Vấn đề | Kiểm tra |
| :--- | :--- |
| App sập ngay khi mở | Kích hoạt `.venv`, cài `requirements.txt` |
| Không tải được model | Đường dẫn đúng? Đủ 3 file `.xml` + `.bin` + `metadata.yaml`? |
| Kết nối PLC thất bại | Ping được IP? PUT/GET đã bật? DB tắt Optimized access? |
| Nút Manual bị ẩn | Đã Control Manual? Công tắc PLC ở vị trí Manual? |
| Google Sheets không sync | `service_account.json` đúng? Đã share quyền Editor? |

📖 Chi tiết: [docs/tonghoploi.md](docs/tonghoploi.md)