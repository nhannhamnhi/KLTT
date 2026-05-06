import { useEffect, useMemo, useRef, useState } from "react";
import {
  apiBase,
  clearHistory,
  exportHistoryUrl,
  fetchBenchmark,
  fetchConfig,
  fetchHealth,
  fetchHistory,
  fetchStats,
  monitorWsUrl,
  postConfig,
  postContinue,
  postMode,
  postTrigger,
  setDemoPlc,
  setRealPlc,
} from "./api";

const EMPTY_MONITOR = {
  timestamp: "",
  frame_base64: "",
  labels: [],
  result: "WAIT",
  counts: { total: 0, passed: 0, failed: 0 },
  fps: 0,
  plc_state: {},
  mode: "manual",
};

export default function App() {
  const [monitor, setMonitor] = useState(EMPTY_MONITOR);
  const [health, setHealth] = useState(null);
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [benchmark, setBenchmark] = useState(null);
  const [historyDate, setHistoryDate] = useState("");
  const [mode, setMode] = useState("manual");
  const [wsState, setWsState] = useState("connecting");
  const [message, setMessage] = useState("");
  const [config, setConfig] = useState({
    camera_source: 0,
    brightness: 0,
    saturation: 0,
    confidence: 0.7,
    expected_slots: 6,
    model_path: "",
  });
  const [activeTab, setActiveTab] = useState("monitor");
  const [plcForm, setPlcForm] = useState({ ip: "192.168.0.1", rack: 0, slot: 1 });

  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);

  const frameSrc = useMemo(() => {
    if (!monitor.frame_base64) return "";
    return `data:image/jpeg;base64,${monitor.frame_base64}`;
  }, [monitor.frame_base64]);

  useEffect(() => {
    loadHealth();
    loadConfig();
    loadHistory();
    loadStats();
    loadBenchmark();
    connectWs();
    const healthTimer = setInterval(loadHealth, 3000);
    const statsTimer = setInterval(loadStats, 3000);
    const benchmarkTimer = setInterval(loadBenchmark, 5000);
    return () => {
      clearInterval(healthTimer);
      clearInterval(statsTimer);
      clearInterval(benchmarkTimer);
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  useEffect(() => {
    const historyTimer = setInterval(() => {
      if (activeTab === "history") {
        loadHistory();
      }
    }, 5000);
    return () => clearInterval(historyTimer);
  }, [activeTab, historyDate]);

  useEffect(() => {
    setMode(monitor.mode || "manual");
  }, [monitor.mode]);

  function connectWs() {
    setWsState("connecting");
    const ws = new WebSocket(monitorWsUrl());
    wsRef.current = ws;

    ws.onopen = () => setWsState("connected");
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setMonitor(data);
      } catch {
        // Ignore malformed payloads.
      }
    };
    ws.onerror = () => setWsState("error");
    ws.onclose = () => {
      setWsState("disconnected");
      reconnectTimerRef.current = setTimeout(connectWs, 1500);
    };
  }

  async function loadHealth() {
    try {
      const data = await fetchHealth();
      setHealth(data);
    } catch (err) {
      setMessage(`Health check lỗi: ${err.message}`);
    }
  }

  async function loadConfig() {
    try {
      const data = await fetchConfig();
      setConfig({
        camera_source: data.camera_source ?? 0,
        brightness: data.brightness ?? 0,
        saturation: data.saturation ?? 0,
        confidence: data.confidence ?? 0.7,
        expected_slots: data.expected_slots ?? 6,
        model_path: data.model_path ?? "",
      });
    } catch (err) {
      setMessage(`Load config lỗi: ${err.message}`);
    }
  }

  async function loadHistory() {
    try {
      const data = await fetchHistory(historyDate);
      setHistory(data);
    } catch (err) {
      setMessage(`Load history lỗi: ${err.message}`);
    }
  }

  async function loadStats() {
    try {
      const data = await fetchStats();
      setStats(data);
    } catch {
      // Ignore transient stats fetch errors.
    }
  }

  async function loadBenchmark() {
    try {
      const data = await fetchBenchmark();
      setBenchmark(data);
    } catch {
      // Ignore transient benchmark fetch errors.
    }
  }

  async function handleTrigger() {
    try {
      const res = await postTrigger();
      if (!res.saved) {
        setMessage(`Trigger chưa lưu: ${res.reason || "unknown reason"}`);
      } else {
        setMessage("Đã trigger và lưu record.");
      }
      await loadHistory();
    } catch (err) {
      setMessage(`Trigger lỗi: ${err.message}`);
    }
  }

  async function handleContinue() {
    try {
      await postContinue();
      setMessage("Đã continue.");
    } catch (err) {
      setMessage(`Continue lỗi: ${err.message}`);
    }
  }

  async function handleSetMode(nextMode) {
    try {
      const res = await postMode(nextMode);
      setMode(res.mode);
      setMessage(`Đã đổi mode: ${res.mode}`);
    } catch (err) {
      setMessage(`Đổi mode lỗi: ${err.message}`);
    }
  }

  async function handleSaveConfig() {
    try {
      await postConfig({
        camera_source: Number(config.camera_source),
        brightness: Number(config.brightness),
        saturation: Number(config.saturation),
        confidence: Number(config.confidence),
        expected_slots: Number(config.expected_slots),
        model_path: config.model_path.trim() || null,
      });
      setMessage("Đã cập nhật config backend.");
    } catch (err) {
      setMessage(`Lưu config lỗi: ${err.message}`);
    }
  }

  async function handleSetDemoPlc() {
    try {
      await setDemoPlc();
      setMessage("Đã chuyển PLC adapter sang DEMO.");
    } catch (err) {
      setMessage(`Đổi PLC demo lỗi: ${err.message}`);
    }
  }

  async function handleSetRealPlc() {
    try {
      await setRealPlc({
        ip: plcForm.ip.trim(),
        rack: Number(plcForm.rack),
        slot: Number(plcForm.slot),
      });
      setMessage("Đã chuyển PLC adapter sang REAL.");
    } catch (err) {
      setMessage(`Đổi PLC real lỗi: ${err.message}`);
    }
  }

  async function handleClearHistory() {
    try {
      const res = await clearHistory();
      setMessage(`Đã xóa ${res.cleared_rows} dòng history.`);
      await loadHistory();
    } catch (err) {
      setMessage(`Xóa history lỗi: ${err.message}`);
    }
  }

  function renderMonitorTab() {
    return (
      <section className="card-grid">
        <div className="card monitor-card">
          <h3>Monitor</h3>
          {frameSrc ? <img src={frameSrc} alt="monitor" className="monitor-image" /> : <div className="placeholder">Chưa có frame.</div>}
          <div className="row">
            <span className={`result-tag result-${monitor.result.toLowerCase()}`}>{monitor.result}</span>
            <span>FPS: {monitor.fps || 0}</span>
            <span>Mode: {mode}</span>
          </div>
        </div>
        <div className="card">
          <h3>Realtime Stats</h3>
          <p>Tổng: {monitor.counts.total}</p>
          <p>Đạt: {monitor.counts.passed}</p>
          <p>Lỗi: {monitor.counts.failed}</p>
          <p>Labels: {monitor.labels.join(", ") || "--"}</p>
          <p>Timestamp: {monitor.timestamp || "--"}</p>
          <p>FPS avg 60s: {stats?.fps_avg_60s ?? "--"}</p>
          <p>Uptime (s): {stats?.uptime_seconds ?? "--"}</p>
          <p>Saved records: {stats?.records_saved ?? "--"}</p>
          <p>Benchmark min/max: {benchmark ? `${benchmark.fps_min} / ${benchmark.fps_max}` : "--"}</p>
        </div>
      </section>
    );
  }

  function renderControlTab() {
    const plc = monitor.plc_state || {};
    return (
      <section className="card-grid">
        <div className="card">
          <h3>Control</h3>
          <div className="button-row">
            <button onClick={handleTrigger}>Trigger</button>
            <button onClick={handleContinue}>Continue</button>
          </div>
          <div className="button-row">
            <button className={mode === "manual" ? "active" : ""} onClick={() => handleSetMode("manual")}>
              Manual
            </button>
            <button className={mode === "auto_demo" ? "active" : ""} onClick={() => handleSetMode("auto_demo")}>
              Auto Demo
            </button>
          </div>
        </div>
        <div className="card">
          <h3>PLC State ({plc.adapter || "demo"})</h3>
          <p>Connected: {String(plc.connected ?? false)}</p>
          <p>Running: {String(plc.running ?? false)}</p>
          <p>Auto: {String(plc.auto ?? false)}</p>
          <p>Manual: {String(plc.manual ?? false)}</p>
          <p>TriggerReq: {String(plc.trigger_req ?? false)}</p>
          <p>Sensor1: {String(plc.sensor1 ?? false)}</p>
          <p>Sensor2: {String(plc.sensor2 ?? false)}</p>
          <p>PLC endpoint: {plc.ip ? `${plc.ip} (${plc.rack}/${plc.slot})` : "--"}</p>
          <div className="row">
            <button onClick={handleSetDemoPlc}>Use Demo PLC</button>
          </div>
          <div className="form-grid">
            <label>
              PLC IP
              <input type="text" value={plcForm.ip} onChange={(e) => setPlcForm({ ...plcForm, ip: e.target.value })} />
            </label>
            <label>
              Rack
              <input type="number" value={plcForm.rack} onChange={(e) => setPlcForm({ ...plcForm, rack: e.target.value })} />
            </label>
            <label>
              Slot
              <input type="number" value={plcForm.slot} onChange={(e) => setPlcForm({ ...plcForm, slot: e.target.value })} />
            </label>
          </div>
          <button onClick={handleSetRealPlc}>Use Real PLC</button>
        </div>
      </section>
    );
  }

  function renderHistoryTab() {
    return (
      <section className="card">
        <h3>History</h3>
        <div className="row">
          <input type="date" value={historyDate} onChange={(e) => setHistoryDate(e.target.value)} />
          <button onClick={loadHistory}>Load</button>
          <button onClick={handleClearHistory}>Clear</button>
          <a href={exportHistoryUrl(historyDate)} target="_blank" rel="noreferrer" className="button-link">
            Export CSV
          </a>
        </div>
        <div className="history-table-wrap">
          <table className="history-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Time</th>
                <th>Result</th>
                <th>Total</th>
                <th>Passed</th>
                <th>Failed</th>
                <th>Mode</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {history.map((row) => (
                <tr key={row.id}>
                  <td>{row.id}</td>
                  <td>{row.timestamp}</td>
                  <td>{row.result}</td>
                  <td>{row.total}</td>
                  <td>{row.passed}</td>
                  <td>{row.failed}</td>
                  <td>{row.mode}</td>
                  <td>{row.trigger_source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    );
  }

  function renderSettingsTab() {
    return (
      <section className="card">
        <h3>Settings</h3>
        <div className="form-grid">
          <label>
            Camera Source
            <input
              type="number"
              value={config.camera_source}
              onChange={(e) => setConfig({ ...config, camera_source: e.target.value })}
            />
          </label>
          <label>
            Brightness (-100..100)
            <input
              type="number"
              value={config.brightness}
              onChange={(e) => setConfig({ ...config, brightness: e.target.value })}
            />
          </label>
          <label>
            Saturation (-100..100)
            <input
              type="number"
              value={config.saturation}
              onChange={(e) => setConfig({ ...config, saturation: e.target.value })}
            />
          </label>
          <label>
            Confidence (0.05..0.99)
            <input
              type="number"
              step="0.01"
              value={config.confidence}
              onChange={(e) => setConfig({ ...config, confidence: e.target.value })}
            />
          </label>
          <label>
            Expected Slots
            <input
              type="number"
              value={config.expected_slots}
              onChange={(e) => setConfig({ ...config, expected_slots: e.target.value })}
            />
          </label>
          <label className="wide">
            Model Path (optional)
            <input
              type="text"
              value={config.model_path}
              onChange={(e) => setConfig({ ...config, model_path: e.target.value })}
            />
          </label>
        </div>
        <button onClick={handleSaveConfig}>Save Config</button>
      </section>
    );
  }

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>KLTT Web Monitor</h1>
          <p>Backend: {apiBase}</p>
        </div>
        <div className="status-group">
          <span className={`pill ${wsState}`}>WS: {wsState}</span>
          <span className="pill">API: {health?.status || "--"}</span>
          <span className="pill">PLC: {health?.plc_adapter || "--"}</span>
          <span className="pill">Cam: {health?.camera_source ?? "--"}</span>
          <span className="pill">Clients: {health?.websocket_clients ?? 0}</span>
        </div>
      </header>
      {health?.last_error ? <div className="error-banner">Warning: {health.last_error}</div> : null}

      <nav className="tabs">
        {[
          ["monitor", "Monitor"],
          ["control", "Control"],
          ["history", "History"],
          ["settings", "Settings"],
        ].map(([key, label]) => (
          <button key={key} className={activeTab === key ? "active" : ""} onClick={() => setActiveTab(key)}>
            {label}
          </button>
        ))}
      </nav>

      <main>
        {activeTab === "monitor" && renderMonitorTab()}
        {activeTab === "control" && renderControlTab()}
        {activeTab === "history" && renderHistoryTab()}
        {activeTab === "settings" && renderSettingsTab()}
      </main>

      <footer className="message-bar">{message || "Ready."}</footer>
    </div>
  );
}
