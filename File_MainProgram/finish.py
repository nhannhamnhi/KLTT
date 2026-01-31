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
    change_pixmap_signal = QtCore.pyqtSignal(np.ndarray, np.ndarray)

    def __init__(self, detector=None):
        super().__init__()
        self._run_flag = True
        self.detector = detector

    def run(self):
        # Mở webcam (ID 0 là webcam mặc định của laptop)
        cap = cv2.VideoCapture(0)
        
        while self._run_flag:
            ret, cv_img = cap.read()
            if ret:
                # Xử lý AI ngay trong luồng này để không chặn giao diện
                if self.detector:
                    try:
                        processed_img = self.detector.detect_objects(cv_img.copy())
                    except Exception as e:
                        print(f"Lỗi AI detect trong thread: {e}")
                        processed_img = cv_img.copy()
                else:
                    processed_img = cv_img.copy()

                # Gửi cả 2 ảnh về giao diện
                self.change_pixmap_signal.emit(cv_img, processed_img)
            
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
        USER_SETUP = "admin"
        PASS_SETUP = "123456"
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

    def update_image(self, cv_img_goc, cv_img_xuly):
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
