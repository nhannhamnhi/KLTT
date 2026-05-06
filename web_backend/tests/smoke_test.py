from fastapi.testclient import TestClient

from web_backend.app.main import app


def test_smoke_core_endpoints() -> None:
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        health_data = health.json()
        assert "plc_adapter" in health_data
        assert "camera_source" in health_data

        stats = client.get("/stats")
        assert stats.status_code == 200
        stats_data = stats.json()
        assert "fps_avg_60s" in stats_data
        assert "uptime_seconds" in stats_data
        assert "records_saved" in stats_data

        benchmark = client.get("/benchmark")
        assert benchmark.status_code == 200
        benchmark_data = benchmark.json()
        assert "fps_avg" in benchmark_data
        assert "fps_min" in benchmark_data
        assert "fps_max" in benchmark_data

        assert client.get("/config").status_code == 200
        assert client.post("/mode", json={"mode": "manual"}).status_code == 200
        assert client.post("/config", json={"confidence": 0.6, "expected_slots": 6}).status_code == 200
        assert client.get("/history").status_code == 200
        assert client.get("/history/export").status_code == 200
        assert client.delete("/history").status_code == 200
        assert client.post("/plc/demo").status_code == 200
