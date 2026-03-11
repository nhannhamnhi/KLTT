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
| **Dữ liệu** | **JSON** + **openpyxl** | Lưu trữ kết quả và xuất Excel |

---

## 📁 Cấu Trúc Thư Mục

```
KLTT/
├── File_MainProgram/          # 🧠 Code xử lý chính
│   ├── finish.py              # File khởi chạy - Điều phối toàn bộ hệ thống
│   ├── Class_AI.py            # Lớp YOLO_Detector - Xử lý nhận diện AI
│   ├── data_manager.py        # Lớp DataManager - Quản lý lưu/xuất dữ liệu
│   └── data/
│       └── data_history.json  # File lưu lịch sử kết quả phát hiện
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
- **OK** (nền xanh): Tất cả viên đều là `Full`
- **NG** (nền đỏ): Có bất kỳ viên `Partial` hoặc `Empty` nào

**⑤ Lưu trữ & Xuất dữ liệu**
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
pip install PyQt5 opencv-python ultralytics openvino openpyxl
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
| **Cảm biến** | Nút **Trigger** | Đóng băng camera + Lưu dữ liệu |
| | Nút **Continue** | Tiếp tục quét sau khi Trigger |
| **Dữ liệu** | Danh sách kết quả | Hiển thị lịch sử kiểm tra hôm nay |
| | Nút **Xuất Excel** | Chọn ngày → Xuất file `.xlsx` |
| **Status Bar** | Thanh trạng thái | Hệ thống / Model / Camera / FPS / Thời gian |

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

## ⚠️ Lưu Ý Quan Trọng

1. **Camera:** Đảm bảo Camera/Webcam đã được **kết nối vật lý** trước khi nhấn nút Kết nối
2. **Model AI:** Phải nạp model thành công (kiểm tra Status Bar) trước khi kết quả nhận diện hoạt động
3. **Hiệu năng:** OpenVINO tối ưu nhất trên CPU Intel. FPS hiển thị trên Status Bar giúp đánh giá hiệu suất
4. **Tài khoản đăng nhập mặc định:** Có thể thay đổi trong `finish.py` tại biến `USER_SETUP` và `PASS_SETUP`
5. **Giao diện UI:** Các file `.py` trong `File_QTtoPY/` được **sinh tự động** từ Qt Designer → Không nên chỉnh sửa trực tiếp. Nếu muốn thay đổi UI, hãy sửa file `.ui` trong `File_QT/` rồi chạy lại `pyuic5`

---

## 📝 Thông Tin Bổ Sung

### Các thư viện Python chính

```
PyQt5          - Giao diện Desktop
opencv-python  - Xử lý hình ảnh và camera
ultralytics    - Framework YOLO cho nhận diện vật thể
openvino       - Tăng tốc inference trên CPU Intel
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
