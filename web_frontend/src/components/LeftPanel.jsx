/**
 * LeftPanel — Khu vực bên trái (75%)
 * Chứa 2 camera feeds (gốc + AI) và thanh điều chỉnh camera
 */
export default function LeftPanel({ frameSrc, config, setConfig, handleSaveConfig }) {
  /* Xử lý thay đổi slider — cập nhật config rồi auto-save */
  const handleSlider = (key, value) => {
    setConfig((prev) => ({ ...prev, [key]: Number(value) }));
  };

  /* Reset sliders về 0 */
  const handleReset = () => {
    setConfig((prev) => ({ ...prev, brightness: 0, saturation: 0 }));
  };

  return (
    <div className="left-panel">
      {/* Camera Feeds Row */}
      <div className="camera-feeds">
        {/* Camera Gốc */}
        <div className="camera-feed">
          <div className="camera-feed__header">
            <span className="text-label-caps" style={{ color: "var(--text-secondary)" }}>
              CAMERA GỐC
            </span>
            <div className={`status-dot ${frameSrc ? "ok" : "err"}`} />
          </div>
          <div className="camera-feed__body">
            {frameSrc ? (
              <img src={frameSrc} alt="Camera gốc" style={{ filter: "grayscale(0.3)", opacity: 0.9 }} />
            ) : (
              <span className="camera-feed__placeholder">Chưa có tín hiệu camera</span>
            )}
          </div>
        </div>

        {/* AI Xử Lý */}
        <div className="camera-feed active">
          <div className="camera-feed__header active">
            <span className="text-label-caps" style={{ color: "var(--cyan-electric)" }}>
              AI XỬ LÝ
            </span>
            <span className="text-data-sm" style={{ color: "var(--cyan-electric)" }}>
              LIVE
            </span>
          </div>
          <div className="camera-feed__body">
            {frameSrc ? (
              <img src={frameSrc} alt="AI xử lý" />
            ) : (
              <span className="camera-feed__placeholder">Chờ dữ liệu AI...</span>
            )}
          </div>
        </div>
      </div>

      {/* Camera Adjustment Card */}
      <div className="camera-adjust">
        <div className="camera-adjust__header">
          <span className="text-h2-label">Điều chỉnh Camera</span>
          <button className="btn btn-reset text-label-caps" onClick={handleReset}>
            ĐẶT LẠI
          </button>
        </div>
        <div className="camera-adjust__sliders">
          {/* Độ sáng */}
          <div className="slider-row">
            <span className="slider-row__label">Độ sáng</span>
            <input
              className="slider-row__input"
              type="range"
              min="-100"
              max="100"
              value={config.brightness}
              onChange={(e) => handleSlider("brightness", e.target.value)}
              style={{
                background: `linear-gradient(to right, var(--cyan-sky) ${
                  ((Number(config.brightness) + 100) / 200) * 100
                }%, var(--border-industrial) ${((Number(config.brightness) + 100) / 200) * 100}%)`,
              }}
            />
            <span className="slider-row__value">{config.brightness}</span>
          </div>

          {/* Độ bão hòa */}
          <div className="slider-row">
            <span className="slider-row__label">Độ bão hòa</span>
            <input
              className="slider-row__input"
              type="range"
              min="-100"
              max="100"
              value={config.saturation}
              onChange={(e) => handleSlider("saturation", e.target.value)}
              style={{
                background: `linear-gradient(to right, var(--cyan-sky) ${
                  ((Number(config.saturation) + 100) / 200) * 100
                }%, var(--border-industrial) ${((Number(config.saturation) + 100) / 200) * 100}%)`,
              }}
            />
            <span className="slider-row__value">{config.saturation}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
