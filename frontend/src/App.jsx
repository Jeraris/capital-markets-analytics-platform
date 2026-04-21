import { useState } from "react";
import MarketBar    from "./components/MarketBar.jsx";
import PriceChart   from "./components/PriceChart.jsx";
import PortfolioPnL from "./components/PortfolioPnL.jsx";
import TradeBlotter from "./components/TradeBlotter.jsx";

const TABS = [
  { id: "market",    label: "Market Data" },
  { id: "portfolio", label: "Portfolio" },
  { id: "blotter",   label: "Trade Blotter" },
];

export default function App() {
  const [tab, setTab] = useState("market");

  return (
    <div style={layout}>
      {/* Header */}
      <header style={header}>
        <div style={logo}>
          <span style={logoAccent}>▸</span>
          CAPITAL MARKETS
          <span style={logoDim}>/ ANALYTICS</span>
        </div>

        {/* Tabs */}
        <nav style={nav}>
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)} style={tabBtn(tab === t.id)}>
              {t.label}
            </button>
          ))}
        </nav>

        <div style={headerRight}>
          <span style={statusDot} />
          <span style={statusText}>LIVE</span>
        </div>
      </header>

      {/* Market ticker */}
      <MarketBar />

      {/* Main content */}
      <main style={main}>
        {tab === "market" && (
          <div style={grid}>
            <PriceChart />
          </div>
        )}
        {tab === "portfolio" && (
          <div style={grid}>
            <PortfolioPnL />
          </div>
        )}
        {tab === "blotter" && (
          <div style={grid}>
            <TradeBlotter />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer style={footer}>
        <span>Capital Markets Analytics Platform</span>
        <span style={{ color: "var(--muted)" }}>·</span>
        <span style={{ color: "var(--muted)" }}>FastAPI + PostgreSQL + React</span>
        <span style={{ color: "var(--muted)" }}>·</span>
        <span style={{ color: "var(--muted)" }}>Jeremiah Arisekola-Ojo</span>
      </footer>
    </div>
  );
}

const layout = {
  display: "flex", flexDirection: "column",
  height: "100vh", overflow: "hidden",
};
const header = {
  display: "flex", alignItems: "center",
  padding: "0 24px", height: 52, flexShrink: 0,
  borderBottom: "1px solid var(--border)",
  background: "var(--surface)",
  gap: 32,
};
const logo = {
  fontFamily: "var(--mono)", fontSize: 13,
  fontWeight: 500, letterSpacing: "0.12em",
  color: "var(--text)", flexShrink: 0,
  display: "flex", alignItems: "center", gap: 8,
};
const logoAccent = { color: "var(--accent)", fontSize: 16 };
const logoDim    = { color: "var(--muted)", fontWeight: 400 };
const nav = { display: "flex", gap: 0, flex: 1 };
const tabBtn = (active) => ({
  fontFamily: "var(--mono)", fontSize: 11, letterSpacing: "0.1em",
  padding: "0 20px", height: 52,
  background: "none", border: "none",
  borderBottom: `2px solid ${active ? "var(--accent)" : "transparent"}`,
  color: active ? "var(--text)" : "var(--muted)",
  cursor: "pointer", transition: "all 0.15s",
  textTransform: "uppercase",
});
const headerRight = {
  display: "flex", alignItems: "center", gap: 6, flexShrink: 0,
};
const statusDot = {
  width: 6, height: 6, borderRadius: "50%",
  background: "var(--gain)",
  animation: "pulse 2s ease-in-out infinite",
  display: "inline-block",
};
const statusText = {
  fontFamily: "var(--mono)", fontSize: 10,
  color: "var(--gain)", letterSpacing: "0.12em",
};
const main = {
  flex: 1, overflowY: "auto", padding: "24px",
};
const grid = {
  display: "flex", flexDirection: "column", gap: 16,
  maxWidth: 1200, margin: "0 auto",
};
const footer = {
  display: "flex", gap: 12, alignItems: "center",
  padding: "10px 24px", flexShrink: 0,
  borderTop: "1px solid var(--border)",
  background: "var(--surface)",
  fontFamily: "var(--mono)", fontSize: 10,
  color: "var(--text)", letterSpacing: "0.06em",
};
