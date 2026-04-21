import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { useData } from "../useData.js";
import { api } from "../api.js";
import { Card, Spinner, EmptyState, Num } from "./ui.jsx";

const SECTOR_COLORS = [
  "var(--accent)", "var(--accent2)", "var(--warn)",
  "#a78bfa", "#f472b6", "#34d399",
];

const PieLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, sector }) => {
  if (percent < 0.06) return null;
  const RADIAN = Math.PI / 180;
  const r = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + r * Math.cos(-midAngle * RADIAN);
  const y = cy + r * Math.sin(-midAngle * RADIAN);
  return (
    <text x={x} y={y} fill="var(--bg)" textAnchor="middle" dominantBaseline="central"
      style={{ fontFamily: "var(--mono)", fontSize: 10 }}>
      {(percent * 100).toFixed(0)}%
    </text>
  );
};

export default function PortfolioPnL() {
  const { data: pnl,      loading: pnlLoad }  = useData(api.getPnL);
  const { data: exposure, loading: expLoad }  = useData(api.getExposure);

  const loading = pnlLoad || expLoad;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 280px", gap: 16 }}>
      {/* P&L table */}
      <Card title="Portfolio P&L" accent="var(--gain)">
        {loading ? <Spinner /> : !pnl ? <EmptyState /> : (
          <>
            {/* Summary row */}
            <div style={summary}>
              <div>
                <div style={metaLabel}>Total Market Value</div>
                <div style={metaValue}>
                  <Num value={pnl.total_market_value} decimals={2} prefix="$" />
                </div>
              </div>
              <div>
                <div style={metaLabel}>Unrealized P&amp;L</div>
                <div style={metaValue}>
                  <Num value={pnl.total_unrealized_pnl} decimals={2} prefix="$" colored />
                </div>
              </div>
              <div>
                <div style={metaLabel}>Positions</div>
                <div style={metaValue}>{pnl.positions?.length ?? 0}</div>
              </div>
            </div>

            {/* Table */}
            <table style={table}>
              <thead>
                <tr>
                  {["Symbol", "Qty", "Avg Cost", "Current", "P&L", "P&L %"].map(h => (
                    <th key={h} style={th}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pnl.positions?.map(pos => (
                  <tr key={pos.symbol} style={trStyle}>
                    <td style={{ ...td, color: "var(--text)", fontWeight: 500 }}>{pos.symbol}</td>
                    <td style={td}><Num value={pos.quantity} decimals={0} /></td>
                    <td style={td}><Num value={pos.avg_cost} decimals={2} prefix="$" /></td>
                    <td style={td}><Num value={pos.current_price} decimals={2} prefix="$" /></td>
                    <td style={td}><Num value={pos.unrealized_pnl} decimals={2} prefix="$" colored /></td>
                    <td style={td}><Num value={pos.unrealized_pnl_pct} decimals={2} suffix="%" colored /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </Card>

      {/* Sector donut */}
      <Card title="Sector Exposure" accent="var(--warn)">
        {expLoad ? <Spinner /> : !exposure ? <EmptyState /> : (
          <>
            <ResponsiveContainer width="100%" height={160}>
              <PieChart>
                <Pie
                  data={exposure.exposures}
                  dataKey="market_value"
                  nameKey="sector"
                  cx="50%" cy="50%"
                  innerRadius={42} outerRadius={72}
                  paddingAngle={2}
                  labelLine={false}
                  label={PieLabel}
                >
                  {exposure.exposures?.map((_, i) => (
                    <Cell key={i} fill={SECTOR_COLORS[i % SECTOR_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(v) => [`$${v.toLocaleString("en-US", { maximumFractionDigits: 0 })}`, "Market Value"]}
                  contentStyle={{
                    background: "var(--bg)", border: "1px solid var(--border2)",
                    fontFamily: "var(--mono)", fontSize: 11, borderRadius: 3,
                  }}
                />
              </PieChart>
            </ResponsiveContainer>

            {/* Legend */}
            <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 8 }}>
              {exposure.exposures?.map((e, i) => (
                <div key={e.sector} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{ width: 8, height: 8, borderRadius: 2, background: SECTOR_COLORS[i % SECTOR_COLORS.length], flexShrink: 0 }} />
                  <span style={{ fontFamily: "var(--mono)", fontSize: 11, color: "var(--muted)", flex: 1 }}>
                    {e.sector}
                  </span>
                  <span style={{ fontFamily: "var(--mono)", fontSize: 11 }}>
                    {e.weight_pct?.toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          </>
        )}
      </Card>
    </div>
  );
}

const summary = {
  display: "flex", gap: 32, marginBottom: 20,
  paddingBottom: 16, borderBottom: "1px solid var(--border)",
};
const metaLabel = { fontFamily: "var(--mono)", fontSize: 10, color: "var(--muted)", marginBottom: 4, letterSpacing: "0.08em" };
const metaValue = { fontFamily: "var(--mono)", fontSize: 16 };
const table = { width: "100%", borderCollapse: "collapse" };
const th = {
  fontFamily: "var(--mono)", fontSize: 10, color: "var(--muted)",
  textAlign: "right", padding: "4px 8px", letterSpacing: "0.08em",
  borderBottom: "1px solid var(--border)", textTransform: "uppercase",
};
const td = {
  fontFamily: "var(--mono)", fontSize: 12, textAlign: "right",
  padding: "8px 8px", borderBottom: "1px solid var(--border)",
  color: "var(--muted)",
};
const trStyle = { transition: "background 0.1s" };
