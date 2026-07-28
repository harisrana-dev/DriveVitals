import { useState, useCallback } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

export function AppShell() {
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

  const marginLeft = sidebarCollapsed ? 64 : 240;

  return (
    <>
      <style>{`
        .sidebar-desktop { display: flex; }
        .sidebar-mobile { display: none; }
        .sidebar-overlay { display: none !important; }
        .main-content { margin-left: ${marginLeft}px; transition: margin-left 0.2s ease; }
        .mobile-menu-btn { display: none !important; }
        .topbar-search { display: flex !important; }
        .profile-name { display: inline; }
        @media (max-width: 1024px) {
          .sidebar-desktop { display: none !important; }
          .sidebar-mobile { display: flex !important; }
          .sidebar-overlay { display: block !important; }
          .main-content { margin-left: 0 !important; }
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

      <div className="main-content" style={{ flex: 1, minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <TopBar onMenuClick={handleMobileMenu} />
        <main style={{ flex: 1, padding: 24, overflow: 'auto' }}>
          <Outlet />
        </main>
      </div>
    </>
  );
}
