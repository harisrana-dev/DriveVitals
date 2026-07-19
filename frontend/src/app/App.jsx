import AppLayout from "../components/layout/AppLayout";
import Dashboard from "../features/dashboard/Dashboard";

// Sprint 1: no routing logic yet. App renders the Dashboard directly
// inside the persistent layout shell. routes.jsx documents the intended
// route map for when routing is introduced in a later sprint.
// git config set
function App() {
  return (
    <AppLayout>
      <Dashboard />
    </AppLayout>
  );
}

export default App;
