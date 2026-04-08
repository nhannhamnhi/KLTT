<!-- ⚠️ SYSTEM NOTICE FOR AI AGENTS: Bất cứ khi nào bạn (hoặc LLM khác) nhận yêu cầu chỉnh sửa logic hệ thống / luồng truyền thông PLC / chức năng GUI từ User, BẠN BẮT BUỘC phải đối chiếu và tự động CẬP NHẬT file này để phản ánh chính xác cấu trúc vận hành mới nhất. -->

# QUY TRÌNH VẬN HÀNH CHI TIẾT HỆ THỐNG PHÂN LOẠI VỈ THUỐC

Tài liệu này mô tả từng bước dòng chảy dữ liệu (Data Flow) và cách hệ thống cơ điện tử phối hợp nội bộ với Phần mềm Trung tâm AI để vận hành dây chuyền.

---

## 1. QUY TRÌNH KHỞI ĐỘNG VÀ THIẾT LẬP (STARTUP)
Trước khi chạy máy, người vận hành thực hiện các bước trên giao diện (GUI):

1. **Khởi động Camera:**
   - Chọn nguồn vào trong combobox (Webcam 1, Webcam 2 hoặc Camera_custom).
   - *Lưu ý:* Nếu chọn `Camera_custom`, hệ thống sẽ yêu cầu nhập URL luồng video (ví dụ: HTTP/RTSP từ IP Camera / App Điện thoại).
   - Nhấn **"Kết Nối Camera"**. Tinh chỉnh độ sáng/bão hòa nếu cần.
2. **Khởi động Trí Tuệ Nhân Tạo (AI):**
   - Bấm **"Browser"** để chọn đường dẫn mô hình đồ thị YOLO (file định dạng `.pt`, `.onnx` hoặc OpenVINO XML).
   - Nhấn **"Tải Model"** để khởi tạo Core suy luận thời gian thực.
3. **Kết Nối Trung Tâm (PC ↔ PLC):**
   - Điền thông số PLC mạng hở: `Đời CPU` (S7-1200, 1500, 400), `IP`, `Rack`, `Slot`.
   - Bấm **"Kết Nối PLC"**. Trạng thái "Mất kết nối" 🔴 sẽ chuyển sang mức sẵn sàng 🟢.

---

## 2. CHẾ ĐỘ HOẠT ĐỘNG (ROUTING)

### 🔒 2.0 Kích hoạt Master (Khóa Phần Cứng)
Trước khi chọn chế độ Auto hay Manual, người vận hành **bắt buộc** nhấn nút **"🔓 Master"** trên giao diện:
- Khi nhấn Master → PC gửi tín hiệu `PC_Master = TRUE` xuống PLC → PLC vô hiệu hóa các nút vật lý trên tủ điện.
- Giao diện hiển thị thêm 2 nút **Auto** và **Manual** để chọn chế độ.
- Khi tắt Master → Tất cả nút chế độ ẩn đi, PLC mở khóa cho nút vật lý hoạt động trở lại.

Người vận hành chọn 1 trong 2 chế độ bằng cách nhấn nút tương ứng (Auto hoặc Manual).

### 🟢 2A. Chế độ Tự Động (AUTO MODE)
**Đặc điểm:** Phần mềm tự động giám sát cảm biến quang, chạy vòng lặp suy luận và gửi lệnh cho PLC loại bỏ tự động mà không cần can thiệp tay. Sự tương tác diễn ra 100% qua Snap7 ở Back-ground.

* **Bước 1:** Đầu vào. Băng tải chở vỉ thuốc vào buồng chụp.
* **Bước 2:** Kích hoạt (Trigger). Khi vỉ thuốc chạm mốc Cảm biến 0 (S0), PLC dựng cờ hiệu `PLC_TriggerReq = TRUE` đẩy lên cho máy tính (PC).
* **Bước 3:** Chụp & Phân tích (Vision). Phần mềm Python trên PC thấy cờ S0:
  - Lập tức đóng băng 1 Frame hình.
  - Chạy mô hình YOLO đếm số lượng viên đạt `Full`, vỡ `Partial`, trống `Empty`.
* **Bước 4:** Định tuyến kết quả (Decision). Machine Learning đưa ra 1 trong 3 mức độ chất lượng (ghi vào `PC_KetQua`):
  - `OK (1)`: Trạng thái hoàn hảo -> Vỉ thuốc đi thẳng qua khâu đóng gói.
  - `NG_L (2)`: Lỗi nhẹ (thiếu 1-2 viên) -> Tới vị trí xi lanh 1 (cảm biến S1), kích đẩy ra khay hàng tái chế.
  - `NG_H (3)`: Lỗi nặng (hao hụt nhiều) -> Tới vị trí xi lanh 2 (cảm biến S2), kích đẩy thẳng vào thùng rác.
* **Bước 5:** Báo tin (Handshake). PC báo `PC_DataReady = TRUE` báo PLC "Đã suy luận xong!". PLC nhận tin, thực thi xi lanh và hạ cờ S0.

### 🔵 2B. Chế độ Thủ Công (MANUAL MODE)
**Đặc điểm:** Vô hiệu hóa tính năng ra quyết định vòng kín của PLC, giao toàn quyền điều khiển từng bộ phận cơ khí riêng lẻ cho người trực máy thông qua các nút trên màn hình máy tính.

- **Điều khiển Băng tải (`btConveyor`):** Nhấn để băng tải chạy cưỡng bức, nhấn lần nữa để dừng. Truyền tín hiệu On/Off vào `PC_Conveyor`.
- **Điều khiển Xy-lanh (`btCylinder1`, `btCylinder2`):** Nhấn để ép ty xy lanh đi ra, nhấn tắt để thu ty xy lanh lại. Dùng bảo trì/kẹt phôi.
- **Mô phỏng Chụp (Nút `Trigger`):** Ép Camera đóng băng hình ảnh hiện tại và xử lý AI tức thì để ghi dữ liệu/biên bản kết quả (Không đợi mạch PLC).
- **Tiếp tục (Nút `Continue`):** Thả frame bị đóng băng, đưa hình ảnh Camera về dạng video Live Stream.

---

## 3. LOGGING: THỐNG KÊ & XUẤT BÁO CÁO
Bất kể hoạt động ở chế độ Auto hay Manual (`Trigger` ép tay), mọi kết quả nhận diện đều được ghi vào danh sách Database cục bộ:
1. **Lưu vết Real-time:** Tổng số viên trên vỉ, số viên Đạt, số viên Lỗi, kèm timestamp vào bảng List trên giao diện chính.
2. **Xuất sổ tay Excel:** Nút **"Xuất Excel"** sẽ tổng hợp toán bộ lịch sử hoạt động thành định dạng Bảng Tính `.xlsx`, phục vụ cho kế toán chất lượng / QAS.

---
📅 *Ngày cập nhật gần nhất: Tự động ghi nhận theo Git/Lần tương tác.*
