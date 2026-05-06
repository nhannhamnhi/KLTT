# Lưu Đồ Hoạt Động Chế Độ Auto (giải thích tiếng Việt)

Tài liệu này mô tả “chương trình Auto hoạt động ra sao” theo đúng ý bạn: hệ thống có thể có nhiều sản phẩm trên băng tải cùng lúc, PLC vẫn “nhớ” được từng sản phẩm để phân loại đúng.

## 1) Ý tưởng cốt lõi: FIFO để ghi nhớ thứ tự sản phẩm

- Mỗi khi sản phẩm đi tới vị trí camera (cảm biến `SS0`), PLC sẽ yêu cầu PC chụp/AI.
- PC trả về kết quả phân loại (mã `PC_KetQua`).
- PLC sẽ **đẩy kết quả đó vào FIFO** (hàng đợi) theo đúng thứ tự sản phẩm đi qua `SS0`.

FIFO giống như “danh sách chờ”: phần tử ở **đầu FIFO** luôn là sản phẩm đi trước, sẽ tới `SS1`/`SS2` trước.

Giới hạn FIFO: 10 phần tử (đủ cho băng tải ngắn và test liên tiếp 2..7 vỉ như bạn nói). Nếu đầy -> lỗi `overflow`.

## 2) Mã kết quả AI dùng trong PLC

- `0 = WAIT`: không có dữ liệu hợp lệ (thường dùng khi chưa có vật)
- `1 = OK`: đạt
- `2 = NG_L`: lỗi nhẹ, xử lý ở nhánh xilanh 1
- `3 = NG_H`: lỗi nặng, xử lý ở nhánh xilanh 2
- `4 = MISSING`: thiếu số lượng theo khuôn, vẫn cần xử lý riêng (đang gắn vào nhánh xilanh 2 trong logic hiện tại)

## 3) Luồng hoạt động từng bước (từ lúc sản phẩm vào tới lúc rời hệ thống)

### Bước A: Sản phẩm tới camera (SS0)
1. `SS0` có cạnh lên (`ss0Rise = 1`).
2. PLC set `PLC_TriggerReq = 1` để báo PC bắt đầu xử lý AI cho sản phẩm này.
3. PLC mở một “chu kỳ trigger” (`triggerCycleActive = 1`) và đặt cờ `aiConsumedThisCycle = 0`.

### Bước B: PC trả kết quả (DataReady)
4. Khi PC xử lý xong, PC set `PC_DataReady = 1` và đặt `PC_KetQua`.
5. PLC chỉ **đọc/consume đúng 1 lần** trong chu kỳ này:
   - Nếu `PC_DataReady = 1` và `aiConsumedThisCycle = 0` và `triggerCycleActive = 1`:
     - kiểm tra `PC_KetQua` hợp lệ `0..4`
     - `PUSH` kết quả vào FIFO
     - set `aiConsumedThisCycle = 1` (để không push lặp dù `DataReady` giữ mức 1)

### Bước C: Kết thúc chu kỳ trigger theo SS0 xuống
6. Khi `SS0` xuống (`ss0Fall = 1`), PLC clear `PLC_TriggerReq = 0`, đóng chu kỳ trigger và reset `aiConsumedThisCycle`.

Ghi chú: cơ chế này khớp yêu cầu “DataReady chỉ về 0 khi SS0 xuống” của chương trình Python hiện tại.

### Bước D: Sản phẩm đi qua vị trí xilanh 1 (SS1)
7. Khi sản phẩm tới `SS1` (cạnh lên `ss1Rise = 1`), PLC **nhìn phần tử đầu FIFO** (peek).
8. Nếu đầu FIFO là `NG_L (2)`:
   - PLC chạy trình tự xilanh 1: ra hết (LS1=1) -> về (LS1=0).
   - Trong thời gian xilanh đang chạy, **băng tải tạm dừng** để phân loại ổn định.
   - Xong trình tự, PLC `POP` FIFO (kết thúc vòng đời của sản phẩm này).
9. Nếu đầu FIFO là `OK/NG_H/MISSING`:
   - Không kích xilanh 1, để sản phẩm đi tiếp về phía `SS2`.
   - FIFO vẫn giữ nguyên (chưa pop), vì sản phẩm này chưa được xử lý xong.

### Bước E: Sản phẩm đi qua vị trí xilanh 2 (SS2)
10. Khi sản phẩm tới `SS2` (cạnh lên `ss2Rise = 1`), PLC again peek đầu FIFO.
11. Nếu đầu FIFO là `NG_H (3)` hoặc `MISSING (4)`:
   - PLC chạy trình tự xilanh 2: ra hết (LS2=1) -> về (LS2=0).
   - Trong thời gian xilanh đang chạy, **băng tải tạm dừng**.
   - Xong trình tự, PLC `POP` FIFO.
12. Nếu đầu FIFO là `OK (1)`:
   - Không kích xilanh 2, coi như sản phẩm OK đi thẳng.
   - PLC `POP` FIFO ngay tại SS2 (vì sản phẩm đã kết thúc vòng đời trong hệ thống).

## 4) “Dừng băng tải” là dừng cái gì?

- Chỉ dừng **output băng tải** (`Conveyor := FALSE`) khi xilanh đang phân loại.
- PLC scan vẫn chạy bình thường, state machine vẫn chạy, xilanh vẫn chạy trình tự ra/về theo limit switch.

Lý do: nếu dừng cả chu trình (đứng state machine), thì trình tự ra/về xilanh sẽ bị đứng theo, dễ kẹt và khó recover.

## 5) Vì sao cách này cho phép nhiều sản phẩm cùng lúc?

Vì mỗi sản phẩm khi qua `SS0` sẽ sinh ra 1 “record” kết quả trong FIFO.

Khi sản phẩm tới `SS1/SS2`, PLC luôn lấy đúng record ở đầu FIFO (đúng thứ tự thời gian), nên vẫn phân loại đúng dù nhiều vỉ đang nằm trên băng tải.

Điều kiện để FIFO không bị lệch:
- Thứ tự cảm biến phải đúng chiều băng tải: `SS0 -> SS1 -> SS2`.
- Mỗi sản phẩm chỉ trigger SS0 đúng 1 lần (hoặc nếu có nhiễu thì phải lọc cạnh ổn định).

