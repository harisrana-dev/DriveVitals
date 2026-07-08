import Sidebar from './Sidebar/Sidebar';
import TopNavbar from './TopNavbar/TopNavbar';

// AppLayout: the persistent shell around every route.
// Sprint 1 has a single route (Dashboard), passed in as children.
function AppLayout({ children }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-main">
        <TopNavbar />
        <main className="app-content">{children}</main>
      </div>
    </div>
  );
}

export default AppLayout;
