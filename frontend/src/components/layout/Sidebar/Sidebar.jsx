import {
  LayoutDashboard,
  Truck,
  Car,
  Users,
  Route,
  Wrench,
  FileBarChart2,
  Settings,
  Gauge,
} from 'lucide-react';
import './Sidebar.css';

// Sprint 1: static nav config. No routing yet — clicking does nothing.
const NAV_ITEMS = [
  { key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { key: 'fleet', label: 'Fleet', icon: Truck },
  { key: 'vehicles', label: 'Vehicles', icon: Car },
  { key: 'drivers', label: 'Drivers', icon: Users },
  { key: 'trips', label: 'Trips', icon: Route },
  { key: 'maintenance', label: 'Maintenance', icon: Wrench },
  { key: 'reports', label: 'Reports', icon: FileBarChart2 },
  { key: 'settings', label: 'Settings', icon: Settings },
];

// Active item is static for Sprint 1 (no routing logic yet).
const ACTIVE_KEY = 'dashboard';

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-brand-mark">
          <Gauge size={20} strokeWidth={2} />
        </div>
        <div className="sidebar-brand-text">
          <span className="sidebar-brand-name">DriveVitals</span>
          <span className="sidebar-brand-sub text-caption">Fleet Intelligence</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <ul className="sidebar-nav-list">
          {NAV_ITEMS.map(({ key, label, icon: Icon }) => (
            <li key={key}>
              <button
                type="button"
                className={`sidebar-nav-item${key === ACTIVE_KEY ? ' sidebar-nav-item--active' : ''}`}
              >
                <Icon size={18} strokeWidth={2} className="sidebar-nav-icon" />
                <span className="sidebar-nav-label">{label}</span>
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}

export default Sidebar;
