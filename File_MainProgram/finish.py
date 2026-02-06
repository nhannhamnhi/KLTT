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
from Class_AI import YOLO_Detector, DEFAULT_MODEL_PATH

import cv2
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QGraphicsScene, QFileDialog
from PyQt5.QtGui import QImage, QPixmap
from datetime import datetime

# Thêm đường dẫn thư mục 'File_QTtoPY' vào sys.path để có thể import các file GUI
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
gui_dir = os.path.join(parent_dir, 'File_QTtoPY')
sys.path.append(gui_dir)

# Import các giao diện từ các file của bạn (nằm trong File_QTtoPY)
from Background import Ui_Background
from Login import Ui_Login
from Main import Ui_Main

# Import module quản lý dữ liệu
from data_manager import get_data_manager

# ================================================================
# LỚP XỬ LÝ LUỒNG CAMERA (CAMERA THREAD)
# Giúp việc đọc camera và XỬ LÝ AI không làm treo giao diện chính
# ================================================================
class CameraThread(QtCore.QThread):
    # Signal gửi về 2 ảnh: Ảnh gốc và Ảnh đã xử lý (đều là numpy array)
    # Signal gửi về 2 ảnh: Ảnh gốc, Ảnh đã xử lý và danh sách nhãn (list)
    change_pixmap_signal = QtCore.pyqtSignal(np.ndarray, np.ndarray, list)
    # Signal báo lỗi kết nối
    error_signal = QtCore.pyqtSignal(str)

    def __init__(self, detector=None, camera_source=0):
        super().__init__()
        self._run_flag = True
        self.detector = detector
        self.camera_source = camera_source
        
        # Giá trị thông số camera mặc định (0 là trạng thái giữ nguyên mặc định phần cứng)
        self.brightness = 0
        self.saturation = 0
        
        # Cờ báo hiệu có thay đổi thông số
        self.params_changed = False
        
        # Cờ báo hiệu tạm dừng hình ảnh (đóng băng)
        self.is_paused = False

    def set_brightness(self, val):
        self.brightness = val
        self.params_changed = True

    def set_saturation(self, val):
        self.saturation = val
        self.params_changed = True

    def run(self):
        # Mở camera dựa trên nguồn được truyền vào
        cap = cv2.VideoCapture(self.camera_source)
        
        if not cap.isOpened():
            self.error_signal.emit(f"Không thể mở nguồn camera: {self.camera_source}")
            self._run_flag = False
            return
        
        while self._run_flag:
            ret, cap_img = cap.read()
            if ret:
                cv_img = cap_img.copy()
                
                # --- XỬ LÝ ẢNH PHẦN MỀM ---
                # 1. Điều chỉnh độ sáng (Beta cộng thêm vào giá trị pixel)
                if self.brightness != 0:
                    cv_img = cv2.convertScaleAbs(cv_img, alpha=1.0, beta=self.brightness)
                
                # 2. Điều chỉnh độ bão hòa (Tỉ lệ nhân hệ số)
                if self.saturation != 0:
                    hsv = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV).astype("float32")
                    (h, s, v) = cv2.split(hsv)
                    # 0 -> hệ số 1.0 (không đổi), 100 -> hệ số 2.0 (tăng gấp đôi), -100 -> hệ số 0 (trắng đen)
                    alpha = (100 + self.saturation) / 100.0
                    s = s * alpha
                    s = np.clip(s, 0, 255)
                    hsv = cv2.merge([h, s, v])
                    cv_img = cv2.cvtColor(hsv.astype("uint8"), cv2.COLOR_HSV2BGR)
                # Xử lý AI ngay trong luồng này...
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

                # Gửi cả 2 ảnh và danh sách nhãn về giao diện (chỉ gửi khi không bị pause)
                if not self.is_paused:
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
        
        # Thiết lập đường dẫn model mặc định và cập nhật UI ban đầu
        self.default_model_path = DEFAULT_MODEL_PATH
        self.ui_main.duongdanmodel.setPlainText(self.default_model_path)
        QtCore.QTimer.singleShot(100, self.handle_model_selection_changed) # Delay nhỏ để UI kịp render rồi mới khóa nút
        
        # Biến quản lý luồng camera
        self.thread_camera = None

        # Thiết lập phạm vi và giá trị mặc định cho các Slider (-100 đến 100, mốc 0 ở giữa)
        self.ui_main.Slider_Dosang.setRange(-100, 100)
        self.ui_main.Slider_baohoa.setRange(-100, 100)
        self.ui_main.Slider_Dosang.setValue(0)
        self.ui_main.Slider_baohoa.setValue(0)

        # Vô hiệu hóa ô nhập địa chỉ camera lúc mới khởi động
        self.ui_main.diachicamera.setEnabled(False)

        # Kết nối các sự kiện nút bấm
        self.setup_connections()

        # --- PHẦN MỚI: Quản lý dữ liệu và hiển thị ---
        # Khởi tạo Data Manager (singleton)
        self.data_manager = get_data_manager()

        # Model cho QListView để hiển thị danh sách kết quả
        self.data_model = QtCore.QStringListModel()
        self.ui_main.Hienthidulieu.setModel(self.data_model)

        # Load dữ liệu ngày hôm nay lên danh sách
        self.update_data_list()

        # Biến lưu trữ kết quả hiện tại để ghi mỗi 10 giây
        self.current_total = 0
        self.current_passed = 0
        self.current_failed = 0
        self.current_result = "WAIT"

        # Timer cập nhật thời gian nội bộ
        self.time_timer = QtCore.QTimer()
        self.time_timer.timeout.connect(self.update_datetime)
        self.time_timer.start(1000)  # 1 giây

        # Ghi chú: Đã tắt timer ghi dữ liệu tự động 10s để sử dụng nút Trigger thủ công
        # self.data_timer = QtCore.QTimer()
        # self.data_timer.timeout.connect(self.save_current_data)
        # self.data_timer.start(10000)

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
        
        # Kết nối sự kiện thay đổi lựa chọn của combobox camera
        self.ui_main.cbKetnoicamera.currentIndexChanged.connect(self.on_camera_selection_changed)

        # Kết nối các Slider để thay đổi từng thông số camera riêng biệt
        self.ui_main.Slider_Dosang.valueChanged.connect(self.update_brightness)
        self.ui_main.Slider_baohoa.valueChanged.connect(self.update_saturation)

        # Kết nối nút Reset hình ảnh
        self.ui_main.Resset_hinhanh.clicked.connect(self.reset_camera_params)

        # Kết nối nút Xuất Excel
        self.ui_main.btXuat.clicked.connect(self.export_excel)

        # Kết nối các nút mô phỏng cảm biến (Trigger và Continue)
        self.ui_main.btTrigger.clicked.connect(self.handle_trigger)
        self.ui_main.btContinue.clicked.connect(self.handle_continue)

        # --- PHẦN MỚI: Kết nối các nút quản lý Model AI ---
        self.ui_main.cbTaimodel.currentIndexChanged.connect(self.handle_model_selection_changed)
        self.ui_main.btBrowser.clicked.connect(self.handle_browse_model)
        self.ui_main.btTaimodel.clicked.connect(self.handle_load_model)
        self.ui_main.btKhoiphuc.clicked.connect(self.handle_restore_model)

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

    def on_camera_selection_changed(self):
        """Xử lý khi thay đổi lựa chọn loại camera trong combobox"""
        loai_camera = self.ui_main.cbKetnoicamera.currentText()
        if loai_camera == "Camera_custom":
            # Nếu là camera tùy chỉnh thì cho phép người dùng nhập địa chỉ
            self.ui_main.diachicamera.setEnabled(True)
            self.ui_main.diachicamera.setFocus()
        else:
            # Ngược lại thì vô hiệu hóa ô nhập và xóa nội dung
            self.ui_main.diachicamera.setEnabled(False)

    def handle_camera_error(self, message):
        """Xử lý khi có lỗi từ luồng camera"""
        QMessageBox.critical(self.main_win, "Lỗi kết nối Camera", message)
        self.ngat_ket_noi_camera()

    # --- PHẦN THÊM MỚI: Các hàm xử lý Camera ---
    def ket_noi_camera(self):
        """Hàm xử lý khi nhấn nút Kết nối Camera"""
        # Nếu đang có luồng chạy, hãy ngắt nó trước khi bắt đầu cái mới
        if self.thread_camera is not None and self.thread_camera.isRunning():
            self.ngat_ket_noi_camera()

        loai_camera = self.ui_main.cbKetnoicamera.currentText()
        camera_source = 0 # Mặc định là webcam laptop

        if loai_camera == "Webcam":
            camera_source = 0
        elif loai_camera == "Camera_USB":
            camera_source = 1 # Webcam rời thường có ID là 1
        elif loai_camera == "Camera_custom":
            # Lấy nội dung từ ô nhập địa chỉ và làm sạch chuỗi
            raw_source = self.ui_main.diachicamera.toPlainText().strip()
            
            # Xóa các ký tự ngoặc kép nếu người dùng lỡ dán vào
            raw_source = raw_source.replace('"', '').replace("'", "")
            
            if not raw_source:
                QMessageBox.warning(self.main_win, "Cảnh báo", "Vui lòng nhập địa chỉ camera hoặc ID chuyên biệt!")
                return
            
            # Thử chuyển đổi sang số nguyên nếu người dùng nhập ID camera (0, 1, 2...)
            try:
                camera_source = int(raw_source)
            except ValueError:
                # Nếu không phải số, là link RTSP hoặc link Droidcam (http://...)
                camera_source = raw_source

        # Khởi tạo và kết nối các signal
        self.thread_camera = CameraThread(detector=self.detector, camera_source=camera_source)
        self.thread_camera.change_pixmap_signal.connect(self.update_image)
        self.thread_camera.error_signal.connect(self.handle_camera_error)
        
        self.thread_camera.start()
        print(f"Đang thử kết nối tới camera nguồn: {camera_source}")

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

    def reset_camera_params(self):
        """Khôi phục cài đặt gốc của camera và đưa slider về 0"""
        # 1. Tạm thời chặn tín hiệu từ slider để không gọi update liên tục khi set value
        self.ui_main.Slider_Dosang.blockSignals(True)
        self.ui_main.Slider_baohoa.blockSignals(True)
        
        # 2. Đưa các slider về vị trí mặc định (0 là giá trị gốc)
        self.ui_main.Slider_Dosang.setValue(0)
        self.ui_main.Slider_baohoa.setValue(0)
        
        # 3. Mở lại chặn tín hiệu
        self.ui_main.Slider_Dosang.blockSignals(False)
        self.ui_main.Slider_baohoa.blockSignals(False)
        
        # 4. Nếu camera đang chạy, khởi động lại nó để xóa cấu hình phần cứng cũ
        if self.thread_camera is not None and self.thread_camera.isRunning():
            self.ngat_ket_noi_camera()
            self.ket_noi_camera()
            print("Đã Reset Camera về mặc định phần cứng.")

    def handle_trigger(self):
        """Xử lý khi nhấn nút Trigger: Dừng hình và Lưu dữ liệu"""
        if self.thread_camera is not None and self.thread_camera.isRunning():
            # 1. Đóng băng hình ảnh
            self.thread_camera.is_paused = True
            
            # 2. Lưu dữ liệu hiện tại ngay lập tức
            self.save_current_data()
            print("[TRIGGER] Đã đóng băng camera và lưu dữ liệu.")
        else:
            QMessageBox.warning(self.main_win, "Thông báo", "Vui lòng kết nối Camera trước khi Trigger!")

    def handle_continue(self):
        """Xử lý khi nhấn nút Continue: Tiếp tục luồng camera"""
        if self.thread_camera is not None and self.thread_camera.isRunning():
            self.thread_camera.is_paused = False
            print("[CONTINUE] Camera đã hoạt động trở lại.")

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

            # Lưu kết quả hiện tại để timer ghi sau
            self.current_total = tong_so
            self.current_passed = vien_dat
            self.current_failed = vien_loi
            self.current_result = "OK" if vien_dat == tong_so else "NG"

    def convert_cv_qt(self, cv_img):
        """Chuyển đổi hình ảnh từ OpenCV sang QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        
        # Không giới hạn kích thước ở đây để fitInView xử lý việc zoom full
        return QPixmap.fromImage(convert_to_Qt_format)

    # --- CÁC HÀM MỚI CHO QUẢN LÝ DỮ LIỆU ---
    def update_datetime(self):
        """Cập nhật thời gian nội bộ (có thể dùng để log hoặc hiển thị QLabel nếu cần)"""
        pass

    def save_current_data(self):
        """Lưu dữ liệu hiện tại vào file JSON (được gọi mỗi 10 giây)"""
        # Chỉ lưu khi có kết quả thực sự (không phải WAIT)
        if self.current_result != "WAIT":
            display_str = self.data_manager.save_record(
                total=self.current_total,
                passed=self.current_passed,
                failed=self.current_failed,
                result=self.current_result
            )
            print(f"[GHI DỮ LIỆU] {display_str}")
            self.update_data_list()

    # --- CÁC HÀM XỬ LÝ MODEL AI ---
    def handle_model_selection_changed(self):
        """Xử lý khóa/mở các nút dựa trên lựa chọn loại model"""
        lua_chon = self.ui_main.cbTaimodel.currentText()
        
        if lua_chon == "Default":
            # Khóa các nút và ô nhập
            self.ui_main.duongdanmodel.setEnabled(False)
            self.ui_main.btBrowser.setEnabled(False)
            self.ui_main.btTaimodel.setEnabled(False)
            self.ui_main.btKhoiphuc.setEnabled(False)
            # Đưa link về mặc định
            self.ui_main.duongdanmodel.setPlainText(self.default_model_path)
        elif "custom" in lua_chon.lower():
            # Mở khóa cho chế độ Custom
            self.ui_main.duongdanmodel.setEnabled(True)
            self.ui_main.btBrowser.setEnabled(True)
            self.ui_main.btTaimodel.setEnabled(True)
            self.ui_main.btKhoiphuc.setEnabled(True)

    def handle_browse_model(self):
        """Duyệt file hoặc thư mục để chọn model"""
        lua_chon = self.ui_main.cbTaimodel.currentText()
        
        if "custom" in lua_chon.lower():
            # Chế độ custom mới: Cho phép chọn cả file (.pt, .onnx) và thư mục (OpenVINO)
            # Đầu tiên hỏi người dùng muốn chọn file hay thư mục
            msg = QMessageBox()
            msg.setWindowTitle("Chọn loại model")
            msg.setText("Bạn muốn tải file model (.pt, .onnx) hay thư mục model OpenVINO?")
            btn_file = msg.addButton("Chọn File (.pt, .onnx)", QMessageBox.ActionRole)
            btn_folder = msg.addButton("Chọn Thư mục (OpenVINO)", QMessageBox.ActionRole)
            msg.addButton("Hủy", QMessageBox.RejectRole)
            
            msg.exec_()
            
            if msg.clickedButton() == btn_file:
                file_path, _ = QFileDialog.getOpenFileName(
                    self.main_win, "Chọn file Model AI", "", "AI Models (*.pt *.onnx);;All Files (*)"
                )
                if file_path:
                    self.ui_main.duongdanmodel.setPlainText(file_path)
            elif msg.clickedButton() == btn_folder:
                dir_path = QFileDialog.getExistingDirectory(self.main_win, "Chọn thư mục Model OpenVINO")
                if dir_path:
                    self.ui_main.duongdanmodel.setPlainText(dir_path)

    def handle_load_model(self):
        """Kiểm tra định dạng và tải model lên hệ thống"""
        path = self.ui_main.duongdanmodel.toPlainText().strip()
        lua_chon = self.ui_main.cbTaimodel.currentText()
        
        if not path:
            QMessageBox.warning(self.main_win, "Cảnh báo", "Vui lòng chọn đường dẫn model!")
            return

        # 1. Validation định dạng linh hoạt cho OpenVION-custom
        if "custom" in lua_chon.lower():
            is_valid = False
            # Trường hợp là file
            if os.path.isfile(path):
                if path.lower().endswith('.pt') or path.lower().endswith('.onnx'):
                    is_valid = True
                else:
                    QMessageBox.critical(self.main_win, "Lỗi định dạng", 
                                       "Nếu là file, vui lòng chọn đúng định dạng .pt hoặc .onnx!")
                    return
            # Trường hợp là thư mục (OpenVINO)
            elif os.path.isdir(path):
                files = os.listdir(path)
                if any(f.endswith('.xml') for f in files):
                    is_valid = True
                else:
                    huong_dan = (
                        "Thư mục không đúng cấu trúc OpenVINO!\n\n"
                        "Yêu cầu: Thư mục phải chứa file .xml và .bin tương ứng."
                    )
                    QMessageBox.critical(self.main_win, "Lỗi cấu trúc", huong_dan)
                    return
            else:
                QMessageBox.critical(self.main_win, "Lỗi", "Đường dẫn không tồn tại!")
                return

        # 2. Thực hiện tải model
        try:
            print(f"Đang tải model mới: {path}")
            new_detector = YOLO_Detector(model_path=path)
            
            if new_detector.model is not None:
                self.detector = new_detector
                # Cập nhật detector cho luồng camera nếu đang chạy
                if self.thread_camera is not None:
                    self.thread_camera.detector = self.detector
                
                QMessageBox.information(self.main_win, "Thành công", f"Đã tải thành công model AI từ:\n{path}")
            else:
                QMessageBox.critical(self.main_win, "Lỗi", "Không thể nạp model. Vui lòng kiểm tra lại file!")
        except Exception as e:
            QMessageBox.critical(self.main_win, "Lỗi hệ thống", f"Phát sinh lỗi khi tải model: {e}")

    def handle_restore_model(self):
        """Khôi phục về cài đặt mặc định (Default)"""
        # Đưa combobox về lựa chọn 'Default'
        # Việc thay đổi index sẽ tự động kích hoạt handle_model_selection_changed
        self.ui_main.cbTaimodel.setCurrentText("Default")
        print("Đã khôi phục cài đặt model về mặc định.")

    def update_data_list(self):
        """Cập nhật danh sách hiển thị từ dữ liệu ngày hôm nay"""
        records = self.data_manager.get_today_records()
        self.data_model.setStringList(records)
        
        # Tự động cuộn xuống dòng mới nhất
        if records:
            index = self.data_model.index(len(records) - 1)
            self.ui_main.Hienthidulieu.scrollTo(index)

    def export_excel(self):
        """Xuất dữ liệu ra file Excel - Hiển thị chọn ngày cụ thể"""
        # 1. Tạo hộp thoại chọn ngày (Calendar Dialog)
        dialog = QtWidgets.QDialog(self.main_win)
        dialog.setWindowTitle("Chọn ngày xuất dữ liệu")
        layout = QtWidgets.QVBoxLayout(dialog)
        
        calendar = QtWidgets.QCalendarWidget()
        calendar.setGridVisible(True)
        
        # Chỉ tích chọn các ngày có dữ liệu (nếu muốn) 
        # Để đơn giản, cho phép chọn bất kỳ ngày nào, nếu không có data sẽ thông báo
        
        layout.addWidget(calendar)
        
        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)
        
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            selected_date = calendar.selectedDate().toString("yyyy-MM-dd")
            
            # Kiểm tra xem ngày này có dữ liệu không
            # Lấy data từ manager
            if selected_date not in self.data_manager.data:
                QMessageBox.warning(self.main_win, "Thông báo", f"Không có dữ liệu cho ngày {selected_date}")
                return

            # 2. Hiển thị dialog chọn nơi lưu
            today_str = datetime.now().strftime('%Y-%m-%d')
            default_filename = f"KetQua_{selected_date}.xlsx"
            
            filepath, _ = QFileDialog.getSaveFileName(
                self.main_win,
                "Chọn nơi lưu file Excel",
                default_filename,
                "Excel Files (*.xlsx);;All Files (*)"
            )
            
            if filepath:
                # Đảm bảo có đuôi .xlsx
                if not filepath.endswith('.xlsx'):
                    filepath += '.xlsx'
                
                success = self.data_manager.export_to_excel(filepath, date_filter=selected_date)
                
                if success:
                    QMessageBox.information(
                        self.main_win,
                        "Thành công",
                        f"Đã xuất file Excel thành công cho ngày {selected_date}!\n\nĐường dẫn: {filepath}"
                    )
                else:
                    QMessageBox.critical(
                        self.main_win,
                        "Lỗi",
                        "Không thể xuất file Excel!"
                    )
        
        # Kết thúc hàm

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    
    # Khởi tạo và chạy chương trình
    controller = Controller()
    controller.show_background()
    
    sys.exit(app.exec_())
