from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ModeValue = Literal["manual", "auto_demo"]


class HealthResponse(BaseModel):
    status: str
    camera_connected: bool
    model_loaded: bool
    plc_connected: bool
    plc_adapter: str
    websocket_clients: int
    mode: ModeValue
    camera_source: int
    last_error: str | None = None


class StatsResponse(BaseModel):
    timestamp: datetime
    total: int
    passed: int
    failed: int
    result: str
    fps: float
    fps_avg_60s: float
    uptime_seconds: float
    records_saved: int
    mode: ModeValue


class HistoryRecord(BaseModel):
    id: int
    timestamp: datetime
    total: int
    passed: int
    failed: int
    result: str
    mode: str
    trigger_source: str


class TriggerResponse(BaseModel):
    saved: bool
    reason: str = ""


class ConfigRequest(BaseModel):
    camera_source: int | None = Field(default=None, ge=0)
    brightness: int | None = Field(default=None, ge=-100, le=100)
    saturation: int | None = Field(default=None, ge=-100, le=100)
    confidence: float | None = Field(default=None, ge=0.05, le=0.99)
    expected_slots: int | None = Field(default=None, ge=1, le=64)
    model_path: str | None = None


class ConfigResponse(BaseModel):
    camera_source: int
    brightness: int
    saturation: int
    confidence: float
    expected_slots: int
    model_path: str


class ModeRequest(BaseModel):
    mode: ModeValue


class ModeResponse(BaseModel):
    mode: ModeValue


class PLCRealRequest(BaseModel):
    ip: str = "192.168.0.1"
    rack: int = Field(default=0, ge=0, le=10)
    slot: int = Field(default=1, ge=0, le=10)


class PLCAdapterResponse(BaseModel):
    plc_adapter: str
    ip: str | None = None
    rack: int | None = None
    slot: int | None = None
