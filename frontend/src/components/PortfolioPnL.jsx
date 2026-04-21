import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { useData } from "../useData.js";
import { api } from "../api.js";
import { Card, Spinner, EmptyState, ErrorState, Num } from "./ui.jsx";

const SECTOR_COLORS = ["var(--accent)", "var(--accent2)", "var(--warn)", "#a78bfa", "#f472b6", "#34d399"];

export default function PortfolioPnL() {
  const { data: pnl,      loading: pnlLoad,  error: pnlErr  } = useData(api.getPnL);
  const { data: exposure, loading: expLoad,  error: expErr  } = useData(api.getExposure);

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: 16, alignItems: "start" }}>

      {/* P&L table */}
      <Card title="Portfolio P&L" accent="var(--gain)">
        {pnlErr   ? <ErrorState message={pnlErr} /> :
         pnlLoad  ? <Spinner /> :
         !pnl     ? <EmptyState /> : (
          <>
            {/* Summary strip */}
            <div style={summary}>
              <Metric label="Market Value"    value={<Num value={pnl.total_market_value}   decimals={2} prefix="$" />} />
              <Metric label="Unrealized P&L"  value={<Num value={pnl.total_unrealized_pnl} decimals={2} prefix="$" colored />} />
              <Metric label="Open Positions"  value={pnl.positions?.length ?? 0} />
              <Metric label="As of"           value={
                <span style={{ fontSize: 11 }}>
                  {new Date(pnl.as_of).toLocaleTimeString("en-CA", { hour: "2-digit", minute: "2-digit" })}
                </span>
              } />
            </div>

            {/* Table */}
            <div style={{ overflowX: "auto" }}>
              <table style={table}>
                <thead>
                  <tr>
                    {["Symbol", "Qty", "Avg Cost", "Current", "P&L ($)", "P&L (%)"].map(h => (
                      <th key={h} style={th}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {pnl.positions?.map(pos => {
                    const up = pos.unrealized_pnl >= 0;
                    return (
                      <tr key={pos.symbol} style={{ borderBottom: "1px solid var(--border)", background: "transparent" }}>
                        <td style={{ ...td, color: "var(--text)", fontWeight: 500, textAlign: "left" }}>{pos.symbol}</td>
                        <td style={td}><Num value={pos.quantity} decimals={0} /></td>
                        <td style={td}><Num value={pos.avg_cost} decimals={2} prefix="$" /></td>
                        <td style={td}><Num value={pos.current_price} decimals={2} prefix="$" /></td>
                        <td style={td}><Num value={pos.unrealized_pnl} decimals={2} prefix="$" colored /></td>
                        <td style={td}>
                          <span style={{
                            display: "inline-flex", alignItems: "center", gap: 4,
                            color: up ? "var(--gain)" : "var(--loss)",
                            fontFamily: "var(--mono)",
                          }}>
                            {up ? "▲" : "▼"}
                            {Math.abs(pos.unrealized_pnl_pct).toFixed(2)}%
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        )}
      </Card>

      {/* Sector donut */}
      <Card title="Sector Exposure" accent="var(--warn)">
        {expErr   ? <ErrorState message={expErr} /> :
         expLoad  ? <Spinner /> :
         !exposure ? <EmptyState /> : (
          <>
            <div style={{ textAlign: "center", marginBottom: 4, fontFamily: "var(--mono)", fontSize: 10, color: "var(--muted)" }}>
              Total ${(exposure.total_market_value / 1000).toFixed(1)}k
            </div>
            <ResponsiveContainer width="100%" height={170}>
              <PieChart>
                <Pie
                  data={exposure.exposures}
                  dataKey="market_value"
                  nameKey="sector"
                  cx="50%" cy="50%"
                  innerRadius={46} outerRadius={76}
                  paddingAngle={2}
                  strokeWidth={0}
                >
                  {exposure.exposures?.map((_, i) => (
                    <Cell key={i} fill={SECTOR_COLORS[i % SECTOR_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={v => [`$${v.toLocaleString("en-US", { maximumFractionDigits: 0 })}`, "Mkt Value"]}
                  contentStyle={{
                    background: "var(--bg)", border: "1px solid var(--border2)",
                    fontFamily: "var(--mono)", fontSize: 11, borderRadius: 3,
                  }}
                />
              </PieChart>
            </ResponsiveContainer>

            <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 12 }}>
              {exposure.exposures?.map((e, i) => (
                <div key={e.sector}>
                  <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 3 }}>
                    <div style={{ width: 8, height: 8, borderRadius: 1, background: SECTOR_COLORS[i % SECTOR_COLORS.length], flexShrink: 0 }} />
                    <span style={{ fontFamily: "var(--mono)", fontSize: 11, color: "var(--muted)", flex: 1 }}>{e.sector}</span>
                    <span style={{ fontFamily: "var(--mono)", fontSize: 11 }}>{e.weight_pct?.toFixed(1)}%</span>
                  </div>
                  {/* Mini progress bar */}
                  <div style={{ height: 2, background: "var(--border)", borderRadius: 1 }}>
                    <div style={{ height: "100%", width: `${e.weight_pct}%`, background: SECTOR_COLORS[i % SECTOR_COLORS.length], borderRadius: 1, transition: "width 0.6s ease" }} />
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </Card>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div>
      <div style={{ fontFamily: "var(--mono)", fontSize: 10, color: "var(--muted)", marginBottom: 4, letterSpacing: "0.08em", textTransform: "uppercase" }}>{label}</div>
      <div style={{ fontFamily: "var(--mono)", fontSize: 15 }}>{value}</div>
    </div>
  );
}

const summary = {
  display: "flex", gap: 28, marginBottom: 20,
  paddingBottom: 16, borderBottom: "1px solid var(--border)",
  flexWrap: "wrap",
};
const table = { width: "100%", borderCollapse: "collapse" };
const th = {
  fontFamily: "var(--mono)", fontSize: 10, color: "var(--muted)",
  textAlign: "right", padding: "4px 10px", letterSpacing: "0.08em",
  borderBottom: "1px solid var(--border)", textTransform: "uppercase",
};
const td = {
  fontFamily: "var(--mono)", fontSize: 12, textAlign: "right",
  padding: "9px 10px", color: "var(--muted)",
};
