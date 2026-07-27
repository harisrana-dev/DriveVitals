import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/setsetting.css";
import ThemeToggle from "../components/ThemeToggle";

function Settings() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    email: "",
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });

  const [status, setStatus] = useState("idle"); // idle | success | error
  const [errorMsg, setErrorMsg] = useState("");

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setStatus("idle");
    setErrorMsg("");
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const { email, currentPassword, newPassword, confirmPassword } = formData;

    if (!email || !currentPassword || !newPassword || !confirmPassword) {
      setErrorMsg("Please fill in all fields.");
      setStatus("error");
      return;
    }

    if (newPassword !== confirmPassword) {
      setErrorMsg("New passwords do not match.");
      setStatus("error");
      return;
    }

    if (newPassword.length < 6) {
      setErrorMsg("New password must be at least 6 characters.");
      setStatus("error");
      return;
    }

    // TODO: replace with real API call
    setStatus("success");
  };

  /* ── Success state ── */
  if (status === "success") {
    return (
      <div className="settings-page">
        <div className="settings-theme-btn"><ThemeToggle /></div>

        <div className="settings-success-card">
          {/* Checkmark icon */}
          <div className="success-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2.2"
              strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <h2 className="success-title">Credentials updated</h2>
          <p className="success-sub">
            Your account credentials have been updated successfully.
            For your security, please sign in using your new credentials.
          </p>
          <button className="settings-btn" onClick={() => navigate("/dashboard")}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2.2"
              strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="7" height="7" rx="1"/>
              <rect x="14" y="3" width="7" height="7" rx="1"/>
              <rect x="3" y="14" width="7" height="7" rx="1"/>
              <rect x="14" y="14" width="7" height="7" rx="1"/>
            </svg>
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  /* ── Form state ── */
  return (
    <div className="settings-page">
      <div className="settings-theme-btn"><ThemeToggle /></div>

      <div className="settings-wrapper">

        {/* Header */}
        <div className="settings-header">
          <button className="settings-back-btn" onClick={() => navigate(-1)}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2.2"
              strokeLinecap="round" strokeLinejoin="round">
              <line x1="19" y1="12" x2="5" y2="12"/>
              <polyline points="12 19 5 12 12 5"/>
            </svg>
            Back
          </button>
          <div>
            <h1 className="settings-title">Account Settings</h1>
            <p className="settings-subtitle">Manage your credentials and access security</p>
          </div>
        </div>

        {/* Card */}
        <div className="settings-card">

          <div className="settings-card-header">
            <div className="settings-card-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="2"
                strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
            </div>
            <div>
              <h2 className="settings-card-title">Account Access</h2>
              <p className="settings-card-sub">Update your credentials or re-authenticate</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="settings-form">

            <div className="form-field">
              <label htmlFor="email">Email Address</label>
              <input
                type="email"
                id="email"
                name="email"
                placeholder="you@drivevitals.com"
                value={formData.email}
                onChange={handleChange}
              />
            </div>

            <div className="form-divider" />

            <div className="form-field">
              <label htmlFor="currentPassword">Current Password</label>
              <input
                type="password"
                id="currentPassword"
                name="currentPassword"
                placeholder="Enter current password"
                value={formData.currentPassword}
                onChange={handleChange}
              />
            </div>

            <div className="form-field">
              <label htmlFor="newPassword">New Password</label>
              <input
                type="password"
                id="newPassword"
                name="newPassword"
                placeholder="Min. 6 characters"
                value={formData.newPassword}
                onChange={handleChange}
              />
            </div>

            <div className="form-field">
              <label htmlFor="confirmPassword">Confirm New Password</label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                placeholder="Re-enter new password"
                value={formData.confirmPassword}
                onChange={handleChange}
              />
            </div>

            {status === "error" && (
              <p className="settings-error">{errorMsg}</p>
            )}

            <div className="settings-form-actions">
              <button type="button" className="settings-btn-ghost"
                onClick={() => navigate("/dashboard")}>
                Cancel
              </button>
              <button type="submit" className="settings-btn">
                Update Security
              </button>
            </div>

          </form>
        </div>

      </div>
    </div>
  );
}

export default Settings;
