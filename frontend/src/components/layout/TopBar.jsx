import { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Bell, Menu, Search, ChevronDown, User, Settings, RefreshCw, LogOut } from 'lucide-react';
import ThemeToggle from '../common/ThemeToggle';
import { ConnectionBadge } from '../ui/ConnectionBadge';
import { useUnacknowledgedAlertCount } from '../../hooks/useFleetData';
import { useLiveData } from '../../context/useLiveData';
import { useNow } from '../../hooks/useNow';
import { deriveConnectionState } from '../../utils/dashboard';
import { getInitials, getRoleLabel } from '../../utils/identity';
import { useAuth } from '../../hooks/useAuth';

const pageTitles = {
  '/dashboard': 'Dashboard',
  '/fleet': 'Fleet',
  '/trips': 'Trips',
  '/drivers': 'Drivers',
  '/alerts': 'Alerts',
  '/analytics': 'Analytics & Reports',
  '/vehicle-health': 'Vehicle Health',
  '/maintenance': 'Maintenance',
  '/settings': 'Settings',
};

function formatTime(timestamp) {
  if (!timestamp) return '--:--:--';
  return new Date(timestamp).toLocaleTimeString([], { hour12: false });
}

export function TopBar({ onMenuClick }) {
  const location = useLocation();
  const navigate = useNavigate();
  const alertCount = useUnacknowledgedAlertCount();
  const { connectionStatus: rawConnectionStatus, lastUpdate, syncing, sync } = useLiveData();
  const { user, logout, canAccessSettings } = useAuth();
  const now = useNow(5000);
  const connectionStatus = deriveConnectionState(rawConnectionStatus, lastUpdate, now);
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef(null);

  const fullName = user?.full_name || '';
  const initials = getInitials(fullName);
  const roleLabel = getRoleLabel(user?.role);

  const handleLogout = async () => {
    setProfileOpen(false);
    await logout();
    navigate('/login', { replace: true });
  };

  useEffect(() => {
    function handleClick(e) {
      if (profileRef.current && !profileRef.current.contains(e.target)) {
        setProfileOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  return (
    <header style={{
      height: 56,
      background: 'var(--color-topbar-bg)',
      borderBottom: '1px solid var(--color-border)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px',
      position: 'sticky',
      top: 0,
      zIndex: 50,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <button
          onClick={onMenuClick}
          aria-label="Toggle mobile menu"
          className="mobile-menu-btn"
          style={{
            display: 'none',
            alignItems: 'center',
            justifyContent: 'center',
            width: 36,
            height: 36,
            borderRadius: 8,
            color: 'var(--color-text-secondary)',
          }}
        >
          <Menu size={20} strokeWidth={1.8} />
        </button>

        <div>
          <h1 style={{ fontSize: 16, fontWeight: 600, color: 'var(--color-text-primary)', lineHeight: 1.2 }}>
            {pageTitles[location.pathname] || 'DriveVitals'}
          </h1>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <ConnectionBadge status={connectionStatus} />

        <span
          style={{
            fontSize: 12,
            color: 'var(--color-text-muted)',
            whiteSpace: 'nowrap',
          }}
          title="Time of the most recent telemetry update"
        >
          Last Update: {formatTime(lastUpdate)}
        </span>

        <button
          onClick={sync}
          disabled={syncing}
          aria-label="Sync data"
          title="Reconnect and re-fetch all data"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 32,
            height: 32,
            borderRadius: 8,
            border: '1px solid var(--color-border)',
            background: 'var(--color-surface)',
            color: 'var(--color-text-secondary)',
            cursor: syncing ? 'default' : 'pointer',
            transition: 'all 0.15s ease',
          }}
          onMouseEnter={(e) => {
            if (!syncing) {
              e.currentTarget.style.background = 'var(--color-surface-hover)';
              e.currentTarget.style.color = 'var(--color-text-primary)';
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'var(--color-surface)';
            e.currentTarget.style.color = 'var(--color-text-secondary)';
          }}
        >
          <RefreshCw
            size={15}
            strokeWidth={1.8}
            style={{ animation: syncing ? 'spin 1s linear infinite' : 'none' }}
          />
        </button>

        <div
          className="topbar-search"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '6px 12px',
            border: '1px solid var(--color-border)',
            borderRadius: 8,
            background: 'var(--color-surface)',
            color: 'var(--color-text-muted)',
            fontSize: 13,
            minWidth: 200,
            cursor: 'text',
          }}
        >
          <Search size={15} strokeWidth={1.8} />
          <span>Search...</span>
        </div>

        <ThemeToggle />

        <button
          aria-label={`Notifications (${alertCount} unread)`}
          title="Notifications"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 36,
            height: 36,
            borderRadius: 8,
            border: '1px solid var(--color-border)',
            background: 'var(--color-surface)',
            color: 'var(--color-text-secondary)',
            position: 'relative',
            transition: 'all 0.15s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--color-surface-hover)';
            e.currentTarget.style.color = 'var(--color-text-primary)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'var(--color-surface)';
            e.currentTarget.style.color = 'var(--color-text-secondary)';
          }}
        >
          <Bell size={18} strokeWidth={1.8} />
          {alertCount > 0 && (
            <span style={{
              position: 'absolute',
              top: 4,
              right: 4,
              width: 16,
              height: 16,
              borderRadius: 8,
              background: 'var(--color-red)',
              color: '#fff',
              fontSize: 9,
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              {alertCount}
            </span>
          )}
        </button>

        <div ref={profileRef} style={{ position: 'relative' }}>
          <button
            onClick={() => setProfileOpen(!profileOpen)}
            aria-label="User menu"
            aria-expanded={profileOpen}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '4px 8px 4px 4px',
              borderRadius: 8,
              border: '1px solid var(--color-border)',
              background: 'var(--color-surface)',
              transition: 'all 0.15s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'var(--color-surface-hover)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'var(--color-surface)';
            }}
          >
            <div style={{
              width: 28,
              height: 28,
              borderRadius: 6,
              background: 'var(--color-accent-light)',
              color: 'var(--color-accent)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 600,
              fontSize: 12,
            }}>
              {initials}
            </div>
            <span className="profile-name" style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-text-primary)' }}>
              {fullName}
            </span>
            <ChevronDown size={14} style={{ color: 'var(--color-text-muted)' }} />
          </button>

          {profileOpen && (
            <div style={{
              position: 'absolute',
              top: '100%',
              right: 0,
              marginTop: 4,
              width: 200,
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: 10,
              boxShadow: 'var(--color-shadow-lg)',
              padding: 4,
              animation: 'fadeIn 0.15s ease-out',
              zIndex: 100,
            }}>
              <div style={{ padding: '8px 10px', borderBottom: '1px solid var(--color-border-light)' }}>
                <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-text-primary)' }}>{fullName}</div>
                <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>{roleLabel}</div>
              </div>
              {[
                { icon: <User size={15} />, label: 'Profile', action: () => setProfileOpen(false) },
                ...(canAccessSettings
                  ? [{ icon: <Settings size={15} />, label: 'Settings', action: () => { setProfileOpen(false); navigate('/settings'); } }]
                  : []),
                { icon: <LogOut size={15} />, label: 'Sign out', action: handleLogout },
              ].map((item) => (
                <button
                  key={item.label}
                  onClick={item.action}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    width: '100%',
                    padding: '7px 10px',
                    borderRadius: 6,
                    fontSize: 13,
                    color: 'var(--color-text-secondary)',
                    transition: 'all 0.1s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'var(--color-surface-hover)';
                    e.currentTarget.style.color = 'var(--color-text-primary)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'transparent';
                    e.currentTarget.style.color = 'var(--color-text-secondary)';
                  }}
                >
                  {item.icon}
                  {item.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
