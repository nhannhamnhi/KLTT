# 🎓 KHÓA LUẬN TỐT NGHIỆP
## Xây dựng hệ thống giám sát và phát hiện vật thể dựa trên thị giác máy tính

---

### 📋 Giới Thiệu
**Đề tài:** Phát hiện lỗi sản phẩm (vỉ thuốc) sử dụng mô hình Deep Learning **YOLO** và tối ưu hóa tốc độ xử lý thời gian thực với **OpenVINO**.

Dự án xây dựng một ứng dụng Desktop hoàn chỉnh giúp tự động hóa quy trình kiểm tra chất lượng sản phẩm thông qua camera.

### 🛠 Công Nghệ Sử Dụng
| Thành phần | Công nghệ |
| :--- | :--- |
| **Ngôn ngữ lập trình** | ![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat&logo=python) |
| **Giao diện người dùng** | **PyQt5** (Thiết kế hiện đại, thân thiện) |
| **Mô hình AI** | **YOLOv8** (Oriented Bounding Box - OBB) |
| **Tăng tốc phần cứng** | **Intel OpenVINO™** |

---

### ⚙️ Hướng Dẫn Cài Đặt & Sử Dụng

#### 1. Tải Model AI (Bắt buộc)
Do kích thước file model (OpenVINO IR) khá lớn nên không được lưu trữ trực tiếp trên Git. Bạn vui lòng tải về từ liên kết dưới đây:

📥 **[Google Drive - Download Model OpenVINO](https://drive.google.com/drive/folders/1GZrhgVkqMVZgJNROqwBPujrJ1-hqv6_k?usp=sharing)**

#### 2. Cấu Hình Đường Dẫn
Sau khi tải và giải nén model, mở file `File_MainProgram/Class_AI.py` và cập nhật biến `model_path`:

```python
# Ví dụ:
model_path = r"D:\KL_2025\model\yolov8-obb\yolov8_openvino_model"
```
![Hướng dẫn thay đổi đường dẫn model](images/change_model_path.png)

#### 3. Cài Đặt Thư Viện
Đảm bảo bạn đã kích hoạt môi trường ảo (venv) và cài đặt các dependencies:
```bash
pip install -r requirements.txt
# Hoặc cài trực tiếp:
pip install PyQt5 opencv-python ultralytics openvino
```

#### 4. Chạy Chương Trình
Khởi chạy ứng dụng từ file chính:
```bash
python File_MainProgram/finish.py
```

---
> **Lưu ý:** Đảm bảo Camera/Webcam đã được kết nối trước khi khởi động chức năng nhận diện.
