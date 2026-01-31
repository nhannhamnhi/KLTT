import sys
import os

# Cho phép chạy nhiều thư viện OpenMP cùng lúc để tránh crash (thường gặp với torch/cv2)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Sửa lỗi "DLL load failed: c10.dll" cho torch trên Windows
try:
    if os.name == 'nt':
        import importlib.util
        spec = importlib.util.find_spec('torch')
        if spec is not None and spec.submodule_search_locations:
            torch_path = spec.submodule_search_locations[0]
            torch_dll_path = os.path.join(torch_path, 'lib')
            if os.path.exists(torch_dll_path):
                # Thêm thư mục chứa các file DLL của torch vào đường dẫn tìm kiếm
                os.add_dll_directory(torch_dll_path)
except Exception as e:
    print(f"Lưu ý: Không thể nạp DLL bổ sung cho torch: {e}")

# Import AI Detector trước để nạp các DLL cần thiết
from Class_AI import YOLO_Detector

import cv2
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QGraphicsScene
from PyQt5.QtGui import QImage, QPixmap

# Thêm đường dẫn thư mục 'File_QTtoPY' vào sys.path để có thể import các file GUI
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
gui_dir = os.path.join(parent_dir, 'File_QTtoPY')
sys.path.append(gui_dir)

# Import các giao diện từ các file của bạn (nằm trong File_QTtoPY)
from Background import Ui_Background
from Login import Ui_Login
from Main import Ui_Main

# ================================================================
# LỚP XỬ LÝ LUỒNG CAMERA (CAMERA THREAD)
# Giúp việc đọc camera và XỬ LÝ AI không làm treo giao diện chính
# ================================================================
class CameraThread(QtCore.QThread):
    # Signal gửi về 2 ảnh: Ảnh gốc và Ảnh đã xử lý (đều là numpy array)
    # Signal gửi về 2 ảnh: Ảnh gốc, Ảnh đã xử lý và danh sách nhãn (list)
    change_pixmap_signal = QtCore.pyqtSignal(np.ndarray, np.ndarray, list)

    def __init__(self, detector=None):
        super().__init__()
        self._run_flag = True
        self.detector = detector
        
        # Giá trị thông số camera mặc định
        self.brightness = None
        self.saturation = None
        self.exposure = None
        
        # Cờ báo hiệu có thay đổi thông số
        self.params_changed = False

    def set_brightness(self, val):
        self.brightness = val
        self.params_changed = True

    def set_saturation(self, val):
        self.saturation = val
        self.params_changed = True

    def set_exposure(self, val):
        self.exposure = val
        self.params_changed = True

    def run(self):
        # Mở webcam (ID 0 là webcam mặc định của laptop)
        cap = cv2.VideoCapture(0)
        
        while self._run_flag:
            # Nếu có thay đổi thông số từ thanh trượt, áp dụng vào camera
            if self.params_changed:
                if self.brightness is not None:
                    # OpenCV thường nhận giá trị từ 0.0 đến 1.0 hoặc tùy driver
                    # Ở đây ta giả sử slider truyền vào giá trị đã được scale phù hợp
                    cap.set(cv2.CAP_PROP_BRIGHTNESS, self.brightness)
                if self.saturation is not None:
                    cap.set(cv2.CAP_PROP_SATURATION, self.saturation)
                if self.exposure is not None:
                    cap.set(cv2.CAP_PROP_EXPOSURE, self.exposure)
                self.params_changed = False

            ret, cap_img = cap.read()
            if ret:
                cv_img = cap_img.copy()
                # Xử lý AI ngay trong luồng này để không chặn giao diện
                if self.detector:
                    try:
                        # detect_objects giờ trả về 2 giá trị: ảnh và list nhãn
                        processed_img, labels = self.detector.detect_objects(cv_img.copy())
                    except Exception as e:
                        print(f"Lỗi AI detect trong thread: {e}")
                        processed_img = cv_img.copy()
                        labels = []
                else:
                    processed_img = cv_img.copy()
                    labels = []

                # Gửi cả 2 ảnh và danh sách nhãn về giao diện
                self.change_pixmap_signal.emit(cv_img, processed_img, labels)
            
            # Thêm một chút delay nhỏ để giảm tải CPU nếu cần (không bắt buộc)
            # self.msleep(10) 

        cap.release()

    def stop(self):
        """Dừng luồng camera"""
        self._run_flag = False
        self.wait()

class Controller:
    def __init__(self):
        # Khởi tạo các cửa sổ chính
        self.background_win = QtWidgets.QMainWindow()
        self.login_win = QtWidgets.QMainWindow()
        self.main_win = QtWidgets.QMainWindow()

        # Thiết lập UI cho từng cửa sổ
        self.ui_background = Ui_Background()
        self.ui_background.setupUi(self.background_win)

        self.ui_login = Ui_Login()
        self.ui_login.setupUi(self.login_win)
        
        # Sửa lỗi hiển thị Password bằng dấu *
        self.ui_login.matkhau.setEchoMode(QtWidgets.QLineEdit.Password)

        self.ui_main = Ui_Main()
        self.ui_main.setupUi(self.main_win)

        # Cấu hình cho cửa sổ Login
        # Ghim giao diện Login lên trên đầu (Always on Top)
        self.login_win.setWindowFlags(self.login_win.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

        # --- PHẦN THÊM MỚI: Khởi tạo Scene cho hiển thị ảnh ---
        self.scene_goc = QGraphicsScene()
        self.scene_xuly = QGraphicsScene()
        self.ui_main.Anhgoc.setScene(self.scene_goc)
        self.ui_main.Anhdaxuly.setScene(self.scene_xuly)
        
        # Khởi tạo Detector AI
        # Khởi tạo Detector AI (mặc định sẽ dùng OpenVINO trong folder bạn đã cung cấp)
        # Lưu ý: Việc load model có thể mất vài giây, làm treo nhẹ lúc khởi động.
        # Nếu muốn mượt hơn nữa, có thể chuyển việc load model sang QThread khác.
        print("Đang khởi tạo AI Model...")
        self.detector = YOLO_Detector()
        
        # Biến quản lý luồng camera
        self.thread_camera = None

        # Kết nối các sự kiện nút bấm
        self.setup_connections()

    def setup_connections(self):
        # Khi nhấn nút btBatdau ở Background -> Hiện Login
        self.ui_background.btBatdau.clicked.connect(self.show_login)
        
        # Khi nhấn nút btDangnhap ở Login -> Kiểm tra thông tin
        self.ui_login.btDangnhap.clicked.connect(self.handle_login)

        # Nhấn Enter ở ô nhập tên -> Chuyển focus sang ô mật khẩu
        self.ui_login.nhapten.returnPressed.connect(self.ui_login.matkhau.setFocus)
        # Nhấn Enter ở ô mật khẩu -> Thực hiện đăng nhập
        self.ui_login.matkhau.returnPressed.connect(self.handle_login)

        # --- PHẦN THÊM MỚI: Kết nối nút bấm Camera ---
        self.ui_main.btKetnoicamera.clicked.connect(self.ket_noi_camera)
        self.ui_main.btNgatketnoicamera.clicked.connect(self.ngat_ket_noi_camera)

        # Kết nối các Slider để thay đổi từng thông số camera riêng biệt
        self.ui_main.Slider_Dosang.valueChanged.connect(self.update_brightness)
        self.ui_main.Slider_baohoa.valueChanged.connect(self.update_saturation)
        self.ui_main.Slider_phoisang.valueChanged.connect(self.update_exposure)

        # Kết nối nút Reset hình ảnh
        self.ui_main.Resset_hinhanh.clicked.connect(self.reset_camera_params)

    def show_background(self):
        self.background_win.show()

    def show_login(self):
        self.login_win.show()

    def handle_login(self):
        # Lấy dữ liệu từ ô nhập liệu
        username = self.ui_login.nhapten.text()
        password = self.ui_login.matkhau.text()

        # ================================================================
        # VỊ TRÍ THAY ĐỔI TÊN ĐĂNG NHẬP VÀ MẬT KHẨU Ở ĐÂY
        # Bạn có thể thay đổi 'admin' và '123456' bằng thông tin bạn muốn
        # ================================================================
        USER_SETUP = "ad"
        PASS_SETUP = "1"
        # ================================================================

        if username == USER_SETUP and password == PASS_SETUP:
            # Đăng nhập thành công: Đóng Background và Login, hiện Main
            self.login_win.close()
            self.background_win.close()
            self.main_win.show()
        else:
            # Đăng nhập thất bại: Hiển thị cảnh báo
            msg = QMessageBox(self.login_win) # Gắn msg vào login_win để nó hiện trên cùng
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Thông báo đăng nhập")
            msg.setText("Mật khẩu hoặc tên người dùng không đúng vui lòng kiểm tra và đăng nhập lại")
            
            #Làm cho giao diện giống Windows (nền trắng, chữ đen, hiện đại)
            msg.setStyleSheet("""
                * {
                    background-color: white; /* Ép mọi thành phần con kể cả icon về nền trắng */
                }
                QLabel {
                    color: black;
                }
                QPushButton {
                    background-color: #e1e1e1;
                    color: black;
                    border: 1px solid #adadad;
                    min-width: 80px;
                    min-height: 23px;
                }
                QPushButton:hover {
                    background-color: #e5f1fb;
                    border: 1px solid #0078d7;
                }
            """)
            
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            
            # Xóa mật khẩu cũ để người dùng nhập lại dễ hơn
            self.ui_login.matkhau.clear()
            self.ui_login.matkhau.setFocus() # Đưa con trỏ chuột vào ô mật khẩu

    # --- PHẦN THÊM MỚI: Các hàm xử lý Camera ---
    def ket_noi_camera(self):
        """Hàm xử lý khi nhấn nút Kết nối Camera"""
        loai_camera = self.ui_main.cbKetnoicamera.currentText()
        
        if loai_camera == "Webcam":
            if self.thread_camera is None or not self.thread_camera.isRunning():
                # Truyền detector vào thread
                self.thread_camera = CameraThread(detector=self.detector)
                
                # KHÔNG gọi update_camera_params ở đây để camera dùng mặc định của nó
                # Chỉ khi người dùng kéo thanh trượt thì mới áp dụng thông số mới
                
                self.thread_camera.change_pixmap_signal.connect(self.update_image)
                self.thread_camera.start()
        else:
            QMessageBox.information(self.main_win, "Thông báo", f"Chức năng cho {loai_camera} đang được phát triển.")

    def ngat_ket_noi_camera(self):
        """Hàm xử lý khi nhấn nút Ngắt kết nối camera"""
        if self.thread_camera is not None and self.thread_camera.isRunning():
            # Ngắt kết nối tín hiệu trước khi dừng để đảm bảo không có frame nào được gửi đến sau khi clear
            try:
                self.thread_camera.change_pixmap_signal.disconnect(self.update_image)
            except:
                pass
                
            self.thread_camera.stop()
            self.thread_camera = None
        
        # Xóa toàn bộ nội dung trong scene
        self.scene_goc.clear()
        self.scene_xuly.clear()
        
        # Đặt lại màu nền trắng cho scene (nếu cần)
        self.scene_goc.setBackgroundBrush(QtGui.QColor("white"))
        self.scene_xuly.setBackgroundBrush(QtGui.QColor("white"))
        
        # Cập nhật lại khung nhìn để xóa dấu vết của frame cuối cùng
        self.ui_main.Anhgoc.viewport().update()
        self.ui_main.Anhdaxuly.viewport().update()
        
        # Reset lại transform (zoom/pan)
        self.ui_main.Anhgoc.resetTransform()
        self.ui_main.Anhdaxuly.resetTransform()

    def update_brightness(self):
        """Cập nhật độ sáng"""
        if self.thread_camera is not None:
            self.thread_camera.set_brightness(self.ui_main.Slider_Dosang.value())

    def update_saturation(self):
        """Cập nhật độ bão hòa"""
        if self.thread_camera is not None:
            self.thread_camera.set_saturation(self.ui_main.Slider_baohoa.value())

    def update_exposure(self):
        """Cập nhật phơi sáng"""
        if self.thread_camera is not None:
            self.thread_camera.set_exposure(self.ui_main.Slider_phoisang.value())

    def reset_camera_params(self):
        """Khôi phục cài đặt gốc của camera và đưa slider về 0"""
        # 1. Tạm thời chặn tín hiệu từ slider để không gọi update liên tục khi set value
        self.ui_main.Slider_Dosang.blockSignals(True)
        self.ui_main.Slider_baohoa.blockSignals(True)
        self.ui_main.Slider_phoisang.blockSignals(True)
        
        # 2. Đưa các slider về vị trí mặc định (0)
        self.ui_main.Slider_Dosang.setValue(0)
        self.ui_main.Slider_baohoa.setValue(0)
        self.ui_main.Slider_phoisang.setValue(0)
        
        # 3. Mở lại chặn tín hiệu
        self.ui_main.Slider_Dosang.blockSignals(False)
        self.ui_main.Slider_baohoa.blockSignals(False)
        self.ui_main.Slider_phoisang.blockSignals(False)
        
        # 4. Nếu camera đang chạy, khởi động lại nó để xóa cấu hình phần cứng cũ
        if self.thread_camera is not None and self.thread_camera.isRunning():
            self.ngat_ket_noi_camera()
            self.ket_noi_camera()
            print("Đã Reset Camera về mặc định phần cứng.")

    def update_image(self, cv_img_goc, cv_img_xuly, labels):
        """Cập nhật hình ảnh lên giao diện khi có frame mới"""
        
        # Chuyển đổi từ OpenCV (BGR) sang QImage (RGB)
        qt_img_goc = self.convert_cv_qt(cv_img_goc)
        qt_img_xuly = self.convert_cv_qt(cv_img_xuly)
        
        # Hiển thị lên Ảnh gốc
        self.scene_goc.clear()
        self.scene_goc.addPixmap(qt_img_goc)
        # Sử dụng IgnoreAspectRatio để phóng full khung nếu cần, hoặc KeepAspectRatioByExpanding
        self.ui_main.Anhgoc.fitInView(self.scene_goc.itemsBoundingRect(), QtCore.Qt.IgnoreAspectRatio)
        
        # Hiển thị lên Ảnh đã xử lý (Ảnh đã được AI vẽ khung)
        self.scene_xuly.clear()
        self.scene_xuly.addPixmap(qt_img_xuly)
        self.ui_main.Anhdaxuly.fitInView(self.scene_xuly.itemsBoundingRect(), QtCore.Qt.IgnoreAspectRatio)

        # --- XỬ LÝ LOGIC HIỂN THỊ KẾT QUẢ OK/NG/WAIT ---
        # Logic:
        # - Chưa phát hiện vật (list rỗng) -> WAIT (Nền trắng)
        # - Có phát hiện:
        #     + Nếu TẤT CẢ là 'full' -> OK (Nền xanh)
        #     + Nếu chỉ cần có 1 cái 'partial' hoặc 'empty' -> NG (Nền đỏ)
        
        color_wait = "background-color: white; color: black; border: 2px solid #47A3A7; border-radius: 8px;"
        color_ok = "background-color: #349d00; color: white; border: 2px solid #47A3A7; border-radius: 8px;"
        color_ng = "background-color: red; color: white; border: 2px solid #47A3A7; border-radius: 8px;"

        if not labels:
            # Không phát hiện vật gì -> WAIT
            self.ui_main.hienthiKQ.setStyleSheet(color_wait)
            self.ui_main.hienthiKQ.setText("WAIT")
            self.ui_main.hienthiKQ.setAlignment(QtCore.Qt.AlignCenter)
            
            # Reset các ô đếm về 0 khi không có vật
            self.ui_main.Tongsovien.setText("0")
            self.ui_main.Viendat.setText("0")
            self.ui_main.Vienloi.setText("0")
        else:
            # --- ĐẾM SỐ LƯỢNG ---
            tong_so = len(labels)
            vien_dat = 0
            for label in labels:
                if label.strip().lower() == 'full':
                    vien_dat += 1
            
            vien_loi = tong_so - vien_dat
            
            # Hiển thị lên các ô đếm
            self.ui_main.Tongsovien.setText(str(tong_so))
            self.ui_main.Viendat.setText(str(vien_dat))
            self.ui_main.Vienloi.setText(str(vien_loi))

            # --- LOGIC OK/NG ---
            # 'OK' chỉ khi TẤT CẢ các vật detect được là 'Full'
            if vien_dat == tong_so:
                self.ui_main.hienthiKQ.setStyleSheet(color_ok)
                self.ui_main.hienthiKQ.setText("OK")
                self.ui_main.hienthiKQ.setAlignment(QtCore.Qt.AlignCenter)
            else:
                # Bất kỳ trường hợp nào khác (có ít nhất 1 viên không phải 'Full') -> NG
                self.ui_main.hienthiKQ.setStyleSheet(color_ng)
                self.ui_main.hienthiKQ.setText("NG")
                self.ui_main.hienthiKQ.setAlignment(QtCore.Qt.AlignCenter)

    def convert_cv_qt(self, cv_img):
        """Chuyển đổi hình ảnh từ OpenCV sang QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        
        # Không giới hạn kích thước ở đây để fitInView xử lý việc zoom full
        return QPixmap.fromImage(convert_to_Qt_format)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    
    # Khởi tạo và chạy chương trình
    controller = Controller()
    controller.show_background()
    
    sys.exit(app.exec_())
