# YÊU CẦU VÀ KẾT QUẢ ĐỀ TÀI

**Tên đề tài:** Xây Dựng Hệ Thống Giám Sát Và Phát Hiện Lỗi Sản Phẩm Vỉ Thuốc Dựa Trên Thị Giác Máy Tính Và Deep Learning

---

## 3. Các yêu cầu chủ yếu

- **Huấn luyện mô hình AI:** Xây dựng và thiết lập mô hình học sâu (như họ mô hình YOLO) để nhận diện và phân loại chi tiết trạng thái của từng viên thuốc trên vỉ (ví dụ: Full - đầy đủ, Partial - mẻ/thiếu một phần, Empty - trống).
- **Tối ưu hóa hiệu năng:** Áp dụng các kỹ thuật tối ưu hóa (như Intel OpenVINO) nhằm đảm bảo tốc độ suy luận (inference) đáp ứng yêu cầu xử lý thời gian thực trên các thiết bị máy tính thông dụng.
- **Xây dựng phần mềm trung tâm:** Lập trình hệ thống điều khiển trung tâm bằng Python bao gồm các chức năng cốt lõi:
  - Đọc và đồng bộ luồng dữ liệu hình ảnh trực tiếp từ camera.
  - Vận hành pipeline AI nhận diện lỗi.
  - Lưu vết, thống kê lịch sử kết quả kiểm tra hệ thống.
  - Thiết lập kênh truyền thông hai chiều thời gian thực với trạm PLC (ứng dụng thư viện Snap7).
- **Thiết kế và thi công phần cứng:** Xây dựng sa bàn/mô hình vật lý hoàn chỉnh bao gồm: băng tải chuyển hàng, giá đỡ camera, và hệ thống xy-lanh khí nén đa cấp để rẽ nhánh phân loại sản phẩm.
- **Tích hợp tự động hóa:** Thiết lập phần mềm trên PLC Siemens (S7-1200) nhằm tiếp nhận lệnh từ phần mềm trung tâm và trực tiếp điều khiển các cơ cấu chấp hành.

---

## 4. Kết quả tối thiểu phải có

- **Mô hình vật lý hoạt động đồng bộ:** Hệ thống thực tế có khả năng giao tiếp mượt mà với phần mềm, tự động gạt/phân loại chính xác các vỉ thuốc lỗi ra khỏi băng chuyền dựa trên tín hiệu AI.
- **Chương trình xử lý ổn định:** Toàn bộ luồng xử lý (từ lúc camera chụp ảnh, AI phân tích, đến khi PLC kích hoạt xy-lanh) diễn ra chính xác, độ trễ thấp và không bị mất kết nối trong quá trình vận hành liên tục.
- **Giao diện giám sát trực quan (GUI/Web/App):** Cung cấp trung tâm điều khiển cho người vận hành có thể: theo dõi hình ảnh thực tế, xem đánh dấu (bounding box) lỗi trên vỉ thuốc, và theo dõi các thông số thống kê, trạng thái PLC ngay theo thời gian thực.
- **Quyển báo cáo thuyết minh:** Trình bày chi tiết, có cơ sở khoa học về toàn bộ quy trình thực hiện: từ thiết kế cơ bản, huấn luyện mô hình AI, thiết kế sơ đồ điện - khí nén, lập trình cấu hình cho đến đánh giá sai số của hệ thống.
