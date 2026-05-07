# KLTT Web Backend

## Start
```powershell
cd D:\KL_2025\KLTT\web_backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Endpoints
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
- `POST /mode`
- `POST /plc/demo`
- `POST /plc/real`
- `WS /ws/monitor`

## Notes
- Default DB path: `%TEMP%\kltt_web\history.db`
- Override DB path: environment variable `KLTT_DB_PATH`
- For quick quality gate from repo root:
```powershell
.\run_quality_gate.ps1
```
