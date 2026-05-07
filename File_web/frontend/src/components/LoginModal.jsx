import { useState } from "react";

/**
 * LoginModal — Modal đăng nhập để mở khóa control section
 * Xác thực đơn giản: username="admin", password="123"
 */
export default function LoginModal({ show, onClose, onSuccess }) {
  const [user, setUser] = useState("");
  const [pass, setPass] = useState("");
  const [error, setError] = useState("");

  if (!show) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (user === "admin" && pass === "123") {
      setError("");
      setUser("");
      setPass("");
      onSuccess();
    } else {
      setError("Sai tên đăng nhập hoặc mật khẩu!");
    }
  };

  const handleClose = () => {
    setError("");
    setUser("");
    setPass("");
    onClose();
  };

  return (
    <div className="modal-backdrop" onClick={handleClose}>
      <div className="login-modal" onClick={(e) => e.stopPropagation()}>
        <div className="login-modal__header">
          <div className="login-modal__icon">
            <span className="material-symbols-outlined">shield_lock</span>
          </div>
          <div className="login-modal__title">Xác Thực Hệ Thống</div>
          <div className="login-modal__subtitle">Nhập thông tin để mở khóa điều khiển</div>
        </div>
        <form className="login-modal__body" onSubmit={handleSubmit}>
          {error && <div className="login-modal__error">{error}</div>}
          <div className="form-field">
            <label>Tên đăng nhập</label>
            <input
              type="text"
              value={user}
              onChange={(e) => setUser(e.target.value)}
              placeholder="admin"
              autoFocus
            />
          </div>
          <div className="form-field">
            <label>Mật khẩu</label>
            <input
              type="password"
              value={pass}
              onChange={(e) => setPass(e.target.value)}
              placeholder="••••"
            />
          </div>
          <div className="login-modal__actions">
            <button type="button" className="btn btn-secondary" onClick={handleClose}>HỦY</button>
            <button type="submit" className="btn btn-primary">ĐĂNG NHẬP</button>
          </div>
        </form>
      </div>
    </div>
  );
}
