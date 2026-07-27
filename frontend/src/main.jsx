import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./styles/globals.css";

import { DashboardProvider } from "./context/DashboardContext";
import { ThemeProvider } from "./context/ThemeContext";
import GetStarted from "./pages/Introductionpage";
import Login from "./pages/login";
import Signup from "./pages/signup";
import DashboardPage from "./pages/DashboardPage";
import Settings from "./pages/setting";
import Reports from "./pages/report";
import Trips from "./pages/trip";
import NotFound from "./pages/404page";

ReactDOM.createRoot(document.getElementById("root")).render(
    <React.StrictMode>
        <BrowserRouter>
            <ThemeProvider>
                <DashboardProvider>
                    <Routes>
                        <Route path="/"          element={<GetStarted />} />
                        <Route path="/login"     element={<Login />} />
                        <Route path="/signup"    element={<Signup />} />
                        <Route path="/dashboard" element={<DashboardPage />} />
                        <Route path="/settings"  element={<Settings />} />
                        <Route path="/reports"   element={<Reports />} />
                        <Route path="/trips"     element={<Trips />} />
                        <Route path="*"          element={<NotFound />} />
                    </Routes>
                </DashboardProvider>
            </ThemeProvider>
        </BrowserRouter>
    </React.StrictMode>
);
