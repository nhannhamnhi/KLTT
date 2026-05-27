# Tổng Quan Về OpenVINO & Cách Hoạt Động

**OpenVINO** (Open Visual Inference and Neural network Optimization) là bộ công cụ miễn phí của Intel giúp tối ưu hóa và triển khai các mô hình AI (`Deep Learning`) lên phần cứng của Intel (CPU, iGPU, VPU, FPGA) với tốc độ cực nhanh.

## 1. Tại Sao Nên Dùng OpenVINO?
Nếu bạn chạy AI trên Laptop cá nhân không có Card rời (NVIDIA GPU), việc chạy bằng PyTorch thuần sẽ rất chậm và lag.
- **Tốc độ**: Có thể nhanh hơn gấp 2-5 lần so với PyTorch trên cùng một CPU Intel.
- **Nhẹ nhàng**: Không cần cài bộ thư viện CUDA/cuDNN nặng nề.
- **Tương thích**: Hỗ trợ tốt cho Windows, Linux và được Ultralytics YOLO hỗ trợ chính thức.

## 2. Cách Hoạt Động (Quy Trình 2 Bước)
OpenVINO không huấn luyện (train) mô hình, nó chỉ tối ưu hóa mô hình đã có.

### Bước 1: Model Optimizer (Tối ưu hóa)
Chuyển đổi mô hình gốc (từ PyTorch `.pt`, TensorFlow, ONNX) sang định dạng trung gian (Intermediate Representation - **IR**).
Kết quả tạo ra 2 file:
- **.xml**: Chứa cấu trúc mạng (các lớp layer, kết nối).
- **.bin**: Chứa trọng số (weights/biases) dưới dạng nhị phân.

### Bước 2: Inference Engine (Bộ máy suy luận)
Đọc file `.xml` và `.bin`, sau đó tự động phân phối tính toán lên các tập lệnh phần cứng đặc biệt của Intel (như AVX-512 trên CPU) để chạy nhanh nhất có thể.

## 3. Cách Sử Dụng Với YOLOv8

### A. Xuất Mô Hình (Export)
Để chuyển từ `.pt` sang OpenVINO:
```python
from ultralytics import YOLO

# Load model gốc
model = YOLO("yolov8.pt") 

# Xuất ra định dạng OpenVINO
# format='openvino'
model.export(format="openvino")
```
*Lưu ý: Quá trình này sẽ tạo ra một thư mục `yolov8_openvino_model` chứa file `.xml` và `.bin`.*

### B. Chạy Dự Đoán (Inference)
Sau khi export, bạn chỉ cần trỏ đường dẫn vào thư mục chứa model mới. Ultralytics sẽ tự động kích hoạt backend OpenVINO.

```python
from ultralytics import YOLO

# Load model OpenVINO (trỏ vào thư mục vừa tạo)
# task='detect' (vuông) hoặc 'obb' (xoay) tùy model
model = YOLO("path/to/yolov8_openvino_model", task="obb") 

# Chạy dự đoán như bình thường
results = model("image.jpg")
```

## 4. Các Lưu Ý Quan Trọng
1. **Phiên bản đồng bộ**: Nên export và chạy suy luận trên cùng một máy (hoặc cùng phiên bản thư viện `openvino`) để tránh lỗi không tương thích.
2. **Task**: Phải khai báo đúng loại task (`detect`, `obb`, `segment`) khi load model, nếu sai sẽ bị crash.
3. **Phần cứng**: OpenVINO tối ưu nhất cho chip **Intel**. Nếu dùng chip AMD hoặc NVIDIA, hiệu quả sẽ không cao bằng hoặc phải dùng công cụ khác (như ONNX Runtime hay TensorRT).

## 5. Quy trình Export Thực Tế

### Trên máy local (khuyến nghị)
```python
from ultralytics import YOLO
model = YOLO("best.pt")          # file .pt đã train
model.export(format="openvino")  # sinh thư mục best_openvino_model/
```

### Kiểm tra tương thích sau export
```python
model = YOLO("best_openvino_model", task="obb")
results = model("test.jpg")      # chạy không lỗi → OK
print(results[0].obb)            # in kết quả OBB
```

### Lỗi thường gặp khi export

| Lỗi | Nguyên nhân | Fix |
|-----|-------------|-----|
| `ValueError: Invalid task` | Task không khớp với model | Export đúng task (obb/detect/segment) |
| `RuntimeError: openvino not found` | Chưa cài openvino | `pip install openvino` |
| `FileNotFoundError: .xml not found` | Đường dẫn sai | Kiểm tra thư mục OpenVINO có 3 file |
| `Inference error: wrong shape` | Input size không tương thích | Export lại với `imgsz` đúng (ví dụ 640) |

📖 Chi tiết hướng dẫn export: [docs/export_openvino.md](export_openvino.md)
📖 Troubleshooting: [docs/tonghoploi.md](tonghoploi.md)
