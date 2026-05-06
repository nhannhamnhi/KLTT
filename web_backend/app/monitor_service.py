from __future__ import annotations

import asyncio
import base64
import os
import tempfile
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from .database import HistoryStore
from .plc_adapters import DemoPLCAdapter, PLCAdapter, RealPLCAdapter


def _try_load_torch_dlls() -> None:
    try:
        if os.name != "nt":
            return
        import importlib.util

        spec = importlib.util.find_spec("torch")
        if spec is None or not spec.submodule_search_locations:
            return
        torch_dll_path = Path(spec.submodule_search_locations[0]) / "lib"
        if torch_dll_path.exists():
            os.add_dll_directory(str(torch_dll_path))
    except Exception:
        pass


_try_load_torch_dlls()

from ultralytics import YOLO  # noqa: E402


@dataclass
class RuntimeConfig:
    camera_source: int = 0
    brightness: int = 0
    saturation: int = 0
    confidence: float = 0.7
    expected_slots: int = 6
    model_path: str = ""
    mode: str = "manual"


class MonitorService:
    def __init__(self, *, repo_root: Path) -> None:
        default_model = repo_root / "File_modelYOLO" / "model" / "yolov8-obb" / "yolov8_openvino_model"
        default_db = Path(os.environ.get("KLTT_DB_PATH", str(Path(tempfile.gettempdir()) / "kltt_web" / "history.db")))

        self.config = RuntimeConfig(model_path=str(default_model))
        self.history = HistoryStore(default_db)
        self._mode = "manual"
        self._clients: set[Any] = set()
        self._running = False
        self._task: asyncio.Task | None = None
        self._camera_connected = False
        self._model_loaded = False
        self._last_auto_save_at = 0.0
        self._prev_trigger_req = False
        self._camera_source_active = self.config.camera_source
        self._records_saved = 0
        self._started_at = time.time()
        self._last_error: str | None = None
        self._fps_samples: deque[tuple[float, float]] = deque(maxlen=4000)
        self._result_payload: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "frame_base64": "",
            "labels": [],
            "result": "WAIT",
            "counts": {"total": 0, "passed": 0, "failed": 0},
            "fps": 0.0,
            "plc_state": {},
            "mode": self._mode,
        }

        self._detector = self._load_model(self.config.model_path)
        self._plc: PLCAdapter = DemoPLCAdapter()

    @property
    def websocket_clients(self) -> int:
        return len(self._clients)

    def get_mode(self) -> str:
        return self._mode

    def get_config(self) -> dict[str, Any]:
        return {
            "camera_source": self.config.camera_source,
            "brightness": self.config.brightness,
            "saturation": self.config.saturation,
            "confidence": self.config.confidence,
            "expected_slots": self.config.expected_slots,
            "model_path": self.config.model_path,
        }

    def set_mode(self, mode: str) -> None:
        self._mode = mode
        self.config.mode = mode
        self._plc.set_mode(mode)

    def use_demo_plc(self) -> None:
        self._plc = DemoPLCAdapter(mode=self._mode)

    def try_use_real_plc(self, ip: str = "192.168.0.1", rack: int = 0, slot: int = 1) -> None:
        self._plc = RealPLCAdapter(ip=ip, rack=rack, slot=slot, mode=self._mode)

    def clear_history(self) -> int:
        return self.history.clear()

    def _load_model(self, model_path: str) -> YOLO | None:
        if not model_path:
            self._model_loaded = False
            return None
        try:
            model = YOLO(model_path, task="obb")
            self._model_loaded = True
            self._last_error = None
            return model
        except Exception as exc:
            self._model_loaded = False
            self._last_error = f"Model load failed: {exc}"
            return None

    def apply_config(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("camera_source") is not None:
            self.config.camera_source = int(payload["camera_source"])
        if payload.get("brightness") is not None:
            self.config.brightness = int(payload["brightness"])
        if payload.get("saturation") is not None:
            self.config.saturation = int(payload["saturation"])
        if payload.get("confidence") is not None:
            self.config.confidence = float(payload["confidence"])
        if payload.get("expected_slots") is not None:
            self.config.expected_slots = int(payload["expected_slots"])
        if payload.get("model_path") is not None:
            self.config.model_path = str(payload["model_path"]).strip()
            self._detector = self._load_model(self.config.model_path)

        return self.get_config()

    def get_health(self) -> dict[str, Any]:
        plc_state = self._plc.poll_status()
        if not self._camera_connected and self._running:
            self._last_error = self._last_error or "Camera disconnected"
        return {
            "status": "ok" if self._running else "starting",
            "camera_connected": self._camera_connected,
            "model_loaded": self._model_loaded,
            "plc_connected": bool(plc_state.get("connected", False)),
            "plc_adapter": str(plc_state.get("adapter", "unknown")),
            "websocket_clients": self.websocket_clients,
            "mode": self._mode,
            "camera_source": int(self.config.camera_source),
            "last_error": self._last_error,
        }

    def get_stats(self) -> dict[str, Any]:
        counts = self._result_payload["counts"]
        now = time.time()
        self._prune_fps_samples(now)
        fps_avg = float(sum(v for _, v in self._fps_samples) / len(self._fps_samples)) if self._fps_samples else 0.0
        return {
            "timestamp": datetime.fromisoformat(self._result_payload["timestamp"]),
            "total": int(counts["total"]),
            "passed": int(counts["passed"]),
            "failed": int(counts["failed"]),
            "result": str(self._result_payload["result"]),
            "fps": float(self._result_payload["fps"]),
            "fps_avg_60s": round(fps_avg, 2),
            "uptime_seconds": round(now - self._started_at, 2),
            "records_saved": int(self._records_saved),
            "mode": self._mode,
        }

    def get_benchmark(self) -> dict[str, Any]:
        now = time.time()
        self._prune_fps_samples(now)
        samples = [v for _, v in self._fps_samples]
        return {
            "window_seconds": 60,
            "sample_count": len(samples),
            "fps_min": round(min(samples), 2) if samples else 0.0,
            "fps_max": round(max(samples), 2) if samples else 0.0,
            "fps_avg": round(sum(samples) / len(samples), 2) if samples else 0.0,
            "uptime_seconds": round(now - self._started_at, 2),
            "records_saved": int(self._records_saved),
            "mode": self._mode,
        }

    def _prune_fps_samples(self, now: float) -> None:
        cutoff = now - 60.0
        while self._fps_samples and self._fps_samples[0][0] < cutoff:
            self._fps_samples.popleft()

    def get_history(self, date_filter: str | None = None) -> list[dict]:
        return self.history.list(date_filter)

    async def register(self, websocket: Any) -> None:
        self._clients.add(websocket)
        await websocket.send_json(self._result_payload)

    def unregister(self, websocket: Any) -> None:
        self._clients.discard(websocket)

    async def _broadcast(self, payload: dict[str, Any]) -> None:
        if not self._clients:
            return
        stale: list[Any] = []
        for ws in self._clients:
            try:
                await ws.send_json(payload)
            except Exception:
                stale.append(ws)
        for ws in stale:
            self._clients.discard(ws)

    def _apply_adjustments(self, frame: np.ndarray) -> np.ndarray:
        out = frame
        if self.config.brightness != 0:
            out = cv2.convertScaleAbs(out, alpha=1.0, beta=self.config.brightness)
        if self.config.saturation != 0:
            hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV).astype("float32")
            h, s, v = cv2.split(hsv)
            alpha = (100 + self.config.saturation) / 100.0
            s = np.clip(s * alpha, 0, 255)
            hsv = cv2.merge([h, s, v])
            out = cv2.cvtColor(hsv.astype("uint8"), cv2.COLOR_HSV2BGR)
        return out

    def _run_detector(self, frame: np.ndarray) -> tuple[np.ndarray, list[str]]:
        if self._detector is None:
            return frame, []
        try:
            results = self._detector(frame, verbose=False, conf=self.config.confidence)
            labels: list[str] = []
            if results and len(results) > 0:
                det = results[0].obb if results[0].obb is not None else results[0].boxes
                if det is not None:
                    cls_indices = det.cls.cpu().numpy()
                    names = results[0].names
                    labels = [str(names[int(cls_id)]).lower() for cls_id in cls_indices]
                annotated = results[0].plot(line_width=2, conf=False)
            else:
                annotated = frame
            return annotated, labels
        except Exception:
            return frame, []

    def _evaluate_result(self, labels: list[str]) -> tuple[str, int, int, int]:
        total = len(labels)
        if total == 0:
            return "WAIT", 0, 0, 0

        passed = sum(1 for label in labels if label == "full")
        failed = total - passed

        if total < self.config.expected_slots:
            return "MISSING", total, passed, failed
        if failed == 0:
            return "OK", total, passed, failed
        if passed / max(total, 1) > 0.5:
            return "NG_L", total, passed, failed
        return "NG_H", total, passed, failed

    @staticmethod
    def _encode_frame(frame: np.ndarray) -> str:
        ok, buffer = cv2.imencode(".jpg", frame)
        if not ok:
            return ""
        return base64.b64encode(buffer).decode("ascii")

    def _store_record(
        self,
        *,
        trigger_source: str,
        result: str,
        total: int,
        passed: int,
        failed: int,
    ) -> tuple[bool, str]:
        if result == "WAIT":
            return False, "No valid result yet"

        self.history.insert(
            total=total,
            passed=passed,
            failed=failed,
            result=result,
            mode=self._mode,
            trigger_source=trigger_source,
        )
        self._plc.write_result(result)
        self._records_saved += 1
        return True, ""

    def _store_latest_record(self, trigger_source: str) -> tuple[bool, str]:
        counts = self._result_payload["counts"]
        result = str(self._result_payload["result"])
        return self._store_record(
            trigger_source=trigger_source,
            result=result,
            total=int(counts["total"]),
            passed=int(counts["passed"]),
            failed=int(counts["failed"]),
        )

    def trigger_manual(self) -> tuple[bool, str]:
        return self._store_latest_record("manual")

    def continue_manual(self) -> dict[str, Any]:
        self._prev_trigger_req = False
        return {"continued": True, "mode": self._mode}

    async def start(self) -> None:
        if self._task is not None:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop(), name="monitor-loop")

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _loop(self) -> None:
        cap = cv2.VideoCapture(self.config.camera_source)
        self._camera_connected = cap.isOpened()
        self._camera_source_active = self.config.camera_source
        prev_time = time.time()
        while self._running:
            if self._camera_source_active != self.config.camera_source:
                cap.release()
                cap = cv2.VideoCapture(self.config.camera_source)
                self._camera_source_active = self.config.camera_source
                self._camera_connected = cap.isOpened()

            if not cap.isOpened():
                cap.release()
                cap = cv2.VideoCapture(self.config.camera_source)
                self._camera_source_active = self.config.camera_source
                self._camera_connected = cap.isOpened()
                await asyncio.sleep(0.5)
                continue

            ok, raw_frame = cap.read()
            if not ok:
                self._camera_connected = False
                self._last_error = "Camera frame read failed"
                await asyncio.sleep(0.05)
                continue
            self._camera_connected = True
            self._last_error = None

            frame = self._apply_adjustments(raw_frame)
            annotated, labels = await asyncio.to_thread(self._run_detector, frame.copy())
            result, total, passed, failed = self._evaluate_result(labels)

            now = time.time()
            fps = 1.0 / max(now - prev_time, 1e-6)
            prev_time = now
            self._fps_samples.append((now, fps))

            plc_state = self._plc.poll_status()
            trigger_req = bool(plc_state.get("trigger_req", False))
            if (
                self._mode == "auto_demo"
                and trigger_req
                and not self._prev_trigger_req
                and result != "WAIT"
                and (now - self._last_auto_save_at) > 0.8
            ):
                self._store_record(trigger_source="auto_demo", result=result, total=total, passed=passed, failed=failed)
                self._last_auto_save_at = now
            self._prev_trigger_req = trigger_req

            self._result_payload = {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "frame_base64": self._encode_frame(annotated),
                "labels": labels,
                "result": result,
                "counts": {"total": total, "passed": passed, "failed": failed},
                "fps": round(fps, 2),
                "plc_state": plc_state,
                "mode": self._mode,
            }
            await self._broadcast(self._result_payload)
            await asyncio.sleep(0.01)

        cap.release()
        self._camera_connected = False
