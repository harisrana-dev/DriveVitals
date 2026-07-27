import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "../styles/signup.css";
import ThemeToggle from "../components/ThemeToggle";

/* ── Inline route/network SVG illustration ───────────────── */
function RouteIllustration() {
  return (
    <svg className="panel-illustration" viewBox="0 0 420 260" fill="none"
      xmlns="http://www.w3.org/2000/svg" aria-hidden="true">

      {/* Route path */}
      <path d="M40 200 Q100 120 180 140 Q260 160 300 80 Q340 20 390 50"
        stroke="var(--accent)" strokeWidth="2.5" strokeDasharray="6 5"
        opacity="0.4" fill="none"/>

      {/* Waypoint nodes */}
      <circle cx="40"  cy="200" r="8" fill="var(--accent)" opacity="0.9"/>
      <circle cx="40"  cy="200" r="14" fill="var(--accent)" opacity="0.12"/>
      <circle cx="180" cy="140" r="6" fill="#22c55e" opacity="0.9"/>
      <circle cx="180" cy="140" r="12" fill="#22c55e" opacity="0.12"/>
      <circle cx="300" cy="80"  r="6" fill="#f59e0b" opacity="0.9"/>
      <circle cx="300" cy="80"  r="12" fill="#f59e0b" opacity="0.12"/>
      <circle cx="390" cy="50"  r="8" fill="var(--accent)" opacity="0.9"/>
      <circle cx="390" cy="50"  r="14" fill="var(--accent)" opacity="0.12"/>

      {/* Truck icon on route */}
      <g transform="translate(224, 126)">
        <rect x="0"  y="4"  width="32" height="18" rx="3" fill="var(--accent)" opacity="0.85"/>
        <rect x="32" y="8"  width="16" height="14" rx="2" fill="var(--accent)"/>
        <rect x="34" y="10" width="10" height="8"  rx="1" fill="white" opacity="0.2"/>
        <circle cx="8"  cy="24" r="5" fill="currentColor" opacity="0.45"/>
        <circle cx="8"  cy="24" r="2.5" fill="currentColor" opacity="0.25"/>
        <circle cx="28" cy="24" r="5" fill="currentColor" opacity="0.45"/>
        <circle cx="28" cy="24" r="2.5" fill="currentColor" opacity="0.25"/>
        <circle cx="42" cy="24" r="5" fill="currentColor" opacity="0.45"/>
        <circle cx="42" cy="24" r="2.5" fill="currentColor" opacity="0.25"/>
      </g>

      {/* Info cards */}
      <rect x="50"  y="30"  width="110" height="56" rx="8"
        fill="currentColor" opacity="0.05"
        stroke="currentColor" strokeOpacity="0.1" strokeWidth="1"/>
      <rect x="62" y="44" width="50" height="5" rx="2" fill="currentColor" opacity="0.2"/>
      <rect x="62" y="55" width="74" height="4" rx="2" fill="var(--accent)" opacity="0.4"/>
      <rect x="62" y="65" width="56" height="4" rx="2" fill="#22c55e" opacity="0.35"/>

      <text x="104" y="42" fontSize="7" fill="currentColor" opacity="0.3"
        fontFamily="Inter,sans-serif" fontWeight="600">FLEET STATUS</text>

      <rect x="260" y="145" width="110" height="56" rx="8"
        fill="currentColor" opacity="0.05"
        stroke="currentColor" strokeOpacity="0.1" strokeWidth="1"/>
      <rect x="272" y="159" width="50" height="5" rx="2" fill="currentColor" opacity="0.2"/>
      <rect x="272" y="170" width="74" height="4" rx="2" fill="#f59e0b" opacity="0.4"/>
      <rect x="272" y="181" width="40" height="4" rx="2" fill="#22c55e" opacity="0.35"/>
      <text x="314" y="157" fontSize="7" fill="currentColor" opacity="0.3"
        fontFamily="Inter,sans-serif" fontWeight="600">DRIVER SCORE</text>

      {/* Speed / signal bars */}
      <g transform="translate(355, 85)" opacity="0.6">
        <rect x="0" y="12" width="5" height="6"  rx="1" fill="var(--accent)"/>
        <rect x="7" y="8"  width="5" height="10" rx="1" fill="var(--accent)"/>
        <rect x="14" y="4" width="5" height="14" rx="1" fill="var(--accent)"/>
        <rect x="21" y="0" width="5" height="18" rx="1" fill="var(--accent)" opacity="0.4"/>
      </g>
    </svg>
  );
}

/* ── Component ───────────────────────────────────────────── */
function Signup() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    fullName: "", email: "", password: "", confirmPassword: "",
  });
  const [error, setError] = useState("");

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError("");
  };

  const handleSignup = (e) => {
    e.preventDefault();
    const { fullName, email, password, confirmPassword } = formData;

    if (!fullName || !email || !password || !confirmPassword) {
      setError("Please fill in all fields.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    console.log("Registering user:", { fullName, email });
    navigate("/login");
  };

  return (
    <div className="signup-container">

      {/* Left branding panel */}
      <div className="signup-panel">
        <div className="panel-brand">
          <div className="panel-logo-mark">DV</div>
          <span className="panel-logo-name">DriveVitals</span>
        </div>
        <RouteIllustration />
        <p className="panel-tagline">Smarter fleets start here.</p>
        <p className="panel-sub">
          Join fleet operators who rely on DriveVitals for live
          route tracking, fuel insights, and zero-surprise maintenance.
        </p>
      </div>

      {/* Right form panel */}
      <div className="signup-box">
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
        <p className="signup-box-title">Create your account</p>
        <p>Get full access to your fleet command center</p>

        <form onSubmit={handleSignup}>
          <div className="input-group">
            <input type="text" name="fullName" placeholder="Full name"
              value={formData.fullName} onChange={handleChange} />
          </div>
          <div className="input-group">
            <input type="email" name="email" placeholder="Work email"
              value={formData.email} onChange={handleChange} />
          </div>
          <div className="input-group">
            <input type="password" name="password" placeholder="Password"
              value={formData.password} onChange={handleChange} />
          </div>
          <div className="input-group">
            <input type="password" name="confirmPassword" placeholder="Confirm password"
              value={formData.confirmPassword} onChange={handleChange} />
          </div>

          {error && <p className="error-msg">{error}</p>}

          <button type="submit" className="signup-btn">Create Account</button>
        </form>

        <p className="login-text">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>

    </div>
  );
}

export default Signup;
