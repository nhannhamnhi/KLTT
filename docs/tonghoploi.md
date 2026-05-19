## 🛠 TỔNG HỢP CÁC LỖI THƯỜNG GẶP VÀ CÁCH KHẮC PHỤC

Tài liệu này tổng hợp toàn bộ các sự cố thường gặp trong quá trình vận hành hệ thống kiểm tra vỉ thuốc (Camera + AI + PLC + Google Sheets) và hướng dẫn chi tiết cách xử lý nhanh.

---

### 📋 Danh Sách Các Lỗi

- [1. Lỗi Khởi Động Phần Mềm (Crash/Sập Ngay Lúc Mở)](#1-lỗi-khởi-động-phần-mềm-crashsập-ngay-lúc-mở)
- [2. Lỗi Không Thể Tải Model AI](#2-lỗi-không-thể-tải-model-ai)
- [3. Lỗi Kết Nối PLC Thất Bại](#3-lỗi-kết-nối-plc-thất-bại)
- [4. Lỗi Sai Dòng CPU PLC Khi Kết Nối](#4-lỗi-sai-dòng-cpu-plc-khi-kết-nối)
- [5. Lỗi Không Thể Kích Hoạt Các Nút Điều Khiển Manual](#5-lỗi-không-thể-kích-hoạt-các-nút-điều-khiển-manual)
- [6. Lỗi Không Thể Kết Nối Camera Custom (Camera IP/Mạng)](#6-lỗi-không-thể-kết-nối-camera-custom-camera-ipmạng)
- [7. Lỗi Đồng Bộ Google Sheets Thất Bại](#7-lỗi-đồng-bộ-google-sheets-thất-bại)

---

### 1. Lỗi Khởi Động Phần Mềm (Crash/Sập Ngay Lúc Mở)

#### 🔴 Triệu chứng
Khi nhấp đúp tệp `run_app.bat` hoặc chạy lệnh `python src/ui/finish.py`, màn hình đen CMD xuất hiện rồi biến mất ngay lập tức, không hiển thị giao diện đăng nhập.

#### 🔍 Nguyên nhân
- Chưa cài đặt môi trường ảo `.venv` hoặc thiếu các thư viện phụ thuộc trong `requirements.txt`.
- Lỗi nạp thư viện động PyTorch (`DLL load failed: c10.dll` hoặc tương tự trên hệ điều hành Windows).

#### ✅ Khắc phục
1. **Kiểm tra môi trường ảo:** Đảm bảo thư mục `.venv` tồn tại và bạn đã cài đặt các thư viện bằng cách mở Terminal và chạy:
   ```bash
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Lỗi DLL của Torch:** Chương trình đã tích hợp sẵn cơ chế tự động tìm kiếm đường dẫn `torch/lib` và thêm vào danh sách DLL Path trong file `finish.py`. Nếu vẫn lỗi, hãy chắc chắn bạn đã kích hoạt đúng môi trường ảo có cài đặt `torch`.

---

### 2. Lỗi Không Thể Tải Model AI

#### 🔴 Triệu chứng
Sau khi nhấn nút **Tải Model**, thanh trạng thái ở góc dưới phần mềm hiển thị màu đỏ báo lỗi, hoặc ứng dụng bị treo đơ.

#### 🔍 Nguyên nhân
- Đường dẫn trỏ tới mô hình không chính xác.
- Phiên bản thư viện `openvino` trên máy tính không khớp với định dạng tệp tin mô hình đã export từ máy khác.
- Thiết bị xử lý (CPU/GPU) cấu hình sai trong môi trường.

#### ✅ Khắc phục
1. **Kiểm tra tệp tin:** Khi tải mô hình OpenVINO, bạn phải trỏ đường dẫn tới **thư mục chứa mô hình** (thư mục phải bao gồm đủ cả 3 tệp tin: `yolov8.xml`, `yolov8.bin` và `metadata.yaml`). Không chọn riêng lẻ tệp tin `.xml`.
2. **Đồng bộ phiên bản:** Nếu xuất mô hình từ Google Colab hoặc máy tính khác, hãy chạy script Python sau ngay trên máy vận hành thực tế để xuất mô hình tương thích tuyệt đối với phần cứng cục bộ:
   ```python
   from ultralytics import YOLO
   model = YOLO("yolov8.pt")
   model.export(format="openvino")
   ```
   Thư mục mới được sinh ra sẽ chạy rất mượt và không bị lỗi.

---

### 3. Lỗi Kết Nối PLC Thất Bại

#### 🔴 Triệu chứng
Điền địa chỉ IP của PLC và bấm **Kết Nối PLC** nhưng phần mềm báo lỗi: *"Không thể kết nối tới PLC!"*.

#### 🔍 Nguyên nhân
- Dây cáp mạng LAN bị lỏng hoặc địa chỉ IP của máy tính PC không cùng lớp mạng (subnet) với PLC.
- Tính năng truyền thông PUT/GET chưa được mở khóa trên cấu hình phần cứng PLC Siemens trong phần mềm TIA Portal.
- Khối DB (Data Block) cấu hình sai kích thước hoặc chưa tắt tính năng tối ưu hóa truy cập (Optimized block access).

#### ✅ Khắc phục
1. **Kiểm tra lớp mạng IP:** Địa chỉ IP của máy tính phải đặt tĩnh và cùng lớp mạng với PLC (Ví dụ: IP PLC là `192.168.0.1` thì IP máy tính PC phải là `192.168.0.100`, Subnet Mask: `255.255.255.0`). Thử ping địa chỉ PLC trên CMD: `ping 192.168.0.1`.
2. **Kích hoạt PUT/GET trên TIA Portal:**
   - Mở dự án PLC trên TIA Portal → Chọn thiết bị PLC (Device configuration) → Thuộc tính (Properties).
   - Chọn mục **Protection & Security** → **Connection mechanisms**.
   - Tích chọn **Permit access with PUT/GET communication from remote partner**.
   - Biên dịch (Compile) và nạp cấu hình phần cứng mới xuống PLC.
3. **Cấu hình DB không tối ưu hóa:**
   - Nhấp chuột phải vào khối DB1 (DB_GET) và DB2 (DB_PUT) → Chọn **Properties**.
   - Bỏ tích chọn **Optimized block access**.
   - Biên dịch và nạp lại xuống PLC.

---

### 4. Lỗi Sai Dòng CPU PLC Khi Kết Nối

#### 🔴 Triệu chứng
Bấm kết nối PLC thành công nhưng giao diện lập tức hiện cảnh báo đỏ: *"Dòng CPU không khớp!"* và tự động ngắt kết nối.

#### 🔍 Nguyên nhân
- Người dùng chọn sai dòng CPU trên giao diện (Ví dụ: PLC thực tế là S7-1500 nhưng trên giao diện Combobox lại chọn S7-1200). Phần mềm có cơ chế đọc Order Code của PLC khi vừa kết nối để đối chiếu và ngăn chặn các xung đột địa chỉ truyền thông nguy hiểm.

#### ✅ Khắc phục
- Chọn lại đúng dòng CPU phù hợp với thiết bị thực tế tại Combobox **CPU_PLC** trên giao diện chính, sau đó nhấn **Kết Nối PLC** lại.

---

### 5. Lỗi Không Thể Kích Hoạt Các Nút Điều Khiển Manual

#### 🔴 Triệu chứng
Ứng dụng đã kết nối PLC thành công, nhưng các nút nhấn điều khiển thủ công như *Trigger, Continue, ON/OFF Conveyor, Cylinder 1/2* vẫn bị ẩn hoàn toàn hoặc không thể nhấp chọn.

#### 🔍 Nguyên nhân
- Chưa đáp ứng đủ quy trình xác thực an toàn 2 lớp của chế độ Manual.

#### ✅ Khắc phục
Người vận hành phải thực hiện đủ 2 thao tác sau:
1. Nhấn nút **⚙️ Control Manual** trên phần mềm → Nhập đúng tài khoản đăng nhập admin (`admin` / `123`) để mở khóa trên PC.
2. Xoay công tắc vật lý chọn chế độ trên tủ điện cơ khí sang vị trí **Manual** (để PLC kích hoạt cờ hiệu `PLC_Manual = TRUE`).
- Khi cả hai điều kiện trên đồng thời thỏa mãn, các nút nhấn điều khiển tay sẽ xuất hiện trên màn hình.

---

### 6. Lỗi Không Thể Kết Nối Camera Custom (Camera IP/Mạng)

#### 🔴 Triệu chứng
Chọn nguồn `Camera_custom`, nhập địa chỉ URL HTTP hoặc RTSP của luồng video nhưng phần mềm thông báo lỗi kết nối và không hiển thị hình ảnh.

#### 🔍 Nguyên nhân
- URL truyền vào sai định dạng.
- Máy tính PC và điện thoại/IP Camera không kết nối chung một mạng Wi-Fi/mạng nội bộ.
- Thiết bị phát luồng video chưa bật quyền chia sẻ hoặc yêu cầu tài khoản mật khẩu xác thực.

#### ✅ Khắc phục
1. **Kiểm tra ping:** Đảm bảo máy tính ping thông tới địa chỉ IP của thiết bị camera mạng.
2. **Kiểm tra URL bằng VLC:** Tải phần mềm VLC Media Player trên PC, chọn **Media** → **Open Network Stream**, dán URL của bạn vào xem có hiển thị được video không. Nếu VLC chạy được mà phần mềm bị lỗi, hãy kiểm tra xem URL có chứa ký tự đặc biệt nào không.
3. **Định dạng phổ biến:**
   - DroidCam: `http://192.168.1.15:4747/video`
   - IP Webcam: `http://192.168.1.15:8080/video` hoặc `http://192.168.1.15:8080/shot.jpg`

---

### 7. Lỗi Đồng Bộ Google Sheets Thất Bại

#### 🔴 Triệu chứng
Dữ liệu kiểm tra lưu cục bộ bình thường nhưng không hiển thị trên Google Sheets, hoặc khi nhấn nút **Sync Google Sheets** thủ công trong bảng dữ liệu báo lỗi kết nối.

#### 🔍 Nguyên nhân
- Chưa chia sẻ quyền truy cập bảng tính cho email của tài khoản dịch vụ (Service Account).
- Tệp tin xác thực `service_account.json` bị thiếu hoặc không chính xác.
- Địa chỉ bảng tính ID cấu hình trong `config.py` bị sai lệch.

#### ✅ Khắc phục
1. **Chia sẻ bảng tính Google Sheets:** Mở tệp tin `service_account.json` của bạn ra, tìm từ khóa `"client_email"` và sao chép địa chỉ email tương ứng (định dạng: `xxx@xxx.iam.gserviceaccount.com`). Mở bảng tính Google Sheets trên trình duyệt, nhấn nút **Chia Sẻ (Share)**, dán email này vào và cấp quyền **Editor (Người chỉnh sửa)**.
2. **Kiểm tra ID bảng tính:** Mở file `src/data/config.py` và kiểm tra hằng số `SPREADSHEET_ID` xem đã đúng với ID bảng tính của bạn chưa (ID là chuỗi ký tự dài nằm giữa `/d/` và `/edit` trên đường dẫn URL trình duyệt).
3. **Kiểm tra hàng chờ offline:** Khi mất kết nối mạng, dữ liệu sẽ được lưu tạm tại `src/data/data/pending_queue.json`. Ngay khi có mạng trở lại, hãy bấm nút **Sync Google Sheets** trong cửa sổ quản lý dữ liệu để đồng bộ hết hàng chờ lên đám mây.
