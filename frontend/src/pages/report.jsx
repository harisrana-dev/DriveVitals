import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/report.css";
import ThemeToggle from "../components/ThemeToggle";

/* ══════════════════════════════════════════════════════════
   MOCK DATA
══════════════════════════════════════════════════════════ */
const KPI_DATA = [
  { label: "Total Trips",          value: "1,284", delta: "+12%", up: true,  color: "#22c55e" },
  { label: "Total Distance (km)",  value: "94,210",delta: "+8%",  up: true,  color: "#3b82f6" },
  { label: "Fuel Consumed (L)",    value: "48,320",delta: "+4%",  up: false, color: "#f59e0b" },
  { label: "Fleet Operating Cost", value: "$18,740",delta: "-2%", up: true,  color: "#3b82f6" },
  { label: "Maintenance Due",      value: "7",     delta: "+2",   up: false, color: "#ef4444" },
  { label: "Active Drivers",       value: "34",    delta: "+3",   up: true,  color: "#22c55e" },
];

const DISTANCE_TREND = [120,145,132,160,175,155,190,210,198,220,215,240];
const FUEL_DATA      = [80, 95, 88, 102,110,98, 115,125,118,130,128,145];
const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

const UTILIZATION = [
  { vehicle: "Ford Transit",   pct: 82 },
  { vehicle: "Toyota Hiace",   pct: 67 },
  { vehicle: "Isuzu D-Max",    pct: 91 },
  { vehicle: "Honda Civic",    pct: 74 },
  { vehicle: "Suzuki Bolan",   pct: 58 },
  { vehicle: "Nissan Urvan",   pct: 88 },
];

const MAINT_COST = [
  { month: "Feb", cost: 1200 },
  { month: "Mar", cost: 980  },
  { month: "Apr", cost: 1540 },
  { month: "May", cost: 870  },
  { month: "Jun", cost: 2100 },
  { month: "Jul", cost: 1350 },
];

const DRIVERS = [
  { name: "A. Raza",   trips: 48, score: 91, distance: "8,420 km", fuel: "7.2 L/100", grade: "Excellent" },
  { name: "M. Ahmed",  trips: 44, score: 88, distance: "7,810 km", fuel: "7.8 L/100", grade: "Excellent" },
  { name: "K. Sheikh", trips: 39, score: 85, distance: "6,950 km", fuel: "8.1 L/100", grade: "Good"      },
  { name: "N. Iqbal",  trips: 36, score: 79, distance: "6,200 km", fuel: "8.6 L/100", grade: "Good"      },
  { name: "S. Khan",   trips: 31, score: 74, distance: "5,480 km", fuel: "9.2 L/100", grade: "Average"   },
  { name: "F. Bilal",  trips: 27, score: 63, distance: "4,100 km", fuel: "10.4 L/100","grade":"Needs Coaching"},
];

const VEHICLES = [
  { id:"VH-1042", name:"Ford Transit",  status:"Active",  distance:"12,400 km", fuel:"74%", health:96, alerts:0  },
  { id:"VH-0988", name:"Honda Civic",   status:"Active",  distance:"11,200 km", fuel:"58%", health:92, alerts:0  },
  { id:"VH-0876", name:"Nissan Urvan",  status:"Active",  distance:"9,800 km",  fuel:"65%", health:89, alerts:1  },
  { id:"VH-1017", name:"Toyota Hiace",  status:"Warning", distance:"8,100 km",  fuel:"22%", health:81, alerts:2  },
  { id:"VH-0954", name:"Isuzu D-Max",   status:"Critical",distance:"6,700 km",  fuel:"11%", health:54, alerts:3  },
  { id:"VH-0901", name:"Suzuki Bolan",  status:"Offline", distance:"—",         fuel:"—",   health:"—",alerts:0  },
];

const TRIPS = [
  { id:"TRP-881", driver:"A. Raza",   vehicle:"VH-0988", from:"Lahore",  to:"Islamabad", dist:"380 km", dur:"4h 12m", fuel:"31 L", date:"Jul 25" },
  { id:"TRP-880", driver:"M. Ahmed",  vehicle:"VH-1042", from:"Karachi", to:"Hyderabad", dist:"162 km", dur:"2h 05m", fuel:"14 L", date:"Jul 25" },
  { id:"TRP-879", driver:"K. Sheikh", vehicle:"VH-0876", from:"Lahore",  to:"Faisalabad",dist:"128 km", dur:"1h 48m", fuel:"11 L", date:"Jul 24" },
  { id:"TRP-878", driver:"S. Khan",   vehicle:"VH-1017", from:"Multan",  to:"Lahore",    dist:"341 km", dur:"4h 30m", fuel:"34 L", date:"Jul 24" },
  { id:"TRP-877", driver:"N. Iqbal",  vehicle:"VH-0901", from:"Karachi", to:"Sukkur",    dist:"476 km", dur:"5h 55m", fuel:"48 L", date:"Jul 23" },
];

const ALERTS = [
  { id:"ALT-041", type:"Critical",  vehicle:"VH-0954", msg:"Engine oil pressure critically low",       time:"2h ago"  },
  { id:"ALT-040", type:"Warning",   vehicle:"VH-1017", msg:"Fuel level below 25% threshold",           time:"3h ago"  },
  { id:"ALT-039", type:"Warning",   vehicle:"VH-0876", msg:"Driver harsh braking detected (3 events)", time:"5h ago"  },
  { id:"ALT-038", type:"Info",      vehicle:"VH-1042", msg:"Scheduled maintenance due in 400 km",      time:"6h ago"  },
  { id:"ALT-037", type:"Critical",  vehicle:"VH-0954", msg:"Battery voltage below 11.8 V",             time:"8h ago"  },
];

const AI_INSIGHTS = [
  { icon:"🤖", text:"Fleet fuel efficiency dropped 4% this month. VH-0954 and VH-1017 are outliers — inspect injectors and tyre pressure." },
  { icon:"📊", text:"Driver F. Bilal's score has declined 8 pts over 3 weeks. Recommend targeted coaching session." },
  { icon:"🔧", text:"7 vehicles due for service within the next 14 days. Scheduling now can prevent 3 predicted breakdowns." },
  { icon:"📍", text:"Route Lahore→Islamabad averages 12% higher fuel cost vs. alternate M-2 route. Consider rerouting." },
];

/* ══════════════════════════════════════════════════════════
   SVG CHART HELPERS
══════════════════════════════════════════════════════════ */
function LineChart({ data, color, label }) {
  const W = 100, H = 60, pad = 4;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const pts = data.map((v, i) => {
    const x = pad + (i / (data.length - 1)) * (W - pad * 2);
    const y = pad + (1 - (v - min) / range) * (H - pad * 2);
    return `${x},${y}`;
  });
  const polyline = pts.join(" ");
  const area = `${pts[0].split(",")[0]},${H} ` + pts.join(" ") + ` ${pts[pts.length-1].split(",")[0]},${H}`;

  return (
    <div className="chart-wrap">
      <p className="chart-label">{label}</p>
      <svg viewBox={`0 0 ${W} ${H}`} className="line-chart-svg" preserveAspectRatio="none">
        <defs>
          <linearGradient id={`grad-${label}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%"   stopColor={color} stopOpacity="0.18"/>
            <stop offset="100%" stopColor={color} stopOpacity="0"/>
          </linearGradient>
        </defs>
        <polygon points={area} fill={`url(#grad-${label})`}/>
        <polyline points={polyline} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round"/>
        {pts.map((pt, i) => (
          <circle key={i} cx={pt.split(",")[0]} cy={pt.split(",")[1]} r="1.8" fill={color}/>
        ))}
      </svg>
      <div className="chart-x-labels">
        {MONTHS.map((m) => <span key={m}>{m}</span>)}
      </div>
    </div>
  );
}

function BarChart({ data, color, label }) {
  const max = Math.max(...data.map(d => d.cost));
  return (
    <div className="chart-wrap">
      <p className="chart-label">{label}</p>
      <div className="bar-chart">
        {data.map((d) => (
          <div key={d.month} className="bar-col">
            <span className="bar-val">${(d.cost/1000).toFixed(1)}k</span>
            <div className="bar-track">
              <div className="bar-fill" style={{ height:`${(d.cost/max)*100}%`, background: color }}/>
            </div>
            <span className="bar-month">{d.month}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function UtilizationBars({ data }) {
  return (
    <div className="chart-wrap">
      <p className="chart-label">Vehicle Utilization</p>
      <div className="util-list">
        {data.map((d) => {
          const color = d.pct >= 80 ? "#22c55e" : d.pct >= 60 ? "#3b82f6" : "#f59e0b";
          return (
            <div key={d.vehicle} className="util-row">
              <span className="util-name">{d.vehicle}</span>
              <div className="util-track">
                <div className="util-fill" style={{ width:`${d.pct}%`, background: color }}/>
              </div>
              <span className="util-pct" style={{ color }}>{d.pct}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════
   SMALL REUSABLE ATOMS
══════════════════════════════════════════════════════════ */
const STATUS_COLOR = { Active:"#22c55e", Warning:"#f59e0b", Critical:"#ef4444", Offline:"#6b7280" };
const GRADE_COLOR  = { Excellent:"#22c55e", Good:"#3b82f6", Average:"#f59e0b", "Needs Coaching":"#ef4444" };
const ALERT_COLOR  = { Critical:"#ef4444", Warning:"#f59e0b", Info:"#3b82f6" };

function Badge({ label, color }) {
  return (
    <span className="r-badge" style={{ color, background:`${color}18`, border:`1px solid ${color}30` }}>
      {label}
    </span>
  );
}

function HealthBar({ value }) {
  if (value === "—") return <span className="r-muted">—</span>;
  const color = value >= 85 ? "#22c55e" : value >= 65 ? "#f59e0b" : "#ef4444";
  return (
    <div className="health-bar-wrap">
      <div className="health-track">
        <div style={{ width:`${value}%`, background: color, height:"100%", borderRadius:4 }}/>
      </div>
      <span style={{ color, fontSize:12, fontWeight:600 }}>{value}%</span>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════
   MAIN COMPONENT
══════════════════════════════════════════════════════════ */
function Reports() {
  const navigate = useNavigate();
  const [dateFilter, setDateFilter]     = useState("Last 30 Days");
  const [vehicleFilter, setVehicleFilter] = useState("All Vehicles");
  const [driverFilter, setDriverFilter]  = useState("All Drivers");

  return (
    <div className="rpt-page">
      <div className="rpt-theme-btn"><ThemeToggle /></div>

      {/* ── Header ── */}
      <div className="rpt-header">
        <button className="rpt-back-btn" onClick={() => navigate(-1)}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>
          </svg>
          Back
        </button>
        <div className="rpt-header-text">
          <h1 className="rpt-title">Reports</h1>
          <p className="rpt-subtitle">Fleet analytics and exportable performance data</p>
        </div>
        <button className="rpt-btn">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          Export All
        </button>
      </div>

      {/* ── Filters ── */}
      <div className="rpt-filters">
        <div className="rpt-filter-group">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/>
            <line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
          <select value={dateFilter} onChange={e => setDateFilter(e.target.value)} className="rpt-select">
            <option>Last 7 Days</option>
            <option>Last 30 Days</option>
            <option>Last 90 Days</option>
            <option>This Year</option>
          </select>
        </div>
        <div className="rpt-filter-group">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="1" y="3" width="15" height="13" rx="2"/>
            <path d="M16 8h4l3 3v5h-7V8z"/>
            <circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>
          </svg>
          <select value={vehicleFilter} onChange={e => setVehicleFilter(e.target.value)} className="rpt-select">
            <option>All Vehicles</option>
            {VEHICLES.map(v => <option key={v.id}>{v.name} · {v.id}</option>)}
          </select>
        </div>
        <div className="rpt-filter-group">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
          </svg>
          <select value={driverFilter} onChange={e => setDriverFilter(e.target.value)} className="rpt-select">
            <option>All Drivers</option>
            {DRIVERS.map(d => <option key={d.name}>{d.name}</option>)}
          </select>
        </div>
        <button className="rpt-filter-clear" onClick={() => { setDateFilter("Last 30 Days"); setVehicleFilter("All Vehicles"); setDriverFilter("All Drivers"); }}>
          Reset Filters
        </button>
      </div>

      {/* ── 6 KPI Cards ── */}
      <div className="rpt-kpi-grid">
        {KPI_DATA.map((k) => (
          <div className="rpt-kpi-card" key={k.label} style={{ borderTop:`3px solid ${k.color}` }}>
            <p className="rpt-kpi-label">{k.label}</p>
            <p className="rpt-kpi-value">{k.value}</p>
            <p className="rpt-kpi-delta" style={{ color: k.up ? "#22c55e" : "#f59e0b" }}>
              {k.up ? "▲" : "▼"} {k.delta} vs prev. period
            </p>
          </div>
        ))}
      </div>

      {/* ── Row 1: Distance Trend + Fuel Consumption ── */}
      <div className="rpt-chart-row">
        <div className="rpt-chart-card">
          <div className="rpt-section-head">
            <h2 className="rpt-section-title">Distance Trend</h2>
            <span className="rpt-section-sub">Monthly km travelled across fleet</span>
          </div>
          <LineChart data={DISTANCE_TREND} color="#3b82f6" label="" />
        </div>
        <div className="rpt-chart-card">
          <div className="rpt-section-head">
            <h2 className="rpt-section-title">Fuel Consumption</h2>
            <span className="rpt-section-sub">Monthly litres consumed across fleet</span>
          </div>
          <LineChart data={FUEL_DATA} color="#f59e0b" label="" />
        </div>
      </div>

      {/* ── Row 2: Vehicle Utilization + Maintenance Cost ── */}
      <div className="rpt-chart-row">
        <div className="rpt-chart-card">
          <div className="rpt-section-head">
            <h2 className="rpt-section-title">Vehicle Utilization</h2>
            <span className="rpt-section-sub">% of scheduled hours in use</span>
          </div>
          <UtilizationBars data={UTILIZATION} />
        </div>
        <div className="rpt-chart-card">
          <div className="rpt-section-head">
            <h2 className="rpt-section-title">Maintenance Cost</h2>
            <span className="rpt-section-sub">USD spend per month</span>
          </div>
          <BarChart data={MAINT_COST} color="#a855f7" label="" />
        </div>
      </div>

      {/* ── Driver Performance Table ── */}
      <div className="rpt-table-card">
        <div className="rpt-section-head rpt-section-head--padded">
          <div>
            <h2 className="rpt-section-title">Driver Performance</h2>
            <span className="rpt-section-sub">Ranked by score · {dateFilter}</span>
          </div>
        </div>
        <div className="rpt-table-scroll">
          <table className="rpt-table">
            <thead>
              <tr>
                <th>#</th><th>Driver</th><th>Trips</th>
                <th>Distance</th><th>Fuel Avg</th><th>Score</th><th>Grade</th>
              </tr>
            </thead>
            <tbody>
              {DRIVERS.map((d, i) => (
                <tr key={d.name}>
                  <td className="r-muted">{i + 1}</td>
                  <td className="r-bold">{d.name}</td>
                  <td>{d.trips}</td>
                  <td>{d.distance}</td>
                  <td>{d.fuel}</td>
                  <td>
                    <div className="score-cell">
                      <span className="score-num" style={{ color: GRADE_COLOR[d.grade] }}>{d.score}</span>
                      <div className="score-track">
                        <div style={{ width:`${d.score}%`, background: GRADE_COLOR[d.grade], height:"100%", borderRadius:4 }}/>
                      </div>
                    </div>
                  </td>
                  <td><Badge label={d.grade} color={GRADE_COLOR[d.grade]} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Vehicle Status Table ── */}
      <div className="rpt-table-card">
        <div className="rpt-section-head rpt-section-head--padded">
          <div>
            <h2 className="rpt-section-title">Vehicle Status</h2>
            <span className="rpt-section-sub">Current fleet health snapshot</span>
          </div>
        </div>
        <div className="rpt-table-scroll">
          <table className="rpt-table">
            <thead>
              <tr>
                <th>Vehicle ID</th><th>Name</th><th>Status</th>
                <th>Distance</th><th>Fuel</th><th>Health</th><th>Alerts</th>
              </tr>
            </thead>
            <tbody>
              {VEHICLES.map((v) => (
                <tr key={v.id}>
                  <td className="r-mono">{v.id}</td>
                  <td className="r-bold">{v.name}</td>
                  <td><Badge label={v.status} color={STATUS_COLOR[v.status]} /></td>
                  <td>{v.distance}</td>
                  <td>{v.fuel}</td>
                  <td><HealthBar value={v.health} /></td>
                  <td>
                    {v.alerts > 0
                      ? <span style={{ color:"#ef4444", fontWeight:600 }}>{v.alerts}</span>
                      : <span className="r-muted">—</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Recent Trips ── */}
      <div className="rpt-table-card">
        <div className="rpt-section-head rpt-section-head--padded">
          <div>
            <h2 className="rpt-section-title">Recent Trips</h2>
            <span className="rpt-section-sub">Last completed trips across the fleet</span>
          </div>
        </div>
        <div className="rpt-table-scroll">
          <table className="rpt-table">
            <thead>
              <tr>
                <th>Trip ID</th><th>Driver</th><th>Vehicle</th>
                <th>Route</th><th>Distance</th><th>Duration</th><th>Fuel</th><th>Date</th>
              </tr>
            </thead>
            <tbody>
              {TRIPS.map((t) => (
                <tr key={t.id}>
                  <td className="r-mono">{t.id}</td>
                  <td className="r-bold">{t.driver}</td>
                  <td className="r-muted">{t.vehicle}</td>
                  <td>{t.from} → {t.to}</td>
                  <td>{t.dist}</td>
                  <td>{t.dur}</td>
                  <td>{t.fuel}</td>
                  <td className="r-muted">{t.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Alerts & AI Fleet Insights ── */}
      <div className="rpt-bottom-row">

        {/* Alerts */}
        <div className="rpt-table-card">
          <div className="rpt-section-head rpt-section-head--padded">
            <div>
              <h2 className="rpt-section-title">Alerts</h2>
              <span className="rpt-section-sub">Active fleet warnings and critical events</span>
            </div>
          </div>
          <div className="rpt-alert-list">
            {ALERTS.map((a) => (
              <div className="rpt-alert-row" key={a.id}>
                <div className="rpt-alert-dot" style={{ background: ALERT_COLOR[a.type] }}/>
                <div className="rpt-alert-body">
                  <span className="rpt-alert-msg">{a.msg}</span>
                  <span className="rpt-alert-meta">{a.vehicle} · {a.time}</span>
                </div>
                <Badge label={a.type} color={ALERT_COLOR[a.type]} />
              </div>
            ))}
          </div>
        </div>

        {/* AI Insights */}
        <div className="rpt-table-card rpt-ai-card">
          <div className="rpt-section-head rpt-section-head--padded">
            <div>
              <h2 className="rpt-section-title">AI Fleet Insights</h2>
              <span className="rpt-section-sub">Automated pattern detection and recommendations</span>
            </div>
          </div>
          <div className="rpt-ai-list">
            {AI_INSIGHTS.map((ins, i) => (
              <div className="rpt-ai-row" key={i}>
                <span className="rpt-ai-icon">{ins.icon}</span>
                <p className="rpt-ai-text">{ins.text}</p>
              </div>
            ))}
          </div>
        </div>

      </div>

    </div>
  );
}

export default Reports;
