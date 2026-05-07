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

import TopBar from "./components/TopBar";
import LeftPanel from "./components/LeftPanel";
import RightPanel from "./components/RightPanel";
import FloatingPanels from "./components/FloatingPanels";
import LoginModal from "./components/LoginModal";
import StatusBar from "./components/StatusBar";

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
  /* ====== STATE GIỮ NGUYÊN từ bản cũ ====== */
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
  const [plcForm, setPlcForm] = useState({ ip: "192.168.0.1", rack: 0, slot: 1 });

  /* ====== STATE MỚI — thêm vào, không thay thế ====== */
  const [authenticated, setAuthenticated] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [openPanel, setOpenPanel] = useState(null); // "ai"|"camera"|"plc"|"history"|null
  const [clock, setClock] = useState("");

  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);

  const frameSrc = useMemo(() => {
    if (!monitor.frame_base64) return "";
    return `data:image/jpeg;base64,${monitor.frame_base64}`;
  }, [monitor.frame_base64]);

  /* ====== useEffect GIỮ NGUYÊN ====== */
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
      if (openPanel === "history") {
        loadHistory();
      }
    }, 5000);
    return () => clearInterval(historyTimer);
  }, [openPanel, historyDate]);

  useEffect(() => {
    setMode(monitor.mode || "manual");
  }, [monitor.mode]);

  /* ====== useEffect MỚI — đồng hồ realtime ====== */
  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setClock(now.toLocaleTimeString("vi-VN", { hour12: false }));
    };
    updateClock();
    const timer = setInterval(updateClock, 1000);
    return () => clearInterval(timer);
  }, []);

  /* ====== HANDLER FUNCTIONS GIỮ NGUYÊN 100% ====== */
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
        // Bỏ qua payload lỗi format
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
      // Bỏ qua lỗi stats tạm thời
    }
  }

  async function loadBenchmark() {
    try {
      const data = await fetchBenchmark();
      setBenchmark(data);
    } catch {
      // Bỏ qua lỗi benchmark tạm thời
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

  /* ====== RENDER — Layout mới theo Stitch design ====== */
  return (
    <div className="app-shell">
      {/* CRT Scan Line Overlay */}
      <div className="scan-lines" />

      {/* Thanh công cụ phía trên */}
      <TopBar
        wsState={wsState}
        health={health}
        openPanel={openPanel}
        setOpenPanel={setOpenPanel}
        mode={mode}
      />

      {/* Nội dung chính — 2 cột */}
      <main className="main-content">
        <LeftPanel
          frameSrc={frameSrc}
          config={config}
          setConfig={setConfig}
          handleSaveConfig={handleSaveConfig}
        />
        <RightPanel
          monitor={monitor}
          authenticated={authenticated}
          setShowLoginModal={setShowLoginModal}
          handleTrigger={handleTrigger}
          handleContinue={handleContinue}
        />
      </main>

      {/* Floating Panels — overlay khi bấm toolbar */}
      <FloatingPanels
        openPanel={openPanel}
        setOpenPanel={setOpenPanel}
        config={config}
        setConfig={setConfig}
        plcForm={plcForm}
        setPlcForm={setPlcForm}
        handleSaveConfig={handleSaveConfig}
        handleSetRealPlc={handleSetRealPlc}
        handleSetDemoPlc={handleSetDemoPlc}
        history={history}
        historyDate={historyDate}
        setHistoryDate={setHistoryDate}
        loadHistory={loadHistory}
        handleClearHistory={handleClearHistory}
        exportHistoryUrl={exportHistoryUrl}
      />

      {/* Login Modal */}
      <LoginModal
        show={showLoginModal}
        onClose={() => setShowLoginModal(false)}
        onSuccess={() => {
          setAuthenticated(true);
          setShowLoginModal(false);
        }}
      />

      {/* Thanh trạng thái phía dưới */}
      <StatusBar
        health={health}
        config={config}
        monitor={monitor}
        mode={mode}
        clock={clock}
      />
    </div>
  );
}
