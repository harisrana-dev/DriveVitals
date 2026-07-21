import "../styles/Introductionpage.css";
import { useNavigate } from "react-router-dom";
import ThemeToggle from "../components/ThemeToggle";

function GetStarted() {
  const navigate = useNavigate();

  return (
    <div className="intro-page">

      <header className="intro-nav">
        <div className="intro-nav-logo">
          <span className="logo-mark">DV</span>
          <span className="logo-name">DriveVitals</span>
        </div>
        <div className="intro-nav-actions">
          <ThemeToggle />
          <button className="btn-ghost" onClick={() => navigate("/login")}>Sign In</button>
          <button className="btn-primary" onClick={() => navigate("/signup")}>Request Access</button>
        </div>
      </header>

      <main className="intro-hero">
        <div className="intro-hero-content">
          <p className="intro-eyebrow">Fleet Intelligence Platform</p>
          <h1 className="intro-heading">
            Full visibility into<br />every vehicle, every trip.
          </h1>
          <p className="intro-sub">
            DriveVitals gives logistics and fleet operators real-time telemetry,
            predictive maintenance alerts, and driver performance analytics —
            all in one command center.
          </p>
          <div className="intro-cta-row">
            <button className="btn-primary btn-lg" onClick={() => navigate("/signup")}>
              Get Started
            </button>
            <button className="btn-outline btn-lg" onClick={() => navigate("/login")}>
              Sign In
            </button>
          </div>
          <p className="intro-trust">Trusted by fleet operators managing 50 to 5,000+ vehicles</p>
        </div>

        <div className="intro-stats">
          <div className="stat-item">
            <span className="stat-value">99.9%</span>
            <span className="stat-label">Uptime SLA</span>
          </div>
          <div className="stat-divider" />
          <div className="stat-item">
            <span className="stat-value">&lt; 2s</span>
            <span className="stat-label">Telemetry Latency</span>
          </div>
          <div className="stat-divider" />
          <div className="stat-item">
            <span className="stat-value">ISO 27001</span>
            <span className="stat-label">Certified Security</span>
          </div>
          <div className="stat-divider" />
          <div className="stat-item">
            <span className="stat-value">24 / 7</span>
            <span className="stat-label">Enterprise Support</span>
          </div>
        </div>
      </main>

    </div>
  );
}

export default GetStarted;
