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

# Đường dẫn model mặc định
DEFAULT_MODEL_PATH = r"D:\KL_2025\KLTT\File_modelYOLO\model\yolov8-obb\yolov8_openvino_model"

class YOLO_Detector:
    def __init__(self, model_path=None):
        # Tải mô hình YOLO (hỗ trợ cả .pt và folder OpenVINO)
        if model_path is None:
            model_path = DEFAULT_MODEL_PATH
        
        self.model_path_loaded = model_path

            
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
            
            # Lấy danh sách tên các class đã dectect được
            detected_classes = []
            if results and len(results) > 0:
                # Với model OBB, kết quả nằm trong results[0].obb
                # Với model thường (Detection), kết quả nằm trong results[0].boxes
                
                det_result = None
                if results[0].obb is not None:
                    det_result = results[0].obb
                elif results[0].boxes is not None:
                    det_result = results[0].boxes
                
                if det_result is not None:
                    # Lấy danh sách class ID của các vật thể phát hiện được
                    cls_indices = det_result.cls.cpu().numpy()
                    # Map từ ID sang tên class (ví dụ: 'full', 'empty', 'partial')
                    names = results[0].names
                    detected_classes = [names[int(cls_id)] for cls_id in cls_indices]

            # Lấy ảnh kết quả (annotated frame)
            # line_width=2: Giảm độ dày nét vẽ khung để nhìn thanh thoát hơn
            annotated_frame = results[0].plot(line_width=2, conf=False)
            
            # Trả về cả ảnh và danh sách nhãn
            return annotated_frame, detected_classes
            
        except Exception as e:
            print(f"Lỗi khi xử lý frame AI: {e}")
            return frame, []

    def get_model_info(self):
        """Trả về thông tin về loại task và định dạng model (VD: OBB - OpenVINO)"""
        if self.model is None:
            return "No Model"
        
        # 1. Xác định Task (Detect hay OBB)
        try:
            # Thuộc tính task thường có trong model object của ultralytics
            task = self.model.task 
            if task == 'obb':
                task_str = "OBB"
            elif task == 'detect':
                task_str = "DETECT"
            else:
                task_str = task.upper()
        except:
            task_str = "UNKNOWN"

        # 2. Xác định định dạng (Format) dựa vào đường dẫn file
        format_str = "Unknown"
        if hasattr(self, 'model_path_loaded'):
            path_lower = self.model_path_loaded.lower()
            if os.path.exists(self.model_path_loaded) and os.path.isdir(self.model_path_loaded):
                format_str = "OpenVINO"
            elif path_lower.endswith('.pt'):
                format_str = ".pt"
            elif path_lower.endswith('.onnx'):
                format_str = "ONNX"
            elif 'openvino' in path_lower: # Fallback check tên
                format_str = "OpenVINO"
        
        return f"{task_str} - {format_str}"
