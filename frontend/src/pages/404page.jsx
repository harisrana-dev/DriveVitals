import { useNavigate, useLocation } from "react-router-dom";
import "../styles/404page.css";
import ThemeToggle from "../components/ThemeToggle";

/* ── Lost truck SVG illustration ─────────────────────────── */
function LostTruckIllustration() {
  return (
    <svg className="notfound-illustration" viewBox="0 0 460 220"
      fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">

      {/* Broken / dashed road going nowhere */}
      <line x1="0" y1="178" x2="460" y2="178"
        stroke="currentColor" strokeOpacity="0.08" strokeWidth="6"/>
      {/* Road dashes */}
      {[0,1,2,3,4,5,6].map((i) => (
        <rect key={i} x={30 + i * 64} y="174" width="32" height="5" rx="2.5"
          fill="currentColor" opacity="0.14"/>
      ))}

      {/* Road abruptly ends — cliff edge */}
      <rect x="310" y="174" width="150" height="6" rx="3"
        fill="currentColor" opacity="0.05"/>
      <line x1="308" y1="172" x2="308" y2="186"
        stroke="currentColor" strokeOpacity="0.25" strokeWidth="2"
        strokeDasharray="3 3"/>

      {/* Confused waypoint markers */}
      {/* Green — start */}
      <circle cx="40"  cy="155" r="6"  fill="#22c55e" opacity="0.85"/>
      <circle cx="40"  cy="155" r="12" fill="#22c55e" opacity="0.12"/>
      {/* Accent — mid */}
      <circle cx="160" cy="145" r="5"  fill="var(--accent)" opacity="0.7"/>
      <circle cx="160" cy="145" r="10" fill="var(--accent)" opacity="0.1"/>
      {/* Yellow — warning */}
      <circle cx="270" cy="148" r="5"  fill="#f59e0b" opacity="0.8"/>
      <circle cx="270" cy="148" r="10" fill="#f59e0b" opacity="0.1"/>
      {/* Red — broken destination */}
      <circle cx="380" cy="152" r="6"  fill="#ef4444" opacity="0.85"/>
      <circle cx="380" cy="152" r="13" fill="#ef4444" opacity="0.1"/>
      {/* X on broken destination */}
      <line x1="376" y1="148" x2="384" y2="156"
        stroke="#ef4444" strokeWidth="1.8" strokeOpacity="0.9"/>
      <line x1="384" y1="148" x2="376" y2="156"
        stroke="#ef4444" strokeWidth="1.8" strokeOpacity="0.9"/>

      {/* Route line — dashed, ends at cliff */}
      <path d="M40 155 Q100 120 160 145 Q220 165 270 148 Q300 138 308 152"
        stroke="currentColor" strokeWidth="1.5" strokeDasharray="5 4"
        opacity="0.2" fill="none"/>

      {/* ── Truck stopped at edge ── */}
      <g transform="translate(200, 110)">
        {/* Cargo body */}
        <rect x="0"   y="18" width="88" height="36" rx="4"
          fill="var(--accent)" opacity="0.55"/>
        {/* Cab */}
        <rect x="88"  y="22" width="50" height="32" rx="5"
          fill="var(--accent)" opacity="0.85"/>
        {/* Windshield */}
        <rect x="95"  y="28" width="28" height="16" rx="3"
          fill="white" opacity="0.18"/>
        {/* Headlight */}
        <rect x="134" y="40" width="7"  height="5"  rx="2"
          fill="#fbbf24" opacity="0.9"/>
        {/* Wheels */}
        <circle cx="22"  cy="56" r="10" fill="currentColor" opacity="0.4"/>
        <circle cx="22"  cy="56" r="5"  fill="currentColor" opacity="0.25"/>
        <circle cx="72"  cy="56" r="10" fill="currentColor" opacity="0.4"/>
        <circle cx="72"  cy="56" r="5"  fill="currentColor" opacity="0.25"/>
        <circle cx="114" cy="56" r="10" fill="currentColor" opacity="0.4"/>
        <circle cx="114" cy="56" r="5"  fill="currentColor" opacity="0.25"/>
        {/* Question mark above truck */}
        <text x="68" y="14" fontSize="22" fill="var(--accent)" opacity="0.9"
          fontFamily="Inter,sans-serif" fontWeight="700" textAnchor="middle">?</text>
      </g>

      {/* Signal bars — no signal */}
      <g transform="translate(400, 30)" opacity="0.35">
        <rect x="0"  y="14" width="5" height="5"  rx="1" fill="currentColor"/>
        <rect x="7"  y="10" width="5" height="9"  rx="1" fill="currentColor" opacity="0.4"/>
        <rect x="14" y="6"  width="5" height="13" rx="1" fill="currentColor" opacity="0.2"/>
        <rect x="21" y="2"  width="5" height="17" rx="1" fill="currentColor" opacity="0.1"/>
        {/* No-signal X */}
        <line x1="0" y1="0" x2="26" y2="20"
          stroke="#ef4444" strokeWidth="1.5" strokeOpacity="0.6"/>
      </g>
    </svg>
  );
}

/* ── Page component ──────────────────────────────────────── */
function NotFound() {
  const navigate   = useNavigate();
  const { pathname } = useLocation();

  return (
    <div className="notfound-page">
      <div className="notfound-theme">
        <ThemeToggle />
      </div>

      <LostTruckIllustration />

      <p className="notfound-code">4<span>0</span>4</p>
      <h1 className="notfound-title">Route not found</h1>
      <p className="notfound-sub">
        Looks like this truck took a wrong turn. The page you're
        looking for doesn't exist or has been moved.
      </p>

      <button className="notfound-btn" onClick={() => navigate("/")}>
        {/* Arrow left */}
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2.2"
          strokeLinecap="round" strokeLinejoin="round">
          <line x1="19" y1="12" x2="5" y2="12"/>
          <polyline points="12 19 5 12 12 5"/>
        </svg>
        Back to Get Started
      </button>

      <p className="notfound-path">{pathname}</p>
    </div>
  );
}

export default NotFound;
