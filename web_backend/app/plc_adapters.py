from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


RESULT_MAP = {"WAIT": 0, "OK": 1, "NG_L": 2, "NG_H": 3, "MISSING": 4}


class PLCAdapter(Protocol):
    def set_mode(self, mode: str) -> None: ...

    def write_result(self, result: str) -> bool: ...

    def poll_status(self) -> dict: ...


@dataclass
class DemoPLCAdapter:
    mode: str = "manual"
    last_result: str = "WAIT"
    trigger_req: bool = False
    connected: bool = True
    running: bool = True
    _tick: int = 0
    _trigger_latch: int = 0

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        self.trigger_req = False
        self._trigger_latch = 0

    def write_result(self, result: str) -> bool:
        self.last_result = result
        # Simulate a short pulse that PLC consumed data.
        self.trigger_req = True
        self._trigger_latch = 3
        return True

    def poll_status(self) -> dict:
        self._tick += 1
        if self.mode == "auto_demo" and self._tick % 30 == 0 and self._trigger_latch == 0:
            self.trigger_req = True
            self._trigger_latch = 2

        if self._trigger_latch > 0:
            self._trigger_latch -= 1
        else:
            self.trigger_req = False

        return {
            "adapter": "demo",
            "connected": self.connected,
            "running": self.running,
            "auto": self.mode == "auto_demo",
            "manual": self.mode == "manual",
            "trigger_req": self.trigger_req,
            "sensor1": self.mode == "auto_demo" and (self._tick % 11 == 0),
            "sensor2": self.mode == "auto_demo" and (self._tick % 17 == 0),
            "last_result": self.last_result,
        }


@dataclass
class RealPLCAdapter:
    ip: str = "192.168.0.1"
    rack: int = 0
    slot: int = 1
    mode: str = "manual"
    _client: object | None = None
    _connected: bool = False
    _snap7_error: str | None = None
    _const: dict = field(default_factory=lambda: {"db_get": 1, "db_put": 2, "db_get_size": 3, "db_put_size": 1})

    def __post_init__(self) -> None:
        try:
            import snap7

            self._snap7 = snap7
            self._util = snap7.util
            self._client = snap7.client.Client()
            self._client.connect(self.ip, self.rack, self.slot)
            self._connected = bool(self._client.get_connected())
        except Exception as exc:  # pragma: no cover - hardware-dependent path
            self._connected = False
            self._snap7_error = str(exc)

    def set_mode(self, mode: str) -> None:
        self.mode = mode

    def write_result(self, result: str) -> bool:
        if not self._connected or self._client is None:
            return False
        try:  # pragma: no cover - hardware-dependent path
            result_code = RESULT_MAP.get(result.upper(), 0)
            data = self._client.db_read(self._const["db_get"], 0, self._const["db_get_size"])
            self._util.set_int(data, 0, result_code)
            self._util.set_bool(data, 2, 0, True)
            self._client.db_write(self._const["db_get"], 0, data)
            return True
        except Exception:
            self._connected = False
            return False

    def poll_status(self) -> dict:
        if not self._connected or self._client is None:
            return {
                "adapter": "real",
                "ip": self.ip,
                "rack": self.rack,
                "slot": self.slot,
                "connected": False,
                "running": False,
                "auto": self.mode == "auto_demo",
                "manual": self.mode == "manual",
                "trigger_req": False,
                "sensor1": False,
                "sensor2": False,
                "last_result": "WAIT",
                "error": self._snap7_error or "PLC disconnected",
            }

        try:  # pragma: no cover - hardware-dependent path
            data = self._client.db_read(self._const["db_put"], 0, self._const["db_put_size"])
            return {
                "adapter": "real",
                "ip": self.ip,
                "rack": self.rack,
                "slot": self.slot,
                "connected": True,
                "running": bool(self._util.get_bool(data, 0, 2)),
                "auto": bool(self._util.get_bool(data, 0, 0)),
                "manual": bool(self._util.get_bool(data, 0, 1)),
                "trigger_req": bool(self._util.get_bool(data, 0, 3)),
                "sensor1": bool(self._util.get_bool(data, 0, 4)),
                "sensor2": bool(self._util.get_bool(data, 0, 5)),
                "last_result": "UNKNOWN",
            }
        except Exception as exc:
            self._connected = False
            return {
                "adapter": "real",
                "ip": self.ip,
                "rack": self.rack,
                "slot": self.slot,
                "connected": False,
                "running": False,
                "auto": False,
                "manual": False,
                "trigger_req": False,
                "sensor1": False,
                "sensor2": False,
                "last_result": "WAIT",
                "error": str(exc),
            }
