import cv2
import os
import sys

# Sửa lỗi load DLL cho torch trên Windows giúp tránh lỗi "DLL load failed: c10.dll"
try:
    if os.name == 'nt':
        import importlib.util
        spec = importlib.util.find_spec('torch')
        if spec is not None and spec.submodule_search_locations:
            torch_path = spec.submodule_search_locations[0]
            torch_dll_path = os.path.join(torch_path, 'lib')
            if os.path.exists(torch_dll_path):
                os.add_dll_directory(torch_dll_path)
except Exception:
    pass

from ultralytics import YOLO

class YOLO_Detector:
    def __init__(self, model_path=None):
        # Tải mô hình YOLO (hỗ trợ cả .pt và folder OpenVINO)
        if model_path is None:
            # Sử dụng model OpenVINO vừa được export lại chính xác
            model_path = r"D:\KL_2025\KLTT\File_modelYOLO\model\yolov8-obb\yolov8_openvino_model"
            
        try:
            # Sử dụng task='obb' vì mô hình của bạn là loại Oriented Bounding Box
            self.model = YOLO(model_path, task='obb')
            print(f"Đã tải thành công model AI (OpenVINO): {model_path}")
        except Exception as e:
            print(f"Lỗi khi tải model AI: {e}")
            # Nếu OpenVINO lỗi, thử quay lại load file .pt mặc định nếu có
            try:
                self.model = YOLO("yolov8.pt")
                print("Đã quay lại sử dụng model .pt mặc định")
            except Exception as e2:
                print(f"Không thể nạp model dự phòng: {e2}")
                self.model = None

    def detect_objects(self, frame):
        """
        Nhận frame từ camera, chạy nhận diện và trả về ảnh đã được vẽ kết quả.
        """
        if self.model is None:
            return frame
        
        try:
            # Chạy dự đoán trên frame với ngưỡng tin cậy thấp hơn (conf=0.25)
            # để dễ dàng phát hiện vật thể hơn.
            results = self.model(frame, verbose=False, conf=0.7)
            
            # Lấy ảnh kết quả (annotated frame)
            # line_width=1: Giảm độ dày nét vẽ khung để nhìn thanh thoát hơn
            annotated_frame = results[0].plot(line_width=2)
            return annotated_frame
            
        except Exception as e:
            # Nếu bị lỗi trong lúc dự đoán (thường do OpenVINO runtime)
            # In lỗi ra console thay vì làm crash toàn bộ giao diện
            print(f"Lỗi khi xử lý frame AI: {e}")
            return frame
