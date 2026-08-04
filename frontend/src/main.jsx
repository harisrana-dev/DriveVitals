import React from "react";
import ReactDOM from "react-dom/client";
import "./styles/globals.css";
import "./styles/dashboard-theme.css";
import App from "./App";
import { applyInitialTheme } from "./hooks/useTheme";

applyInitialTheme();

ReactDOM.createRoot(document.getElementById("root")).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
