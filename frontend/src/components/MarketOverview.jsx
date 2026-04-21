import { useData } from "../useData.js";
import { api } from "../api.js";
import { Card, Spinner, ErrorState, Num } from "./ui.jsx";

export default function MarketOverview() {
  const { data, loading, error } = useData(api.getAllMarketData);

  return (
    <Card title="Market Overview" accent="var(--accent)">
      {error   ? <ErrorState message={error} /> :
       loading ? <Spinner /> : (
        <div style={grid}>
          {data?.map(d => {
            const up = d.change_pct >= 0;
            return (
              <div key={d.symbol} style={tile(up)}>
                <div style={tileSym}>{d.symbol}</div>
                <div style={{ fontFamily: "var(--mono)", fontSize: 18, color: up ? "var(--gain)" : "var(--loss)", marginBottom: 2 }}>
                  ${d.price?.toFixed(2)}
                </div>
                <div style={{ fontFamily: "var(--mono)", fontSize: 11 }}>
                  <Num value={d.change_pct} decimals={2} suffix="%" colored />
                </div>
                <div style={{ fontFamily: "var(--mono)", fontSize: 10, color: "var(--muted)", marginTop: 4 }}>
                  vol {(d.volume / 1e6).toFixed(1)}M
                </div>
                <div style={bar(up, d.change_pct)} />
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}

const grid = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))",
  gap: 10,
};

const tile = (up) => ({
  background: "var(--bg)",
  border: `1px solid ${up ? "rgba(0,212,170,0.2)" : "rgba(255,77,109,0.2)"}`,
  borderRadius: 3,
  padding: "14px 14px 10px",
  position: "relative",
  overflow: "hidden",
  transition: "border-color 0.15s",
});

const tileSym = {
  fontFamily: "var(--mono)", fontSize: 10,
  color: "var(--muted)", letterSpacing: "0.1em",
  marginBottom: 6,
};

// Thin colored bar at the bottom of each tile proportional to % change
const bar = (up, pct) => ({
  position: "absolute", bottom: 0, left: 0,
  height: 2,
  width: `${Math.min(100, Math.abs(pct) * 10)}%`,
  background: up ? "var(--gain)" : "var(--loss)",
  borderRadius: "0 2px 0 0",
});
