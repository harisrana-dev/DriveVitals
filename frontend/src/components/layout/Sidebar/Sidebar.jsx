import { NavLink } from 'react-router-dom';
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
  UserCircle,
} from 'lucide-react';
import { ROUTE_MAP } from '../../../router/routes';
import './Sidebar.css';

const NAV_ITEMS = [
  { key: 'dashboard',   label: 'Dashboard',   icon: LayoutDashboard },
  { key: 'user',        label: 'Users',        icon: UserCircle      },
  { key: 'fleet',       label: 'Fleet',        icon: Truck           },
  { key: 'vehicles',    label: 'Vehicles',     icon: Car             },
  { key: 'drivers',     label: 'Drivers',      icon: Users           },
  { key: 'trips',       label: 'Trips',        icon: Route           },
  { key: 'maintenance', label: 'Maintenance',  icon: Wrench          },
  { key: 'reports',     label: 'Reports',      icon: FileBarChart2   },
  { key: 'settings',    label: 'Settings',     icon: Settings        },
];

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
              <NavLink
                to={ROUTE_MAP[key]}
                className={({ isActive }) =>
                  `sidebar-nav-item${isActive ? ' sidebar-nav-item--active' : ''}`
                }
              >
                <Icon size={18} strokeWidth={2} className="sidebar-nav-icon" />
                <span className="sidebar-nav-label">{label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}

export default Sidebar;
