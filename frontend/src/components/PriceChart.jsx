import { useState, useMemo } from "react";
import {
  ComposedChart, Area, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, Legend,
} from "recharts";
import { useData } from "../useData.js";
import { api } from "../api.js";
import { Card, Spinner, EmptyState, ErrorState, Num } from "./ui.jsx";

const SYMBOLS = ["AAPL", "MSFT", "GOOG", "JPM", "BNS.TO", "TSLA"];
const WINDOWS = [30, 60, 90];

/** Compute SMA over a sliding window from an array of closes */
function computeSMA(closes, window) {
  return closes.map((_, i) => {
    if (i < window - 1) return null;
    const slice = closes.slice(i - window + 1, i + 1);
    return parseFloat((slice.reduce((a, b) => a + b, 0) / window).toFixed(4));
  });
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "var(--bg)", border: "1px solid var(--border2)",
      padding: "10px 14px", borderRadius: 3,
      fontFamily: "var(--mono)", fontSize: 11,
    }}>
      <div style={{ color: "var(--muted)", marginBottom: 6 }}>{label}</div>
      {payload.map(p => (
        p.value != null && (
          <div key={p.dataKey} style={{ color: p.color, marginBottom: 2 }}>
            {p.dataKey === "close" ? "close" : "sma20"}{" "}
            <strong>${p.value?.toFixed(2)}</strong>
          </div>
        )
      ))}
    </div>
  );
};

export default function PriceChart() {
  const [symbol,  setSymbol]  = useState("AAPL");
  const [days,    setDays]    = useState(60);
  const [showSma, setShowSma] = useState(true);

  // Single fetch for price history — symbol selector refetch is clean
  const { data: hist, loading, error } = useData(
    () => api.getPriceHistory(symbol, days),
    [symbol, days]
  );
  const { data: quote } = useData(() => api.getSymbol(symbol), [symbol]);

  // Compute SMA from the history data — no extra API call needed
  const chartData = useMemo(() => {
    const rows = hist?.history ?? [];
    if (!rows.length) return [];
    const closes = rows.map(r => r.close);
    const smaValues = computeSMA(closes, 20);
    return rows.map((r, i) => ({
      ...r,
      sma20: showSma ? smaValues[i] : undefined,
    }));
  }, [hist, showSma]);

  const rows   = hist?.history ?? [];
  const minP   = rows.length ? Math.min(...rows.map(r => r.low))  * 0.995 : 0;
  const maxP   = rows.length ? Math.max(...rows.map(r => r.high)) * 1.005 : 0;
  const first  = rows[0]?.close ?? 0;
  const last   = rows[rows.length - 1]?.close ?? 0;
  const pct    = first ? ((last - first) / first) * 100 : 0;
  const isUp   = pct >= 0;

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
      {/* Symbol pills */}
      <div style={{ display: "flex", gap: 6, marginBottom: 16, flexWrap: "wrap" }}>
        {SYMBOLS.map(s => (
          <button key={s} onClick={() => setSymbol(s)} style={symBtn(symbol === s)}>
            {s}
          </button>
        ))}
        <button
          onClick={() => setShowSma(v => !v)}
          style={{ ...symBtn(showSma), marginLeft: "auto", borderColor: showSma ? "var(--warn)" : "var(--border)", color: showSma ? "var(--warn)" : "var(--muted)" }}
        >
          SMA 20
        </button>
      </div>

      {/* Quote strip */}
      {quote && (
        <div style={{ display: "flex", gap: 24, marginBottom: 20, fontFamily: "var(--mono)", alignItems: "baseline" }}>
          <span style={{ fontSize: 24, color: isUp ? "var(--gain)" : "var(--loss)" }}>
            ${quote.price?.toFixed(2)}
          </span>
          <span style={{ fontSize: 12 }}>
            <Num value={quote.change} decimals={2} prefix="$" colored />
            {"  "}
            <Num value={quote.change_pct} decimals={2} suffix="%" colored />
          </span>
          <span style={{ fontSize: 11, color: "var(--muted)" }}>
            {days}d change{"  "}
            <Num value={pct} decimals={2} suffix="%" colored />
          </span>
          <span style={{ fontSize: 10, color: "var(--muted)", marginLeft: "auto" }}>
            vol {quote.volume?.toLocaleString()}
          </span>
        </div>
      )}

      {error    ? <ErrorState message={error} />  :
       loading  ? <Spinner />                     :
       !rows.length ? <EmptyState />              : (
        <ResponsiveContainer width="100%" height={240}>
          <ComposedChart data={chartData} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor={isUp ? "var(--gain)" : "var(--loss)"} stopOpacity={0.15} />
                <stop offset="95%" stopColor={isUp ? "var(--gain)" : "var(--loss)"} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fontFamily: "var(--mono)", fontSize: 10, fill: "var(--muted)" }}
              tickLine={false} axisLine={false}
              interval={Math.max(1, Math.floor(rows.length / 6))}
            />
            <YAxis
              domain={[minP, maxP]}
              tick={{ fontFamily: "var(--mono)", fontSize: 10, fill: "var(--muted)" }}
              tickLine={false} axisLine={false}
              tickFormatter={v => `$${v.toFixed(0)}`}
              width={54}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone" dataKey="close"
              stroke={isUp ? "var(--gain)" : "var(--loss)"}
              strokeWidth={1.5}
              fill="url(#priceGrad)"
              dot={false}
              activeDot={{ r: 3 }}
            />
            {showSma && (
              <Line
                type="monotone" dataKey="sma20"
                stroke="var(--warn)" strokeWidth={1.2}
                strokeDasharray="4 3"
                dot={false} activeDot={false}
                connectNulls={false}
              />
            )}
          </ComposedChart>
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
