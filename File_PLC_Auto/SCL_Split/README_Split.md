# Bộ SCL Đã Tách (để tránh giới hạn copy/dòng trong TIA Portal)

Mục tiêu của thư mục này là tách chương trình Auto thành nhiều khối nhỏ, để bạn copy/import vào TIA Portal dễ hơn và cũng dễ debug theo từng phần.

Nếu bạn cần đọc “luồng Auto chạy như thế nào, nhớ sản phẩm ra sao, xử lý theo FIFO ra sao”, xem thêm:
- `00_LuuDo_Auto.md`
- `SCL_Split_Block_IO.xlsx`

## 1) Danh sách khối
- `FB_Auto_Main.scl`: khối chính, chạy state machine Auto, gọi các khối con
- `FC_EdgesAndMode.scl`: bắt cạnh (StartStop/SS0/SS1/SS2) + chốt RUN + chọn mode Auto/Manual
- `FC_AI_Handshake.scl`: handshake PLC <-> Python (SS0 trigger, consume DataReady đúng 1 lần)
- `FB_FIFO10.scl`: bộ nhớ FIFO 10 phần tử để “ghi nhớ” kết quả theo thứ tự sản phẩm
- `FC_Cylinder1_Seq.scl`: trình tự ra/về xilanh 1 theo LS1 (không dùng timer reset)
- `FC_Cylinder2_Seq.scl`: trình tự ra/về xilanh 2 theo LS2 (không dùng timer reset)
- `FC_FaultManager.scl`: gom lỗi, xuất `ErrorActive`/`ErrorCode`
- `FC_ClassifyRule.scl`: hàm phụ (tùy chọn) để map/chuẩn hóa mã kết quả (0..4)
- `OB1_Call_Split_Example.scl`: ví dụ gọi khối trong OB1

## 2) Điều kiện đầu vào cho từng khối (tóm tắt)

### `FC_EdgesAndMode`
- Cần input phần cứng: `btAuto`, `btManual`, `StartStop`, `SS0`, `SS1`, `SS2`
- Cần vùng nhớ `prev*`, `runLatch` truyền kiểu `VAR_IN_OUT` (để bắt cạnh đúng theo scan PLC)

### `FC_AI_Handshake`
- Cần tín hiệu cạnh từ `FC_EdgesAndMode`: `ss0Rise`, `ss0Fall`
- Cần dữ liệu từ PC: `PC_DataReady`, `PC_KetQua`
- Cần `queueCount` để chặn FIFO overflow

### `FB_FIFO10`
- `Push/PushValue` từ handshake AI
- `Pop` từ khối chính sau khi xử lý xong sản phẩm (đã phân loại hoặc đã đi qua nhánh OK)

### `FC_Cylinder1_Seq` / `FC_Cylinder2_Seq`
- Nhận lệnh `StartAction` (xung) từ state machine
- Dùng tín hiệu phản hồi thật `LS1` / `LS2`

### `FC_FaultManager`
- Nhận các cờ lỗi con và xuất ra 1 cờ tổng `ErrorActive` + `ErrorCode`

### `FB_Auto_Main`
- Tích hợp tất cả khối con và xuất output cuối: băng tải + 2 xilanh + cờ mode/run/trigger

## 3) Cách tích hợp trong OB1
1. Gọi `FB_Auto_Main` (khuyến nghị, đơn giản nhất)
2. Mapping tag phần cứng + DB_GET/DB_PUT ở OB1, còn lại nằm trong FB
