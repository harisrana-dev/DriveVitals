import React from "react";
import ReactDOM from "react-dom/client";
import "./styles/globals.css";
import "./styles/dashboard-theme.css";
import App from "./App";

function initTheme() {
  const stored = localStorage.getItem('drivevitals-theme');
  if (stored === 'dark' || stored === 'light') {
    document.documentElement.setAttribute('data-theme', stored);
  } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.documentElement.setAttribute('data-theme', 'dark');
  } else {
    document.documentElement.setAttribute('data-theme', 'light');
  }
}

initTheme();

ReactDOM.createRoot(document.getElementById("root")).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
