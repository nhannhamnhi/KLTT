# Hướng Dẫn Export OpenVINO Từ Local

Quy trình export file .pt → OpenVINO ngay trên máy local để đảm bảo tương thích CPU.

---

## 1. Tại sao cần export local?

- Model export từ Colab có thể không tương thích tập lệnh CPU trên máy khác.
- Export local sinh ra file .xml + .bin khớp với phần cứng thật.

## 2. Yêu cầu

`ash
pip install ultralytics openvino
`

## 3. Export

`python
from ultralytics import YOLO

# Load file .pt đã train (ví dụ best.pt hoặc yolov8n-obb.pt)
model = YOLO("best.pt")

# Export sang OpenVINO
model.export(format="openvino")
`

Kết quả: tạo thư mục est_openvino_model/ chứa:
- est.xml
- est.bin
- metadata.yaml

## 4. Sử dụng

Di chuyển thư mục vào models/yolov8-obb/yolov8_openvino_model/.

Trên giao diện: Duyệt → chọn thư mục đó → Tải Model.

## 5. Kiểm tra tương thích

`python
from ultralytics import YOLO
model = YOLO("models/yolov8-obb/yolov8_openvino_model")
results = model("test.jpg")        # phải chạy không lỗi
`

## 6. Lưu ý

- Phiên bản ultralytics trên máy local phải **giống** với phiên bản đã dùng để train.
- Nếu đã có thư mục OpenVINO cũ, xóa đi rồi export lại.
