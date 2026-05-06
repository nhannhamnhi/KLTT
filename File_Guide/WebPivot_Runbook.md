# Web Pivot Runbook (4-5 ngày)

## 1. Cấu trúc mới
- `web_backend/`: FastAPI backend + WebSocket + SQLite + PLC adapters
- `web_frontend/`: React + Vite web GUI

## 2. Chạy backend
```powershell
cd D:\KL_2025\KLTT\web_backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 3. Chạy frontend
```powershell
cd D:\KL_2025\KLTT\web_frontend
npm install
npm run dev
```

Mở trình duyệt:
- `http://127.0.0.1:5173`

## 3.1 Chạy nhanh 1 lệnh
```powershell
cd D:\KL_2025\KLTT
.\run_web_demo.ps1
```

## 4. API chính
- `GET /health`
- `GET /stats`
- `GET /benchmark`
- `GET /history`
- `GET /history/export`
- `DELETE /history`
- `POST /trigger`
- `POST /continue`
- `GET /config`
- `POST /config`
- `POST /mode` với payload `{"mode":"manual"}` hoặc `{"mode":"auto_demo"}`
- `POST /plc/demo`
- `POST /plc/real` với payload `{"ip":"192.168.0.1","rack":0,"slot":1}`
- `WS /ws/monitor`

## 5. Payload WebSocket monitor
```json
{
  "timestamp": "2026-05-06T22:12:12",
  "frame_base64": "...",
  "labels": ["full", "partial"],
  "result": "NG_L",
  "counts": { "total": 2, "passed": 1, "failed": 1 },
  "fps": 21.4,
  "plc_state": { "adapter": "demo", "auto": false, "manual": true },
  "mode": "manual"
}
```

## 6. Checklist test nhanh (30-60 phút)
1. `Monitor` có ảnh realtime và FPS cập nhật liên tục.
2. WebSocket tự reconnect khi refresh tab.
3. `Trigger` lưu lịch sử mới trong tab `History`.
4. Đổi `Manual` <-> `Auto Demo` thấy state cập nhật.
5. Đổi adapter PLC `Demo`/`Real` trong tab Control.
6. Đổi config camera/brightness/saturation/confidence có tác dụng.
7. Export CSV từ tab History hoạt động.
8. Rút camera hoặc tắt camera tạm thời: backend không crash, tự thử reconnect.

## 6.1 Chạy smoke test backend
```powershell
cd D:\KL_2025\KLTT
python -m pytest web_backend/tests/smoke_test.py -q
```

## 6.2 Chạy quality gate đầy đủ
```powershell
cd D:\KL_2025\KLTT
.\run_quality_gate.ps1
```

## 8. Troubleshooting nhanh
1. Không có ảnh monitor:
- Vào tab Settings, đổi `camera_source` (0 -> 1 -> 2), bấm Save Config.
- Kiểm tra banner lỗi trên UI (`Camera disconnected` / `Camera frame read failed`).

2. Không kết nối được PLC thật:
- Dùng tab Control chuyển về `Use Demo PLC` để không chặn demo.
- Xác nhận lại `ip/rack/slot`, subnet LAN, và DB mapping trong TIA trước khi đổi lại Real.

3. WS bị disconnect:
- UI tự reconnect sau vài giây.
- Kiểm tra backend còn chạy ở `:8000` và không bị firewall chặn.

4. Trigger không lưu:
- Nếu kết quả đang `WAIT` thì backend cố ý không lưu.
- Đặt vỉ thuốc vào khung hình hoặc giảm `confidence` trong Settings.

## 7. Lưu ý quan trọng
- Giai đoạn này `Auto` là demo-safe, chưa điều khiển phần cứng thật.
- Backend mặc định dùng model YOLOv8-OBB OpenVINO ở:
  - `D:\KL_2025\KLTT\File_modelYOLO\model\yolov8-obb\yolov8_openvino_model`
- Có thể override bằng `POST /config` với `model_path`.
- SQLite mặc định ghi ở `%TEMP%\kltt_web\history.db` (đổi bằng biến môi trường `KLTT_DB_PATH`).
