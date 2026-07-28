import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Truck,
  Radio,
  MapPin,
  Users,
  AlertTriangle,
  BarChart3,
  HeartPulse,
  Wrench,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: <LayoutDashboard size={18} strokeWidth={1.8} />, section: 'overview' },
  { to: '/fleet', label: 'Fleet', icon: <Truck size={18} strokeWidth={1.8} />, section: 'operations' },
  { to: '/live-telemetry', label: 'Live Telemetry', icon: <Radio size={18} strokeWidth={1.8} />, section: 'operations' },
  { to: '/trips', label: 'Trips', icon: <MapPin size={18} strokeWidth={1.8} />, section: 'operations' },
  { to: '/drivers', label: 'Drivers', icon: <Users size={18} strokeWidth={1.8} />, section: 'intelligence' },
  { to: '/alerts', label: 'Alerts', icon: <AlertTriangle size={18} strokeWidth={1.8} />, section: 'intelligence' },
  { to: '/analytics', label: 'Analytics & Reports', icon: <BarChart3 size={18} strokeWidth={1.8} />, section: 'intelligence' },
  { to: '/vehicle-health', label: 'Vehicle Health', icon: <HeartPulse size={18} strokeWidth={1.8} />, section: 'care' },
  { to: '/maintenance', label: 'Maintenance', icon: <Wrench size={18} strokeWidth={1.8} />, section: 'care' },
];

const sectionLabels = {
  overview: 'OVERVIEW',
  operations: 'FLEET OPERATIONS',
  intelligence: 'INTELLIGENCE',
  care: 'VEHICLE CARE',
};

function SidebarContent({ collapsed, onToggle }) {
  const location = useLocation();
  const sections = ['overview', 'operations', 'intelligence', 'care'];

  return (
    <>
      <div style={{
        padding: collapsed ? '20px 12px' : '20px 20px',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        borderBottom: '1px solid var(--color-sidebar-border)',
        minHeight: 64,
      }}>
        <div style={{
          width: 32,
          height: 32,
          borderRadius: 8,
          background: 'var(--color-accent)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
        </div>
        {!collapsed && (
          <div style={{ overflow: 'hidden' }}>
            <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--color-text-primary)', lineHeight: 1.2, letterSpacing: '-0.02em' }}>
              DRIVEVITALS
            </div>
            <div style={{ fontSize: 11, color: 'var(--color-text-muted)', letterSpacing: '0.02em' }}>
              Fleet Intelligence
            </div>
          </div>
        )}
      </div>

      <nav style={{ flex: 1, overflowY: 'auto', padding: collapsed ? '8px 8px' : '8px 12px' }}>
        {sections.map((section) => (
          <div key={section} style={{ marginBottom: 4 }}>
            {!collapsed && (
              <div style={{
                fontSize: 10,
                fontWeight: 600,
                color: 'var(--color-text-muted)',
                letterSpacing: '0.08em',
                padding: '12px 8px 4px',
                textTransform: 'uppercase',
              }}>
                {sectionLabels[section]}
              </div>
            )}
            {navItems
              .filter((item) => item.section === section)
              .map((item) => {
                const isActive = location.pathname === item.to;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    title={collapsed ? item.label : undefined}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      padding: '8px 10px',
                      borderRadius: 8,
                      marginBottom: 2,
                      color: isActive ? 'var(--color-sidebar-active-text)' : 'var(--color-text-secondary)',
                      background: isActive ? 'var(--color-sidebar-active)' : 'transparent',
                      fontWeight: isActive ? 500 : 400,
                      fontSize: 13.5,
                      transition: 'all 0.15s ease',
                      textDecoration: 'none',
                      justifyContent: collapsed ? 'center' : 'flex-start',
                    }}
                    onMouseEnter={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.background = 'var(--color-sidebar-hover)';
                        e.currentTarget.style.color = 'var(--color-text-primary)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.background = 'transparent';
                        e.currentTarget.style.color = 'var(--color-text-secondary)';
                      }
                    }}
                  >
                    <span style={{ flexShrink: 0, display: 'flex' }}>{item.icon}</span>
                    {!collapsed && <span>{item.label}</span>}
                  </NavLink>
                );
              })}
          </div>
        ))}
      </nav>

      <div style={{ borderTop: '1px solid var(--color-sidebar-border)', padding: collapsed ? '8px' : '8px 12px' }}>
        <NavLink
          to="/settings"
          title={collapsed ? 'Settings' : undefined}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '10px',
            borderRadius: 8,
            color: location.pathname === '/settings' ? 'var(--color-sidebar-active-text)' : 'var(--color-text-secondary)',
            background: location.pathname === '/settings' ? 'var(--color-sidebar-active)' : 'transparent',
            textDecoration: 'none',
            fontSize: 13.5,
            transition: 'all 0.15s ease',
            justifyContent: collapsed ? 'center' : 'flex-start',
          }}
          onMouseEnter={(e) => {
            if (location.pathname !== '/settings') {
              e.currentTarget.style.background = 'var(--color-sidebar-hover)';
            }
          }}
          onMouseLeave={(e) => {
            if (location.pathname !== '/settings') {
              e.currentTarget.style.background = 'transparent';
            }
          }}
        >
          <Settings size={18} strokeWidth={1.8} />
          {!collapsed && <span>Settings</span>}
        </NavLink>

        <button
          onClick={onToggle}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '100%',
            padding: '8px',
            marginTop: 4,
            borderRadius: 8,
            color: 'var(--color-text-muted)',
            transition: 'all 0.15s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--color-sidebar-hover)';
            e.currentTarget.style.color = 'var(--color-text-primary)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'transparent';
            e.currentTarget.style.color = 'var(--color-text-muted)';
          }}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>
    </>
  );
}

export function Sidebar({ collapsed, onToggle, mobileOpen, onMobileClose }) {
  return (
    <>
      <aside
        style={{
          width: collapsed ? 64 : 240,
          background: 'var(--color-sidebar-bg)',
          borderRight: '1px solid var(--color-sidebar-border)',
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
          position: 'fixed',
          top: 0,
          left: 0,
          zIndex: 100,
          transition: 'width 0.2s ease',
          overflow: 'hidden',
        }}
        className="sidebar-desktop"
      >
        <SidebarContent collapsed={collapsed} onToggle={onToggle} />
      </aside>

      {mobileOpen && (
        <div
          onClick={onMobileClose}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.4)',
            zIndex: 200,
            display: 'none',
          }}
          className="sidebar-overlay"
        />
      )}

      <aside
        style={{
          width: 260,
          background: 'var(--color-sidebar-bg)',
          borderRight: '1px solid var(--color-sidebar-border)',
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
          position: 'fixed',
          top: 0,
          left: mobileOpen ? 0 : -260,
          zIndex: 201,
          transition: 'left 0.25s ease',
          overflow: 'hidden',
        }}
        className="sidebar-mobile"
      >
        <SidebarContent collapsed={false} onToggle={onToggle} />
      </aside>
    </>
  );
}
