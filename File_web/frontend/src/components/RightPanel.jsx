/**
 * RightPanel — Khu vực bên phải (25%)
 * Chứa result badge, stat counters, và control section
 */
export default function RightPanel({
  monitor,
  authenticated,
  setShowLoginModal,
  handleTrigger,
  handleContinue,
}) {
  /* Map result code → Vietnamese label + CSS class */
  const resultMap = {
    WAIT: { label: "CHỜ", cls: "wait" },
    OK: { label: "ĐẠT", cls: "ok" },
    NG_L: { label: "LỖI NHẸ", cls: "ng_l" },
    NG_H: { label: "LỖI NẶNG", cls: "ng_h" },
    MISSING: { label: "THIẾU", cls: "missing" },
  };

  const result = resultMap[monitor.result] || resultMap.WAIT;
  const counts = monitor.counts || { total: 0, passed: 0, failed: 0 };

  /* Badge accent color — lấy từ border-color tương ứng */
  const accentColors = {
    wait: "var(--gray-muted)",
    ok: "var(--green-neon)",
    ng_l: "var(--amber-warning)",
    ng_h: "var(--red-vivid)",
    missing: "var(--purple-violet)",
  };

  return (
    <div className="right-panel">
      {/* Result Badge — hiển thị kết quả kiểm tra */}
      <div className={`result-badge ${result.cls}`}>
        <div className="result-badge__accent" style={{ background: accentColors[result.cls] }} />
        <span className="result-badge__label">{result.label}</span>
        <div className="result-badge__meta">
          <span>FPS: {monitor.fps || 0}</span>
          <span>T/S: {monitor.timestamp?.split(" ")[1] || "--:--:--"}</span>
        </div>
      </div>

      {/* Stat Counters — thống kê tổng/đạt/lỗi */}
      <div className="stat-card">
        <div className="stat-row">
          <span className="text-label-caps stat-row__label">TỔNG SỐ</span>
          <span className="stat-row__value" style={{ color: "white" }}>
            {counts.total.toLocaleString()}
          </span>
        </div>
        <div className="stat-row">
          <span className="text-label-caps stat-row__label">ĐẠT</span>
          <span className="stat-row__value" style={{ color: "var(--green-neon)" }}>
            {counts.passed.toLocaleString()}
          </span>
        </div>
        <div className="stat-row">
          <span className="text-label-caps stat-row__label">LỖI</span>
          <span className="stat-row__value" style={{ color: "var(--red-vivid)" }}>
            {counts.failed.toLocaleString()}
          </span>
        </div>
      </div>

      {/* Control Section — nút điều khiển máy */}
      <div className="control-section">
        {!authenticated ? (
          /* Chưa đăng nhập → hiện nút lock */
          <button className="btn btn-login text-label-caps" onClick={() => setShowLoginModal(true)}>
            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>lock</span>
            ĐĂNG NHẬP
          </button>
        ) : (
          /* Đã đăng nhập → hiện các nút điều khiển */
          <>
            <button className="btn btn-login text-label-caps" style={{ borderColor: "var(--green-neon)", color: "var(--green-neon)" }}>
              <span className="material-symbols-outlined" style={{ fontSize: 16 }}>lock_open</span>
              ĐÃ XÁC THỰC
            </button>
            <div className="btn-grid-2">
              <button className="btn btn-primary" onClick={handleTrigger}>KÍCH HOẠT</button>
              <button className="btn btn-secondary" onClick={handleContinue}>TIẾP TỤC</button>
            </div>
            <button className="btn btn-secondary btn-full">BĂNG TẢI</button>
            <div className="btn-grid-2">
              <button className="btn btn-ghost">XI LANH 1</button>
              <button className="btn btn-ghost">XI LANH 2</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
