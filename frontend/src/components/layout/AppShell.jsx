import { useState, useCallback } from 'react';
import { Outlet } from 'react-router-dom';
import { WifiOff, RefreshCw } from 'lucide-react';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { getMainContentMargin } from './sidebarLayout';
import { VehicleDrawerProvider } from '../../context/VehicleDrawerContext';
import { VehicleDrawer } from '../fleet/VehicleDrawer';
import { MaintenanceDrawer } from '../maintenance/MaintenanceDrawer';
import { useVehicleDrawer } from '../../context/useVehicleDrawer';
import { useLiveData } from '../../context/useLiveData';
import { useNow } from '../../hooks/useNow';
import { deriveConnectionState } from '../../utils/dashboard';

function AppShellInner() {
  const {
    selectedVehicleId, drawerDepth, closeDrawer,
    maintenanceVehicleId, maintenanceDepth, closeMaintenance,
    openMaintenance,
  } = useVehicleDrawer();
  const { connectionStatus: rawConnectionStatus, lastUpdate, syncing, sync } = useLiveData();
  const now = useNow(5000);
  const connectionStatus = deriveConnectionState(rawConnectionStatus, lastUpdate, now);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed((prev) => !prev);
  }, []);

  const handleMobileClose = useCallback(() => {
    setMobileOpen(false);
  }, []);

  const handleMobileMenu = useCallback(() => {
    setMobileOpen((prev) => !prev);
  }, []);

  const marginLeft = getMainContentMargin(sidebarCollapsed);

  return (
    <>
      <style>{`
        .sidebar-desktop { display: flex; }
        .sidebar-mobile { display: none; }
        .sidebar-overlay { display: none !important; }
        #dv-app-shell { margin-left: ${marginLeft}px; transition: margin-left 0.2s ease; }
        .mobile-menu-btn { display: none !important; }
        .topbar-search { display: flex !important; }
        .profile-name { display: inline; }
        @media (max-width: 1024px) {
          .sidebar-desktop { display: none !important; }
          .sidebar-mobile { display: flex !important; }
          .sidebar-overlay { display: block !important; }
          #dv-app-shell { margin-left: 0 !important; }
          .mobile-menu-btn { display: flex !important; }
          .topbar-search { display: none !important; }
          .profile-name { display: none; }
        }
      `}</style>

      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={toggleSidebar}
        mobileOpen={mobileOpen}
        onMobileClose={handleMobileClose}
      />

      <div id="dv-app-shell" className="main-content" style={{ flex: 1, minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <TopBar onMenuClick={handleMobileMenu} />
        {(connectionStatus === 'offline' || connectionStatus === 'stale') && (
          <div
            className="fade-in"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '10px 24px',
              background: 'var(--color-amber-bg)',
              borderBottom: '1px solid var(--color-amber)',
              fontSize: 12,
              fontWeight: 500,
              color: 'var(--color-text-primary)',
            }}
          >
            <WifiOff size={14} style={{ color: 'var(--color-amber)', flexShrink: 0 }} />
            <span style={{ flex: 1 }}>
              Backend disconnected — showing recent known state.
            </span>
            <button
              onClick={sync}
              disabled={syncing}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                padding: '5px 12px',
                borderRadius: 6,
                border: '1px solid var(--color-amber)',
                background: 'transparent',
                color: 'var(--color-amber)',
                fontSize: 11,
                fontWeight: 600,
                cursor: syncing ? 'default' : 'pointer',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => { if (!syncing) { e.currentTarget.style.background = 'var(--color-amber)'; e.currentTarget.style.color = '#fff'; } }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--color-amber)'; }}
            >
              <RefreshCw size={12} style={{ animation: syncing ? 'spin 1s linear infinite' : 'none' }} />
              Retry
            </button>
          </div>
        )}
        <main style={{ flex: 1, padding: 24, overflow: 'auto' }}>
          <Outlet />
        </main>
      </div>

      {selectedVehicleId && (
        <VehicleDrawer
          vehicleId={selectedVehicleId}
          onClose={closeDrawer}
          depth={drawerDepth}
          onOpenMaintenance={openMaintenance}
        />
      )}
      {maintenanceVehicleId && (
        <MaintenanceDrawer
          vehicleId={maintenanceVehicleId}
          onClose={closeMaintenance}
          depth={maintenanceDepth}
        />
      )}
    </>
  );
}

export function AppShell() {
  return (
    <VehicleDrawerProvider>
      <AppShellInner />
    </VehicleDrawerProvider>
  );
}
