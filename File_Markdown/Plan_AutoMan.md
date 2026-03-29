# Kế Hoạch: Giao Diện Điều Khiển Auto / Manual

## Mô tả

Hiện tại chương trình chưa có cơ chế chọn chế độ Auto/Manual từ phía PC. Cần thêm:
- 2 biến mới `PC_Auto`, `PC_Man` trong DB_GET để PC **thông báo** cho PLC biết người dùng đã chọn chế độ nào
- Giao diện cho phép chọn chế độ khi vừa mở chương trình
- Chế độ **Auto**: ẩn các nút điều khiển thủ công
- Chế độ **Man**: hiện các nút Trigger, Continue, Conveyor, Cylinder1, Cylinder2

---

## 1. Thay đổi DB Mapping

### DB_GET — PC → PLC (mở rộng từ 3 → 4 bytes)

| Offset | Tên | Kiểu | Mô tả | Trạng thái |
|--------|-----|------|-------|------------|
| 0-1 | `PC_KetQua` | INT | Kết quả AI (0/1/2/3) | **Giữ nguyên** |
| 2.0 | `PC_DataReady` | BOOL | Có kết quả mới | **Giữ nguyên** |
| 2.1 | `PC_Conveyor` | BOOL | Lệnh băng tải | **Giữ nguyên** |
| 2.2 | `PC_Cylinder1` | BOOL | Lệnh xy-lanh 1 | **Giữ nguyên** |
| 2.3 | `PC_Cylinder2` | BOOL | Lệnh xy-lanh 2 | **Giữ nguyên** |
| 2.4 | `PC_Auto` | BOOL | PC chọn chế độ Auto | 🆕 **MỚI** |
| 2.5 | `PC_Man` | BOOL | PC chọn chế độ Manual | 🆕 **MỚI** |

```
DB_GET (DB1) — Non-Optimized (3 bytes, bổ sung bit)
┌─────────┬───────────────┬──────┬──────────────────────────┐
│ Offset  │ Tên           │ Kiểu │ Mô tả                    │
├─────────┼───────────────┼──────┼──────────────────────────┤
│  0 -  1 │ PC_KetQua     │ INT  │ Kết quả AI (0/1/2/3)    │
│  2.0    │ PC_DataReady  │ BOOL │ Có kết quả mới           │
│  2.1    │ PC_Conveyor   │ BOOL │ Lệnh băng tải (Manual)   │
│  2.2    │ PC_Cylinder1  │ BOOL │ Lệnh xy-lanh 1           │
│  2.3    │ PC_Cylinder2  │ BOOL │ Lệnh xy-lanh 2           │
│  2.4    │ PC_Auto       │ BOOL │ 🆕 PC chọn Auto          │
│  2.5    │ PC_Man        │ BOOL │ 🆕 PC chọn Manual        │
└─────────┴───────────────┴──────┴──────────────────────────┘
```

---

## 2. Chi tiết thực hiện

### Class_dataplc.py (Backend PLC)
- Đã thêm hàm `write_mode_auto()` ghi Offset 2.4=True, 2.5=False
- Đã thêm hàm `write_mode_manual()` ghi Offset 2.4=False, 2.5=True

### Main.py (GUI Layout - Đã hiện thực thông qua code Python)
Chèn thủ công các đối tượng như Nút chọn chế độ, xuất excel, trigger, continue, điều khiển xy lanh, v.v...

### finish.py (Logic chính)
- Xử lý các logic Enable/Disable (ẩn hiện các nút) tùy theo chế độ đang chọn (Auto hay Manual).
- Thực thi ghi lệnh toggle xuống PLC do các nút cơ cấu điều khiển (Conveyor, Cylinder).
- Cập nhật dòng chữ cảnh báo ngữ cảnh (`lbGoiY`).

---

**Xác nhận thiết lập:**
- Nút tác động kiểu **Toggle**.
- Chế độ Auto/Manual độc lập hoàn toàn với việc lấy mẫu tự động bằng Camera.
- Nút xuất Excel phục vụ mọi lúc.
