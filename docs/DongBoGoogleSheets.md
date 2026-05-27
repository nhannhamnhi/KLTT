## 📊 HƯỚNG DẪN CẤU HÌNH VÀ ĐỒNG BỘ GOOGLE SHEETS

Hệ thống hỗ trợ lưu trữ dữ liệu kiểm tra vỉ thuốc song song dưới máy tính cục bộ và đồng bộ lên đám mây Google Sheets. Tài liệu này hướng dẫn chi tiết cách thiết lập và cơ chế vận hành hàng chờ khi mất mạng.

---

### 1. Cơ Chế Hoạt Động Của Hệ Thống

Dữ liệu kiểm tra (Thời gian, Tổng số, Đạt, Lỗi, Kết quả AI) được quản lý theo mô hình lai:
1. **Chế độ Online:** Nếu có mạng internet, dữ liệu được ghi vào tệp cục bộ đồng thời đẩy thẳng lên Google Sheets thời gian thực.
2. **Chế độ Offline:** Khi mất kết nối internet hoặc lỗi API, dữ liệu kiểm tra sẽ tự động lưu vào hàng chờ tạm thời tại tệp `src/data/data/pending_queue.json`.
3. **Cơ chế đồng bộ lại (Sync):** Khi mạng ổn định trở lại, người vận hành nhấn nút **Sync Google Sheets** trên giao diện để giải phóng hàng chờ và cập nhật đầy đủ lên đám mây.

---

### 2. Các Bước Thiết Lập Google Cloud API

Để phần mềm có quyền ghi dữ liệu vào bảng tính Google Sheets của bạn, hãy thực hiện theo quy trình sau:

#### Bước 1: Tạo Dự Án Trên Google Cloud Console
1. Truy cập vào trang quản lý [Google Cloud Console](https://console.cloud.google.com/).
2. Đăng nhập bằng tài khoản Google của bạn và nhấn **Create Project** để tạo một dự án mới.
3. Đặt tên dự án dễ nhớ (Ví dụ: `KLTT-Project`) và nhấn **Create**.

#### Bước 2: Kích Hoạt Các Dịch Vụ API Cần Thiết
1. Tại thanh tìm kiếm trên cùng của Cloud Console, tìm từ khóa **Google Sheets API** và nhấn chọn.
2. Nhấn nút **Enable** để kích hoạt API bảng tính.
3. Tiếp tục tìm kiếm từ khóa **Google Drive API** và nhấn chọn.
4. Nhấn nút **Enable** để kích hoạt API dịch vụ lưu trữ.

#### Bước 3: Tạo Tài Khoản Dịch Vụ (Service Account)
1. Truy cập menu bên trái: chọn **IAM & Admin** → **Service Accounts**.
2. Nhấn nút **Create Service Account** ở thanh menu trên cùng.
3. Điền thông tin tên tài khoản dịch vụ và nhấn **Create and Continue**.
4. Ở bước phân quyền (Role), bạn có thể bỏ qua hoặc chọn quyền **Editor** rồi nhấn **Done**.

#### Bước 4: Tạo Và Tải Về Khóa Xác Thực JSON
1. Nhấp chọn vào tài khoản dịch vụ vừa tạo trong danh sách.
2. Chọn tab **Keys** ở menu phía trên.
3. Nhấn **Add Key** → Chọn **Create new key**.
4. Chọn định dạng **JSON** và nhấn **Create**. Một tệp tin dạng `.json` sẽ tự động được tải về máy tính của bạn.

#### Bước 5: Đưa Khóa Vào Thư Mục Mã Nguồn
1. Đổi tên tệp tin `.json` vừa tải về thành: `service_account.json`.
2. Sao chép tệp tin này và đặt vào thư mục: `src/data/` của dự án.
3. *Lưu ý: Tệp tin này chứa khóa bảo mật quan trọng, đã được cấu hình trong `.gitignore` để tránh bị lộ lên GitHub.*

---

### 3. Cấu Hình Phần Mềm Thực Tế

Sau khi đã có tệp khóa xác thực, bạn cần thực hiện 2 bước cấu hình cuối cùng:

#### Bước 1: Chia Sẻ Bảng Tính Google Sheets
1. Mở tệp tin `src/data/service_account.json` bằng Notepad.
2. Tìm dòng có chứa `"client_email"` và sao chép địa chỉ email dạng: `tên-tài-khoản@dự-án.iam.gserviceaccount.com`.
3. Mở bảng tính Google Sheets dùng để lưu dữ liệu trên trình duyệt.
4. Nhấn nút **Chia Sẻ (Share)** ở góc trên bên phải → Dán địa chỉ email vừa sao chép vào.
5. Cấp quyền **Editor (Người chỉnh sửa)** và bỏ tích chọn gửi thông báo email → Nhấn **Chia sẻ**.

#### Bước 2: Tạo File Cấu Hình config.py
1. Sao chép tệp tin mẫu [config.py.example](file:///d:/KL_2025/KLTT/src/data/config.py.example) tại thư mục `src/data/`.
2. Đổi tên tệp tin sao chép thành `config.py`.
3. Mở tệp `config.py` bằng trình soạn thảo và thay đổi giá trị `SPREADSHEET_ID` bằng ID bảng tính của bạn.
    - *Mẹo: ID bảng tính là chuỗi ký tự nằm giữa `/d/` và `/edit` trên thanh địa chỉ trình duyệt.*
    - Ví dụ: Với URL `https://docs.google.com/spreadsheets/d/1A2B3C4D5E6F7G8H9I0J/edit`, ID sẽ là `1A2B3C4D5E6F7G8H9I0J`.

---

### 4. Xử Lý Sự Cố Google Sheets

#### Xóa cache pending_queue.json
Nếu hàng chờ bị treo (dữ liệu không sync dù đã nhấn nút):
1. Tắt chương trình.
2. Mở file `src/data/data/pending_queue.json` bằng Notepad.
3. Xóa toàn bộ nội dung và ghi `[]` (mảng rỗng).
4. Lưu file và khởi động lại chương trình.

#### Sheet bị hỏng cấu trúc (missing header, sai cột)
1. Tạo một sheet mới trên cùng Google Spreadsheet hoặc tạo file riêng.
2. Cập nhật `SHEET_NAME` trong `config.py`.
3. Nhấn **Sync Google Sheets** → hệ thống sẽ tự động tạo header (cột) cho sheet mới.

#### Không kết nối được Google API (firewall/proxy)
- Kiểm tra máy tính có truy cập được `https://sheets.googleapis.com` không.
- Nếu dùng proxy, cấu hình biến môi trường:
  ```bash
  set HTTP_PROXY=http://proxy:port
  set HTTPS_PROXY=http://proxy:port
  ```
- Thử tắt firewall tạm thời để kiểm tra.

---

### 5. Lưu Ý Quan Trọng
- File `service_account.json` đã được thêm vào `.gitignore` → không bị đẩy lên GitHub.
- `pending_queue.json` chỉ lưu tạm dữ liệu chưa sync. Nếu xóa file này, dữ liệu chưa sync sẽ mất vĩnh viễn.
- Giới hạn Google Sheets API: 60 requests/phút. Nếu sync quá nhiều dữ liệu cùng lúc có thể bị rate limit, hãy sync từng phần.
