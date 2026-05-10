# Tổng Hợp Các Lỗi Quan Trọng & Cách Khắc Phục

Tài liệu này tổng hợp lại quá trình xử lý sự cố để chạy thành công mô hình YOLOv8-OBB với OpenVINO trên giao diện PyQt5.

## 1. Lỗi Môi Trường Python (Environment Corruption)
- **Triệu chứng**: Gặp lỗi `ImportError`, `DLL load failed`, hoặc không tìm thấy file cấu hình `pyvenv.cfg`.
- **Nguyên nhân**: Môi trường ảo (`venv`) cũ bị lỗi hoặc xung đột thư viện do cài đặt nhiều lần.
- **Khắc phục**:
    1. Xóa hoàn toàn thư mục `venv`.
    2. Tạo lại môi trường mới: `python -m venv venv`.
    3. Cài đặt lại thư viện sạch sẽ: `pip install PyQt5 opencv-python ultralytics openvino`.

## 2. Lỗi Sai Loại Tác Vụ (Task Mismatch)
- **Triệu chứng**: Ứng dụng bị **Crash (thoát đột ngột)** ngay khi nhấn nút kết nối camera để load model.
- **Nguyên nhân**: Trong code cấu hình `task='detect'` (nhận diện hình chữ nhật đứng), nhưng model thực tế là **OBB** (Oriented Bounding Box - nhận diện xoay). Thư viện Ultralytics không thể khớp định dạng đầu ra.
- **Khắc phục**:
    - Sửa file `Class_AI.py`:
    ```python
    # Phải chỉ định rõ là task 'obb'
    self.model = YOLO(model_path, task='obb')
    ```

## 3. Lỗi Tương Thích Phiên Bản Export (Incompatible Export)
- **Triệu chứng**: Lỗi Runtime khó hiểu khi chạy dự đoán (`AttributeError: 'NoneType' object has no attribute 'args'` hoặc crash sâu trong thư viện C++).
- **Nguyên nhân**: File OpenVINO (`.xml`, `.bin`) cũ được export từ một phiên bản Ultralytics/PyTorch khác, không tương thích với phiên bản mới nhất vừa cài đặt trên máy.
- **Khắc phục**:
    - Sử dụng file `.pt` gốc để export lại model ngay trên môi trường hiện tại:
    ```python
    from ultralytics import YOLO
    model = YOLO('yolov8.pt')
    model.export(format='openvino')
    ```
    - Trỏ code vào thư mục model mới vừa export.

## 4. Lỗi Không Hiển Thị Kết Quả Nhận Diện (No Detections)
- **Triệu chứng**: Chương trình chạy mượt, không lỗi, nhưng trên màn hình "Ảnh đã xử lý" không hiện khung chữ nhật nào quanh vật thể.
- **Nguyên nhân**:
    - Mặc định ngưỡng tự tin (confidence threshold) của model quá cao.
    - Model OBB cần góc nhìn và ánh sáng phù hợp.
- **Khắc phục**:
    - Giảm ngưỡng tin cậy trong hàm dự đoán:
    ```python
    results = self.model(frame, verbose=False, conf=0.25)
    ```

---
**Kết quả hiện tại**: Hệ thống đã chạy ổn định với chế độ OpenVINO (CPU Latency Mode), nhận diện được vật thể xoay và hiển thị mượt mà trên giao diện.
