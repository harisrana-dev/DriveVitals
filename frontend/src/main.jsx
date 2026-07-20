import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./styles/globals.css";

import { DashboardProvider } from "./context/DashboardContext";
import GetStarted from "./pages/Introductionpage";
import Login from "./pages/login";
import Signup from "./pages/signup";
import DashboardPage from "./pages/DashboardPage";

ReactDOM.createRoot(document.getElementById("root")).render(
    <React.StrictMode>
        <BrowserRouter>
            <DashboardProvider>
                <Routes>
                    <Route path="/"          element={<GetStarted />} />
                    <Route path="/login"     element={<Login />} />
                    <Route path="/signup"    element={<Signup />} />
                    <Route path="/dashboard" element={<DashboardPage />} />
                </Routes>
            </DashboardProvider>
        </BrowserRouter>
    </React.StrictMode>
);
