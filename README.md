# 🎓 KHÓA LUẬN TỐT NGHIỆP

## Xây dựng hệ thống giám sát và phát hiện lỗi sản phẩm dựa trên thị giác máy tính

> **Đề tài:** Phát hiện lỗi sản phẩm (vỉ thuốc) sử dụng mô hình Deep Learning **YOLOv8-OBB** kết hợp tối ưu hóa tốc độ xử lý thời gian thực với **Intel OpenVINO™**.

Ứng dụng Desktop được xây dựng bằng **PyQt5**, tự động hóa quy trình kiểm tra chất lượng vỉ thuốc thông qua camera. Hệ thống nhận diện từng viên thuốc trên vỉ, phân loại trạng thái (`Full`, `Partial`, `Empty`) và đưa ra kết quả đánh giá **OK/NG** theo thời gian thực.

---

## 📋 Mục Lục

- [Công Nghệ Sử Dụng](#-công-nghệ-sử-dụng)
- [Cấu Trúc Thư Mục](#-cấu-trúc-thư-mục)
- [Nguyên Lý Hoạt Động](#-nguyên-lý-hoạt-động)
- [Hướng Dẫn Cài Đặt](#%EF%B8%8F-hướng-dẫn-cài-đặt)
- [Hướng Dẫn Sử Dụng](#-hướng-dẫn-sử-dụng)
- [Quản Lý Model AI](#-quản-lý-model-ai)
- [Quản Lý Dữ Liệu](#-quản-lý-dữ-liệu)
- [Cấu Hình Truyền Thông PLC](#-cấu-hình-truyền-thông-plc)
- [Lưu Ý Quan Trọng](#-lưu-ý-quan-trọng)

---

## 🛠 Công Nghệ Sử Dụng

| Thành phần | Công nghệ | Vai trò |
| :--- | :--- | :--- |
| **Ngôn ngữ** | ![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat&logo=python) | Ngôn ngữ chính |
| **Giao diện** | **PyQt5** | Thiết kế UI Desktop đa cửa sổ |
| **Mô hình AI** | **YOLOv8** (OBB - Oriented Bounding Box) | Nhận diện và phân loại viên thuốc |
| **Tăng tốc AI** | **Intel OpenVINO™** | Tối ưu inference trên CPU Intel |
| **Xử lý ảnh** | **OpenCV** | Đọc camera, điều chỉnh ảnh |
| **Truyền thông PLC** | **python-snap7** | Giao tiếp với PLC Siemens qua S7 Protocol |
| **Dữ liệu** | **JSON** + **openpyxl** | Lưu trữ kết quả và xuất Excel |

---

## 📁 Cấu Trúc Thư Mục

```
KLTT/
├── File_MainProgram/          # 🧠 Code xử lý chính
│   ├── finish.py              # File khởi chạy - Điều phối toàn bộ hệ thống
│   ├── Class_AI.py            # Lớp YOLO_Detector - Xử lý nhận diện AI
│   ├── Class_dataplc.py       # Lớp PLCConnector - Truyền thông PLC Siemens
│   ├── plc_diagnostics.py     # Script chẩn đoán kiểm tra cấu hình DB PLC
│   ├── data_manager.py        # Lớp DataManager - Quản lý lưu/xuất dữ liệu
│   └── data/
│       └── data_history.json  # File lưu lịch sử kết quả phát hiện
│
│── File_Markdown/             # 📝 Tài liệu hướng dẫn & Spec
│   ├── Snap7_DataMap.md       # 📋 Tài liệu chi tiết bản đồ dữ liệu PLC
│   ├── QuyTrinhVanHanh.md     # Hướng dẫn vận hành chi tiết
│   └── ModeAuto-Man.md        # Giải thích logic Auto/Manual
│
├── File_QT/                   # 🎨 File giao diện Qt Designer (.ui)
│   ├── Background.ui          # Màn hình khởi động
│   ├── Login.ui               # Màn hình đăng nhập
│   ├── Main.ui                # Màn hình giao diện chính
│   ├── hinhanh/               # Hình ảnh tài nguyên cho giao diện
│   └── hinhanh.qrc            # File tài nguyên Qt
│
├── File_QTtoPY/               # 🔄 File Python sinh từ Qt Designer
│   ├── Background.py          # Code Python cho màn hình khởi động
│   ├── Login.py               # Code Python cho màn hình đăng nhập
│   ├── Main.py                # Code Python cho giao diện chính
│   └── hinhanh_rc.py          # Resource hình ảnh đã biên dịch
│
├── File_modelYOLO/            # 🤖 Thư mục chứa model AI
│   └── model/yolov8-obb/      # Model YOLOv8-OBB định dạng OpenVINO
│
├── images/                    # Hình ảnh minh họa cho README
├── venv/                      # Môi trường ảo Python
└── README.md                  # File hướng dẫn này
```

---

## 🔬 Nguyên Lý Hoạt Động

### Luồng xử lý tổng quan

```
Khởi động → Đăng nhập → Kết nối Camera → AI nhận diện → Hiển thị OK/NG → Lưu dữ liệu
                                                              ↓
                                               Kết nối PLC → Gửi kết quả → Điều khiển cơ cấu
```

### Các bước hoạt động chính

**① Khởi động & Đăng nhập**
- Ứng dụng hiển thị màn hình chào mừng → Nhấn **Bắt đầu** → Đăng nhập bằng tài khoản → Vào giao diện chính

**② Thu nhận hình ảnh**
- Camera chạy trên **luồng riêng** để giao diện không bị treo
- Hỗ trợ điều chỉnh **độ sáng** và **độ bão hòa** qua Slider
- Hiển thị song song: ảnh gốc và ảnh đã qua AI xử lý

**③ Nhận diện bằng AI**
- Model **YOLOv8-OBB** quét từng frame, phát hiện và phân loại viên thuốc trên vỉ
- Tăng tốc xử lý bằng **OpenVINO** trên CPU Intel
- Mỗi viên thuốc được gán 1 trong 3 nhãn:

| Nhãn | Ý nghĩa | Đánh giá |
| :--- | :--- | :--- |
| `Full` | Viên thuốc đầy đủ, nguyên vẹn | ✅ Đạt |
| `Partial` | Viên thuốc bị thiếu một phần | ❌ Lỗi |
| `Empty` | Vị trí trống, không có viên | ❌ Lỗi |

**④ Đánh giá kết quả**
- **WAIT** (nền trắng): Chưa phát hiện vỉ thuốc trong khung hình
- **MISSING** (nền cam): Phát hiện ít hơn số ô khuôn chuẩn (6 ô)
- **OK** (nền xanh): Tất cả viên đều là `Full`
- **NG_L** (nền vàng): Lỗi nhẹ — hơn 50% viên đạt
- **NG_H** (nền đỏ): Lỗi nặng — ≤50% viên đạt

**⑤ Truyền thông PLC**
- Kết quả AI được gửi xuống PLC qua **Snap7** (S7 Protocol)
- PLC điều khiển cơ cấu: băng tải, xy-lanh phân loại
- **Auto** (PLC tự động): Sensor S0 phát hiện sản phẩm → AI tự động ghi kết quả & DataReady xuống PLC.
- **Manual** (Điều khiển từ PC): Yêu cầu **bảo mật 2 lớp** (Đăng nhập tài khoản điều khiển + Gạt công tắc vật lý PLC sang Manual). Các nút điều khiển chỉ xuất hiện khi đủ cả 2 điều kiện.

**⑥ Lưu trữ & Xuất dữ liệu**
- Nhấn **Trigger** để đóng băng hình ảnh và lưu kết quả kiểm tra vào file JSON
- Nhấn **Continue** để tiếp tục quét
- Hỗ trợ **xuất Excel** theo ngày với format chuyên nghiệp
- Dữ liệu cũ hơn 15 ngày được tự động dọn dẹp

---

## ⚙️ Hướng Dẫn Cài Đặt

### Bước 1: Clone hoặc tải mã nguồn

```bash
git clone <URL_REPOSITORY>
cd KLTT
```

### Bước 2: Tạo và kích hoạt môi trường ảo

```bash
python -m venv venv

# Windows:
venv\Scripts\activate
```

### Bước 3: Cài đặt thư viện

```bash
pip install PyQt5 opencv-python ultralytics openvino openpyxl python-snap7
```

> **Lưu ý:** Nên cài đặt `ultralytics` và `openvino` cùng phiên bản đã dùng để huấn luyện model.

### Bước 4: Tải Model AI

Do file model khá lớn, cần tải riêng từ Google Drive:

📥 **[Google Drive - Download Model OpenVINO](https://drive.google.com/drive/folders/1GZrhgVkqMVZgJNROqwBPujrJ1-hqv6_k?usp=sharing)**

Sau khi tải, đặt thư mục model vào bất kỳ vị trí nào trên máy (ví dụ: `File_modelYOLO/model/`).

### Bước 5: Chạy chương trình và nạp Model

```bash
python File_MainProgram/finish.py
```

Sau khi vào giao diện chính, nạp model AI theo các bước:

1. Nhấn nút **Duyệt** → Chọn thư mục model OpenVINO (hoặc file `.pt`, `.onnx`)
2. Nhấn nút **Tải Model** → Hệ thống sẽ kiểm tra và nạp model
3. Kiểm tra **Status Bar** phía dưới để xác nhận model đã được nạp thành công

> 💡 **Không cần sửa code** — Mọi thao tác nạp/thay đổi model đều thực hiện trực tiếp trên giao diện.

---

## 🚀 Hướng Dẫn Sử Dụng

### Luồng sử dụng cơ bản

```
1. Khởi chạy → Màn hình Background hiện ra
2. Nhấn nút "Bắt đầu" → Chuyển sang đăng nhập
3. Nhập Tên (admin) + Mật khẩu (123) → Vào giao diện chính
4. Chọn Camera (Webcam_1 hoặc Webcam_2) → Nhấn "Kết nối"
5. Hệ thống tự động nhận diện vỉ thuốc → Hiển thị OK/NG
6. Nhấn "Trigger" để dừng hình + lưu kết quả
7. Nhấn "Continue" để tiếp tục quét
8. Nhấn "Xuất" để export kết quả ra Excel
```

### Các chức năng trên giao diện chính

| Khu vực | Thành phần | Chức năng |
| :--- | :--- | :--- |
| **Camera** | Combobox chọn Camera | Chọn `Webcam_1` (ID=0) hoặc `Webcam_2` (ID=1) |
| | Nút **Kết nối** | Bật camera và bắt đầu xử lý AI |
| | Nút **Ngắt kết nối** | Tắt camera, xóa hình trên màn hình |
| **Điều chỉnh ảnh** | Slider **Độ sáng** | Tăng/giảm độ sáng (-100 đến +100) |
| | Slider **Độ bão hòa** | Tăng/giảm màu sắc (-100 đến +100) |
| | Nút **Reset** | Đưa tất cả slider về 0, khởi động lại camera |
| **Hiển thị** | Ảnh gốc | Hình ảnh thô từ camera |
| | Ảnh đã xử lý | Hình ảnh có vẽ khung nhận diện AI |
| | Ô kết quả (OK/NG/WAIT) | Kết quả tổng hợp với màu trực quan |
| | Bộ đếm | Tổng số viên / Viên đạt / Viên lỗi |
| **PLC** | Kết nối PLC | Nhập IP, Rack, Slot → Kết nối PLC Siemens (Có xác minh dòng CPU) |
| | Nút **Control Manual** | Đăng nhập quyền điều khiển thủ công (Mặc định: `admin`/`123`) |
| | Chế độ Auto/Manual | Hiển thị trạng thái đồng bộ từ công tắc vật lý của PLC |
| **Điều khiển** | Nút **Trigger** | (Manual) Đóng băng camera + Ghi kết quả xuống PLC |
| | Nút **Continue** | (Manual) Tiếp tục quét sau khi Trigger |
| | Nút **Conveyor** | (Manual - Momentary) Nhấn giữ để chạy băng tải, nhả để dừng |
| | Các nút **Cylinder** | (Manual - Momentary) Nhấn giữ để kích xy-lanh, nhả để thu |
| **Dữ liệu** | Danh sách kết quả | Hiển thị lịch sử kiểm tra hôm nay |
| | Nút **Xuất Excel** | Chọn ngày → Xuất file `.xlsx` |
| **Status Bar** | Thanh trạng thái | Hệ thống / Model / Camera / FPS / PLC / Mode / Sensor |

---

## 🤖 Quản Lý Model AI

### Thay đổi model từ giao diện (không cần sửa code)

1. Trên giao diện chính, tìm khu vực **Quản lý Model AI**
2. Nhấn nút **Duyệt** → Chọn loại model:
   - **File:** `.pt` (PyTorch) hoặc `.onnx`
   - **Thư mục:** OpenVINO (chứa `.xml` + `.bin` + `metadata.yaml`)
3. Nhấn nút **Tải Model** → Hệ thống kiểm tra và nạp model mới
4. Nhấn nút **Khôi phục** → Xóa đường dẫn model đã chọn

### Tự huấn luyện model và mang về máy cá nhân

> ⚠️ **Lưu ý quan trọng về OpenVINO**

Nếu huấn luyện model trên **Google Colab** rồi mang về sử dụng:

1. **Đồng bộ phiên bản:** `ultralytics` và `openvino` trên máy cá nhân phải **trùng** với Colab
2. **Quy trình khuyên dùng:**
   - **KHÔNG** tải trực tiếp thư mục OpenVINO từ Colab → Có thể lỗi CPU instruction set
   - **NÊN** chỉ tải file trọng số gốc `best.pt` về
   - Sau đó **export lại** trên máy cá nhân:
     ```python
     from ultralytics import YOLO
     model = YOLO("path/to/best.pt")
     model.export(format="openvino")
     ```
3. **Cấu trúc thư mục model OpenVINO:** Phải chứa đầy đủ 3 file (`.xml`, `.bin`, `metadata.yaml`). Không được di chuyển hay xóa lẻ bất kỳ file nào.

---

## 📊 Quản Lý Dữ Liệu

### Lưu trữ

- Dữ liệu được lưu vào `File_MainProgram/data/data_history.json`
- Mỗi bản ghi gồm: Thời gian, Tổng số viên, Viên đạt, Viên lỗi, Kết quả (OK/NG)
- Dữ liệu được phân nhóm theo **ngày** (key: `YYYY-MM-DD`)
- Tự động xóa dữ liệu cũ hơn **15 ngày**

### Xuất Excel

1. Nhấn nút **Xuất** trên giao diện
2. Chọn **ngày** cần xuất từ lịch (Calendar)
3. Chọn **vị trí lưu** file `.xlsx`
4. File Excel được format chuyên nghiệp với merge cell và tiêu đề

---

## 🔌 Cấu Hình Truyền Thông PLC

Hệ thống sử dụng **python-snap7** để giao tiếp với PLC Siemens qua giao thức S7 (TCP/IP cổng 102). Cấu hình biến PLC được khai báo trực tiếp trong mã nguồn file `Class_dataplc.py`.

> 📋 Tài liệu chi tiết về bản đồ dữ liệu: xem file [Snap7_DataMap.md](file:///d:/KL_2025/KLTT/File_Markdown/Snap7_DataMap.md)

### Kiến trúc 2 DB tách biệt

```
┌──────────────────┐         Snap7 (TCP/IP)         ┌──────────────────┐
│   PC (Python)    │  ──── GHI → DB_GET ─────────→  │   PLC Siemens    │
│                  │  ←─── ĐỌC ← DB_PUT ────────   │   (S7-1200/1500) │
│  Class_dataplc   │         Port 102               │  DB_GET + DB_PUT │
└──────────────────┘                                └──────────────────┘
```

### Bảng biến DB_GET — PC GHI xuống PLC (DB1, 3 bytes)

| Offset | Tên biến | Kiểu | Giá trị | Mô tả |
| :--- | :--- | :--- | :--- | :--- |
| 0 - 1 | `PC_KetQua` | INT | 0=WAIT, 1=OK, 2=NG_L, 3=NG_H | Kết quả phân loại AI |
| 2.0 | `PC_DataReady` | BOOL | TRUE/FALSE | Cờ báo PLC có kết quả mới cần đọc |
| 2.1 | `PC_Conveyor` | BOOL | TRUE/FALSE | Lệnh chạy/dừng băng tải (Manual) |
| 2.2 | `PC_Cylinder1` | BOOL | TRUE/FALSE | Kích/thu xy-lanh 1 — đẩy vỉ NG_L |
| 2.3 | `PC_Cylinder2` | BOOL | TRUE/FALSE | Kích/thu xy-lanh 2 — đẩy vỉ NG_H |

### Bảng biến DB_PUT — PLC GỬI lên PC (DB2, 1 byte)

| Offset | Tên biến | Kiểu | Mô tả |
| :--- | :--- | :--- | :--- |
| 0.0 | `PLC_Auto` | BOOL | Chế độ Tự động đang kích hoạt |
| 0.1 | `PLC_Manual` | BOOL | Chế độ Thủ công đang kích hoạt |
| 0.2 | `PLC_Running` | BOOL | Hệ thống sẵn sàng (FALSE khi E-Stop/lỗi) |
| 0.3 | `PLC_TriggerReq` | BOOL | Sensor 0 phát hiện vỉ → yêu cầu chụp |
| 0.4 | `PLC_Sensor1` | BOOL | Sensor 1 — vỉ tới vị trí xy-lanh 1 |
| 0.5 | `PLC_Sensor2` | BOOL | Sensor 2 — vỉ tới vị trí xy-lanh 2 |

### Hướng dẫn chỉnh sửa biến PLC

Khi cần **thêm biến mới** hoặc **thay đổi offset**, chỉnh sửa theo các bước sau:

**Bước 1:** Cập nhật hằng số trong `Class_dataplc.py` (dòng 11-18)

```python
# File: File_MainProgram/Class_dataplc.py

DB_GET = 1            # Số hiệu DB (đổi nếu dùng DB khác trong TIA Portal)
DB_GET_SIZE = 3       # Tổng kích thước DB_GET (bytes) — tăng nếu thêm biến

DB_PUT = 2            # Số hiệu DB
DB_PUT_SIZE = 1       # Tổng kích thước DB_PUT (bytes) — tăng nếu thêm biến
```

**Bước 2:** Thêm/sửa hàm đọc-ghi tương ứng trong class `PLCConnector`

```python
# Ví dụ: Thêm biến PLC_Sensor3 tại offset 0.6 trong DB_PUT
# → Sửa hàm read_plc_status(), thêm dòng:
"sensor3": get_bool(data, 0, 6),  # Offset 0.6: PLC_Sensor3

# → Nhớ tăng DB_PUT_SIZE nếu biến mới nằm ở byte mới
```

**Bước 3:** Cập nhật luồng polling trong class `PLCPollingThread` (nếu cần)

**Bước 4:** Cập nhật giao diện `finish.py` để hiển thị biến mới (nếu cần)

> ⚠️ **Quan trọng:** Sau khi chỉnh sửa Python, phải đảm bảo DB trong TIA Portal cũng được cập nhật tương ứng (cùng offset, cùng kiểu dữ liệu, tắt "Optimized block access").

### Kiểm tra đồng bộ Python ↔ TIA Portal

Sử dụng script chẩn đoán để xác minh cấu hình DB trong PLC khớp với Python:

```bash
python File_MainProgram/plc_diagnostics.py
```

Script sẽ tự động kiểm tra:
1. ✅ DB có tồn tại và đúng kích thước
2. ✅ Đọc thử tất cả biến → offset nào lỗi sẽ báo ngay
3. ✅ Ghi pattern test (VD: `PC_KetQua = 42`) → đối chiếu trong Watch Table
4. ✅ Xác minh dòng CPU (S7-1200/1500) qua Order Code

### Cơ chế ổn định (Debounce)
Vòng lặp đọc PLC (`PLCPollingThread`) được thiết lập cơ chế **Debounce** (xác minh lỗi liên tiếp ~3 giây) giúp giao diện không bị báo mất kết nối ảo khi mạng chập chờn hoặc PLC đang bận xử lý (Job pending).

---

## ⚠️ Lưu Ý Quan Trọng

1. **Camera:** Đảm bảo Camera/Webcam đã được **kết nối vật lý** trước khi nhấn nút Kết nối
2. **Model AI:** Phải nạp model thành công (kiểm tra Status Bar) trước khi kết quả nhận diện hoạt động
3. **Hiệu năng:** OpenVINO tối ưu nhất trên CPU Intel. FPS hiển thị trên Status Bar giúp đánh giá hiệu suất
4. **PLC:** Phải bật **PUT/GET** trong TIA Portal (Properties → Protection). Nếu dùng PLCSim, cần mở **NetToPLCSim**
5. **Tài khoản đăng nhập mặc định:** Có thể thay đổi trong `finish.py` tại biến `USER_SETUP` và `PASS_SETUP`
6. **Giao diện UI:** Các file `.py` trong `File_QTtoPY/` được **sinh tự động** từ Qt Designer → Không nên chỉnh sửa trực tiếp. Nếu muốn thay đổi UI, hãy sửa file `.ui` trong `File_QT/` rồi chạy lại `pyuic5`

---

## 📝 Thông Tin Bổ Sung

### Các thư viện Python chính

```
PyQt5          - Giao diện Desktop
opencv-python  - Xử lý hình ảnh và camera
ultralytics    - Framework YOLO cho nhận diện vật thể
openvino       - Tăng tốc inference trên CPU Intel
python-snap7   - Giao tiếp PLC Siemens qua S7 Protocol
openpyxl       - Đọc/ghi file Excel
numpy          - Xử lý mảng và tính toán số học
```

### Chạy lệnh sinh code Python từ file UI (nếu cần)

```bash
# Sinh lại file Python từ .ui (chạy tại thư mục gốc project)
pyuic5 File_QT/Main.ui -o File_QTtoPY/Main.py
pyuic5 File_QT/Login.ui -o File_QTtoPY/Login.py
pyuic5 File_QT/Background.ui -o File_QTtoPY/Background.py

# Sinh lại file resource
pyrcc5 File_QT/hinhanh.qrc -o File_QTtoPY/hinhanh_rc.py
```
