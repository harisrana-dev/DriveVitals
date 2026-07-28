import { useState, useEffect } from "react";

/*
  AppLoader — minimal enterprise boot screen.
  Shows branding + telemetry pulse for ~1.8s then calls onComplete.
  Inherits theme from the [data-theme] attribute on <html>.
*/

const THEME = {
  light: {
    bg: "#f5f6f8",
    surface: "#ffffff",
    text: "#1a1d26",
    muted: "#8b919a",
    accent: "#3b5bdb",
    accentLight: "rgba(59, 91, 219, 0.10)",
    border: "#e2e5ea",
  },
  dark: {
    bg: "#0F172A",
    surface: "#1E293B",
    text: "#F8FAFC",
    muted: "#94A3B8",
    accent: "#5c7cfa",
    accentLight: "rgba(92, 124, 250, 0.10)",
    border: "#243044",
  },
};

function getTheme() {
  const attr = document.documentElement.getAttribute("data-theme");
  return attr === "light" ? THEME.light : THEME.dark;
}

export default function AppLoader({ onComplete }) {
  const [t, setT] = useState(() => getTheme());
  const [phase, setPhase] = useState("enter"); // enter → hold → exit

  // Sync theme if user toggles mid-animation
  useEffect(() => {
    const obs = new MutationObserver(() => setT(getTheme()));
    obs.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });
    return () => obs.disconnect();
  }, []);

  // Phase sequencer
  useEffect(() => {
    const t1 = setTimeout(() => setPhase("hold"), 400);
    const t2 = setTimeout(() => setPhase("exit"), 1800);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, []);

  // Fire onComplete after exit fade finishes
  useEffect(() => {
    if (phase !== "exit") return;
    const id = setTimeout(() => onComplete?.(), 450);
    return () => clearTimeout(id);
  }, [phase, onComplete]);

  const fade = phase === "enter"
    ? { opacity: 0 }
    : phase === "exit"
    ? { opacity: 0 }
    : { opacity: 1 };

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 9999,
      display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center",
      backgroundColor: t.bg,
      transition: "opacity 0.4s ease",
      ...fade,
    }}>
      {/* Logo mark + wordmark */}
      <div style={{
        display: "flex", alignItems: "center", gap: 12,
        marginBottom: 32,
        opacity: phase === "enter" ? 0 : 1,
        transform: phase === "enter" ? "translateY(6px)" : "translateY(0)",
        transition: "opacity 0.5s ease 0.1s, transform 0.5s ease 0.1s",
      }}>
        <div style={{
          width: 40, height: 40,
          backgroundColor: t.accent,
          color: "#fff",
          fontSize: 13, fontWeight: 700,
          borderRadius: 10,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontFamily: "'Inter', sans-serif",
          letterSpacing: "-0.3px",
        }}>DV</div>
        <span style={{
          fontSize: 20, fontWeight: 700,
          color: t.text,
          letterSpacing: "-0.4px",
          fontFamily: "'Inter', sans-serif",
        }}>DriveVitals</span>
      </div>

      {/* Progress rail */}
      <div style={{
        width: 180, height: 3,
        borderRadius: 2,
        backgroundColor: t.border,
        overflow: "hidden",
        marginBottom: 20,
      }}>
        <div style={{
          width: phase === "enter" ? "0%" : phase === "hold" ? "100%" : "100%",
          height: "100%",
          borderRadius: 2,
          backgroundColor: t.accent,
          transition: phase === "enter"
            ? "none"
            : "width 1.4s cubic-bezier(0.4, 0, 0.2, 1)",
        }} />
      </div>

      {/* Status label */}
      <span style={{
        fontSize: 12,
        color: t.muted,
        fontFamily: "'Inter', sans-serif",
        fontWeight: 500,
        letterSpacing: "0.2px",
        opacity: phase === "enter" ? 0 : 1,
        transition: "opacity 0.4s ease 0.2s",
      }}>
        Establishing telemetry link…
      </span>
    </div>
  );
}
