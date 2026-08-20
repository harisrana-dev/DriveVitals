import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "../styles/login.css";
import ThemeToggle from "../components/common/ThemeToggle";
import AppLoader from "../components/common/AppLoader";

/* ── Inline fleet SVG illustration ──────────────────────── */
function FleetIllustration() {
  return (
    <svg className="panel-illustration" viewBox="0 0 420 260" fill="none"
      xmlns="http://www.w3.org/2000/svg" aria-hidden="true">

      {/* Road */}
      <rect x="0" y="190" width="420" height="8" rx="4" fill="currentColor" opacity="0.08"/>
      <rect x="60" y="192" width="30" height="4" rx="2" fill="currentColor" opacity="0.18"/>
      <rect x="130" y="192" width="30" height="4" rx="2" fill="currentColor" opacity="0.18"/>
      <rect x="200" y="192" width="30" height="4" rx="2" fill="currentColor" opacity="0.18"/>
      <rect x="270" y="192" width="30" height="4" rx="2" fill="currentColor" opacity="0.18"/>
      <rect x="340" y="192" width="30" height="4" rx="2" fill="currentColor" opacity="0.18"/>

      {/* Truck 1 — large, front */}
      <g transform="translate(80, 128)">
        {/* Cab */}
        <rect x="120" y="20" width="70" height="50" rx="6" fill="var(--accent)" opacity="0.9"/>
        {/* Windshield */}
        <rect x="128" y="26" width="40" height="22" rx="3" fill="white" opacity="0.25"/>
        {/* Cargo body */}
        <rect x="0" y="26" width="122" height="44" rx="4" fill="var(--accent)" opacity="0.6"/>
        {/* Wheels */}
        <circle cx="28" cy="72" r="12" fill="currentColor" opacity="0.5"/>
        <circle cx="28" cy="72" r="6" fill="currentColor" opacity="0.3"/>
        <circle cx="100" cy="72" r="12" fill="currentColor" opacity="0.5"/>
        <circle cx="100" cy="72" r="6" fill="currentColor" opacity="0.3"/>
        <circle cx="158" cy="72" r="12" fill="currentColor" opacity="0.5"/>
        <circle cx="158" cy="72" r="6" fill="currentColor" opacity="0.3"/>
        {/* Headlight */}
        <rect x="186" y="46" width="8" height="6" rx="2" fill="#fbbf24" opacity="0.9"/>
        {/* DriveVitals tag */}
        <rect x="16" y="34" width="88" height="20" rx="3" fill="white" opacity="0.08"/>
        <text x="60" y="48" fontSize="8" fill="white" opacity="0.5" textAnchor="middle"
          fontFamily="Inter, sans-serif" fontWeight="600">DRIVEVITALS</text>
      </g>

      {/* Truck 2 — small, background */}
      <g transform="translate(280, 148)" opacity="0.5">
        <rect x="60" y="8" width="42" height="32" rx="4" fill="var(--accent)"/>
        <rect x="66" y="12" width="24" height="14" rx="2" fill="white" opacity="0.2"/>
        <rect x="0" y="14" width="62" height="26" rx="3" fill="var(--accent)" opacity="0.6"/>
        <circle cx="14" cy="42" r="8" fill="currentColor" opacity="0.4"/>
        <circle cx="14" cy="42" r="4" fill="currentColor" opacity="0.3"/>
        <circle cx="56" cy="42" r="8" fill="currentColor" opacity="0.4"/>
        <circle cx="56" cy="42" r="4" fill="currentColor" opacity="0.3"/>
        <circle cx="90" cy="42" r="8" fill="currentColor" opacity="0.4"/>
        <circle cx="90" cy="42" r="4" fill="currentColor" opacity="0.3"/>
      </g>

      {/* Telemetry ping dots */}
      <circle cx="170" cy="100" r="5" fill="var(--accent)" opacity="0.8"/>
      <circle cx="170" cy="100" r="10" fill="var(--accent)" opacity="0.15"/>
      <circle cx="170" cy="100" r="16" fill="var(--accent)" opacity="0.07"/>

      <circle cx="320" cy="118" r="4" fill="#22c55e" opacity="0.8"/>
      <circle cx="320" cy="118" r="8" fill="#22c55e" opacity="0.15"/>

      {/* Signal lines */}
      <line x1="170" y1="100" x2="230" y2="55" stroke="var(--accent)" strokeWidth="1"
        strokeDasharray="4 4" opacity="0.3"/>
      <line x1="320" y1="118" x2="280" y2="68" stroke="#22c55e" strokeWidth="1"
        strokeDasharray="4 4" opacity="0.3"/>

      {/* Mini dashboard card */}
      <rect x="210" y="30" width="100" height="52" rx="7"
        fill="currentColor" opacity="0.06" stroke="currentColor" strokeOpacity="0.12" strokeWidth="1"/>
      <rect x="220" y="40" width="36" height="5" rx="2" fill="currentColor" opacity="0.2"/>
      <rect x="220" y="51" width="60" height="4" rx="2" fill="var(--accent)" opacity="0.4"/>
      <rect x="220" y="61" width="44" height="4" rx="2" fill="#22c55e" opacity="0.4"/>

      <rect x="244" y="30" width="100" height="52" rx="7"
        fill="currentColor" opacity="0.04" stroke="currentColor" strokeOpacity="0.1" strokeWidth="1"/>
    </svg>
  );
}

/* ── Component ───────────────────────────────────────────── */
function Login() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [showLoader, setShowLoader] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError("");
  };

  const handleLogin = (e) => {
    e.preventDefault();
    const { email, password } = formData;

    if (!email || !password) {
      setError("Please fill in all fields.");
      return;
    }

    setShowLoader(true);
  };

  return (
    <div className="login-container">

      {/* Left branding panel */}
      <div className="login-panel">
        <div className="panel-brand">
          <div className="panel-logo-mark">DV</div>
          <span className="panel-logo-name">DriveVitals</span>
        </div>
        <FleetIllustration />
        <p className="panel-tagline">Your fleet. Always in view.</p>
        <p className="panel-sub">
          Real-time telemetry, predictive maintenance, and driver
          analytics — built for logistics operators.
        </p>
      </div>

      {/* Right form panel */}
      <div className="login-box">
        <div className="form-theme-btn"><ThemeToggle /></div>

        {/* Back button */}
        <button className="form-back-btn" onClick={() => navigate(-1)} aria-label="Go back">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2.2"
            strokeLinecap="round" strokeLinejoin="round">
            <line x1="19" y1="12" x2="5" y2="12"/>
            <polyline points="12 19 5 12 12 5"/>
          </svg>
          Back
        </button>

        <h1>DriveVitals</h1>
        <p className="login-title">Welcome back</p>
        <p className="login-subtitle">Sign in to your fleet dashboard</p>

        <form onSubmit={handleLogin}>
          <div className="input-group">
            <input type="email" name="email" placeholder="Work email"
              value={formData.email} onChange={handleChange} />
          </div>
          <div className="input-group">
            <input type="password" name="password" placeholder="Password"
              value={formData.password} onChange={handleChange} />
          </div>

          {error && <p className="login-error">{error}</p>}

          <button type="submit" className="login-btn">Sign In</button>
        </form>

        <div className="forgot-password">
          <a href="#">Forgot password?</a>
        </div>

        <div className="signup-text">
          Don't have an account? <Link to="/signup">Create one</Link>
        </div>
      </div>

      {showLoader && (
        <AppLoader onComplete={() => navigate("/dashboard")} />
      )}
    </div>
  );
}

export default Login;
