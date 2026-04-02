# Kế Hoạch Triển Khai: Chế Độ Manual + Auto

---

## 1. Tổng quan hệ thống

### 1.1 Sơ đồ vật lý

```
                      [CAMERA + AI]
                           ↓
  ═══════════════════════════════════════════════════════ BĂNG TẢI ═══
  Vỉ vào →  [Sensor 0]  →       [Sensor 1]    →    [Sensor 2]    → Vỉ OK ra
            (vị trí cam)       (trước XL1)        (trước XL2)
                                    ↓                   ↓
                               [XL1: NG_L]         [XL2: NG_H]
                                    ↓                   ↓
                               Thùng NG_L          Thùng NG_H

   [NÚT VẬT LÝ] ← Chuyển Manual ↔ Auto (nối vào PLC Input)
   [NÚT MASTER]  ← PC khóa cứng nút vật lý qua Snap7
```

### 1.2 Danh sách phần cứng

| STT | Thiết bị | Số lượng | Vai trò |
|-----|----------|----------|---------|
| 1 | Cảm biến quang (Sensor 0) | 1 | Phát hiện vỉ tại vùng camera |
| 2 | Cảm biến quang (Sensor 1) | 1 | Phát hiện vỉ trước xy-lanh 1 |
| 3 | Cảm biến quang (Sensor 2) | 1 | Phát hiện vỉ trước xy-lanh 2 |
| 4 | Xy-lanh 1 (XL1) | 1 | Đẩy sản phẩm NG_L |
| 5 | Xy-lanh 2 (XL2) | 1 | Đẩy sản phẩm NG_H |
| 6 | Băng tải (Conveyor) | 1 | Vận chuyển vỉ thuốc |
| 7 | Nút chuyển chế độ | 1 | Manual ↔ Auto |

### 1.3 Quy tắc phân loại kết quả

| Kết quả AI | Mã PLC | XL1 (NG_L) | XL2 (NG_H) | Hành vi |
|---|---|---|---|---|
| **OK** | 1 | Bỏ qua | Bỏ qua | Vỉ đi thẳng ra cuối băng tải |
| **NG_L** | 2 | **Đẩy ra** | — | Vỉ bị đẩy vào thùng tái kiểm |
| **NG_H** | 3 | Bỏ qua | **Đẩy ra** | Vỉ bị đẩy vào thùng loại bỏ |
| **MISSING** | 2 (=NG_L) | **Đẩy ra** | — | Thiếu viên → tái kiểm như NG_L |
| **WAIT** | 0 | Bỏ qua | Bỏ qua | Không hành động |

---

## 2. Chế Độ MANUAL — Thao tác qua GUI

### 2.1 Khi nào dùng?

| Tình huống | Lý do |
|---|---|
| Chạy máy lần đầu trong ngày | Kiểm tra camera, model AI, ánh sáng trước khi Auto |
| Debug / Xử lý sự cố | Chạy từng bước, tìm lỗi khi Auto gặp vấn đề |
| Demo / Bảo vệ khóa luận | Trình bày từng chức năng rõ ràng cho hội đồng |
| Test mẫu mới | Kiểm tra vài vỉ trước khi chạy tự động hàng loạt |

### 2.2 Luồng vận hành Manual (chi tiết từng bước)

```
┌─────────────────────────────────────────────────────────────────────┐
│  GIAI ĐOẠN 1: KIỂM TRA AI                                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Bước 1: Đặt vỉ thuốc lên băng tải tại vị trí camera              │
│                                                                     │
│  Bước 2: Nhấn [TRIGGER] trên GUI                                   │
│          → Camera đóng băng + AI phân tích                          │
│          → Hiển thị kết quả: OK / NG_L / NG_H / MISSING            │
│          💡 GUI hiện gợi ý: "Nhấn CONTINUE để tiếp tục camera"     │
│                                                                     │
│  Bước 3: Nhấn [CONTINUE] trên GUI                                  │
│          → Camera hoạt động trở lại                                 │
│          💡 GUI hiện gợi ý: "Nhấn CONVEYOR để chạy băng tải"       │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  GIAI ĐOẠN 2: VẬN CHUYỂN TỚI XY-LANH 1                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Bước 4: Nhấn [CONVEYOR] trên GUI                                  │
│          → Băng tải chạy                                            │
│          → Tự động dừng khi Sensor 1 phát hiện vỉ                  │
│                                                                     │
│  Bước 5: Xử lý tại Sensor 1                                        │
│          ┌──────────────────────────────────────────────────┐       │
│          │ Nếu kết quả = NG_L hoặc MISSING:                │       │
│          │   💡 GUI: "Vỉ lỗi nhẹ! Nhấn CYLINDER_1 để đẩy" │       │
│          │   → Nhấn [CYLINDER_1] → XL1 đẩy vỉ ra           │       │
│          │   → Nhấn [CONVEYOR] để tiếp tục                  │       │
│          ├──────────────────────────────────────────────────┤       │
│          │ Nếu kết quả = OK hoặc NG_H:                     │       │
│          │   💡 GUI: "Bỏ qua XL1. Nhấn CONVEYOR tiếp tục"  │       │
│          │   → Nhấn [CONVEYOR] → băng tải chạy tiếp        │       │
│          └──────────────────────────────────────────────────┘       │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  GIAI ĐOẠN 3: VẬN CHUYỂN TỚI XY-LANH 2                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Bước 6: Băng tải dừng khi Sensor 2 phát hiện vỉ                   │
│          ┌──────────────────────────────────────────────────┐       │
│          │ Nếu kết quả = NG_H:                              │       │
│          │   💡 GUI: "Vỉ lỗi nặng! Nhấn CYLINDER_2 để đẩy" │       │
│          │   → Nhấn [CYLINDER_2] → XL2 đẩy vỉ ra           │       │
│          ├──────────────────────────────────────────────────┤       │
│          │ Nếu kết quả = OK:                                │       │
│          │   💡 GUI: "Sản phẩm OK! Nhấn CONVEYOR → hoàn tất"│       │
│          │   → Nhấn [CONVEYOR] → vỉ đi ra cuối băng tải    │       │
│          └──────────────────────────────────────────────────┘       │
│                                                                     │
│  Bước 7: Quay về Bước 1 cho vỉ tiếp theo                           │
│          💡 GUI: "Sẵn sàng! Đặt vỉ mới và nhấn TRIGGER"           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 Tính năng "Gợi ý hành động" trên GUI

Thêm 1 label `lbGoiY` trên giao diện hiển thị hướng dẫn theo ngữ cảnh:

| Thời điểm | Nội dung gợi ý | Màu nền |
|---|---|---|
| Khởi động / Sẵn sàng | "📌 Đặt vỉ vào vị trí → Nhấn TRIGGER" | Xanh dương nhạt |
| Sau TRIGGER | "📌 Xem kết quả → Nhấn CONTINUE" | Xám |
| Sau CONTINUE | "📌 Nhấn CONVEYOR để chạy băng tải" | Xám |
| Sensor 1 + NG_L | "⚠️ Vỉ lỗi nhẹ! Nhấn CYLINDER_1 để đẩy" | Vàng |
| Sensor 1 + OK/NG_H | "📌 Bỏ qua XL1 → Nhấn CONVEYOR tiếp tục" | Xám |
| Sensor 2 + NG_H | "❌ Vỉ lỗi nặng! Nhấn CYLINDER_2 để đẩy" | Đỏ nhạt |
| Sensor 2 + OK | "✅ Sản phẩm OK! Nhấn CONVEYOR để hoàn tất" | Xanh lá nhạt |
| Sau khi xong 1 vỉ | "📌 Sẵn sàng! Đặt vỉ mới và nhấn TRIGGER" | Xanh dương nhạt |

> [!TIP]
> **Giá trị của tính năng gợi ý:**
> - Người vận hành mới không cần nhớ quy trình
> - Demo trước hội đồng trở nên mượt mà, chuyên nghiệp
> - Tránh nhầm lẫn thứ tự thao tác (ví dụ nhấn cylinder sai)

---

## 3. Chế Độ AUTO — Tự động qua PLC

### 3.1 Luồng vận hành Auto

```
┌────────────────────────────────────────────────────────────┐
│  Bước 1: Nhấn nút vật lý → PLC chuyển sang Auto           │
│          → PC nhận tín hiệu → GUI cập nhật "🟠 AUTO"      │
│          → Các nút Manual bị disable                       │
│          → Băng tải chạy liên tục                          │
├────────────────────────────────────────────────────────────┤
│  Bước 2: Sensor 0 phát hiện vỉ vào vùng camera            │
│          → PLC gửi PLC_TriggerReq = TRUE                   │
│          → PC chụp + AI phân tích                          │
│          → PC gửi kết quả (PC_KetQua) xuống PLC           │
│          → PLC lưu kết quả vào hàng đợi FIFO              │
├────────────────────────────────────────────────────────────┤
│  Bước 3: Sensor 1 phát hiện vỉ tới vị trí XL1             │
│          → PLC lấy kết quả từ FIFO                         │
│          → Nếu NG_L (hoặc MISSING) → XL1 đẩy ra           │
│          → Nếu OK hoặc NG_H → bỏ qua                      │
├────────────────────────────────────────────────────────────┤
│  Bước 4: Sensor 2 phát hiện vỉ tới vị trí XL2             │
│          → PLC lấy kết quả từ FIFO                         │
│          → Nếu NG_H → XL2 đẩy ra                          │
│          → Nếu OK → vỉ đi thẳng ra cuối                   │
├────────────────────────────────────────────────────────────┤
│  Lặp lại Bước 2 → 4 liên tục                              │
│  Nhấn nút vật lý → chuyển về Manual                       │
└────────────────────────────────────────────────────────────┘
```

> [!WARNING]
> **Hàng đợi FIFO trên PLC là bắt buộc** vì trên băng tải có thể có nhiều vỉ cùng lúc. Vỉ đang ở camera và vỉ đang ở sensor là **2 vỉ khác nhau**. PLC phải nhớ kết quả theo đúng thứ tự.

---

## 4. Dữ liệu trao đổi PC ↔ PLC

> **Nguyên tắc:** GUI (Python) = Frontend hiển thị chi tiết (TongSo, VienDat, VienLoi, FPS...). PLC = Backend chỉ nhận **kết quả phân loại** để điều khiển cơ cấu.
>
> **Kiến trúc 2 DB tách biệt (từ góc nhìn PLC):**
> - **DB_GET** (DB1) — PLC "lấy" dữ liệu từ PC → Python GHI (3 bytes)
> - **DB_PUT** (DB2) — PLC "đẩy" dữ liệu lên PC → Python ĐỌC (1 byte)

Chi tiết đầy đủ tham khảo tại [Snap7_DataMap.md](file:///d:/KL_2025/KLTT/Snap7_DataMap.md)

#### DB_GET — PC → PLC (Python ghi)

| Offset | Tên | Kiểu | Giá trị |
|--------|-----|------|---------|
| 0 | `PC_KetQua` | INT | 0=WAIT, 1=OK, 2=NG_L, 3=NG_H |
| 2.0 | `PC_DataReady` | BOOL | Có kết quả mới để PLC đọc |
| 2.1 | `PC_Conveyor` | BOOL | Lệnh chạy băng tải (Manual) |
| 2.2 | `PC_Cylinder1` | BOOL | Lệnh kích XL1 (Manual) |
| 2.3 | `PC_Cylinder2` | BOOL | Lệnh kích XL2 (Manual) |
| 2.4 | `PC_Auto` | BOOL | Chế độ Auto |
| 2.5 | `PC_Man` | BOOL | Chế độ Manual |
| **2.6** | **`PC_Master`** | **BOOL** | **Khóa phần cứng (PC Master)** |

#### DB_PUT — PLC → PC (Python đọc)

| Offset | Tên | Kiểu | Mô tả |
|--------|-----|------|-------|
| 0.0 | `PLC_Mode` | BOOL | FALSE=Manual, TRUE=Auto |
| 0.1 | `PLC_Running` | BOOL | Hệ thống sẵn sàng |
| 0.2 | `PLC_TriggerReq` | BOOL | Sensor 0 — yêu cầu chụp (Auto) |
| 0.3 | `PLC_Sensor1` | BOOL | Sensor 1 tác động |
| 0.4 | `PLC_Sensor2` | BOOL | Sensor 2 tác động |

---

## 5. Thay đổi giao diện GUI

### 5.1 Widget mới

| Widget | Loại | Chức năng |
|--------|------|-----------|
| `btMaster` | QPushButton | **Khóa phần cứng (Toggle)** — BẬT: hiện Auto/Man, TẮT: ẩn tất cả |
| `btConveyor` | QPushButton | Điều khiển băng tải (Manual) |
| `btCylinder1` | QPushButton | Kích xy-lanh 1 — NG_L (Manual) |
| `btCylinder2` | QPushButton | Kích xy-lanh 2 — NG_H (Manual) |
| `lbGoiY` | QLabel | Hiển thị gợi ý hành động theo ngữ cảnh |

### 5.2 Status bar bổ sung

| Widget | Nội dung mẫu |
|--------|-------------|
| `lb_stt_plc` | **"PLC: ✅ 192.168.0.1"** hoặc **"PLC: ❌ Chưa kết nối"** |
| `lb_stt_mode` | **"🔵 MANUAL"** hoặc **"🟠 AUTO"** |
| `lb_stt_sensors` | **"S0:🟢 S1:⚫ S2:⚫"** |

### 5.3 Enable/Disable theo chế độ

| Widget | Master OFF | Master ON + Auto | Master ON + Manual |
|--------|-----------|-----------------|--------------------|
| btMaster | ✅ Hiện | ✅ Hiện | ✅ Hiện |
| btAuto | ❌ Ẩn | ✅ Hiện | ✅ Hiện |
| btManual | ❌ Ẩn | ✅ Hiện | ✅ Hiện |
| btTrigger | ❌ Ẩn | ❌ Ẩn | ✅ Hiện |
| btContinue | ❌ Ẩn | ❌ Ẩn | ✅ Hiện |
| btConveyor | ❌ Ẩn | ❌ Ẩn | ✅ Hiện |
| btCylinder1 | ❌ Ẩn | ❌ Ẩn | ✅ Hiện |
| btCylinder2 | ❌ Ẩn | ❌ Ẩn | ✅ Hiện |
| Camera | Chạy | Chạy | Chạy |
| hienthiKQ | Hiện kết quả | Hiện kết quả | Hiện kết quả |

---

## 6. Test bằng PLCSim + NetToPLCSim

> [!NOTE]
> **Hoàn toàn sử dụng được để test!**
> 1. **PLCSim** mô phỏng PLC S7-1200/1500 trên máy tính
> 2. **NetToPLCSim** tạo cầu nối mạng ảo cho phép snap7 kết nối qua TCP/IP
> 3. Logic đọc/ghi DB **100% giống PLC thật**
>
> **Hạn chế duy nhất:** Không test được timing thực tế của cảm biến/xy-lanh vật lý (nhưng logic điều khiển chính xác hoàn toàn).

---

## 7. Danh sách file cần thay đổi

### [NEW] [Class_dataplc.py](file:///d:/KL_2025/KLTT/File_MainProgram/Class_dataplc.py)
- Class `PLCConnector` quản lý kết nối snap7
- QThread polling đọc PLC mỗi 200ms
- Hàm `write_result()`, `read_plc_status()`
- Hàm `write_conveyor()`, `write_cylinder1()`, `write_cylinder2()`

### [MODIFY] [finish.py](file:///d:/KL_2025/KLTT/File_MainProgram/finish.py)
- Import `PLCConnector`, `PLCPollingThread`
- Kết nối nút `btKetnoiplc`, `btNgatketnoiplc`, `CPU_PLC`
- Thêm `lb_stt_plc`, `lb_stt_mode`, `lb_stt_sensors` vào status bar
- Auto-fill Rack/Slot khi chọn CPU
- Validate IP, thông báo lỗi chi tiết

### [MODIFY] Main.ui → Main.py
- Thêm 3 nút: `btConveyor`, `btCylinder1`, `btCylinder2`
- Thêm label: `lbGoiY`
