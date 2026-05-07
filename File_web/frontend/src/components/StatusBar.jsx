/**
 * StatusBar — Thanh trạng thái cố định phía dưới
 * Hiển thị: camera, model, FPS, PLC, mode badge, sensor dots, clock
 */
export default function StatusBar({ health, config, monitor, mode, clock }) {
  const plc = monitor.plc_state || {};

  return (
    <footer className="statusbar">
      {/* Phần trái: thông tin runtime */}
      <div className="statusbar__left">
        <span>Camera: {health?.camera_source != null ? "Đang chạy" : "Ngắt"}</span>
        <span className="statusbar__divider">|</span>
        <span>Mô hình: {config.model_path?.split(/[\\/]/).pop() || "YOLOv8"}</span>
        <span className="statusbar__divider">|</span>
        <span style={{ color: "var(--red-vivid)" }}>FPS: {monitor.fps || 0}</span>
        <span className="statusbar__divider">|</span>
        <span>PLC: {plc.connected ? "Đã kết nối" : "Mất kết nối"}</span>
      </div>

      {/* Phần phải: mode + sensors + clock */}
      <div className="statusbar__right">
        <div className={`mode-badge ${mode === "manual" ? "manual" : "auto"}`}>
          {mode === "manual" ? "THỦ CÔNG" : "TỰ ĐỘNG"}
        </div>
        <div className="sensor-dots">
          {["S0", "S1", "S2"].map((s, i) => {
            const sensorKeys = ["sensor0", "sensor1", "sensor2"];
            const isActive = plc[sensorKeys[i]] ?? false;
            return (
              <div key={s} className="sensor-dot">
                <div className={`status-dot ${isActive ? "ok" : "err"}`} style={{ width: 6, height: 6 }} />
                <span className="text-data-sm" style={{ color: "var(--text-secondary)" }}>{s}</span>
              </div>
            );
          })}
        </div>
        <span className="statusbar__clock">{clock}</span>
      </div>
    </footer>
  );
}
