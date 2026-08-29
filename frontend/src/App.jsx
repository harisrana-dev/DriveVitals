import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { Dashboard } from './pages/Dashboard';
import { FleetPage } from './pages/Fleet';
import { TripsPage } from './pages/Trips';
import { DriversPage } from './pages/Drivers';
import { AlertsPage } from './pages/Alerts';
import { AnalyticsPage } from './pages/Analytics';
import { VehicleHealthPage } from './pages/VehicleHealth';
import { MaintenancePage } from './pages/Maintenance';
import { SettingsPage } from './pages/Settings';
import GetStarted from './pages/Introductionpage';
import Login from './pages/login';
import Signup from './pages/signup';
import { AuthProvider } from './context/AuthContext';
import {
 FleetProvider
} from "./context/FleetContext";
import {
 TripsProvider
} from "./context/TripsContext";
import {
 TripDrawerProvider
} from "./context/TripDrawerContext";
import {
 LiveDataProvider
} from "./context/LiveDataContext";

function App() {
  return (
    <BrowserRouter>
    <AuthProvider>
    <LiveDataProvider>
    <FleetProvider>
    <TripsProvider>
    <TripDrawerProvider>
      <Routes>
        <Route path="/" element={<GetStarted />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/fleet" element={<FleetPage />} />
            <Route path="/trips" element={<TripsPage />} />
            <Route path="/drivers" element={<DriversPage />} />
            <Route path="/alerts" element={<AlertsPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/vehicle-health" element={<VehicleHealthPage />} />
            <Route path="/maintenance" element={<MaintenancePage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Route>
        </Route>
      </Routes>
    </TripDrawerProvider>
    </TripsProvider>
    </FleetProvider>
    </LiveDataProvider>
    </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
