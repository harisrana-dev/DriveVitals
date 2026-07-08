import { Search, Bell, ChevronDown } from 'lucide-react';
import './TopNavbar.css';

// Sprint 1: static shell only. No search logic, no dropdowns, no data.
function TopNavbar() {
  return (
    <header className="top-navbar">
      <div className="top-navbar-search">
        <Search size={16} strokeWidth={2} className="top-navbar-search-icon" />
        <input
          type="text"
          className="top-navbar-search-input"
          placeholder="Search vehicles, drivers, trips…"
          disabled
        />
      </div>

      <div className="top-navbar-right">
        <div className="fleet-status-indicator">
          <span className="fleet-status-dot" />
          <span className="fleet-status-label">LIVE</span>
        </div>

        <button type="button" className="top-navbar-icon-btn" aria-label="Notifications">
          <Bell size={18} strokeWidth={2} />
          <span className="top-navbar-icon-badge" />
        </button>

        <button type="button" className="top-navbar-profile">
          <span className="top-navbar-profile-avatar">HR</span>
          <span className="top-navbar-profile-info">
            <span className="top-navbar-profile-name">Haris R.</span>
            <span className="top-navbar-profile-role text-caption">Fleet Manager</span>
          </span>
          <ChevronDown size={14} strokeWidth={2} className="top-navbar-profile-chevron" />
        </button>
      </div>
    </header>
  );
}

export default TopNavbar;
