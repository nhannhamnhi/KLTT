<!-- ⚠️ SYSTEM NOTICE FOR AI AGENTS: Khi chỉnh sửa logic hệ thống / luồng PLC / GUI, bắt buộc cập nhật file này. -->

# QUY TRÌNH VẬN HÀNH CHI TIẾT

Tài liệu này mô tả luồng dữ liệu (Data Flow) và cách hệ thống cơ điện tử phối hợp với AI để vận hành dây chuyền.

> ⚡ Hướng dẫn cài đặt & UI cơ bản: [docs/caidat.md](caidat.md) | [docs/huongdanUI.md](huongdanUI.md)

---

## 1. CHẾ ĐỘ HOẠT ĐỘNG

### 🔒 Kích hoạt Điều khiển Thủ công (Control Manual)
Bảo mật 2 lớp:
1. **Phần mềm:** Nhấn **"⚙️ Control Manual"** → nhập `admin` / `123`.
2. **Phần cứng:** Xoay công tắc vật lý trên tủ PLC sang Manual → `PLC_Manual = TRUE`.

Chỉ khi đủ cả 2 điều kiện, các nút thủ công mới hiện: Trigger, Continue, ON/OFF Conveyor, Cylinder 1/2.

### 🟢 Chế độ Tự Động (AUTO)
```
Bước 1: Băng tải đưa vỉ thuốc vào buồng chụp
Bước 2: Sensor S0 → PLC_TriggerReq = TRUE
Bước 3: PC đóng băng frame → AI phân tích (Full/Partial/Empty)
Bước 4: Ghi PC_KetQua (1=OK, 2=NG_L, 3=NG_H, 4=MISSING)
Bước 5: PC_DataReady = TRUE → PLC thực thi xylanh → hạ S0
```

### 🔵 Chế độ Thủ Công (MANUAL)
- **Conveyor:** Nhấn giữ để chạy, nhả để dừng.
- **Cylinder 1/2:** Nhấn giữ đẩy ra, nhả thu về.
- **Trigger:** Chụp & AI phân tích ngay (không chờ PLC).
- **Continue:** Trở lại live stream.

---

## 2. BẢN ĐỒ DỮ LIỆU PLC (Data Mapping)

Cấu hình trong `src/plc/Class_dataplc.py`.

### DB_GET (PC → PLC) — DB1, 3 bytes

| Offset | Kiểu | Tên | Mô tả |
|--------|------|-----|-------|
| 0.0 | INT | `PC_KetQua` | 0=WAIT, 1=OK, 2=NG_L, 3=NG_H, 4=MISSING |
| 2.0 | BOOL | `PC_DataReady` | PC đã có kết quả mới |
| 2.1 | BOOL | `PC_Conveyor` | Lệnh băng tải (Manual) |
| 2.2 | BOOL | `PC_Cylinder1` | Kích xylanh 1 (NG_L) |
| 2.3 | BOOL | `PC_Cylinder2` | Kích xylanh 2 (NG_H) |

### DB_PUT (PLC → PC) — DB2, 1 byte

| Offset | Kiểu | Tên | Mô tả |
|--------|------|-----|-------|
| 0.0 | BOOL | `PLC_Auto` | Chế độ Auto |
| 0.1 | BOOL | `PLC_Manual` | Chế độ Manual |
| 0.2 | BOOL | `PLC_Running` | Hệ thống sẵn sàng |
| 0.3 | BOOL | `PLC_TriggerReq` | Sensor S0 phát hiện vỉ |
| 0.4 | BOOL | `PLC_Sensor1` | Sensor S1 (vị trí xylanh 1) |
| 0.5 | BOOL | `PLC_Sensor2` | Sensor S2 (vị trí xylanh 2) |

**Yêu cầu TIA Portal:**
- Bật **Permit access with PUT/GET** (Protection & Security).
- Tắt **Optimized block access** trên DB1 và DB2.

### Chỉnh sửa DB
1. Sửa hằng số `DB_GET_SIZE` / `DB_PUT_SIZE` trong `Class_dataplc.py`.
2. Thêm logic đọc/ghi bằng `get_bool`, `set_bool`, `get_int`, `set_int`.
3. Kiểm tra: `python src/plc/Class_dataplc.py`

---

## 3. LOGGING & BÁO CÁO
Mọi kết quả (Auto hay Manual) đều được:
1. Ghi vào bảng danh sách real-time trên UI.
2. Lưu vào `data_history.json` + đồng bộ Google Sheets.
3. Xuất Excel (.xlsx) từ DataViewerDialog.

📖 Chi tiết đồng bộ: [docs/DongBoGoogleSheets.md](DongBoGoogleSheets.md)
📖 Chi tiết xuất Excel: [docs/huongdanUI.md](huongdanUI.md)

---
📅 *Cập nhật: tự động theo Git.*
