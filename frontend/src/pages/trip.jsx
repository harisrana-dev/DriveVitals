import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/trip.css";
import ThemeToggle from "../components/ThemeToggle";

/* ══════════════════════════════════════════════════════════
   MOCK DATA
══════════════════════════════════════════════════════════ */
const MOCK_TRIPS = [
  { id:"TRP-001", driver:"A. Raza",   vehicle:"VH-0988 · Honda Civic",   company:"LogiCore Ltd",   fleet:"Fleet A", from:"Lahore",   to:"Islamabad",  dist:380, duration:"4h 12m", fuel:"31 L", start:"2026-07-25 08:00", end:"2026-07-25 12:12", status:"Completed" },
  { id:"TRP-002", driver:"M. Ahmed",  vehicle:"VH-1042 · Ford Transit",  company:"SwiftMove Co",   fleet:"Fleet B", from:"Karachi",  to:"Hyderabad",  dist:162, duration:"2h 05m", fuel:"14 L", start:"2026-07-25 09:30", end:"2026-07-25 11:35", status:"Completed" },
  { id:"TRP-003", driver:"K. Sheikh", vehicle:"VH-0876 · Nissan Urvan",  company:"LogiCore Ltd",   fleet:"Fleet A", from:"Lahore",   to:"Faisalabad", dist:128, duration:"1h 48m", fuel:"11 L", start:"2026-07-24 07:00", end:"2026-07-24 08:48", status:"Completed" },
  { id:"TRP-004", driver:"S. Khan",   vehicle:"VH-1017 · Toyota Hiace",  company:"NorthStar Cargo",fleet:"Fleet C", from:"Multan",   to:"Lahore",     dist:341, duration:"4h 30m", fuel:"34 L", start:"2026-07-24 10:00", end:"2026-07-24 14:30", status:"Active"    },
  { id:"TRP-005", driver:"N. Iqbal",  vehicle:"VH-0901 · Suzuki Bolan",  company:"SwiftMove Co",   fleet:"Fleet B", from:"Karachi",  to:"Sukkur",     dist:476, duration:"5h 55m", fuel:"48 L", start:"2026-07-23 06:00", end:"2026-07-23 11:55", status:"Completed" },
  { id:"TRP-006", driver:"F. Bilal",  vehicle:"VH-0954 · Isuzu D-Max",   company:"NorthStar Cargo",fleet:"Fleet C", from:"Peshawar", to:"Lahore",     dist:447, duration:"—",      fuel:"—",    start:"2026-07-23 08:00", end:"—",                status:"Cancelled" },
  { id:"TRP-007", driver:"A. Raza",   vehicle:"VH-0988 · Honda Civic",   company:"LogiCore Ltd",   fleet:"Fleet A", from:"Islamabad",to:"Rawalpindi", dist:14,  duration:"0h 22m", fuel:"1 L",  start:"2026-07-22 14:00", end:"2026-07-22 14:22", status:"Completed" },
  { id:"TRP-008", driver:"K. Sheikh", vehicle:"VH-0876 · Nissan Urvan",  company:"LogiCore Ltd",   fleet:"Fleet A", from:"Lahore",   to:"Sialkot",    dist:125, duration:"—",      fuel:"—",    start:"2026-07-22 09:00", end:"—",                status:"Active"    },
  { id:"TRP-009", driver:"M. Ahmed",  vehicle:"VH-1042 · Ford Transit",  company:"SwiftMove Co",   fleet:"Fleet B", from:"Hyderabad",to:"Karachi",    dist:162, duration:"2h 10m", fuel:"15 L", start:"2026-07-21 13:00", end:"2026-07-21 15:10", status:"Completed" },
  { id:"TRP-010", driver:"N. Iqbal",  vehicle:"VH-0901 · Suzuki Bolan",  company:"SwiftMove Co",   fleet:"Fleet B", from:"Sukkur",   to:"Larkana",    dist:88,  duration:"1h 15m", fuel:"8 L",  start:"2026-07-21 07:30", end:"2026-07-21 08:45", status:"Completed" },
  { id:"TRP-011", driver:"F. Bilal",  vehicle:"VH-0954 · Isuzu D-Max",   company:"NorthStar Cargo",fleet:"Fleet C", from:"Lahore",   to:"Gujranwala", dist:75,  duration:"—",      fuel:"—",    start:"2026-07-20 11:00", end:"—",                status:"Cancelled" },
  { id:"TRP-012", driver:"S. Khan",   vehicle:"VH-1017 · Toyota Hiace",  company:"NorthStar Cargo",fleet:"Fleet C", from:"Lahore",   to:"Islamabad",  dist:380, duration:"4h 45m", fuel:"38 L", start:"2026-07-20 07:00", end:"2026-07-20 11:45", status:"Completed" },
];

const STATUS_META = {
  Completed: { color: "#22c55e", bg: "rgba(34,197,94,0.1)",   border: "rgba(34,197,94,0.2)"   },
  Active:    { color: "#3b82f6", bg: "rgba(59,130,246,0.1)",  border: "rgba(59,130,246,0.2)"  },
  Cancelled: { color: "#ef4444", bg: "rgba(239,68,68,0.1)",   border: "rgba(239,68,68,0.2)"   },
};

const PAGE_SIZE = 8;

/* ── helpers ─────────────────────────────────────────────── */
function Badge({ label }) {
  const m = STATUS_META[label] ?? STATUS_META.Completed;
  return (
    <span className="trip-badge"
      style={{ color: m.color, background: m.bg, border: `1px solid ${m.border}` }}>
      {label}
    </span>
  );
}

function StatCard({ emoji, label, value, color }) {
  return (
    <div className="trip-stat-card" style={{ borderTop: `3px solid ${color}` }}>
      <span className="trip-stat-emoji">{emoji}</span>
      <p className="trip-stat-label">{label}</p>
      <p className="trip-stat-value" style={{ color }}>{value}</p>
    </div>
  );
}

/* ── Icon SVGs ───────────────────────────────────────────── */
const SearchIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
  </svg>
);
const DownloadIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
  </svg>
);
const ChevronLeft = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="15 18 9 12 15 6"/>
  </svg>
);
const ChevronRight = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="9 18 15 12 9 6"/>
  </svg>
);
const BackIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>
  </svg>
);

/* ══════════════════════════════════════════════════════════
   MAIN COMPONENT
══════════════════════════════════════════════════════════ */
function Trips() {
  const navigate = useNavigate();

  /* ── filter state ── */
  const [search,      setSearch]      = useState("");
  const [dateFrom,    setDateFrom]    = useState("");
  const [dateTo,      setDateTo]      = useState("");
  const [company,     setCompany]     = useState("All");
  const [fleet,       setFleet]       = useState("All");
  const [driver,      setDriver]      = useState("All");
  const [vehicle,     setVehicle]     = useState("All");
  const [statusFilter,setStatusFilter]= useState("All");
  const [page,        setPage]        = useState(1);
  const [sortKey,     setSortKey]     = useState("id");
  const [sortDir,     setSortDir]     = useState("asc");

  /* ── unique filter options ── */
  const companies = ["All", ...new Set(MOCK_TRIPS.map(t => t.company))];
  const fleets    = ["All", ...new Set(MOCK_TRIPS.map(t => t.fleet))];
  const drivers   = ["All", ...new Set(MOCK_TRIPS.map(t => t.driver))];
  const vehicles  = ["All", ...new Set(MOCK_TRIPS.map(t => t.vehicle))];
  const statuses  = ["All", "Completed", "Active", "Cancelled"];

  /* ── filtered + sorted data ── */
  const filtered = useMemo(() => {
    return MOCK_TRIPS
      .filter(t => {
        const q = search.toLowerCase();
        const matchSearch = !q || t.id.toLowerCase().includes(q) ||
          t.driver.toLowerCase().includes(q) || t.from.toLowerCase().includes(q) ||
          t.to.toLowerCase().includes(q) || t.vehicle.toLowerCase().includes(q);
        const matchCompany = company === "All" || t.company === company;
        const matchFleet   = fleet   === "All" || t.fleet   === fleet;
        const matchDriver  = driver  === "All" || t.driver  === driver;
        const matchVehicle = vehicle === "All" || t.vehicle === vehicle;
        const matchStatus  = statusFilter === "All" || t.status === statusFilter;
        const tripDate = t.start.split(" ")[0];
        const matchFrom = !dateFrom || tripDate >= dateFrom;
        const matchTo   = !dateTo   || tripDate <= dateTo;
        return matchSearch && matchCompany && matchFleet && matchDriver &&
               matchVehicle && matchStatus && matchFrom && matchTo;
      })
      .sort((a, b) => {
        const va = a[sortKey] ?? ""; const vb = b[sortKey] ?? "";
        return sortDir === "asc"
          ? String(va).localeCompare(String(vb), undefined, { numeric: true })
          : String(vb).localeCompare(String(va), undefined, { numeric: true });
      });
  }, [search, company, fleet, driver, vehicle, statusFilter, dateFrom, dateTo, sortKey, sortDir]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const paginated  = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const resetFilters = () => {
    setSearch(""); setDateFrom(""); setDateTo("");
    setCompany("All"); setFleet("All"); setDriver("All");
    setVehicle("All"); setStatusFilter("All"); setPage(1);
  };

  const handleSort = (key) => {
    if (sortKey === key) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortKey(key); setSortDir("asc"); }
    setPage(1);
  };

  const SortIcon = ({ k }) => (
    <span className={`sort-icon ${sortKey === k ? "sort-icon--active" : ""}`}>
      {sortKey === k && sortDir === "desc" ? "↓" : "↑"}
    </span>
  );

  /* ── summary card data ── */
  const all        = MOCK_TRIPS;
  const completed  = all.filter(t => t.status === "Completed");
  const active     = all.filter(t => t.status === "Active");
  const cancelled  = all.filter(t => t.status === "Cancelled");
  const totalDist  = completed.reduce((s, t) => s + t.dist, 0).toLocaleString();

  // total driving time in hours (rough sum from mock)
  const drivingMins = completed.reduce((s, t) => {
    const m = t.duration.match(/(\d+)h\s*(\d+)m/);
    return m ? s + parseInt(m[1]) * 60 + parseInt(m[2]) : s;
  }, 0);
  const drivingHrs = Math.floor(drivingMins / 60);
  const drivingMin = drivingMins % 60;

  return (
    <div className="trips-page">
      <div className="trips-theme-btn"><ThemeToggle /></div>

      {/* ── Page Header ── */}
      <div className="trips-header">
        <button className="trips-back-btn" onClick={() => navigate(-1)}>
          <BackIcon /> Back
        </button>
        <div className="trips-header-text">
          <h1 className="trips-title">Trips</h1>
          <p className="trips-subtitle">
            Monitor, search and export all fleet trip records
          </p>
        </div>
        <div className="trips-header-actions">
          <button className="trips-export-btn">
            <DownloadIcon /> Export PDF
          </button>
          <button className="trips-export-btn trips-export-btn--outline">
            <DownloadIcon /> Export Excel
          </button>
        </div>
      </div>

      {/* ── Summary Cards ── */}
      <div className="trips-stats">
        <StatCard emoji="🚗" label="Total Trips"          value={all.length}          color="#3b82f6" />
        <StatCard emoji="📍" label="Total Distance"       value={`${totalDist} km`}   color="#3b82f6" />
        <StatCard emoji="⏱"  label="Total Driving Time"  value={`${drivingHrs}h ${drivingMin}m`} color="#22c55e" />
        <StatCard emoji="✅" label="Completed Trips"      value={completed.length}    color="#22c55e" />
        <StatCard emoji="🚧" label="Active Trips"         value={active.length}       color="#f59e0b" />
        <StatCard emoji="❌" label="Cancelled Trips"      value={cancelled.length}    color="#ef4444" />
      </div>

      {/* ── Filters ── */}
      <div className="trips-filters-card">

        {/* Search */}
        <div className="trips-search-wrap">
          <SearchIcon />
          <input
            className="trips-search"
            placeholder="Search by trip ID, driver, route, vehicle…"
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1); }}
          />
        </div>

        {/* Filter row */}
        <div className="trips-filter-row">
          <div className="trips-filter-group">
            <label>From Date</label>
            <input type="date" className="trips-input" value={dateFrom}
              onChange={e => { setDateFrom(e.target.value); setPage(1); }} />
          </div>
          <div className="trips-filter-group">
            <label>To Date</label>
            <input type="date" className="trips-input" value={dateTo}
              onChange={e => { setDateTo(e.target.value); setPage(1); }} />
          </div>
          <div className="trips-filter-group">
            <label>Company</label>
            <select className="trips-select" value={company}
              onChange={e => { setCompany(e.target.value); setPage(1); }}>
              {companies.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div className="trips-filter-group">
            <label>Fleet</label>
            <select className="trips-select" value={fleet}
              onChange={e => { setFleet(e.target.value); setPage(1); }}>
              {fleets.map(f => <option key={f}>{f}</option>)}
            </select>
          </div>
          <div className="trips-filter-group">
            <label>Driver</label>
            <select className="trips-select" value={driver}
              onChange={e => { setDriver(e.target.value); setPage(1); }}>
              {drivers.map(d => <option key={d}>{d}</option>)}
            </select>
          </div>
          <div className="trips-filter-group">
            <label>Vehicle</label>
            <select className="trips-select" value={vehicle}
              onChange={e => { setVehicle(e.target.value); setPage(1); }}>
              {vehicles.map(v => <option key={v}>{v}</option>)}
            </select>
          </div>
          <div className="trips-filter-group">
            <label>Status</label>
            <select className="trips-select" value={statusFilter}
              onChange={e => { setStatusFilter(e.target.value); setPage(1); }}>
              {statuses.map(s => <option key={s}>{s}</option>)}
            </select>
          </div>
          <button className="trips-reset-btn" onClick={resetFilters}>
            Reset
          </button>
        </div>
      </div>

      {/* ── Table ── */}
      <div className="trips-table-card">
        <div className="trips-table-meta">
          <span className="trips-table-count">
            {filtered.length} trip{filtered.length !== 1 ? "s" : ""} found
          </span>
        </div>

        <div className="trips-table-scroll">
          <table className="trips-table">
            <thead>
              <tr>
                {[
                  ["id",       "Trip ID"],
                  ["driver",   "Driver"],
                  ["vehicle",  "Vehicle"],
                  ["from",     "From"],
                  ["to",       "To"],
                  ["dist",     "Distance"],
                  ["duration", "Duration"],
                  ["fuel",     "Fuel"],
                  ["start",    "Departure"],
                  ["status",   "Status"],
                ].map(([key, label]) => (
                  <th key={key} onClick={() => handleSort(key)} className="trips-th">
                    {label} <SortIcon k={key} />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {paginated.length === 0 ? (
                <tr>
                  <td colSpan={10} className="trips-empty">
                    No trips match the current filters.
                  </td>
                </tr>
              ) : paginated.map((t) => (
                <tr key={t.id} className="trips-row">
                  <td className="t-mono">{t.id}</td>
                  <td className="t-bold">{t.driver}</td>
                  <td className="t-muted t-small">{t.vehicle}</td>
                  <td>{t.from}</td>
                  <td>{t.to}</td>
                  <td>{t.dist} km</td>
                  <td>{t.duration}</td>
                  <td>{t.fuel}</td>
                  <td className="t-muted t-small">{t.start}</td>
                  <td><Badge label={t.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="trips-pagination">
          <span className="trips-page-info">
            Page {page} of {totalPages} · {filtered.length} records
          </span>
          <div className="trips-page-controls">
            <button className="trips-page-btn"
              disabled={page === 1} onClick={() => setPage(p => p - 1)}>
              <ChevronLeft />
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1)
              .filter(p => p === 1 || p === totalPages || Math.abs(p - page) <= 1)
              .reduce((acc, p, i, arr) => {
                if (i > 0 && p - arr[i-1] > 1) acc.push("…");
                acc.push(p); return acc;
              }, [])
              .map((p, i) =>
                p === "…"
                  ? <span key={`e${i}`} className="trips-page-ellipsis">…</span>
                  : <button key={p} className={`trips-page-btn ${p === page ? "trips-page-btn--active" : ""}`}
                      onClick={() => setPage(p)}>{p}</button>
              )}
            <button className="trips-page-btn"
              disabled={page === totalPages} onClick={() => setPage(p => p + 1)}>
              <ChevronRight />
            </button>
          </div>
        </div>
      </div>

    </div>
  );
}

export default Trips;
