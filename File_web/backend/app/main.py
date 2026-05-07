from __future__ import annotations

from pathlib import Path
from typing import Any

import csv
import io
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from .monitor_service import MonitorService
from .schemas import (
    ConfigRequest,
    ConfigResponse,
    HealthResponse,
    HistoryRecord,
    PLCAdapterResponse,
    PLCRealRequest,
    ModeRequest,
    ModeResponse,
    StatsResponse,
    TriggerResponse,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


app = FastAPI(title="KLTT Web Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

monitor = MonitorService(repo_root=_repo_root())

@asynccontextmanager
async def lifespan(_: FastAPI):
    await monitor.start()
    try:
        yield
    finally:
        await monitor.stop()

app.router.lifespan_context = lifespan


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "KLTT backend is running"}


@app.get("/health", response_model=HealthResponse)
async def get_health() -> Any:
    return monitor.get_health()


@app.get("/stats", response_model=StatsResponse)
async def get_stats() -> Any:
    return monitor.get_stats()

@app.get("/benchmark")
async def get_benchmark() -> Any:
    return monitor.get_benchmark()


@app.get("/history", response_model=list[HistoryRecord])
async def get_history(date: str | None = None) -> Any:
    return monitor.get_history(date_filter=date)


@app.get("/history/export")
async def export_history_csv(date: str | None = None) -> Response:
    rows = monitor.get_history(date_filter=date)
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["id", "timestamp", "total", "passed", "failed", "result", "mode", "trigger_source"],
    )
    writer.writeheader()
    writer.writerows(rows)
    csv_data = output.getvalue().encode("utf-8-sig")
    filename = f"history_{date or 'all'}.csv"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=csv_data, media_type="text/csv", headers=headers)


@app.delete("/history")
async def clear_history() -> Any:
    removed = monitor.clear_history()
    return {"cleared_rows": removed}


@app.post("/trigger", response_model=TriggerResponse)
async def trigger_manual() -> Any:
    saved, reason = monitor.trigger_manual()
    return {"saved": saved, "reason": reason}


@app.post("/continue")
async def continue_manual() -> Any:
    return monitor.continue_manual()


@app.get("/config", response_model=ConfigResponse)
async def get_config() -> Any:
    return monitor.get_config()


@app.post("/config", response_model=ConfigResponse)
async def update_config(payload: ConfigRequest) -> Any:
    return monitor.apply_config(payload.model_dump())


@app.post("/mode", response_model=ModeResponse)
async def set_mode(payload: ModeRequest) -> Any:
    monitor.set_mode(payload.mode)
    return {"mode": monitor.get_mode()}


@app.post("/plc/demo", response_model=PLCAdapterResponse)
async def set_demo_plc() -> Any:
    monitor.use_demo_plc()
    return {"plc_adapter": "demo"}


@app.post("/plc/real", response_model=PLCAdapterResponse)
async def set_real_plc(payload: PLCRealRequest) -> Any:
    monitor.try_use_real_plc(ip=payload.ip, rack=payload.rack, slot=payload.slot)
    return {"plc_adapter": "real", "ip": payload.ip, "rack": payload.rack, "slot": payload.slot}


@app.websocket("/ws/monitor")
async def ws_monitor(websocket: WebSocket) -> None:
    await websocket.accept()
    await monitor.register(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        monitor.unregister(websocket)
    except ValidationError:
        monitor.unregister(websocket)
    except Exception:
        monitor.unregister(websocket)
