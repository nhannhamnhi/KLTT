import { exportHistoryUrl } from "../api";

/**
 * FloatingPanels — Các panel nổi khi bấm toolbar buttons
 * Hỗ trợ 4 panels: AI Model, Camera, PLC, History
 */
export default function FloatingPanels({
  openPanel, setOpenPanel, config, setConfig,
  plcForm, setPlcForm, handleSaveConfig,
  handleSetRealPlc, handleSetDemoPlc,
  history, historyDate, setHistoryDate,
  loadHistory, handleClearHistory,
}) {
  if (!openPanel) return null;
  const close = () => setOpenPanel(null);

  /* Render nội dung theo loại panel */
  function renderBody() {
    switch (openPanel) {
      case "ai":
        return (
          <div className="panel-form-grid">
            <div className="form-field">
              <label>Confidence Threshold</label>
              <input type="number" step="0.01" min="0.05" max="0.99"
                value={config.confidence}
                onChange={(e) => setConfig((c) => ({ ...c, confidence: e.target.value }))} />
            </div>
            <div className="form-field">
              <label>Expected Slots</label>
              <input type="number" min="1" max="20"
                value={config.expected_slots}
                onChange={(e) => setConfig((c) => ({ ...c, expected_slots: e.target.value }))} />
            </div>
            <div className="form-field" style={{ gridColumn: "span 2" }}>
              <label>Model Path</label>
              <input type="text" value={config.model_path}
                onChange={(e) => setConfig((c) => ({ ...c, model_path: e.target.value }))}
                placeholder="Đường dẫn tới file model (.pt)" />
            </div>
            <div style={{ gridColumn: "span 2", display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 8 }}>
              <button className="btn btn-primary" onClick={() => { handleSaveConfig(); close(); }}>LƯU CẤU HÌNH</button>
            </div>
          </div>
        );

      case "camera":
        return (
          <div className="panel-form-grid">
            <div className="form-field">
              <label>Camera Source</label>
              <input type="number" value={config.camera_source}
                onChange={(e) => setConfig((c) => ({ ...c, camera_source: e.target.value }))} />
            </div>
            <div className="form-field">
              <label>Brightness</label>
              <input type="number" min="-100" max="100" value={config.brightness}
                onChange={(e) => setConfig((c) => ({ ...c, brightness: e.target.value }))} />
            </div>
            <div className="form-field">
              <label>Saturation</label>
              <input type="number" min="-100" max="100" value={config.saturation}
                onChange={(e) => setConfig((c) => ({ ...c, saturation: e.target.value }))} />
            </div>
            <div style={{ gridColumn: "span 2", display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 8 }}>
              <button className="btn btn-primary" onClick={() => { handleSaveConfig(); close(); }}>LƯU CẤU HÌNH</button>
            </div>
          </div>
        );

      case "plc":
        return (
          <div className="panel-form-grid">
            <div className="form-field">
              <label>PLC IP</label>
              <input type="text" value={plcForm.ip}
                onChange={(e) => setPlcForm((f) => ({ ...f, ip: e.target.value }))} />
            </div>
            <div className="form-field">
              <label>Rack</label>
              <input type="number" value={plcForm.rack}
                onChange={(e) => setPlcForm((f) => ({ ...f, rack: e.target.value }))} />
            </div>
            <div className="form-field">
              <label>Slot</label>
              <input type="number" value={plcForm.slot}
                onChange={(e) => setPlcForm((f) => ({ ...f, slot: e.target.value }))} />
            </div>
            <div style={{ gridColumn: "span 2", display: "flex", gap: 8, marginTop: 8 }}>
              <button className="btn btn-secondary" onClick={() => { handleSetDemoPlc(); close(); }}>DEMO PLC</button>
              <button className="btn btn-primary" onClick={() => { handleSetRealPlc(); close(); }}>KẾT NỐI REAL</button>
            </div>
          </div>
        );

      case "history":
        return (
          <>
            <div style={{ display: "flex", gap: 8, marginBottom: 12, alignItems: "flex-end" }}>
              <div className="form-field" style={{ flex: 1 }}>
                <label>Ngày</label>
                <input type="date" value={historyDate} onChange={(e) => setHistoryDate(e.target.value)} />
              </div>
              <button className="btn btn-secondary" onClick={loadHistory}>TẢI</button>
              <button className="btn btn-ghost" onClick={handleClearHistory}>XÓA</button>
              <a href={exportHistoryUrl(historyDate)} target="_blank" rel="noreferrer"
                className="btn btn-secondary" style={{ textDecoration: "none" }}>XUẤT CSV</a>
            </div>
            <div className="history-table-wrap">
              <table className="history-table">
                <thead>
                  <tr><th>ID</th><th>Thời gian</th><th>Kết quả</th><th>Tổng</th><th>Đạt</th><th>Lỗi</th><th>Mode</th><th>Nguồn</th></tr>
                </thead>
                <tbody>
                  {history.length === 0 ? (
                    <tr><td colSpan={8} style={{ textAlign: "center", color: "var(--text-muted)" }}>Chưa có dữ liệu</td></tr>
                  ) : history.map((row) => (
                    <tr key={row.id}>
                      <td>{row.id}</td><td>{row.timestamp}</td><td>{row.result}</td>
                      <td>{row.total}</td><td>{row.passed}</td><td>{row.failed}</td>
                      <td>{row.mode}</td><td>{row.trigger_source}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        );

      default:
        return null;
    }
  }

  const titles = { ai: "Cài Đặt Mô Hình AI", camera: "Cài Đặt Camera", plc: "Kết Nối PLC", history: "Lịch Sử Kiểm Tra" };

  return (
    <>
      <div className="floating-backdrop" onClick={close} />
      <div className="floating-panel" style={openPanel === "history" ? { width: 720 } : undefined}>
        <div className="floating-panel__header">
          <span className="text-h2-label">{titles[openPanel]}</span>
          <button className="floating-panel__close" onClick={close}>✕</button>
        </div>
        <div className="floating-panel__body">{renderBody()}</div>
      </div>
    </>
  );
}
