# Hướng Dẫn Cài Đặt Chi Tiết

Checklist từng bước để cài đặt và chạy hệ thống lần đầu.

---

## ✅ Checklist cài đặt

- [ ] Cài Python 3.13 (hoặc 3.8+)
- [ ] Clone mã nguồn
- [ ] Tạo môi trường ảo .venv
- [ ] Cài đặt thư viện từ requirements.txt
- [ ] Cài OpenVINO (tùy chọn, để tăng tốc AI)
- [ ] Tải model AI (OpenVINO hoặc .pt)
- [ ] Đặt model đúng đường dẫn
- [ ] Cấu hình Google Sheets (tùy chọn)
- [ ] Chạy thử ứng dụng

---

## 1. Cài Python

Tải Python 3.13 từ [python.org](https://www.python.org/downloads/).

Khi cài: **nhớ tick** "Add Python to PATH".

Kiểm tra:
`ash
python --version
`

## 2. Clone mã nguồn
`ash
git clone <URL_REPOSITORY>
cd KLTT
`

## 3. Tạo môi trường ảo
`ash
python -m venv .venv
.venv\Scripts\activate
`

## 4. Cài thư viện
`ash
pip install -r requirements.txt
pip install openvino
`

## 5. Tải model AI

Tải từ Google Drive:
📥 [Download Model OpenVINO](https://drive.google.com/drive/folders/1GZrhgVkqMVZgJNROqwBPujrJ1-hqv6_k?usp=sharing)

Giải nén vào:
`
models/yolov8-obb/yolov8_openvino_model/
├── yolov8.xml
├── yolov8.bin
└── metadata.yaml
`

## 6. Cấu hình Google Sheets (tùy chọn)
Xem: [docs/DongBoGoogleSheets.md](DongBoGoogleSheets.md)

## 7. Chạy thử
`ash
.venv\Scripts\activate
python src/ui/finish.py
`
Hoặc nhấp đúp un_app.bat.

Đăng nhập: admin / 123.
Duyệt đường dẫn model -> Tải Model -> chạy.

## 8. Lỗi thường gặp khi cài đặt

| Lỗi | Nguyên nhân | Fix |
|---|---|---|
| pip not found | Chưa cài Python / chưa add PATH | Cài lại Python, tick "Add to PATH" |
| DLL load failed: c10.dll | Thiếu thư viện Torch | Kích hoạt đúng .venv, cài lại torch |
| ModuleNotFoundError | Quên pip install | Chạy lại pip install -r requirements.txt |
| No module named openvino | Chưa cài OpenVINO | pip install openvino |

Xem thêm: [docs/tonghoploi.md](tonghoploi.md)
