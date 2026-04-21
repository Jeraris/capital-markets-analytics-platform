import { useData } from "../useData.js";
import { api } from "../api.js";
import { Num } from "./ui.jsx";

export default function MarketBar() {
  const { data } = useData(api.getAllMarketData);

  if (!data?.length) return (
    <div style={bar}>
      <span style={{ color: "var(--muted)", fontFamily: "var(--mono)", fontSize: 11 }}>
        ● connecting to market feed...
      </span>
    </div>
  );

  return (
    <div style={bar}>
      <span style={label}>LIVE</span>
      <div style={track}>
        {[...data, ...data].map((d, i) => (
          <span key={i} style={item}>
            <span style={sym}>{d.symbol}</span>
            <Num value={d.price} decimals={2} prefix="$" />
            <Num value={d.change_pct} decimals={2} suffix="%" colored />
          </span>
        ))}
      </div>
    </div>
  );
}

const bar = {
  background: "var(--surface)",
  borderBottom: "1px solid var(--border)",
  padding: "8px 24px",
  display: "flex",
  alignItems: "center",
  gap: 16,
  overflow: "hidden",
  flexShrink: 0,
};
const label = {
  fontFamily: "var(--mono)",
  fontSize: 10,
  letterSpacing: "0.15em",
  color: "var(--gain)",
  animation: "pulse 2s ease-in-out infinite",
  flexShrink: 0,
};
const track = {
  display: "flex",
  gap: 32,
  overflow: "hidden",
  maskImage: "linear-gradient(to right, transparent, black 5%, black 95%, transparent)",
};
const item = {
  display: "flex",
  gap: 8,
  alignItems: "center",
  flexShrink: 0,
  fontFamily: "var(--mono)",
  fontSize: 12,
};
const sym = {
  color: "var(--muted)",
  fontSize: 11,
  letterSpacing: "0.06em",
};
