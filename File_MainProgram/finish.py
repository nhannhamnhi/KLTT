import sys
import os
import time

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

# Import module quản lý kết nối PLC
import re
from Class_dataplc import PLCConnector, PLCPollingThread

# ================================================================
# LỚP XỬ LÝ LUỒNG CAMERA (CAMERA THREAD)
# Giúp việc đọc camera và XỬ LÝ AI không làm treo giao diện chính
# ================================================================
class CameraThread(QtCore.QThread):
    # Signal gửi về 2 ảnh: Ảnh gốc và Ảnh đã xử lý (đều là numpy array)
    # Signal gửi về 2 ảnh: Ảnh gốc, Ảnh đã xử lý và danh sách nhãn (list)
    # Signal gửi về 2 ảnh: Ảnh gốc, Ảnh đã xử lý, danh sách nhãn (list) và FPS (float)
    change_pixmap_signal = QtCore.pyqtSignal(np.ndarray, np.ndarray, list, float)
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
        
        # Biến tính FPS
        self.prev_time = 0

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
                    except Exception:
                        # print(f"Lỗi AI detect trong thread: {e}")
                        processed_img = cv_img.copy()
                        labels = []
                else:
                    processed_img = cv_img.copy()
                    labels = []

                # Tính FPS (luôn tính, không bao giờ pause)
                curr_time = time.time()
                fps = 0
                if self.prev_time != 0:
                    delta = curr_time - self.prev_time
                    if delta > 0:
                        fps = 1.0 / delta
                self.prev_time = curr_time

                # Luôn emit mọi frame về giao diện (không bao giờ dừng)
                self.change_pixmap_signal.emit(cv_img, processed_img, labels, fps)
            
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

        # Tắt ApplicationModal (set trong .ui) để Login có thể nhận input khi Main đang mở
        self.main_win.setWindowModality(QtCore.Qt.NonModal)

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
        print("Đang khởi tạo AI Model (Chế độ chờ)...")
        self.detector = YOLO_Detector(model_path=None)
        
        # Cập nhật trạng thái model trên status bar ngay lúc khởi động
        # (Nếu DEFAULT_MODEL_PATH sai hoặc không có, detector.model sẽ là None)
        QtCore.QTimer.singleShot(500, self.update_initial_model_status)
        
        # Thiết lập đường dẫn model mặc định và cập nhật UI ban đầu
        # Thiết lập UI cho việc nạp model
        self.ui_main.duongdanmodel.setPlaceholderText("Vui lòng chọn đường dẫn file (.pt, .onnx) hoặc thư mục OpenVINO...")
        
        # Biến quản lý luồng camera
        self.thread_camera = None

        # --- PHẦN MỚI: Khởi tạo kết nối PLC ---
        self.plc = PLCConnector()
        self.plc_polling_thread = None

        # Thiết lập giá trị mặc định cho các widget PLC
        self.ui_main.Ipplc.setPlainText("192.168.0.1")
        self.ui_main.Rackplc.setRange(0, 7)
        self.ui_main.Slotplc.setRange(0, 31)
        self.ui_main.Rackplc.setValue(0)
        self.ui_main.Slotplc.setValue(1)

        # Thiết lập phạm vi và giá trị mặc định cho các Slider (-100 đến 100, mốc 0 ở giữa)
        self.ui_main.Slider_Dosang.setRange(-100, 100)
        self.ui_main.Slider_baohoa.setRange(-100, 100)
        self.ui_main.Slider_Dosang.setValue(0)
        self.ui_main.Slider_baohoa.setValue(0)

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
        
        # Khởi tạo Status Bar
        self.init_statusbar()

        # Biến lưu trữ kết quả hiện tại để ghi mỗi 10 giây
        self.current_total = 0
        self.current_passed = 0
        self.current_failed = 0
        self.current_result = "WAIT"

        # Số ô khuôn chuẩn của vỉ thuốc (hằng số vật lý — thay đổi ở đây nếu đổi khuôn)
        self.SO_O_KHUON = 6

        # Timer cập nhật thời gian nội bộ
        self.time_timer = QtCore.QTimer()
        self.time_timer.timeout.connect(self.update_datetime)
        self.time_timer.start(1000)  # 1 giây

        # Ghi chú: Đã tắt timer ghi dữ liệu tự động 10s để sử dụng nút Trigger thủ công
        # self.data_timer = QtCore.QTimer()
        # self.data_timer.timeout.connect(self.save_current_data)
        # self.data_timer.start(10000)

        # --- PHẦN MỚI: Khởi tạo trạng thái chế độ Auto/Manual ---
        self.manual_authenticated = False  # Đánh dấu đã đăng nhập thủ công hay chưa
        self._prev_trigger_req = False  # Track trạng thái trigger (S0) từ PLC
        self.has_triggered = False  # Cờ đóng băng: False = Anhdaxuly chạy real-time, True = đóng băng
        self._latest_processed_frame = None  # Lưu frame AI mới nhất để dùng khi trigger

        # Toggle state cho các nút điều khiển Manual
        self.conveyor_state = False
        self.cylinder1_state = False
        self.cylinder2_state = False

        # Thiết lập nút Control Manual mới (thay thế nút Master cũ)
        self.ui_main.btControlManual.setText("⚙️ Control Manual")
        self.ui_main.btControlManual.setStyleSheet(self._STYLE_MASTER_OFF)

        # Khởi động: Ẩn tất cả các nút điều khiển thủ công
        self.ui_main.btConveyor.hide()
        self.ui_main.btCylinder1.hide()
        self.ui_main.btCylinder2.hide()

    def setup_connections(self):
        # Khi nhấn nút btBatdau ở Background -> Đi thẳng vào Main
        self.ui_background.btBatdau.clicked.connect(self.show_main_from_background)
        
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

        # Ghi chú: Nút Trigger và Continue đã được loại bỏ.
        # Camera đóng băng/mở băng tự động qua cảm biến S0 (PLC).

        # --- PHẦN MỚI: Kết nối các nút quản lý Model AI ---
        # Kết nối các nút quản lý Model AI
        self.ui_main.btBrowser.clicked.connect(self.handle_browse_model)
        self.ui_main.btTaimodel.clicked.connect(self.handle_load_model)
        self.ui_main.btKhoiphuc.clicked.connect(self.handle_restore_model)

        # --- PHẦN MỚI: Kết nối các nút và sự kiện PLC ---
        self.ui_main.btKetnoiplc.clicked.connect(self.ket_noi_plc)
        self.ui_main.btNgatketnoiplc.clicked.connect(self.ngat_ket_noi_plc)
        self.ui_main.CPU_PLC.currentIndexChanged.connect(self.on_cpu_plc_changed)

        # --- PHẦN MỚI: Kết nối nút Control Manual ---
        self.ui_main.btControlManual.clicked.connect(self.handle_control_manual_click)

        # --- PHẦN MỚI: Kết nối các nút điều khiển Manual ---
        self.ui_main.btConveyor.clicked.connect(self.handle_conveyor)
        self.ui_main.btCylinder1.clicked.connect(self.handle_cylinder1)
        self.ui_main.btCylinder2.clicked.connect(self.handle_cylinder2)

    def show_background(self):
        self.background_win.show()

    def show_main_from_background(self):
        """Nhấn btBatdau ở Background → Đi thẳng vào Main (bỏ qua Login)."""
        self.background_win.close()
        self.main_win.show()

    def show_login_for_master(self):
        """Hiện cửa sổ Login để xác thực trước khi bật Master."""
        # Reset ô nhập liệu
        self.ui_login.nhapten.clear()
        self.ui_login.matkhau.clear()
        # Hiện cửa sổ trước, sau đó mới set focus (widget phải visible mới nhận focus)
        self.login_win.show()
        self.login_win.raise_()           # Đưa lên trên cùng
        self.login_win.activateWindow()   # Kích hoạt cửa sổ để nhận input
        self.ui_login.nhapten.setFocus()  # Focus vào ô nhập tên

    def handle_control_manual_click(self):
        """Xử lý khi nhấn nút Control Manual: mở Login hoặc Đăng xuất."""
        if self.manual_authenticated:
            # Đã đăng nhập → Nhấn để Đăng xuất
            self.manual_authenticated = False
            self.ui_main.btControlManual.setText("⚙️ Control Manual")
            self.ui_main.btControlManual.setStyleSheet(self._STYLE_MASTER_OFF)
            print("[LOGIN] Đã đăng xuất khỏi chế độ điều khiển thủ công.")
            self.update_manual_ui() # Cập nhật lại UI để ẩn các nút nếu đang hiện
        else:
            # Chưa đăng nhập → Hiện Login
            self.show_login_for_master()

    def handle_login(self):
        """Xử lý đăng nhập: thành công → kích hoạt Control Manual."""
        # Lấy dữ liệu từ ô nhập liệu
        username = self.ui_login.nhapten.text()
        password = self.ui_login.matkhau.text()

        # ================================================================
        # VỊ TRÍ THAY ĐỔI TÊN ĐĂNG NHẬP VÀ MẬT KHẨU Ở ĐÂY
        # ================================================================
        USER_SETUP = "admin"
        PASS_SETUP = "123"
        # ================================================================

        if username == USER_SETUP and password == PASS_SETUP:
            # Đăng nhập thành công
            self.login_win.close()
            self.manual_authenticated = True
            
            # Cập nhật nút thành Đăng xuất
            self.ui_main.btControlManual.setText("🔒 Đăng xuất")
            self.ui_main.btControlManual.setStyleSheet(self._STYLE_MASTER_ON)  # Viền/đỏ nhạt báo hiệu quyền điều khiển
            print("[LOGIN] Đăng nhập quyền Control Manual thành công! Chờ vặn công tắc Manual...")
            
            # Cập nhật lại giao diện ngay để xem PLC có đang ở Manual ko
            self.update_manual_ui()
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
        """Xử lý khi thay đổi lựa chọn loại camera trong combobox (nếu cần thêm logic gì khác)"""
        pass

    # ================================================================
    # CÁC HÀM XỬ LÝ KẾT NỐI PLC
    # ================================================================
    def on_cpu_plc_changed(self):
        """Auto-fill Rack/Slot khi thay đổi lựa chọn CPU PLC."""
        cpu = self.ui_main.CPU_PLC.currentText()
        # Mapping CPU → (rack, slot) theo chuẩn Siemens
        cpu_defaults = {
            "S7-1200": (0, 1),
            "S7-1500": (0, 1),
            "S7-300":  (0, 2),
            "S7-400":  (0, 3),
        }
        rack, slot = cpu_defaults.get(cpu, (0, 1))
        self.ui_main.Rackplc.setValue(rack)
        self.ui_main.Slotplc.setValue(slot)

    # ================================================================
    # CÁC HÀM XỬ LÝ CHẾ ĐỘ AUTO / MANUAL
    # ================================================================

    # --- Style constants cho nút chế độ ---
    _STYLE_MODE_ACTIVE = (
        "QPushButton { background-color: #006666; color: white; "
        "border: 2px solid #006666; border-radius: 5px; font-weight: bold; }"
    )
    _STYLE_MODE_INACTIVE = (
        "QPushButton { color: #169393; background-color: #FFFFFF; "
        "border: 2px solid #CEC2B1; border-radius: 5px; }"
        "QPushButton:hover { background-color: #E2C0B2; color: #FFFFFF; }"
    )
    _STYLE_TOGGLE_ON = (
        "QPushButton { background-color: #CC4400; color: white; "
        "border: 2px solid #CC4400; border-radius: 5px; padding: 5px; font-weight: bold; }"
    )
    _STYLE_TOGGLE_OFF = (
        "QPushButton { background-color: #006666; color: white; "
        "border: 2px solid #CEC2B1; border-radius: 5px; padding: 5px; font-weight: bold; }"
        "QPushButton:hover { background-color: #008080; }"
        "QPushButton:pressed { background-color: #0F6A6A; }"
    )
    _STYLE_MASTER_ON = (
        "QPushButton { background-color: #CC0000; color: white; "
        "border: 2px solid #CC0000; border-radius: 5px; font-weight: bold; }"
    )
    _STYLE_MASTER_OFF = (
        "QPushButton { color: #169393; background-color: #FFFFFF; "
        "border: 2px solid #CEC2B1; border-radius: 5px; }"
        "QPushButton:hover { background-color: #E2C0B2; color: #FFFFFF; }"
    )

    def update_manual_ui(self):
        """
        Cập nhật giao diện: Ẩn/Hiện nút điều khiển thủ công 
        dựa trên việc Đăng nhập UI và Công tắc vật lý PLC.
        """
        is_plc_manual = False
        if getattr(self, 'plc_polling_thread', None) is not None:
            # Lấy trạng thái gần nhất thread đã đọc được
            is_plc_manual = self.plc_polling_thread._prev_status.get("manual", False)

        if self.manual_authenticated and is_plc_manual:
            # Cho phép điều khiển (Vì đã vặn Manual cứng + Đã Login phần mềm)
            self.ui_main.btConveyor.show()
            self.ui_main.btCylinder1.show()
            self.ui_main.btCylinder2.show()
            
            # Khởi tạo lại giao diện nút nhấn để tránh dính màu cũ
            self.conveyor_state = False
            self.cylinder1_state = False
            self.cylinder2_state = False
            self.ui_main.btConveyor.setStyleSheet(self._STYLE_TOGGLE_OFF)
            self.ui_main.btConveyor.setText("▶ Conveyor")
            self.ui_main.btCylinder1.setStyleSheet(self._STYLE_TOGGLE_OFF)
            self.ui_main.btCylinder1.setText("Cylinder 1")
            self.ui_main.btCylinder2.setStyleSheet(self._STYLE_TOGGLE_OFF)
            self.ui_main.btCylinder2.setText("Cylinder 2")
        else:
            # Ẩn nút (Nếu ai gạt lại tũ vật lý qua Auto, HOẶC lỡ tay log out màn hình)
            self.ui_main.btConveyor.hide()
            self.ui_main.btCylinder1.hide()
            self.ui_main.btCylinder2.hide()



    def handle_conveyor(self):
        """Toggle bật/tắt băng tải (Manual only)."""
        self.conveyor_state = not self.conveyor_state
        if self.plc.is_connected:
            self.plc.write_conveyor(self.conveyor_state)

        if self.conveyor_state:
            self.ui_main.btConveyor.setStyleSheet(self._STYLE_TOGGLE_ON)
            self.ui_main.btConveyor.setText("■ Conveyor")
            print("[MANUAL] ▶ Băng tải BẬT")
        else:
            self.ui_main.btConveyor.setStyleSheet(self._STYLE_TOGGLE_OFF)
            self.ui_main.btConveyor.setText("▶ Conveyor")
            print("[MANUAL] ■ Băng tải TẮT")

    def handle_cylinder1(self):
        """Toggle kích/thu xy-lanh 1 (Manual only)."""
        self.cylinder1_state = not self.cylinder1_state
        if self.plc.is_connected:
            self.plc.write_cylinder1(self.cylinder1_state)

        if self.cylinder1_state:
            self.ui_main.btCylinder1.setStyleSheet(self._STYLE_TOGGLE_ON)
            self.ui_main.btCylinder1.setText("■ Cylinder 1")
            print("[MANUAL] 🔴 Xy-lanh 1 KÍCH")
        else:
            self.ui_main.btCylinder1.setStyleSheet(self._STYLE_TOGGLE_OFF)
            self.ui_main.btCylinder1.setText("Cylinder 1")
            print("[MANUAL] ⚫ Xy-lanh 1 THU")

    def handle_cylinder2(self):
        """Toggle kích/thu xy-lanh 2 (Manual only)."""
        self.cylinder2_state = not self.cylinder2_state
        if self.plc.is_connected:
            self.plc.write_cylinder2(self.cylinder2_state)

        if self.cylinder2_state:
            self.ui_main.btCylinder2.setStyleSheet(self._STYLE_TOGGLE_ON)
            self.ui_main.btCylinder2.setText("■ Cylinder 2")
            print("[MANUAL] 🔴 Xy-lanh 2 KÍCH")
        else:
            self.ui_main.btCylinder2.setStyleSheet(self._STYLE_TOGGLE_OFF)
            self.ui_main.btCylinder2.setText("Cylinder 2")
            print("[MANUAL] ⚫ Xy-lanh 2 THU")



    def ket_noi_plc(self):
        """Xử lý khi nhấn nút Kết nối PLC."""
        # 1. Lấy thông tin từ GUI
        ip = self.ui_main.Ipplc.toPlainText().strip()
        rack = self.ui_main.Rackplc.value()
        slot = self.ui_main.Slotplc.value()

        # 2. Validate IP — kiểm tra format IPv4
        if not ip:
            QMessageBox.warning(self.main_win, "Cảnh báo", "Vui lòng nhập địa chỉ IP của PLC!")
            return

        # Regex kiểm tra IPv4 hợp lệ (VD: 192.168.0.1)
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(ip_pattern, ip):
            QMessageBox.warning(
                self.main_win, "Lỗi IP",
                f"Địa chỉ IP không hợp lệ: {ip}\n\n"
                "Định dạng đúng: xxx.xxx.xxx.xxx\n"
                "Ví dụ: 192.168.0.1"
            )
            return

        # Kiểm tra từng octet (0–255)
        octets = ip.split('.')
        for octet in octets:
            if int(octet) > 255:
                QMessageBox.warning(
                    self.main_win, "Lỗi IP",
                    f"Địa chỉ IP không hợp lệ: {ip}\n"
                    f"Giá trị '{octet}' vượt quá 255."
                )
                return

        # 3. Ngắt kết nối cũ nếu đang có
        if self.plc.is_connected:
            self.ngat_ket_noi_plc()

        # 4. Thực hiện kết nối
        print(f"[PLC GUI] Đang kết nối tới {ip} (rack={rack}, slot={slot})...")
        success = self.plc.connect(ip, rack, slot)

        if success:
            # ============================================================
            # BƯỚC XÁC MINH: Kiểm tra dòng CPU thực tế có khớp với lựa chọn
            # ============================================================
            selected_cpu = self.ui_main.CPU_PLC.currentText()  # VD: "S7-1200"
            actual_cpu = self.plc.get_cpu_family()              # VD: "S7-1200" hoặc None

            if actual_cpu is not None and actual_cpu != selected_cpu:
                # CPU không khớp → Ngắt kết nối và thông báo lỗi
                self.plc.disconnect()
                QMessageBox.critical(
                    self.main_win, "Sai dòng CPU",
                    f"❌ Dòng CPU không khớp!\n\n"
                    f"🔧 CPU đã chọn trên giao diện: {selected_cpu}\n"
                    f"📋 CPU thực tế của PLC: {actual_cpu}\n\n"
                    f"Vui lòng chọn đúng dòng CPU '{actual_cpu}' "
                    f"trong ô CPU_PLC rồi kết nối lại."
                )
                return

            # Kết nối thành công + CPU khớp (hoặc không đọc được order code → cho qua)
            info_msg = (
                f"✅ Đã kết nối PLC thành công!\n\n"
                f"IP: {ip}\n"
                f"CPU: {selected_cpu}"
            )
            if actual_cpu:
                info_msg += f" (Xác minh: {actual_cpu} ✓)"
            else:
                info_msg += " (⚠️ Không xác minh được dòng CPU)"
            info_msg += f"\nRack: {rack} | Slot: {slot}"

            QMessageBox.information(self.main_win, "Thành công", info_msg)

            # Cập nhật status bar
            if hasattr(self, 'lb_stt_plc'):
                self.lb_stt_plc.setText(f"PLC: ✅ {ip}")
                self.lb_stt_plc.setStyleSheet("color: green; font-weight: bold; padding-right: 15px")

            # Khởi động luồng polling đọc DB_PUT
            self.plc_polling_thread = PLCPollingThread(self.plc, poll_interval_ms=200)
            self.plc_polling_thread.plc_status_changed.connect(self.on_plc_status_changed)
            self.plc_polling_thread.plc_connection_lost.connect(self.on_plc_connection_lost)
            self.plc_polling_thread.start()
        else:
                QMessageBox.critical(
                    self.main_win, "Lỗi kết nối PLC",
                    f"❌ Không thể kết nối tới PLC!\n\n"
                    f"IP: {ip} | Rack: {rack} | Slot: {slot}\n\n"
                    "📋 Checklist kiểm tra:\n"
                    "  1. PLC đã bật nguồn và ở trạng thái RUN?\n"
                    "  2. IP PLC và PC có cùng subnet?\n"
                    "  3. Đã bật PUT/GET trong TIA Portal?\n"
                    "  4. Nếu dùng PLCSim → đã mở NetToPLCSim?"
                )

    def ngat_ket_noi_plc(self):
        """Xử lý khi nhấn nút Ngắt kết nối PLC."""
        # 1. Dừng luồng polling trước
        if self.plc_polling_thread is not None:
            self.plc_polling_thread.stop()
            self.plc_polling_thread = None

        # 2. Ngắt kết nối PLC
        self.plc.disconnect()

        # 3. Cập nhật status bar
        if hasattr(self, 'lb_stt_plc'):
            self.lb_stt_plc.setText("PLC: ❌ Chưa kết nối")
            self.lb_stt_plc.setStyleSheet("color: gray; padding-right: 15px")
        if hasattr(self, 'lb_stt_mode'):
            self.lb_stt_mode.setText("--")
            self.lb_stt_mode.setStyleSheet("font-weight: bold; padding-right: 15px")
        if hasattr(self, 'lb_stt_sensors'):
            self.lb_stt_sensors.setText("S0:⚫ S1:⚫ S2:⚫")
        if hasattr(self, 'lb_stt_running'):
            self.lb_stt_running.setText("Hệ thống: ⚪")
            self.lb_stt_running.setStyleSheet("color: gray; padding-right: 15px")
        if hasattr(self, 'lb_stt_master'):
            self.lb_stt_master.setText("🔓 UNLOCKED")
            self.lb_stt_master.setStyleSheet("color: gray; padding-right: 15px")

        # Reset khóa truy cập tài khoản khi ngắt kết nối
        self.manual_authenticated = False
        self.ui_main.btControlManual.setStyleSheet(self._STYLE_MASTER_OFF)
        self.ui_main.btControlManual.setText("⚙️ Control Manual")
        self.update_manual_ui()


    def on_plc_status_changed(self, status):
        """Slot nhận signal từ PLCPollingThread khi trạng thái PLC thay đổi."""
        # Đồng bộ giao diện ẩn/hiện nút nhấn dựa vào chế độ vật lý của PLC
        self.update_manual_ui()

        # Cập nhật chế độ Manual/Auto hiển thị (Chỉ đọc từ PLC thôi)
        if hasattr(self, 'lb_stt_mode'):
            if status.get("auto", False):
                self.lb_stt_mode.setText("🟠 AUTO (Vật lý)")
                self.lb_stt_mode.setStyleSheet("color: #FF8C00; font-weight: bold; padding-right: 15px")
                self.lb_stt_mode.setEnabled(True)
            elif status.get("manual", False):
                self.lb_stt_mode.setText("🔵 MANUAL (Vật lý)")
                self.lb_stt_mode.setStyleSheet("color: #0078D7; font-weight: bold; padding-right: 15px")
                self.lb_stt_mode.setEnabled(True)
            else:
                self.lb_stt_mode.setText("--")
                self.lb_stt_mode.setEnabled(False)

        # Cập nhật trạng thái PLC_Running
        if hasattr(self, 'lb_stt_running'):
            if status.get("running", False):
                self.lb_stt_running.setText("Hệ thống: 🟢 RUNNING")
                self.lb_stt_running.setStyleSheet("color: green; font-weight: bold; padding-right: 15px")
            else:
                self.lb_stt_running.setText("Hệ thống: 🔴 STOPPED")
                self.lb_stt_running.setStyleSheet("color: red; font-weight: bold; padding-right: 15px")

        # Cập nhật trạng thái sensor (dùng emoji đèn LED)
        if hasattr(self, 'lb_stt_sensors'):
            s0 = "🟢" if status["trigger_req"] else "⚫"
            s1 = "🟢" if status["sensor1"] else "⚫"
            s2 = "🟢" if status["sensor2"] else "⚫"
            self.lb_stt_sensors.setText(f"S0:{s0} S1:{s1} S2:{s2}")

        # XỬ LÝ TRIGGER TỪ SENSOR S0 (CẢ AUTO LẪN MANUAL)
        # Cạnh lên: S0 phát hiện vỉ mới (False → True)
        if status["trigger_req"] and not getattr(self, '_prev_trigger_req', False):
            print(f"[TRIGGER] 📸 Cảm biến S0 kích hoạt! KQ AI hiện tại: {getattr(self, 'current_result', 'WAIT')}")
            if hasattr(self, 'current_result') and self.current_result != "WAIT":
                # 1. Đóng băng Anhdaxuly + số liệu với kết quả hiện tại
                self.freeze_anhdaxuly()
                # 2. Ghi xuống PLC và đóng dấu DataReady = True
                self.plc.write_result(self.current_result, data_ready=True)
                # 3. Lưu lại lịch sử đo đếm vào Excel/Log
                self.save_current_data()
            else:
                print("[TRIGGER] ⚠️ AI chưa có kết quả (Đang WAIT/Không vỉ), bỏ qua.")

        # Cạnh xuống: PLC đã lấy xong dữ liệu (True → False)
        elif not status["trigger_req"] and getattr(self, '_prev_trigger_req', False):
            print("[TRIGGER] ✅ PLC đã nhận dữ liệu, hạ cờ DataReady về False.")
            self.plc.reset_data_ready()

        # Lưu lại cờ trigger_req cho chu kỳ quét tiếp theo
        self._prev_trigger_req = status.get("trigger_req", False)



    def on_plc_connection_lost(self):
        """Slot nhận signal khi mất kết nối PLC."""
        if hasattr(self, 'lb_stt_plc'):
            self.lb_stt_plc.setText("PLC: ⚠️ Mất kết nối")
            self.lb_stt_plc.setStyleSheet("color: red; font-weight: bold; padding-right: 15px")
        if hasattr(self, 'lb_stt_mode'):
            self.lb_stt_mode.setText("--")
        if hasattr(self, 'lb_stt_sensors'):
            self.lb_stt_sensors.setText("S0:⚫ S1:⚫ S2:⚫")
        if hasattr(self, 'lb_stt_running'):
            self.lb_stt_running.setText("Hệ thống: ⚪")
            self.lb_stt_running.setStyleSheet("color: gray; padding-right: 15px")

    def init_statusbar(self):
        """Khởi tạo các widget trên thanh trạng thái (Status Bar)"""
        # Kiểm tra xem giao diện có statusbar không (thường QMainWindow mặc định có)
        if hasattr(self.ui_main, 'statusbar'):
            # 1. Label Trạng thái hệ thống
            self.lb_stt_system = QtWidgets.QLabel("Hệ thống camera: Sẵn sàng")
            self.lb_stt_system.setStyleSheet("color: black; font-weight: bold; padding-right: 15px")
            self.ui_main.statusbar.addWidget(self.lb_stt_system)
            
            # 2. Label Model đang dùng
            self.lb_stt_model = QtWidgets.QLabel("Model: -- [Chưa nạp]")
            self.lb_stt_model.setStyleSheet("color: blue; padding-right: 15px")
            self.ui_main.statusbar.addWidget(self.lb_stt_model)
            
            # 3. Label Camera Info
            self.lb_stt_cam = QtWidgets.QLabel("Cam: Chưa kết nối")
            self.lb_stt_cam.setStyleSheet("padding-right: 15px")
            self.ui_main.statusbar.addWidget(self.lb_stt_cam)
            
            # 4. Label FPS
            self.lb_stt_fps = QtWidgets.QLabel("FPS: --")
            self.lb_stt_fps.setStyleSheet("color: red; font-weight: bold; padding-right: 15px")
            self.ui_main.statusbar.addWidget(self.lb_stt_fps)

            # 5. Label trạng thái PLC
            self.lb_stt_plc = QtWidgets.QLabel("PLC: ❌ Chưa kết nối")
            self.lb_stt_plc.setStyleSheet("color: gray; padding-right: 15px")
            self.ui_main.statusbar.addWidget(self.lb_stt_plc)

            # 6. Label trạng thái Master (Khóa/Mở khóa phần cứng)
            self.lb_stt_master = QtWidgets.QLabel("🔓 UNLOCKED")
            self.lb_stt_master.setStyleSheet("color: gray; padding-right: 15px")
            self.ui_main.statusbar.addWidget(self.lb_stt_master)

            # 7. Label chế độ Manual/Auto
            self.lb_stt_mode = QtWidgets.QLabel("--")
            self.lb_stt_mode.setStyleSheet("font-weight: bold; padding-right: 15px")
            self.ui_main.statusbar.addWidget(self.lb_stt_mode)

            # 7. Label Trạng thái PLC_Running (Hệ thống sẵn sàng)
            self.lb_stt_running = QtWidgets.QLabel("Hệ thống: ⚪")
            self.lb_stt_running.setStyleSheet("color: gray; padding-right: 15px")
            self.ui_main.statusbar.addWidget(self.lb_stt_running)

            # 8. Label trạng thái Sensor (S0 = TriggerReq, S1, S2)
            self.lb_stt_sensors = QtWidgets.QLabel("S0:⚫ S1:⚫ S2:⚫")
            self.lb_stt_sensors.setStyleSheet("padding-right: 15px")
            self.ui_main.statusbar.addWidget(self.lb_stt_sensors)
            
            # 8. Label Thời gian (Nằm về phía bên phải)
            self.lb_stt_time = QtWidgets.QLabel("--:--:--")
            self.ui_main.statusbar.addPermanentWidget(self.lb_stt_time)
        else:
            print("Lỗi: Không tìm thấy widget 'statusbar' trong Ui_Main!")

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
        camera_source = 0  # Mặc định là webcam laptop

        if loai_camera == "Webcam_1":
            camera_source = 0
        elif loai_camera == "Webcam_2":
            camera_source = 1  # Webcam rời thường có ID là 1
        elif loai_camera == "Camera_custom":
            # Hiện dialog nhập URL HTTP cho camera mạng (DroidCam, IP Webcam, v.v.)
            url, ok = QtWidgets.QInputDialog.getText(
                self.main_win,
                "Kết nối Camera HTTP",
                "Nhập URL stream của camera:\n\n"
                "Ví dụ:\n"
                "  • DroidCam: http://192.168.1.100:4747/video\n"
                "  • IP Webcam: http://192.168.1.100:8080/video\n"
                "  • RTSP: rtsp://192.168.1.100:554/stream",
                QtWidgets.QLineEdit.Normal,
                # Giá trị mặc định gợi ý cho DroidCam
                "http://192.168.1.100:4747/video"
            )
            if not ok or not url.strip():
                # Người dùng nhấn Cancel hoặc không nhập gì
                return
            camera_source = url.strip()

        # Khởi tạo và kết nối các signal
        self.thread_camera = CameraThread(detector=self.detector, camera_source=camera_source)
        self.thread_camera.change_pixmap_signal.connect(self.update_image)
        self.thread_camera.error_signal.connect(self.handle_camera_error)
        
        # Reset trạng thái đóng băng khi kết nối camera mới
        self.has_triggered = False
        
        self.thread_camera.start()
        print(f"Đang thử kết nối tới camera nguồn: {camera_source}")
        
        # Cập nhật status bar
        if hasattr(self, 'lb_stt_system'):
            self.lb_stt_system.setText("Hệ thống camera: 🟢 Đang chạy")
        if hasattr(self, 'lb_stt_cam'):
            # Hiển thị tên ngắn gọn trên status bar
            if loai_camera == "Camera_custom":
                self.lb_stt_cam.setText(f"Cam: HTTP ({camera_source[:30]}...)")
            else:
                self.lb_stt_cam.setText(f"Cam: {loai_camera}")

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

        # Cập nhật status bar
        if hasattr(self, 'lb_stt_system'):
            self.lb_stt_system.setText("Hệ thống camera: 🔴 Ngắt kết nối")
        if hasattr(self, 'lb_stt_fps'):
            self.lb_stt_fps.setText("FPS: --")

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

    def freeze_anhdaxuly(self):
        """
        Đóng băng khung Anhdaxuly + số liệu với kết quả AI hiện tại.
        Gọi khi sensor S0 kích (cả Auto & Manual).
        Sau khi gọi hàm này, update_image() sẽ bỏ qua cập nhật Anhdaxuly.
        """
        # Bật cờ đóng băng — update_image() sẽ không đổi Anhdaxuly nữa
        self.has_triggered = True

        # === CẬP NHẬT HÌNH ẢNH AI MỚI NHẤT LÊN Anhdaxuly ===
        # Sử dụng frame AI mới nhất đã lưu (luôn có sẵn từ update_image)
        if self._latest_processed_frame is not None:
            qt_img_xuly = self.convert_cv_qt(self._latest_processed_frame)
            self.scene_xuly.clear()
            self.scene_xuly.addPixmap(qt_img_xuly)
            self.ui_main.Anhdaxuly.fitInView(
                self.scene_xuly.itemsBoundingRect(), QtCore.Qt.IgnoreAspectRatio
            )

        # Cập nhật số liệu lên UI (đóng băng tại khoảnh khắc này)
        self.ui_main.Tongsovien.setText(str(self.current_total))
        self.ui_main.Viendat.setText(str(self.current_passed))
        self.ui_main.Vienloi.setText(str(self.current_failed))

        # Cập nhật nhãn kết quả hienthiKQ với style tương ứng
        _border = "border: 2px solid #47A3A7; border-radius: 8px;"
        styles = {
            "WAIT":    f"background-color: white;   color: black; {_border}",
            "MISSING": f"background-color: #FF8C00; color: white; {_border}",
            "OK":      f"background-color: #349d00; color: white; {_border}",
            "NG_L":    f"background-color: #FFC300; color: black; {_border}",
            "NG_H":    f"background-color: #CC0000; color: white; {_border}",
        }
        self.ui_main.hienthiKQ.setStyleSheet(styles.get(self.current_result, ""))
        self.ui_main.hienthiKQ.setText(self.current_result)
        self.ui_main.hienthiKQ.setAlignment(QtCore.Qt.AlignCenter)

        print(f"[FREEZE] 🧊 Đóng băng Anhdaxuly: {self.current_result} | "
              f"Tổng: {self.current_total}, Đạt: {self.current_passed}, Lỗi: {self.current_failed}")

    def update_image(self, cv_img_goc, cv_img_xuly, labels, fps):
        """Cập nhật hình ảnh lên giao diện khi có frame mới.
        
        Kiến trúc hiển thị:
        - Anhgoc: LUÔN cập nhật ảnh thô (raw) từ camera — quan sát băng tải real-time
        - Anhdaxuly: Có 2 trạng thái:
          + Trước trigger đầu tiên (has_triggered=False): hiển thị real-time ảnh AI (có bbox)
          + Sau trigger (has_triggered=True): ĐÓNG BĂNG ảnh AI tại khoảnh khắc trigger
        - Số liệu + nhãn kết quả: Đóng băng cùng Anhdaxuly khi có trigger
        """
        # Cập nhật FPS lên status bar (luôn cập nhật)
        if hasattr(self, 'lb_stt_fps'):
            self.lb_stt_fps.setText(f"FPS: {fps:.1f}")

        # === KHUNG 1: Anhgoc — LUÔN CẬP NHẬT ảnh thô (raw, không AI bbox) ===
        qt_img_goc = self.convert_cv_qt(cv_img_goc)
        self.scene_goc.clear()
        self.scene_goc.addPixmap(qt_img_goc)
        self.ui_main.Anhgoc.fitInView(
            self.scene_goc.itemsBoundingRect(), QtCore.Qt.IgnoreAspectRatio
        )

        # === KHUNG 2: Anhdaxuly — CÓ ĐIỀU KIỆN ===
        if not self.has_triggered:
            # Chưa có trigger lần nào → hiển thị ảnh AI real-time (có bounding box)
            qt_img_xuly = self.convert_cv_qt(cv_img_xuly)
            self.scene_xuly.clear()
            self.scene_xuly.addPixmap(qt_img_xuly)
            self.ui_main.Anhdaxuly.fitInView(
                self.scene_xuly.itemsBoundingRect(), QtCore.Qt.IgnoreAspectRatio
            )

            # Cập nhật số liệu + nhãn kết quả real-time (khi chưa đóng băng)
            tong_so  = len(labels)
            vien_dat = sum(1 for lb in labels if lb.strip().lower() == 'full')
            vien_loi = tong_so - vien_dat

            self.ui_main.Tongsovien.setText(str(tong_so))
            self.ui_main.Viendat.setText(str(vien_dat))
            self.ui_main.Vienloi.setText(str(vien_loi))

            # --- 5 MÀU TƯƠNG ỨNG 5 TRẠNG THÁI ---
            _border       = "border: 2px solid #47A3A7; border-radius: 8px;"
            color_wait    = f"background-color: white;   color: black; {_border}"
            color_missing = f"background-color: #FF8C00; color: white; {_border}"
            color_ok      = f"background-color: #349d00; color: white; {_border}"
            color_ng_l    = f"background-color: #FFC300; color: black; {_border}"
            color_ng_h    = f"background-color: #CC0000; color: white; {_border}"

            if tong_so == 0:
                ket_qua = "WAIT"
                self.ui_main.hienthiKQ.setStyleSheet(color_wait)
                self.ui_main.hienthiKQ.setText("WAIT")
            elif tong_so < self.SO_O_KHUON:
                ket_qua = "MISSING"
                self.ui_main.hienthiKQ.setStyleSheet(color_missing)
                self.ui_main.hienthiKQ.setText("MISSING")
            else:
                full_chuan = min(vien_dat, self.SO_O_KHUON)
                if full_chuan == self.SO_O_KHUON:
                    ket_qua = "OK"
                    self.ui_main.hienthiKQ.setStyleSheet(color_ok)
                    self.ui_main.hienthiKQ.setText("OK")
                elif full_chuan > self.SO_O_KHUON // 2:
                    ket_qua = "NG_L"
                    self.ui_main.hienthiKQ.setStyleSheet(color_ng_l)
                    self.ui_main.hienthiKQ.setText("NG_L")
                else:
                    ket_qua = "NG_H"
                    self.ui_main.hienthiKQ.setStyleSheet(color_ng_h)
                    self.ui_main.hienthiKQ.setText("NG_H")
            self.ui_main.hienthiKQ.setAlignment(QtCore.Qt.AlignCenter)
        # Nếu has_triggered = True → Anhdaxuly + số liệu + nhãn giữ nguyên (đóng băng)

        # === LUÔN LƯU FRAME AI MỚI NHẤT (để freeze_anhdaxuly dùng khi trigger) ===
        self._latest_processed_frame = cv_img_xuly.copy()

        # === LUÔN TÍNH NỘI BỘ current_result (để sẵn cho PLC khi trigger tiếp theo) ===
        tong_so  = len(labels)
        vien_dat = sum(1 for lb in labels if lb.strip().lower() == 'full')
        vien_loi = tong_so - vien_dat

        if tong_so == 0:
            ket_qua = "WAIT"
        elif tong_so < self.SO_O_KHUON:
            ket_qua = "MISSING"
        else:
            full_chuan = min(vien_dat, self.SO_O_KHUON)
            if full_chuan == self.SO_O_KHUON:
                ket_qua = "OK"
            elif full_chuan > self.SO_O_KHUON // 2:
                ket_qua = "NG_L"
            else:
                ket_qua = "NG_H"

        # Lưu kết quả nội bộ (luôn cập nhật ngầm, dù UI có đóng băng)
        self.current_total  = tong_so
        self.current_passed = vien_dat
        self.current_failed = vien_loi
        self.current_result = ket_qua

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
        now_str = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        if hasattr(self, 'lb_stt_time'):
            self.lb_stt_time.setText(now_str)

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
    def handle_browse_model(self):
        """Duyệt file hoặc thư mục để chọn model"""
        # Cho phép chọn cả file (.pt, .onnx) và thư mục (OpenVINO)
        msg = QMessageBox(self.main_win)
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
        
        if not path:
            QMessageBox.warning(self.main_win, "Cảnh báo", "Vui lòng chọn đường dẫn model!")
            return

        model_name_hienthi = os.path.basename(path)
        if hasattr(self, 'lb_stt_model'):
             # Tạm thời cập nhật tên, chưa có info mới
             self.lb_stt_model.setText(f"Model: {model_name_hienthi} [Loading...]")

        # 1. Validation định dạng linh hoạt
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
                
                # Cập nhật label status với đầy đủ info
                if hasattr(self, 'lb_stt_model'):
                    model_info = self.detector.get_model_info()
                    self.lb_stt_model.setText(f"Model: {os.path.basename(path)} [{model_info}]")
                    self.lb_stt_model.setStyleSheet("color: #349d00; font-weight: bold; padding-right: 15px")
            else:
                QMessageBox.critical(self.main_win, "Lỗi", "Không thể nạp model. Vui lòng kiểm tra lại file!")
        except Exception as e:
            QMessageBox.critical(self.main_win, "Lỗi hệ thống", f"Phát sinh lỗi khi tải model: {e}")

    def handle_restore_model(self):
        """Ngắt kết nối AI (Xóa model đang nạp)"""
        self.ui_main.duongdanmodel.clear()
        
        # Thực hiện ngắt kết nối model thực tế
        if self.detector:
            self.detector.model = None
            print("Đã ngắt kết nối Model AI (Model set to None).")
        
        if hasattr(self, 'lb_stt_model'):
            self.lb_stt_model.setText("Model: -- [Đã ngắt kết nối]")
            self.lb_stt_model.setStyleSheet("color: red; padding-right: 15px")

    def update_initial_model_status(self):
        """Cập nhật trạng thái model AI lên thanh status bar lúc khởi động"""
        if hasattr(self, 'lb_stt_model'):
            if self.detector and self.detector.model is not None:
                model_info = self.detector.get_model_info()
                # Lấy tên folder hoặc file cuối cùng trong đường dẫn
                model_name = os.path.basename(self.detector.model_path_loaded)
                self.lb_stt_model.setText(f"Model: {model_name} [{model_info}]")
                self.lb_stt_model.setStyleSheet("color: #349d00; font-weight: bold; padding-right: 15px")
            else:
                self.lb_stt_model.setText("Model: -- [Chưa nạp / Lỗi]")
                self.lb_stt_model.setStyleSheet("color: red; padding-right: 15px")

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
