## 🎓 KHÓA LUẬN TỐT NGHIỆP

### Xây dựng hệ thống giám sát và phát hiện lỗi sản phẩm dựa trên thị giác máy tính

> **Đề tài:** Phát hiện lỗi sản phẩm (vỉ thuốc) sử dụng mô hình Deep Learning **YOLOv8-OBB** kết hợp tối ưu hóa tốc độ xử lý thời gian thực với **Intel OpenVINO™**.

Ứng dụng Desktop được xây dựng bằng **PyQt5**, tự động hóa quy trình kiểm tra chất lượng vỉ thuốc thông qua camera. Hệ thống nhận diện từng viên thuốc trên vỉ, phân loại trạng thái (`Full`, `Partial`, `Empty`) và đưa ra kết quả đánh giá **OK/NG** theo thời gian thực.

---

### 📋 Mục Lục

- [Công Nghệ Sử Dụng](#-công-nghệ-sử-dụng)
- [Cấu Trúc Thư Mục](#-cấu-trúc-thư-mục)
- [Nguyên Lý Hoạt Động](#-nguyên-lý-hoạt-động)
- [Hướng Dẫn Cài Đặt](#-hướng-dẫn-cài-đặt)
- [Hướng Dẫn Sử Dụng](#-hướng-dẫn-sử-dụng)
- [Quản Lý Model AI](#-quản-lý-model-ai)
- [Quản Lý Dữ Liệu](#-quản-lý-dữ-liệu)
- [Cấu Hình Truyền Thông PLC](#-cấu-hình-truyền-thông-plc)
- [Lưu Ý Quan Trọng](#-lưu-y-quan-trọng)

---

### 🛠 Công Nghệ Sử Dụng

| Thành phần | Công nghệ | Vai trò |
| :--- | :--- | :--- |
| **Ngôn ngữ** | ![Python](https://img.shields.io/badge/Python-3.13-blue?style=flat&logo=python) | Ngôn ngữ chính |
| **Giao diện** | **PyQt5** | Thiết kế UI Desktop đa cửa sổ |
| **Mô hình AI** | **YOLOv8** (OBB - Oriented Bounding Box) | Nhận diện và phân loại viên thuốc dạng xoay |
| **Tăng tốc AI** | **Intel OpenVINO™** | Tối ưu hóa inference trên CPU Intel |
| **Xử lý ảnh** | **OpenCV** | Đọc camera, điều chỉnh độ sáng, độ bão hòa màu |
| **Truyền thông PLC** | **python-snap7** | Giao tiếp với PLC Siemens qua S7 Protocol |
| **Dữ liệu (Local)** | **JSON** + **openpyxl** | Lưu trữ kết quả cục bộ và xuất báo cáo Excel chuyên nghiệp |
| **Dữ liệu (Cloud)** | **gspread** + **google-auth** | Hàng chờ và đồng bộ kết quả lên Google Sheets tự động |

---

### 📁 Cấu Trúc Thư Mục

Dưới đây là sơ đồ tổ chức thư mục thực tế của dự án:

```
KLTT/
├── .venv/                       # Môi trường ảo Python chính (được dùng trong run_app.bat)
├── assets/                      # 🎨 Tài nguyên hình ảnh gốc và file định nghĩa Qt Resource
│   ├── hinhanh.qrc              # File cấu hình tài nguyên Qt Designer
│   └── hinhqrc/                 # Thư mục chứa các file ảnh gốc (.png, .jpeg, .jpg)
│
├── data/                        # Thư mục chứa dữ liệu lịch sử đo đạc ở cấp root (chứa file data_history.json)
│
├── docs/                        # 📝 Tài liệu hướng dẫn & Spec
│   ├── DongBoGoogleSheets.md    # Tài liệu hướng dẫn đồng bộ dữ liệu Google Sheets
│   ├── QuyTrinhVanHanh.md       # Quy trình vận hành hệ thống chi tiết
│   ├── tonghoploi.md            # Các lỗi thường gặp và cách khắc phục
│   └── tongquanOPENVION.md      # Hướng dẫn tổng quan về OpenVINO
│
├── ket_qua/                     # 📊 Kết quả thực hiện và tài liệu hệ thống thực tế
│   ├── hinhanh_codeplc/         # Hình ảnh chụp các khối lệnh logic lập trình PLC
│   │   ├── DB_PLC_Python/       # Các khối DB phục vụ truyền thông PLC-Python
│   │   ├── Main_OB1/            # Các network lệnh chính trong khối OB1
│   │   ├── Mode_Auto/           # Các khối điều khiển chế độ Tự động
│   │   └── Mode_Manual/         # Các khối điều khiển chế độ Thủ công
│   ├── hinhanh_giaodien/        # Hình ảnh chụp màn hình giao diện ứng dụng thực tế
│   │   └── qualy_dulieu/        # Hình ảnh giao diện Dialog xem và quản lý dữ liệu

│
├── models/                      # 🤖 Thư mục chứa các model AI YOLOv8-OBB
│   └── yolov8-obb/
│       ├── yolov8.pt            # Trọng số PyTorch gốc
│       └── yolov8_openvino_model/ # Trọng số định dạng OpenVINO (.xml, .bin, metadata.yaml)
│
├── scripts/                     # ⚙️ Các script tiện ích hỗ trợ phát triển
│   └── pyflakes_check.py        # Script kiểm tra nhanh lỗi cú pháp code
│
├── src/                         # 🧠 Toàn bộ mã nguồn chương trình chính
│   ├── ai/
│   │   └── Class_AI.py          # Lớp YOLO_Detector - Xử lý nhận diện AI (OBB / OpenVINO)
│   ├── data/
│   │   ├── config.py            # Cấu hình Google Sheets, thời gian giữ dữ liệu
│   │   ├── config.py.example    # File mẫu cấu hình Google Sheets (dùng làm mẫu)
│   │   ├── data_manager.py      # Lớp DataManager - Quản lý lưu trữ local, sync queue và xuất Excel
│   │   ├── service_account.json # Credentials xác thực với Google API
│   │   └── data/
│   │       ├── data_history.json # Lưu lịch sử kết quả phát hiện thực tế (JSON cục bộ)
│   │       └── pending_queue.json # Hàng chờ dữ liệu chưa đồng bộ lên Cloud
│   ├── plc/
│   │   └── Class_dataplc.py     # Lớp PLCConnector - Truyền thông Snap7 với PLC Siemens
│   └── ui/
│       ├── finish.py            # File khởi chạy chính - Điều phối toàn bộ hệ thống
│       ├── Main.py              # Logic giao diện chính (sinh từ Main.ui)
│       ├── Login.py             # Logic giao diện đăng nhập (sinh từ Login.ui)
│       ├── Background.py        # Logic màn hình khởi động cũ (không sử dụng trực tiếp)
│       ├── data_viewer_dialog.py # Logic điều khiển Dialog xem/lọc/xuất nhật ký kết quả
│       ├── data_viewer_dialog_ui.py # Giao diện Dialog nhật ký (sinh từ .ui)
│       └── hinhanh_rc.py        # File tài nguyên hình ảnh giao diện đã biên dịch
│
├── ui/                          # 🎨 File thiết kế Qt Designer (.ui)
│   └── forms/
│       ├── Main.ui              # Thiết kế giao diện chính
│       ├── Login.ui             # Thiết kế màn hình đăng nhập
│       ├── data_viewer_dialog.ui # Thiết kế dialog xem lịch sử
│       └── untitled.ui          # File phác thảo thiết kế nháp
│
├── venv/                        # Môi trường ảo Python dự phòng
├── requirements.txt             # Danh sách thư viện Python cần cài đặt
├── run_app.bat                  # File script khởi chạy nhanh trên Windows
├── pyrightconfig.json           # File cấu hình môi trường phát triển Pyright
└── README.md                    # Tài liệu hướng dẫn sử dụng (chính là file này)
```

---

### 🔬 Nguyên Lý Hoạt Động

#### Luồng xử lý tổng quan

```
Khởi chạy (finish.py) → Hiện Login → Đăng nhập thành công → Vào thẳng Main UI → Kết nối Camera & PLC
                                                                                │
                                                                       Luồng camera chạy AI
                                                                                │
             Auto (PLC phát tín hiệu sensor) ←──────────────────────────────────┼──────────────────────────────────→ Manual (Trigger trên PC)
                           │                                                                                                    │
          Sensor S0 kích hoạt (Cạnh lên)                                                                             Nhấn nút "Trigger" trên UI
                           │                                                                                                    │
      Đóng băng ảnh AI + Lưu cục bộ & Cloud                                                                     Đóng băng ảnh AI + Lưu cục bộ & Cloud
                           │                                                                                                    │
          Ghi kết quả & DataReady = True xuống PLC                                                                  Ghi kết quả & DataReady = True xuống PLC
                           │                                                                                                    │
          Sensor S0 ngắt kích hoạt (Cạnh xuống)                                                                      Nhấn nút "Continue" trên UI
                           │                                                                                                    │
               Hạ cờ DataReady về False                                                                                  Hạ cờ DataReady về False
```

#### Các thành phần chính

**① Khởi động & Xác thực**
- Ứng dụng chạy trực tiếp file [finish.py](file:///d:/KL_2025/KLTT/src/ui/finish.py) hoặc nhấp đúp file [run_app.bat](file:///d:/KL_2025/KLTT/run_app.bat).
- Màn hình khởi động cũ `Background.py` được loại bỏ để tối ưu hóa quy trình. Giao diện Login xuất hiện ngay lúc bật ứng dụng.
- Người vận hành nhập thông tin tài khoản (mặc định: `admin` / `123`) để vào giao diện giám sát chính.

**② Thu nhận hình ảnh & Tiền xử lý**
- Camera được chạy trên một luồng phụ tách biệt (`CameraThread`) để đảm bảo không làm giật lag giao diện đồ họa.
- Trên giao diện chính, người dùng có thể điều chỉnh trực tiếp **Độ sáng** (-100 đến +100) và **Độ bão hòa màu** (-100 đến +100) bằng các thanh cuộn Slider giúp tối ưu hóa ảnh đầu vào dưới các điều kiện ánh sáng nhà xưởng khác nhau.

**③ Nhận diện lỗi bằng AI**
- Model **YOLOv8-OBB** quét từng khung hình để phát hiện và khoanh vùng các viên thuốc bằng khung xoay hướng (Oriented Bounding Box).
- Model được tối ưu hóa qua **Intel OpenVINO™** nhằm tăng tốc độ suy luận (Inference) trên vi xử lý CPU Intel ở thời gian thực.
- Các viên thuốc được phân loại vào 3 trạng thái:
  - `Full`: Viên thuốc đầy đủ, nguyên vẹn.
  - `Partial`: Viên thuốc bị vỡ, khuyết góc hoặc bị thiếu một phần.
  - `Empty`: Vị trí khuôn bị trống, không có thuốc.

**④ Đánh giá kết quả vỉ thuốc**
- Trạng thái đánh giá hiển thị trên nhãn màu trực quan:
  - **WAIT** (Nền trắng): Chưa có vỉ thuốc đi vào vùng camera giám sát.
  - **MISSING** (Nền cam): Vỉ thuốc bị thiếu ô khuôn chuẩn (khuôn chuẩn mặc định là 6 ô).
  - **OK** (Nền xanh lá): Tất cả các viên trên vỉ đều ở trạng thái `Full`.
  - **NG_L** (Nền vàng): Lỗi nhẹ — hơn 50% số viên đạt chuẩn.
  - **NG_H** (Nền đỏ): Lỗi nặng — từ 50% số viên trở xuống đạt chuẩn.

**⑤ Truyền thông PLC & Điều khiển cơ cấu**
- Kết quả kiểm tra được gửi trực tiếp xuống PLC Siemens thông qua thư viện **python-snap7**.
- **Chế độ AUTO (Tự động):** Khi cảm biến Sensor S0 của PLC phát hiện vỉ thuốc tới vị trí chụp, luồng truyền thông sẽ bắt tín hiệu → Tự động chụp, đóng băng kết quả, lưu trữ và ghi mã kết quả (`PC_KetQua`) cùng cờ `PC_DataReady = True` xuống PLC để điều khiển xylanh đẩy vỉ NG. Khi Sensor S0 ngắt, PC sẽ hạ cờ `PC_DataReady = False`.
- **Chế độ MANUAL (Thủ công):** Yêu cầu bảo mật 2 lớp:
  - Bước 1: Người dùng nhấn nút **Control Manual** trên UI và xác thực tài khoản `admin`/`123`.
  - Bước 2: Gạt công tắc vật lý trên PLC sang chế độ Manual.
  - Khi đủ 2 điều kiện, các nút điều khiển thủ công (Trigger, Continue, Conveyor On/Off, Cylinder 1, Cylinder 2) sẽ hiển thị. Người dùng có thể nhấn giữ để kích hoạt băng tải hoặc các xylanh thử nghiệm.

**⑥ Quản lý và Đồng bộ dữ liệu**
- Kết quả kiểm tra được lưu trữ cục bộ vào file [data_history.json](file:///d:/KL_2025/KLTT/src/data/data/data_history.json).
- Dữ liệu đồng thời được đẩy lên Google Sheets tự động. Nếu mất mạng hoặc lỗi kết nối, dữ liệu sẽ được lưu tạm vào hàng chờ [pending_queue.json](file:///d:/KL_2025/KLTT/src/data/data/pending_queue.json) và tự động đồng bộ lại khi kết nối internet được khôi phục.
- Chức năng tự động dọn dẹp dữ liệu cũ (mặc định giữ lại 90 ngày) giúp tránh đầy bộ nhớ.

---

### ⚙️ Hướng Dẫn Cài Đặt

#### Bước 1: Tải mã nguồn về máy
```bash
git clone <URL_REPOSITORY>
cd KLTT
```

#### Bước 2: Thiết lập môi trường ảo
Nên sử dụng Python phiên bản 3.13 hoặc 3.8+ để tương thích tốt nhất.
```bash
# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt môi trường ảo (Windows)
.venv\Scripts\activate
```

#### Bước 3: Cài đặt các thư viện phụ thuộc
Cài đặt các gói thư viện cơ bản từ file `requirements.txt`:
```bash
pip install -r requirements.txt
```
*Lưu ý:* Để chạy tăng tốc mô hình bằng OpenVINO, cài đặt thêm gói:
```bash
pip install openvino
```

#### Bước 4: Tải mô hình AI
Do file model lớn nên không đưa lên git, tải thư mục mô hình theo đường dẫn dưới đây:
📥 **[Google Drive - Download Model OpenVINO](https://drive.google.com/drive/folders/1GZrhgVkqMVZgJNROqwBPujrJ1-hqv6_k?usp=sharing)**

Sau khi tải, đặt thư mục mô hình vào đúng đường dẫn:
`models/yolov8-obb/yolov8_openvino_model/` (phải chứa đủ 3 file: `yolov8.xml`, `yolov8.bin`, và `metadata.yaml`).

#### Bước 5: Chạy chương trình
```bash
python src/ui/finish.py
```
Hoặc chạy trực tiếp thông qua file batch:
```cmd
run_app.bat
```
Sau khi giao diện tải xong, thực hiện nạp model AI từ giao diện chính:
1. Tại khung **Quản lý Model AI**, nhấn **Duyệt** → Tìm tới thư mục `models/yolov8-obb/yolov8_openvino_model/` hoặc file trọng số gốc `yolov8.pt`.
2. Nhấn nút **Tải Model** → Kiểm tra thanh **Status Bar** bên dưới xem đã hiển thị model AI thành công hay chưa.

#### Bước 6: Cấu hình Google Sheets (Tùy chọn)
Nếu muốn đồng bộ dữ liệu giám sát trực tuyến lên Cloud:
1. Tạo một dự án trên Google Cloud Console, tạo Service Account và tải file credentials JSON về máy.
2. Đổi tên file credential thành `service_account.json` và lưu vào thư mục `src/data/service_account.json`.
3. Sửa file [config.py](file:///d:/KL_2025/KLTT/src/data/config.py) để điền đúng ID bảng tính Google Sheets của bạn:
   ```python
   SPREADSHEET_ID = "ID_BANG_TINH_GOOGLE_SHEETS"
   SERVICE_ACCOUNT_FILE = "src/data/service_account.json"
   SHEET_NAME = "KLTT_Data"
   DATA_RETENTION_DAYS = 90
   ```
4. Chia sẻ quyền chỉnh sửa (Editor) bảng tính Google Sheet đó cho email của Service Account vừa tạo.

---

### 🚀 Hướng Dẫn Sử Dụng

#### Luồng sử dụng cơ bản
1. Nhấp đúp [run_app.bat](file:///d:/KL_2025/KLTT/run_app.bat) để khởi động chương trình.
2. Nhập tên tài khoản `admin` và mật khẩu `123` để đăng nhập hệ thống.
3. Chọn cổng camera phù hợp (Webcam 1 hoặc Webcam 2) → Nhấn **Kết nối** để nhận luồng video.
4. Chọn đúng dòng CPU PLC Siemens (S7-1200 / S7-1500) → Nhập địa chỉ IP PLC → Nhấn **Kết nối PLC**.
5. Nhập đường dẫn model AI → Nhấn **Tải Model**.
6. Ở chế độ Auto, hệ thống sẽ tự động phân loại và điều khiển cơ cấu phân loại của PLC khi có vỉ chạy qua cảm biến.
7. Để xem lại nhật ký hoặc xuất Excel, nhấn nút **📊 Quản lý dữ liệu**.

#### Các chức năng trên giao diện điều khiển

| Phân vùng | Chức năng | Mô tả |
| :--- | :--- | :--- |
| **Camera** | `Webcam_1` / `Webcam_2` | Combobox chọn Camera ID (0 hoặc 1) |
| | **Kết nối / Ngắt kết nối** | Kích hoạt/dừng việc đọc và phân tích camera |
| **Ảnh & Hiệu chỉnh** | **Độ sáng / Độ bão hòa** | Slider điều chỉnh các thông số chất lượng ảnh đầu vào |
| | **Reset** | Khôi phục chất lượng ảnh mặc định (đưa các slider về 0) |
| **Nhận diện AI** | Màn hình hiển thị | Hiển thị song song luồng ảnh gốc và ảnh đã vẽ khung nhận diện xoay (OBB) |
| | Ô trạng thái | Hiển thị nhãn kết quả phân loại vỉ hiện tại (OK, NG_L, NG_H, MISSING, WAIT) |
| | Khung đếm số lượng | Đếm tổng số viên thuốc phát hiện, số viên đạt và số viên lỗi |
| **Model AI** | **Duyệt / Tải Model** | Chọn đường dẫn và nạp model mới trực tiếp trên giao diện |
| **PLC Siemens** | `IP` / `Rack` / `Slot` | Địa chỉ kết nối đến PLC và chọn loại CPU để auto-fill Rack/Slot |
| | **Control Manual** | Xác thực đăng nhập thủ công cho nhân viên vận hành |
| | Trạng thái hệ thống | Hiển thị trạng thái chế độ hoạt động (AUTO / MANUAL), cảm biến S0/S1/S2 và trạng thái hệ thống |
| **Bảng dữ liệu** | Danh sách lịch sử | Hiển thị tóm tắt các bản ghi đã kiểm tra trong ngày hôm nay |
| | **📊 Quản lý dữ liệu** | Mở Dialog lịch sử chi tiết (DataViewerDialog) |

---

### 🤖 Quản Lý Model AI

#### Cách tải mô hình mới từ giao diện
1. Trên bảng điều khiển chính, di chuyển tới tab quản lý model.
2. Nhấp chọn nút **Duyệt** và trỏ đường dẫn tới file `.pt`, `.onnx` hoặc thư mục OpenVINO.
3. Chọn **Tải Model** → Trạng thái tải và loại mô hình suy luận sẽ được hiển thị ngay trên thanh Status Bar.
4. Để hủy model hiện tại, bấm nút **Khôi phục**.

#### Lưu ý về việc chuyển đổi OpenVINO
Nếu bạn huấn luyện mô hình YOLOv8-OBB trên Google Colab và muốn đem về máy local chạy tăng tốc OpenVINO:
- Phiên bản thư viện `ultralytics` trên máy local phải khớp với phiên bản trên môi trường Colab.
- Không nên tải trực tiếp thư mục OpenVINO được sinh từ Colab về máy vì dễ bị lỗi không tương thích tập lệnh tập tin CPU.
- Cách tốt nhất: Tải file trọng số gốc `best.pt` từ Colab về, sau đó chạy dòng lệnh sau trên máy local để sinh lại thư mục OpenVINO:
  ```python
  from ultralytics import YOLO
  model = YOLO("best.pt")
  model.export(format="openvino")
  ```

---

### 📊 Quản Lý Dữ Liệu

Mọi hoạt động quản lý nhật ký dữ liệu được thực hiện tập trung tại cửa sổ **DataViewerDialog** bằng cách nhấn nút **📊 Quản lý dữ liệu** trên UI:

- **Bộ lọc thông minh:** Cho phép chọn xem dữ liệu theo ngày cụ thể (thông qua Widget QDateEdit trực quan) và lọc chính xác theo từng Model AI đã sử dụng.
- **Thống kê nhanh:** Tự động tính toán tổng số bản ghi, số bản ghi OK, NG_L, NG_H, MISSING và tỷ lệ phần trăm đạt chuẩn (Yield Rate) của tập dữ liệu đang lọc.
- **Đồng bộ Google Sheets thủ công:** 
  - Nếu hàng chờ còn dữ liệu chưa đồng bộ, nút **Sync Google Sheets** sẽ gửi tất cả các bản ghi đang chờ lên Cloud.
  - Nếu hàng chờ trống, hệ thống cho phép người dùng lựa chọn đẩy lại (overwrite/append) toàn bộ dữ liệu lịch sử của ngày đang chọn lên Cloud.
- **Xuất Excel báo cáo:** Xuất toàn bộ dữ liệu đang lọc ra file Excel `.xlsx` định dạng chuyên nghiệp:
  - Cột **Ngày** được tự động gộp ô (merge cell) cho các bản ghi trong cùng một ngày.
  - Có hàng tổng hợp kết quả (OK, NG_L, NG_H, MISSING) tô màu phân biệt ở cuối bảng.

---

### 🔌 Cấu Hình Truyền Thông PLC

Hệ thống sử dụng thư viện **python-snap7** để thực hiện đọc/ghi dữ liệu thời gian thực xuống PLC Siemens thông qua 2 khối DB (Data Block) cấu hình không tối ưu hóa (Optimized block access = Disabled).

#### Bản đồ khối dữ liệu PLC (Data Mapping)

Chi tiết bản đồ offset các biến được định cấu hình trong file [Class_dataplc.py](file:///d:/KL_2025/KLTT/src/plc/Class_dataplc.py):

##### Khối DB_GET (PC ghi xuống PLC — DB1, Kích thước: 3 bytes)
- **Offset 0.0 (INT) - `PC_KetQua`:** Kết quả đánh giá của AI (0 = WAIT, 1 = OK, 2 = NG_L, 3 = NG_H, 4 = MISSING).
- **Offset 2.0 (BOOL) - `PC_DataReady`:** Báo cho PLC biết PC đã có kết quả phân tích mới sẵn sàng.
- **Offset 2.1 (BOOL) - `PC_Conveyor`:** Lệnh chạy/dừng băng tải (chỉ có tác dụng ở chế độ Manual).
- **Offset 2.2 (BOOL) - `PC_Cylinder1`:** Kích hoạt xylanh 1 phân loại vỉ NG_L (chế độ Manual).
- **Offset 2.3 (BOOL) - `PC_Cylinder2`:** Kích hoạt xylanh 2 phân loại vỉ NG_H (chế độ Manual).

##### Khối DB_PUT (PLC gửi lên PC — DB2, Kích thước: 1 byte)
- **Offset 0.0 (BOOL) - `PLC_Auto`:** Báo hệ thống đang hoạt động ở chế độ tự động.
- **Offset 0.1 (BOOL) - `PLC_Manual`:** Báo hệ thống đang hoạt động ở chế độ thủ công.
- **Offset 0.2 (BOOL) - `PLC_Running`:** Hệ thống sẵn sàng hoạt động (đèn RUN sáng, không bị lỗi khẩn cấp E-Stop).
- **Offset 0.3 (BOOL) - `PLC_TriggerReq`:** Cảm biến S0 phát hiện sản phẩm đi qua khuôn chụp.
- **Offset 0.4 (BOOL) - `PLC_Sensor1`:** Cảm biến S1 phát hiện vỉ NG_L đến vị trí xylanh 1.
- **Offset 0.5 (BOOL) - `PLC_Sensor2`:** Cảm biến S2 phát hiện vỉ NG_H đến vị trí xylanh 2.

#### Quy trình chỉnh sửa biến hoặc thay đổi DB
Nếu cần cấu hình thêm các biến mới trong TIA Portal, thực hiện cập nhật mã nguồn Python tương ứng:
1. Mở file [Class_dataplc.py](file:///d:/KL_2025/KLTT/src/plc/Class_dataplc.py), điều chỉnh kích thước DB (`DB_GET_SIZE` hoặc `DB_PUT_SIZE`) tại phần khai báo hằng số.
2. Thêm logic đọc hoặc ghi giá trị tương ứng bằng các hàm tiện ích snap7 (ví dụ: `get_bool`, `set_bool`, `get_int`, `set_int`).
3. Khởi chạy script chẩn đoán lỗi PLC độc lập để kiểm tra tính toàn vẹn:
   ```bash
   python src/plc/Class_dataplc.py
   ```
   *(Script sẽ tự động kết nối kiểm tra dung lượng DB thực tế trên PLC, thực hiện đọc thử và ghi test để xác nhận tính chính xác của bản đồ dữ liệu).*

---

### ⚠️ Lưu Ý Quan Trọng

1. **PUT/GET Access:** Trên cấu hình PLC Siemens trong phần mềm TIA Portal, bắt buộc phải bật tùy chọn **Permit access with PUT/GET communication from remote partner** trong mục Protection & Security thì Snap7 mới có thể kết nối.
2. **Biên dịch giao diện từ file UI:** Nếu bạn thực hiện sửa đổi giao diện đồ họa thông qua phần mềm Qt Designer (các file `.ui` nằm ở thư mục `ui/forms/`), bạn phải chạy lệnh biên dịch để cập nhật mã Python tương ứng:
   ```bash
   pyuic5 ui/forms/Main.ui -o src/ui/Main.py
   pyuic5 ui/forms/Login.ui -o src/ui/Login.py
   pyuic5 ui/forms/data_viewer_dialog.ui -o src/ui/data_viewer_dialog_ui.py
   ```
3. **Môi trường Windows:** Các tiến trình AI chạy trên Torch thường gặp lỗi nạp thư viện DLL (`c10.dll`). Mã nguồn trong [finish.py](file:///d:/KL_2025/KLTT/src/ui/finish.py) và [Class_AI.py](file:///d:/KL_2025/KLTT/src/ai/Class_AI.py) đã tích hợp sẵn đoạn mã tự động phát hiện và import đường dẫn thư viện DLL của PyTorch nhằm tránh lỗi sập phần mềm khi khởi chạy trên Windows.
