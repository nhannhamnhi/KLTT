# Bảng Dữ Liệu Truyền Thông PC ↔ PLC Qua Snap7

## Tổng quan

- **Thư viện:** `python-snap7`
- **Giao thức:** S7 Communication (ISO on TCP — Port 102)
- **Kiến trúc:** 2 DB tách biệt (Non-Optimized)
  - **DB_GET** (DB1) — PLC lấy dữ liệu từ PC: Python **GHI** (3 bytes)
  - **DB_PUT** (DB2) — PLC gửi dữ liệu lên PC: Python **ĐỌC** (1 byte)

---

## Sơ đồ truyền thông

```
┌──────────────────┐         Snap7 (TCP/IP)         ┌──────────────────┐
│                  │  ══════════════════════════════  │                  │
│   PC (Python)    │  ──── GHI → DB_GET ─────────→   │   PLC Siemens    │
│                  │  ←─── ĐỌC ← DB_PUT ────────   │   (S7-1200/1500) │
│   finish.py      │  ══════════════════════════════  │                  │
│   Class_dataplc  │         Port 102                │  DB_GET + DB_PUT │
└──────────────────┘                                 └──────────────────┘
```

> **Nguyên tắc phân chia (từ góc nhìn PLC):**
> - **DB_GET (DB1):** PLC "lấy" dữ liệu → Python chỉ GHI, PLC chỉ ĐỌC
> - **DB_PUT (DB2):** PLC "đẩy" dữ liệu → PLC chỉ GHI, Python chỉ ĐỌC
> - **GUI (Python)** = Frontend → hiển thị TongSo, VienDat, VienLoi, FPS,...
> - **PLC** = Backend → chỉ nhận kết quả phân loại (OK/NG_L/NG_H) để điều khiển cơ cấu

---

## 1. DB_GET — PC → PLC (Python GHI xuống PLC)

### 1.1 Kết quả kiểm tra AI

| Offset | Tên biến | Kiểu | Giá trị | Chức năng |
|--------|----------|------|---------|-----------|
| 0 | `PC_KetQua` | INT (2 bytes) | 0 = WAIT | Chưa có vỉ → PLC không hành động |
| | | | 1 = OK | Tất cả viên đạt → PLC cho vỉ đi thẳng |
| | | | 2 = NG_L | Lỗi nhẹ / MISSING → PLC kích XL1 đẩy ra tái kiểm |
| | | | 3 = NG_H | Lỗi nặng → PLC kích XL2 đẩy ra loại bỏ |
| 2.0 | `PC_DataReady` | BOOL | TRUE | PC báo: "Kết quả mới sẵn sàng, hãy đọc!" |
| | | | FALSE | PLC đã đọc xong → PC reset |

### 1.2 Điều khiển cơ cấu (Chế độ Manual)

| Offset | Tên biến | Kiểu | Giá trị | Chức năng |
|--------|----------|------|---------|-----------|
| 2.1 | `PC_Conveyor` | BOOL | TRUE/FALSE | Lệnh chạy/dừng băng tải (chỉ dùng ở Manual) |
| 2.2 | `PC_Cylinder1` | BOOL | TRUE/FALSE | Kích/thu xy-lanh 1 — đẩy vỉ NG_L |
| 2.3 | `PC_Cylinder2` | BOOL | TRUE/FALSE | Kích/thu xy-lanh 2 — đẩy vỉ NG_H |

### Bản đồ bộ nhớ DB_GET

```
DB_GET (DB1) — Non-Optimized (3 bytes)
┌─────────┬───────────────┬──────┬──────────────────────────┐
│ Offset  │ Tên           │ Kiểu │ Mô tả                    │
├─────────┼───────────────┼──────┼──────────────────────────┤
│  0 -  1 │ PC_KetQua     │ INT  │ Kết quả AI (0/1/2/3)    │
│  2.0    │ PC_DataReady  │ BOOL │ Có kết quả mới           │
│  2.1    │ PC_Conveyor   │ BOOL │ Lệnh băng tải (Manual)   │
│  2.2    │ PC_Cylinder1  │ BOOL │ Lệnh xy-lanh 1           │
│  2.3    │ PC_Cylinder2  │ BOOL │ Lệnh xy-lanh 2           │
└─────────┴───────────────┴──────┴──────────────────────────┘
```

---

## 2. DB_PUT — PLC → PC (Python ĐỌC từ PLC)

| Offset | Tên biến | Kiểu | Giá trị | Chức năng |
|--------|----------|------|---------|-----------|
| 0.0 | `PLC_Auto` | BOOL | TRUE/FALSE | Kích hoạt chế độ Tự động |
| 0.1 | `PLC_Manual` | BOOL | TRUE/FALSE | Kích hoạt chế độ Thủ công |
| 0.2 | `PLC_Running` | BOOL | TRUE/FALSE | PLC báo hệ thống sẵn sàng / dừng (E-Stop, lỗi) |
| 0.3 | `PLC_TriggerReq` | BOOL | TRUE/FALSE | Sensor 0 phát hiện vỉ → yêu cầu PC chụp (Auto) |
| 0.4 | `PLC_Sensor1` | BOOL | TRUE/FALSE | Sensor 1 — vỉ tới vị trí xy-lanh 1 |
| 0.5 | `PLC_Sensor2` | BOOL | TRUE/FALSE | Sensor 2 — vỉ tới vị trí xy-lanh 2 |

### Bản đồ bộ nhớ DB_PUT

```
DB_PUT (DB2) — Non-Optimized (1 byte)
┌─────────┬───────────────┬──────┬──────────────────────────┐
│ Offset  │ Tên           │ Kiểu │ Mô tả                    │
├─────────┼───────────────┼──────┼──────────────────────────┤
│  0.0    │ PLC_Auto      │ BOOL │ Chế độ Tự động           │
│  0.1    │ PLC_Manual    │ BOOL │ Chế độ Thủ công          │
│  0.2    │ PLC_Running   │ BOOL │ Hệ thống sẵn sàng       │
│  0.3    │ PLC_TriggerReq│ BOOL │ Sensor 0 trigger         │
│  0.4    │ PLC_Sensor1   │ BOOL │ Sensor 1                 │
│  0.5    │ PLC_Sensor2   │ BOOL │ Sensor 2                 │
└─────────┴───────────────┴──────┴──────────────────────────┘
```

---

## 3. Code mẫu đọc/ghi snap7

### 3.1 Ghi kết quả AI xuống PLC (DB_GET)
```python
import snap7
from snap7.util import set_int, set_bool

client = snap7.client.Client()
client.connect('192.168.0.1', 0, 1)  # IP, rack, slot

# Đọc 3 bytes từ DB_GET (vùng PC → PLC)
data = client.db_read(1, 0, 3)

# Ghi kết quả
set_int(data, 0, 1)           # PC_KetQua = 1 (OK)
set_bool(data, 2, 0, True)    # PC_DataReady = TRUE

client.db_write(1, 0, data)
```

### 3.2 Đọc chế độ và cảm biến từ PLC (DB_PUT)
```python
# Đọc 1 byte từ DB_PUT (vùng PLC → PC) — offset bắt đầu từ 0
data = client.db_read(2, 0, 1)

auto      = snap7.util.get_bool(data, 0, 0)  # PLC_Auto
manual    = snap7.util.get_bool(data, 0, 1)  # PLC_Manual
running   = snap7.util.get_bool(data, 0, 2)  # PLC_Running
trigger   = snap7.util.get_bool(data, 0, 3)  # PLC_TriggerReq
sensor1   = snap7.util.get_bool(data, 0, 4)  # PLC_Sensor1
sensor2   = snap7.util.get_bool(data, 0, 5)  # PLC_Sensor2
```

### 3.3 Điều khiển cơ cấu Manual (DB_GET)
```python
# Đọc 1 byte từ offset 2 trong DB_GET (byte chứa DataReady + Conveyor + Cylinders)
data = client.db_read(1, 2, 1)

snap7.util.set_bool(data, 0, 1, True)   # PC_Conveyor = TRUE (chạy băng tải)
snap7.util.set_bool(data, 0, 2, True)   # PC_Cylinder1 = TRUE (đẩy XL1)

client.db_write(1, 2, data)
```

### 3.4 Sử dụng Class PLCConnector (Khuyên dùng)
```python
from Class_dataplc import PLCConnector

plc = PLCConnector()
plc.connect('192.168.0.1', 0, 1)

# Ghi kết quả AI
plc.write_result("OK")         # hoặc plc.write_result(1)

# Đọc trạng thái PLC
status = plc.read_plc_status()
print(status["mode"])          # True = Auto, False = Manual

# Điều khiển Manual
plc.write_conveyor(True)       # Chạy băng tải
plc.write_cylinder1(True)      # Kích xy-lanh 1

# Ngắt kết nối
plc.disconnect()
```

---

## 4. Hướng dẫn Setup TIA Portal

### 4.1 Tạo Project và cấu hình PLC

```
Bước 1: Mở TIA Portal → Create new project
Bước 2: Add new device → Chọn đúng CPU (S7-1200 hoặc S7-1500)
Bước 3: Đặt tên PLC (ví dụ: "PLC_KiemTra")
```

### 4.2 Cấu hình mạng (Ethernet)

```
Bước 1: Vào Device configuration → PROFINET interface
Bước 2: Đặt IP cho PLC:
         - IP Address:      192.168.0.1
         - Subnet Mask:     255.255.255.0
Bước 3: Đảm bảo PC cũng nằm cùng subnet:
         - IP PC:           192.168.0.10 (hoặc bất kỳ .2 → .254)
         - Subnet Mask:     255.255.255.0
```

### 4.3 ⚠️ Tắt bảo vệ truy cập (BẮT BUỘC cho snap7)

Snap7 sử dụng giao thức S7 Communication. Nếu không tắt protection, **kết nối sẽ bị từ chối**.

```
Bước 1: Device configuration → Properties → Protection & Security
Bước 2: Tìm mục "Connection mechanisms" hoặc "Protection"
Bước 3: Tích chọn:
         ☑ Permit access with PUT/GET communication from remote partner
         (Cho phép truy cập PUT/GET từ thiết bị bên ngoài)
```

> **S7-1200:** Properties → General → Protection → ☑ Permit access with PUT/GET
>
> **S7-1500:** Properties → General → Protection & Security → Connection mechanisms → ☑ Permit access with PUT/GET

### 4.4 Tạo Data Block — DB_GET

```
Bước 1: Trong Project tree → PLC → Program blocks
Bước 2: Add new block → Data Block (DB) → Đặt tên: "DB_GET"
Bước 3: ⚠️ QUAN TRỌNG: Bỏ tích "Optimized block access"
         (Click phải DB → Properties → Attributes → bỏ ☑ Optimized block access)
Bước 4: Thêm các biến theo bảng sau:
```

| STT | Tên biến | Data Type | Offset | Ghi chú |
|-----|----------|-----------|--------|---------|
| 1 | PC_KetQua | Int | 0 | Kết quả AI (0=WAIT, 1=OK, 2=NG_L, 3=NG_H) |
| 2 | PC_DataReady | Bool | 2.0 | PC báo có kết quả mới |
| 3 | PC_Conveyor | Bool | 2.1 | Lệnh băng tải (Manual) |
| 4 | PC_Cylinder1 | Bool | 2.2 | Lệnh xy-lanh 1 |
| 5 | PC_Cylinder2 | Bool | 2.3 | Lệnh xy-lanh 2 |

### 4.5 Tạo Data Block — DB_PUT

```
Bước 1: Add new block → Data Block (DB) → Đặt tên: "DB_PUT"
Bước 2: ⚠️ Bỏ tích "Optimized block access" (giống DB_GET)
Bước 3: Thêm các biến theo bảng sau:
```

| STT | Tên biến | Data Type | Offset | Ghi chú |
|-----|----------|-----------|--------|---------|
| 1 | PLC_Auto | Bool | 0.0 | Chế độ Tự động |
| 2 | PLC_Manual | Bool | 0.1 | Chế độ Thủ công |
| 3 | PLC_Running | Bool | 0.2 | Hệ thống sẵn sàng |
| 4 | PLC_TriggerReq| Bool | 0.3 | Sensor 0 trigger (Yêu cầu chụp) |
| 5 | PLC_Sensor1 | Bool | 0.4 | Sensor 1 (Vị trí XL1) |
| 6 | PLC_Sensor2 | Bool | 0.5 | Sensor 2 (Vị trí XL2) |

> ⚠️ **Lưu ý:** Khi bỏ "Optimized block access", TIA Portal sẽ tự tính offset theo thứ tự bạn thêm biến. Kiểm tra cột **Offset** trong DB editor phải khớp với bảng trên.

### 4.6 Download vào PLC

```
Bước 1: Compile project (Ctrl + B) → Kiểm tra không có lỗi
Bước 2: Download to device → Chọn PLC interface
Bước 3: Chờ download hoàn tất → PLC chuyển sang RUN
```

---

## 5. Test bằng PLCSim + NetToPLCSim

### 5.1 Khi nào dùng?

Khi **chưa có PLC thật** — dùng phần mềm mô phỏng để test logic truyền thông.

### 5.2 Các bước setup

```
Bước 1: Trong TIA Portal → Download to device → Start simulation
         → PLCSim tự mở và chạy PLC ảo

Bước 2: Tải và mở NetToPLCSim (tải từ Snap7 SourceForge page)
         → Chọn PLCSIM Instance: S7-1200/1500
         → Đặt IP ảo: 192.168.0.1
         → Nhấn Start Server

Bước 3: Trong Python, kết nối tới IP ảo:
         client.connect('192.168.0.1', 0, 1)

Bước 4: Dùng Watch Table trong TIA Portal để theo dõi dữ liệu:
         → Monitoring → Add Watch Table
         → Thêm các biến DB_GET và DB_PUT
         → Bật Monitor để xem giá trị thay đổi realtime
```

### 5.3 Test nhanh

| Hành động | DB | Kỳ vọng |
|-----------|----|---------| 
| Python ghi `PC_KetQua = 1` | DB_GET | Watch Table hiện giá trị 1 |
| Set `PLC_Mode = TRUE` trong Watch Table | DB_PUT | Python đọc được `mode = True` |
| Set `PLC_TriggerReq = TRUE` trong Watch Table | DB_PUT | Python nhận trigger, xử lý AI |
| Python ghi `PC_Conveyor = TRUE` | DB_GET | Watch Table hiện TRUE |

### 5.4 Mô phỏng cảm biến bằng Watch Table

Vì không có phần cứng thật, bạn **set giá trị thủ công** trong Watch Table:

```
1. Mở Watch Table → thêm biến DB_PUT.PLC_Sensor1
2. Cột "Modify value" → nhập TRUE
3. Nhấn "Modify all" → PLC_Sensor1 = TRUE
4. Xem phản ứng từ Python (GUI cập nhật gợi ý,...)
5. Đặt lại FALSE khi test xong
```
