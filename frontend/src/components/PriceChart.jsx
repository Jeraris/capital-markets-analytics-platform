import { useState } from "react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip,
  ResponsiveContainer, ReferenceLine, CartesianGrid,
} from "recharts";
import { useData } from "../useData.js";
import { api } from "../api.js";
import { Card, Spinner, EmptyState, Num } from "./ui.jsx";

const SYMBOLS = ["AAPL", "MSFT", "GOOG", "JPM", "BNS.TO", "TSLA"];
const WINDOWS = [30, 60, 90];

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div style={{
      background: "var(--bg)", border: "1px solid var(--border2)",
      padding: "10px 14px", borderRadius: 3,
      fontFamily: "var(--mono)", fontSize: 11,
    }}>
      <div style={{ color: "var(--muted)", marginBottom: 4 }}>{d.date}</div>
      <div>close <span style={{ color: "var(--accent)" }}>${d.close?.toFixed(2)}</span></div>
      {d.sma != null && (
        <div>sma20 <span style={{ color: "var(--warn)" }}>${d.sma?.toFixed(2)}</span></div>
      )}
    </div>
  );
};

export default function PriceChart() {
  const [symbol, setSymbol] = useState("AAPL");
  const [days,   setDays]   = useState(60);
  const [showSma, setShowSma] = useState(true);

  const { data: hist, loading } = useData(
    () => api.getPriceHistory(symbol, days),
    [symbol, days]
  );
  const { data: quote } = useData(() => api.getSymbol(symbol), [symbol]);
  const { data: smaData } = useData(
    () => showSma ? api.getMovingAverage(symbol, 20) : Promise.resolve(null),
    [symbol, showSma]
  );

  const rows = hist?.history ?? [];
  // Inject SMA as a flat line on the latest value across all visible rows
  const chartData = rows.map((r, i) => ({
    ...r,
    sma: showSma && smaData ? smaData.sma : undefined,
  }));

  const minP  = rows.length ? Math.min(...rows.map(r => r.low))  * 0.995 : 0;
  const maxP  = rows.length ? Math.max(...rows.map(r => r.high)) * 1.005 : 0;
  const first = rows[0]?.close ?? 0;
  const last  = rows[rows.length - 1]?.close ?? 0;
  const pct   = first ? ((last - first) / first) * 100 : 0;

  return (
    <Card
      title="Price Chart"
      accent="var(--accent2)"
      action={
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {WINDOWS.map(w => (
            <button key={w} onClick={() => setDays(w)} style={btnStyle(days === w)}>
              {w}d
            </button>
          ))}
        </div>
      }
    >
      {/* Symbol selector */}
      <div style={{ display: "flex", gap: 6, marginBottom: 16, flexWrap: "wrap" }}>
        {SYMBOLS.map(sym => (
          <button key={sym} onClick={() => setSymbol(sym)} style={symBtn(symbol === sym)}>
            {sym}
          </button>
        ))}
        <button
          onClick={() => setShowSma(v => !v)}
          style={{ ...symBtn(showSma), marginLeft: "auto", color: showSma ? "var(--warn)" : "var(--muted)" }}
        >
          SMA 20
        </button>
      </div>

      {/* Quote strip */}
      {quote && (
        <div style={{ display: "flex", gap: 24, marginBottom: 20, fontFamily: "var(--mono)" }}>
          <span style={{ fontSize: 22, color: "var(--text)" }}>${quote.price?.toFixed(2)}</span>
          <span style={{ fontSize: 13, alignSelf: "center" }}>
            <Num value={quote.change} decimals={2} prefix="$" colored />
            {" / "}
            <Num value={quote.change_pct} decimals={2} suffix="%" colored />
          </span>
          <span style={{ fontSize: 11, color: "var(--muted)", alignSelf: "center" }}>
            {days}d change{" "}
            <Num value={pct} decimals={2} suffix="%" colored />
          </span>
        </div>
      )}

      {loading ? <Spinner /> : rows.length === 0 ? <EmptyState /> : (
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={chartData} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="var(--accent2)" stopOpacity={0.18} />
                <stop offset="95%" stopColor="var(--accent2)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fontFamily: "var(--mono)", fontSize: 10, fill: "var(--muted)" }}
              tickLine={false} axisLine={false}
              interval={Math.floor(rows.length / 5)}
            />
            <YAxis
              domain={[minP, maxP]}
              tick={{ fontFamily: "var(--mono)", fontSize: 10, fill: "var(--muted)" }}
              tickLine={false} axisLine={false}
              tickFormatter={v => `$${v.toFixed(0)}`}
              width={52}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone" dataKey="close"
              stroke="var(--accent2)" strokeWidth={1.5}
              fill="url(#priceGrad)" dot={false} activeDot={{ r: 3, fill: "var(--accent2)" }}
            />
            {showSma && smaData && (
              <ReferenceLine
                y={smaData.sma}
                stroke="var(--warn)"
                strokeDasharray="4 4"
                strokeWidth={1}
                label={{ value: `SMA${smaData.window} $${smaData.sma?.toFixed(2)}`, position: "insideTopRight", fontFamily: "var(--mono)", fontSize: 10, fill: "var(--warn)" }}
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}

const btnStyle = (active) => ({
  fontFamily: "var(--mono)", fontSize: 11,
  padding: "3px 10px", borderRadius: 2,
  border: `1px solid ${active ? "var(--accent2)" : "var(--border2)"}`,
  color: active ? "var(--accent2)" : "var(--muted)",
  background: "none", cursor: "pointer", transition: "all 0.15s",
});
const symBtn = (active) => ({
  fontFamily: "var(--mono)", fontSize: 11,
  padding: "4px 12px", borderRadius: 2,
  border: `1px solid ${active ? "var(--accent)" : "var(--border)"}`,
  background: active ? "rgba(0,212,170,0.08)" : "none",
  color: active ? "var(--accent)" : "var(--muted)",
  cursor: "pointer", transition: "all 0.15s",
  letterSpacing: "0.04em",
});
