import snap7
from snap7.util import get_bool, set_bool, get_int, set_int
from PyQt5 import QtCore
import time


# ================================================================
# HẰNG SỐ CẤU HÌNH — Khớp với Snap7_DataMap.md
# ================================================================

# --- Số hiệu DB (đặt trong TIA Portal) ---
# DB_GET: PLC "lấy" dữ liệu từ PC → Python GHI xuống (3 bytes)
DB_GET = 1
DB_GET_SIZE = 3  # bytes (offset 0 → 2)

# DB_PUT: PLC "đẩy" dữ liệu lên PC → Python ĐỌC lên (1 byte)
DB_PUT = 2
DB_PUT_SIZE = 1  # bytes (offset 0 → 0)

# --- Mã kết quả AI (ghi vào PC_KetQua — INT 2 bytes) ---
RESULT_WAIT = 0   # Chưa có vỉ → PLC không hành động
RESULT_OK   = 1   # Tất cả viên đạt → PLC cho vỉ đi thẳng
RESULT_NG_L = 2   # Lỗi nhẹ / MISSING → PLC kích XL1
RESULT_NG_H = 3   # Lỗi nặng → PLC kích XL2

# --- Mapping tên kết quả → mã số (tiện cho finish.py gọi) ---
RESULT_MAP = {
    "WAIT": RESULT_WAIT,
    "OK":   RESULT_OK,
    "NG_L": RESULT_NG_L,
    "MISSING": RESULT_NG_L,  # MISSING xử lý giống NG_L
    "NG_H": RESULT_NG_H,
}

# --- Cấu hình kết nối mặc định ---
DEFAULT_PLC_IP   = "192.168.0.1"
DEFAULT_PLC_RACK = 0
DEFAULT_PLC_SLOT = 1


# ================================================================
# CLASS CHÍNH: PLCConnector
# Quản lý kết nối và đọc/ghi dữ liệu PLC qua Snap7
# ================================================================
class PLCConnector:
    """
    Quản lý toàn bộ kết nối và truyền nhận dữ liệu với PLC Siemens
    qua thư viện python-snap7.

    Kiến trúc 2 DB tách biệt:
    - DB_GET (DB1): PC GHI xuống → PLC đọc (kết quả AI + lệnh Manual)
    - DB_PUT (DB2): PLC GHI lên → PC đọc (trạng thái + sensor)
    """

    def __init__(self):
        self.client = snap7.client.Client()
        self._connected = False

    # ────────────────────────────────────────────
    # KẾT NỐI
    # ────────────────────────────────────────────
    def connect(self, ip=DEFAULT_PLC_IP, rack=DEFAULT_PLC_RACK, slot=DEFAULT_PLC_SLOT):
        """
        Kết nối tới PLC qua TCP/IP (cổng 102).
        Trả về True nếu thành công, False nếu thất bại.
        """
        try:
            self.client.connect(ip, rack, slot)
            self._connected = self.client.get_connected()
            if self._connected:
                print(f"[PLC] ✅ Kết nối thành công tới {ip} (rack={rack}, slot={slot})")
            return self._connected
        except Exception as e:
            self._connected = False
            print(f"[PLC] ❌ Lỗi kết nối: {e}")
            return False

    def disconnect(self):
        """Ngắt kết nối PLC an toàn."""
        try:
            if self._connected:
                self.client.disconnect()
                print("[PLC] 🔌 Đã ngắt kết nối PLC.")
        except Exception as e:
            print(f"[PLC] ⚠️ Lỗi khi ngắt kết nối: {e}")
        finally:
            self._connected = False

    @property
    def is_connected(self):
        """Kiểm tra trạng thái kết nối hiện tại (có verify lại với PLC)."""
        if self._connected:
            try:
                self._connected = self.client.get_connected()
            except Exception:
                self._connected = False
        return self._connected

    def get_cpu_family(self):
        """
        Đọc order code từ PLC để xác định dòng CPU thực tế.

        Mapping prefix mã order → dòng CPU Siemens:
            6ES7 2xx → S7-1200 (hoặc S7-200, nhưng S7-200 dùng giao thức khác)
            6ES7 5xx → S7-1500
            6ES7 3xx → S7-300
            6ES7 4xx → S7-400

        Trả về:
            str: Tên dòng CPU (VD: "S7-1200") hoặc None nếu không xác định được.
        """
        if not self.is_connected:
            return None

        # Mapping: ký tự thứ 5 trong order code → dòng CPU
        prefix_map = {
            "2": "S7-1200",
            "5": "S7-1500",
            "4": "S7-400",
        }

        try:
            order_code_obj = self.client.get_order_code()
            # Order code trả về dạng bytes, VD: b'6ES7 214-1AG40-0XB0'
            code_str = order_code_obj.OrderCode.decode('utf-8').strip().rstrip('\x00')
            print(f"[PLC] 📋 Order Code đọc được: {code_str}")

            # Tìm ký tự đầu tiên sau "6ES7 " (vị trí thứ 5) để xác định dòng
            # Format chuẩn: "6ES7 Xxx-xxxx-xxxx"
            if len(code_str) >= 6 and code_str.startswith("6ES7"):
                # Ký tự xác định dòng CPU nằm ngay sau "6ES7 " (hoặc "6ES7")
                # Loại bỏ khoảng trắng nếu có
                family_char = code_str.replace(" ", "")[4]  # "6ES7" + ký tự thứ 5
                cpu_family = prefix_map.get(family_char, None)
                if cpu_family:
                    print(f"[PLC] ✅ Xác định dòng CPU: {cpu_family}")
                    return cpu_family
                else:
                    print(f"[PLC] ⚠️ Không nhận diện được dòng CPU từ prefix '{family_char}'")
                    return None
            else:
                print(f"[PLC] ⚠️ Order code không đúng định dạng Siemens: {code_str}")
                return None

        except Exception as e:
            print(f"[PLC] ⚠️ Không thể đọc order code: {e}")
            return None

    # ────────────────────────────────────────────
    # GHI DỮ LIỆU XUỐNG PLC (DB_GET — PC → PLC)
    # ────────────────────────────────────────────
    def write_result(self, result_code, data_ready=True):
        """
        Ghi kết quả phân loại AI xuống PLC.

        Tham số:
            result_code (int hoặc str): Mã kết quả (0-3) hoặc tên ("OK", "NG_L",...)
            data_ready (bool): Cờ báo PLC có kết quả mới cần đọc

        Ví dụ:
            write_result("OK")          → PC_KetQua=1, PC_DataReady=TRUE
            write_result(RESULT_NG_H)   → PC_KetQua=3, PC_DataReady=TRUE
        """
        if not self.is_connected:
            print("[PLC] ⚠️ Chưa kết nối PLC, không thể ghi kết quả.")
            return False

        # Nếu truyền vào tên (str), chuyển sang mã số
        if isinstance(result_code, str):
            result_code = RESULT_MAP.get(result_code.upper(), RESULT_WAIT)

        try:
            # Đọc toàn bộ DB_GET (3 bytes) → sửa → ghi lại
            data = self.client.db_read(DB_GET, 0, DB_GET_SIZE)
            set_int(data, 0, result_code)       # Offset 0-1: PC_KetQua
            set_bool(data, 2, 0, data_ready)    # Offset 2.0: PC_DataReady
            self.client.db_write(DB_GET, 0, data)
            print(f"[PLC] 📤 Ghi kết quả: KetQua={result_code}, DataReady={data_ready}")
            return True
        except Exception as e:
            print(f"[PLC] ❌ Lỗi ghi kết quả: {e}")
            self._connected = False
            return False

    def reset_data_ready(self):
        """Reset cờ PC_DataReady = FALSE sau khi PLC đã đọc xong."""
        if not self.is_connected:
            return False
        try:
            data = self.client.db_read(DB_GET, 2, 1)
            set_bool(data, 0, 0, False)  # Offset 2.0: PC_DataReady = FALSE
            self.client.db_write(DB_GET, 2, data)
            return True
        except Exception as e:
            print(f"[PLC] ❌ Lỗi reset DataReady: {e}")
            self._connected = False
            return False

    def write_conveyor(self, state):
        """
        Bật/tắt băng tải (chỉ dùng ở chế độ Manual).
        state (bool): True = chạy, False = dừng
        """
        return self._write_bool_db_get(2, 1, state, "Conveyor")

    def write_cylinder1(self, state):
        """
        Kích/thu xy-lanh 1 — đẩy vỉ NG_L (chỉ dùng ở chế độ Manual).
        state (bool): True = kích, False = thu
        """
        return self._write_bool_db_get(2, 2, state, "Cylinder1")

    def write_cylinder2(self, state):
        """
        Kích/thu xy-lanh 2 — đẩy vỉ NG_H (chỉ dùng ở chế độ Manual).
        state (bool): True = kích, False = thu
        """
        return self._write_bool_db_get(2, 3, state, "Cylinder2")

    def _write_bool_db_get(self, byte_offset, bit_offset, value, name=""):
        """
        Hàm nội bộ: Ghi 1 bit BOOL vào DB_GET.
        Đọc nguyên byte → sửa bit → ghi lại (tránh ghi đè bit khác cùng byte).
        """
        if not self.is_connected:
            print(f"[PLC] ⚠️ Chưa kết nối PLC, không thể ghi {name}.")
            return False
        try:
            data = self.client.db_read(DB_GET, byte_offset, 1)
            set_bool(data, 0, bit_offset, value)
            self.client.db_write(DB_GET, byte_offset, data)
            print(f"[PLC] 📤 Ghi {name} = {value}")
            return True
        except Exception as e:
            print(f"[PLC] ❌ Lỗi ghi {name}: {e}")
            self._connected = False
            return False

    # ────────────────────────────────────────────
    # ĐỌC DỮ LIỆU TỪ PLC (DB_PUT — PLC → PC)
    # ────────────────────────────────────────────
    def read_plc_status(self):
        """
        Đọc toàn bộ trạng thái từ DB_PUT (1 byte, offset 0.0 → 0.4).

        Trả về dict:
            {
                "auto":        bool,  # TRUE=Auto active
                "manual":      bool,  # TRUE=Manual active
                "running":     bool,  # Hệ thống sẵn sàng
                "trigger_req": bool,  # Sensor 0 yêu cầu chụp (Auto)
                "sensor1":     bool,  # Sensor 1 — vị trí xy-lanh 1
                "sensor2":     bool,  # Sensor 2 — vị trí xy-lanh 2
            }

        Trả về None nếu đọc thất bại.
        """
        if not self.is_connected:
            return None
        try:
            data = self.client.db_read(DB_PUT, 0, DB_PUT_SIZE)
            status = {
                "auto":        get_bool(data, 0, 0),  # Offset 0.0: PLC_Auto
                "manual":      get_bool(data, 0, 1),  # Offset 0.1: PLC_Manual
                "running":     get_bool(data, 0, 2),  # Offset 0.2: PLC_Running
                "trigger_req": get_bool(data, 0, 3),  # Offset 0.3: PLC_TriggerReq
                "sensor1":     get_bool(data, 0, 4),  # Offset 0.4: PLC_Sensor1
                "sensor2":     get_bool(data, 0, 5),  # Offset 0.5: PLC_Sensor2
            }
            return status
        except Exception as e:
            print(f"[PLC] ❌ Lỗi đọc trạng thái PLC: {e}")
            self._connected = False
            return None


# ================================================================
# LUỒNG POLLING: PLCPollingThread
# Quét DB_PUT liên tục mỗi 200ms để cập nhật trạng thái PLC
# ================================================================
class PLCPollingThread(QtCore.QThread):
    """
    QThread chạy nền, liên tục đọc DB_PUT từ PLC.
    Phát signal khi trạng thái thay đổi hoặc mất kết nối.
    """

    # Signal phát khi trạng thái PLC thay đổi (gửi dict trạng thái)
    plc_status_changed = QtCore.pyqtSignal(dict)

    # Signal phát khi mất kết nối PLC
    plc_connection_lost = QtCore.pyqtSignal()

    def __init__(self, plc_connector, poll_interval_ms=200):
        """
        Tham số:
            plc_connector (PLCConnector): Đối tượng kết nối PLC đã tạo sẵn
            poll_interval_ms (int): Chu kỳ quét (mặc định 200ms)
        """
        super().__init__()
        self.plc = plc_connector
        self.poll_interval_ms = poll_interval_ms
        self._run_flag = True

        # ================================================================
        # THAY ĐỔI: Mặc định ban đầu là AUTO (True)
        # ================================================================
        self._prev_status = {
            "auto":        True,  # Mặc định là Auto khi chưa có dữ liệu mới
            "manual":      False,
            "running":     False,
            "trigger_req": False,
            "sensor1":     False,
            "sensor2":     False,
        }

    def run(self):
        """Vòng lặp chính: đọc DB_PUT liên tục."""
        print(f"[PLC Polling] 🚀 Bắt đầu quét PLC mỗi {self.poll_interval_ms}ms")

        while self._run_flag:
            if not self.plc.is_connected:
                # Mất kết nối → phát signal và chờ thử lại
                self.plc_connection_lost.emit()
                self.msleep(1000)  # Chờ 1 giây trước khi thử lại
                continue

            status = self.plc.read_plc_status()

            if status is None:
                # Đọc thất bại → có thể mất kết nối
                self.plc_connection_lost.emit()
                self.msleep(1000)
                continue

            # ================================================================
            # THAY ĐỔI: Nếu các biến dữ liệu (sensor/trigger) thay đổi, 
            # tự động chuyển mode sang MANUAL (False)
            # ================================================================
            data_changed = (
                status["trigger_req"] != self._prev_status["trigger_req"] or
                status["sensor1"]     != self._prev_status["sensor1"]     or
                status["sensor2"]     != self._prev_status["sensor2"]
            )

            if data_changed:
                status["auto"]   = False  # Ngắt Auto
                status["manual"] = True   # Chuyển sang Manual khi có biến dữ liệu thay đổi
                print("[PLC Polling] ⚠️ Dữ liệu thay đổi -> Tự động chuyển MANUAL")

            # Chỉ phát signal khi trạng thái có sự khác biệt so với lần quét trước
            if status != self._prev_status:
                self._prev_status = status.copy()
                self.plc_status_changed.emit(status)

            self.msleep(self.poll_interval_ms)

        print("[PLC Polling] 🛑 Đã dừng quét PLC.")

    def stop(self):
        """Dừng luồng polling an toàn."""
        self._run_flag = False
        self.wait()
