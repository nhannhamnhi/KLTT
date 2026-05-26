# Hướng Dẫn Sử Dụng Giao Diện (UI)

Tài liệu hướng dẫn chi tiết từng khu vực trên giao diện chính.

---

## 1. Tổng quan giao diện

Sau khi đăng nhập (admin / 123), giao diện Main UI gồm các khu vực:

`
┌──────────────────────────────────────────────────────┐
│  [Camera]   [AI Display]   [PLC Status]   [Data]    │
│  ┌───────┐  ┌──────────┐  ┌──────────┐  ┌──────┐   │
│  │Webcam │  │Raw  → AI │  │IP / Rack │  │List  │   │
│  │select │  │side-by-  │  │Auto/Man  │  │result│   │
│  │Kết nối│  │side      │  │S0 S1 S2  │  │charts│   │
│  └───────┘  └──────────┘  └──────────┘  └──────┘   │
│  [Bright/Sat]          [Model AI]  [Data Viewer]    │
└──────────────────────────────────────────────────────┘
`

---

## 2. Khu vực Camera

| Thành phần | Mô tả |
|---|---|
| Combobox Webcam_1 / Webcam_2 | Chọn camera ID (0 hoặc 1) |
| Camera_custom | Nhập URL stream (RTSP/HTTP) nếu chọn custom |
| Nút Kết nối / Ngắt kết nối | Bật/tắt luồng video |
| Slider Độ sáng (-100 → +100) | Điều chỉnh brightness |
| Slider Độ bão hòa (-100 → +100) | Điều chỉnh saturation |
| Nút Reset | Đưa slider về 0 |

**Thao tác:**
1. Chọn camera → Kết nối → thấy khung hình
2. Kéo slider sáng/bão hòa cho đến khi ảnh rõ nhất

---

## 3. Khu vực AI Display

Hiển thị song song 2 khung hình:
- **Raw**: ảnh gốc từ camera
- **AI**: ảnh đã vẽ khung OBB + nhãn Full/Partial/Empty

Phía dưới hiển thị:
- **Trạng thái vỉ**: WAIT / MISSING / OK / NG_L / NG_H (kèm màu nền)
- **Đếm**: Tổng số viên, số đạt, số lỗi

---

## 4. Khu vực PLC

| Thành phần | Mô tả |
|---|---|
| Combobox CPU_PLC | S7-1200 / S7-1500 / S7-400 |
| IP | Địa chỉ IP của PLC |
| Rack / Slot | Tự động fill khi chọn CPU |
| Nút Kết nối PLC | Kết nối Snap7 |
| Nút Control Manual | Xác thực 2 lớp để vào chế độ Manual |

**Trạng thái hiển thị:**
- AUTO / MANUAL (chế độ hiện tại)
- S0/S1/S2 (cảm biến)
- RUN / E-Stop

### Chế độ Manual (2 lớp bảo mật)
1. Nhấn **Control Manual** → nhập admin/123
2. Gạt công tắc vật lý trên tủ PLC sang Manual

Khi đủ điều kiện, các nút thủ công hiện ra:
- **Trigger**: chụp & phân tích AI ngay
- **Continue**: trở lại live stream
- **ON/OFF Conveyor**: băng tải
- **Cylinder 1 / 2**: kích xylanh

---

## 5. Khu vực Model AI

| Thành phần | Mô tả |
|---|---|
| Nút Duyệt | Chọn đường dẫn model (.pt / .onnx / thư mục OpenVINO) |
| Nút Tải Model | Nạp model vào bộ nhận diện |
| Nút Khôi phục | Hủy model hiện tại |

Sau khi tải thành công, status bar hiển thị:
- Loại model (YOLOv8/OBB/OpenVINO)
- Thời gian tải

---

## 6. Khu vực Dữ liệu (Data)

- **Bảng danh sách**: các bản ghi kiểm tra hôm nay
- **Nút 📊 Quản lý dữ liệu**: mở DataViewerDialog
  - Xem lịch sử theo ngày
  - Lọc theo Model AI
  - Thống kê: Tổng, OK, NG_L, NG_H, MISSING, Yield Rate
  - Nút **Sync Google Sheets**: đồng bộ dữ liệu chờ lên Cloud
  - Nút **Xuất Excel**: xuất báo cáo .xlsx (gộp ô theo ngày, tô màu)

---

## 7. Luồng sử dụng cơ bản

1. Chọn camera → Kết nối
2. Duyệt model → Tải Model
3. Nhập IP PLC → Kết nối PLC
4. Chế độ Auto: hệ thống tự chạy
5. Muốn can thiệp tay: Control Manual → gạt Manual PLC → Trigger
6. Xem lại dữ liệu: 📊 Quản lý dữ liệu

---

## 8. Phím tắt (nếu có)

*Chưa hỗ trợ phím tắt. Sử dụng chuột để thao tác.*
