/**
 * TopBar — Thanh công cụ phía trên cùng
 * Hiển thị logo, 4 nút icon (AI/Camera/PLC/History), và status pills
 */
export default function TopBar({ wsState, health, openPanel, setOpenPanel, mode }) {
  /* Danh sách toolbar buttons */
  const toolbarButtons = [
    {
      id: "ai",
      label: "AI MODEL",
      icon: (
        <svg fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
          <circle cx="12" cy="5" r="3" />
          <circle cx="5" cy="19" r="3" />
          <circle cx="19" cy="19" r="3" />
          <path d="M10.3 7.8L6.7 16.2M13.7 7.8l3.6 8.4" />
        </svg>
      ),
    },
    {
      id: "camera",
      label: "CAMERA",
      icon: (
        <svg fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
          <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2v11z" />
          <circle cx="12" cy="13" r="4" />
        </svg>
      ),
    },
    {
      id: "plc",
      label: "PLC",
      icon: (
        <svg fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
          <path d="M4 2v20M20 2v20M4 12h16" />
        </svg>
      ),
    },
    {
      id: "history",
      label: "HISTORY",
      icon: (
        <svg fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
          <path d="M12 8v4l3 3m-11.95-2a9 9 0 1 0 1.36-6.36L3 8m0-5v5h5" />
        </svg>
      ),
    },
  ];

  /* Tính trạng thái connection cho các pill */
  const pills = [
    { label: "WS", ok: wsState === "connected" },
    { label: "API", ok: health?.status === "ok" },
    { label: "PLC", ok: health?.plc_connected !== false },
    { label: "CAM", ok: health?.camera_source != null },
  ];

  /* Toggle panel: bấm nút đang mở → đóng, bấm nút khác → mở panel mới */
  const togglePanel = (id) => {
    setOpenPanel((prev) => (prev === id ? null : id));
  };

  return (
    <header className="topbar">
      {/* Logo + Title */}
      <div style={{ flex: 1, display: "flex", alignItems: "center" }}>
        <span className="topbar__title">HỆ THỐNG KIỂM TRA VỈ THUỐC</span>
      </div>

      {/* Toolbar Icon Buttons */}
      <div className="topbar__center">
        {toolbarButtons.map((btn) => (
          <button
            key={btn.id}
            className={`topbar__icon-btn${openPanel === btn.id ? " active" : ""}`}
            onClick={() => togglePanel(btn.id)}
            title={btn.label}
          >
            {btn.icon}
            <span>{btn.label}</span>
          </button>
        ))}
      </div>

      {/* Status Pills */}
      <div className="topbar__pills" style={{ flex: 1, justifyContent: "flex-end" }}>
        {pills.map((p) => (
          <div key={p.label} className="status-pill">
            <div className={`status-dot ${p.ok ? "ok" : "err"}`} />
            <span>{p.label}</span>
          </div>
        ))}
      </div>
    </header>
  );
}
