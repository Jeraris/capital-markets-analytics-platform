import { useState } from "react";
import { useData } from "../useData.js";
import { api } from "../api.js";
import { Card, Spinner, EmptyState, Num } from "./ui.jsx";

const SIDE_SYMBOLS = ["AAPL", "MSFT", "GOOG", "JPM", "BNS.TO", "TSLA"];

export default function TradeBlotter() {
  const [filterSymbol, setFilterSymbol] = useState("");
  const [filterSide,   setFilterSide]   = useState("");
  const { data: trades, loading, reload } = useData(
    () => api.getTrades({
      symbol: filterSymbol || undefined,
      side:   filterSide   || undefined,
    }),
    [filterSymbol, filterSide]
  );

  const [form,       setForm]       = useState({ symbol: "AAPL", side: "BUY", quantity: "", price: "" });
  const [submitting, setSubmitting] = useState(false);
  const [formError,  setFormError]  = useState(null);
  const [formOk,     setFormOk]     = useState(false);

  async function submitTrade(e) {
    e.preventDefault();
    setSubmitting(true); setFormError(null); setFormOk(false);
    try {
      await api.createTrade({
        symbol:     form.symbol,
        side:       form.side,
        quantity:   parseFloat(form.quantity),
        price:      parseFloat(form.price),
        asset_class: "EQUITY",
      });
      setFormOk(true);
      setForm(f => ({ ...f, quantity: "", price: "" }));
      reload();
      setTimeout(() => setFormOk(false), 3000);
    } catch (err) {
      setFormError(err?.response?.data?.detail ?? "Trade submission failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Submit trade form */}
      <Card title="Submit Trade" accent="var(--accent)">
        <form onSubmit={submitTrade} style={formRow}>
          {/* Symbol */}
          <div style={fieldGroup}>
            <label style={fieldLabel}>Symbol</label>
            <select
              value={form.symbol}
              onChange={e => setForm(f => ({ ...f, symbol: e.target.value }))}
              style={select}
            >
              {SIDE_SYMBOLS.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>

          {/* Side */}
          <div style={fieldGroup}>
            <label style={fieldLabel}>Side</label>
            <div style={{ display: "flex", gap: 0 }}>
              {["BUY", "SELL"].map(side => (
                <button
                  key={side} type="button"
                  onClick={() => setForm(f => ({ ...f, side }))}
                  style={sideBtn(form.side === side, side === "BUY")}
                >
                  {side}
                </button>
              ))}
            </div>
          </div>

          {/* Qty */}
          <div style={fieldGroup}>
            <label style={fieldLabel}>Quantity</label>
            <input
              type="number" placeholder="100" min="1" step="1"
              value={form.quantity}
              onChange={e => setForm(f => ({ ...f, quantity: e.target.value }))}
              required style={input}
            />
          </div>

          {/* Price */}
          <div style={fieldGroup}>
            <label style={fieldLabel}>Price ($)</label>
            <input
              type="number" placeholder="180.00" min="0.01" step="0.01"
              value={form.price}
              onChange={e => setForm(f => ({ ...f, price: e.target.value }))}
              required style={input}
            />
          </div>

          {/* Notional preview */}
          <div style={fieldGroup}>
            <label style={fieldLabel}>Notional</label>
            <div style={{ fontFamily: "var(--mono)", fontSize: 13, padding: "6px 0", color: "var(--accent)" }}>
              {form.quantity && form.price
                ? `$${(parseFloat(form.quantity) * parseFloat(form.price)).toLocaleString("en-US", { maximumFractionDigits: 2 })}`
                : "—"}
            </div>
          </div>

          <button
            type="submit" disabled={submitting}
            style={submitBtn}
          >
            {submitting ? "..." : "Execute"}
          </button>
        </form>

        {formError && (
          <div style={{ marginTop: 10, fontFamily: "var(--mono)", fontSize: 11, color: "var(--loss)" }}>
            ✗ {formError}
          </div>
        )}
        {formOk && (
          <div style={{ marginTop: 10, fontFamily: "var(--mono)", fontSize: 11, color: "var(--gain)" }}>
            ✓ Trade executed and position updated
          </div>
        )}
      </Card>

      {/* Blotter table */}
      <Card
        title="Trade Blotter"
        accent="var(--accent2)"
        action={
          <div style={{ display: "flex", gap: 8 }}>
            <select
              value={filterSymbol}
              onChange={e => setFilterSymbol(e.target.value)}
              style={{ ...select, padding: "2px 8px", fontSize: 11 }}
            >
              <option value="">All symbols</option>
              {SIDE_SYMBOLS.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
            <select
              value={filterSide}
              onChange={e => setFilterSide(e.target.value)}
              style={{ ...select, padding: "2px 8px", fontSize: 11 }}
            >
              <option value="">Both sides</option>
              <option value="BUY">BUY</option>
              <option value="SELL">SELL</option>
            </select>
          </div>
        }
      >
        {loading ? <Spinner /> : !trades?.length ? <EmptyState message="No trades match filters" /> : (
          <div style={{ overflowX: "auto" }}>
            <table style={table}>
              <thead>
                <tr>
                  {["ID", "Symbol", "Side", "Qty", "Price", "Notional", "Timestamp"].map(h => (
                    <th key={h} style={th}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {trades.map(t => (
                  <tr key={t.id} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ ...td, color: "var(--muted)" }}>#{t.id}</td>
                    <td style={{ ...td, color: "var(--text)", fontWeight: 500 }}>{t.symbol}</td>
                    <td style={td}>
                      <span style={{
                        fontFamily: "var(--mono)", fontSize: 10,
                        padding: "2px 7px", borderRadius: 2, letterSpacing: "0.06em",
                        background: t.side === "BUY" ? "rgba(0,212,170,0.12)" : "rgba(255,77,109,0.12)",
                        color: t.side === "BUY" ? "var(--gain)" : "var(--loss)",
                        border: `1px solid ${t.side === "BUY" ? "rgba(0,212,170,0.3)" : "rgba(255,77,109,0.3)"}`,
                      }}>
                        {t.side}
                      </span>
                    </td>
                    <td style={td}><Num value={t.quantity} decimals={0} /></td>
                    <td style={td}><Num value={t.price} decimals={2} prefix="$" /></td>
                    <td style={td}><Num value={t.notional} decimals={2} prefix="$" /></td>
                    <td style={{ ...td, color: "var(--muted)", fontSize: 11 }}>
                      {new Date(t.timestamp).toLocaleString("en-CA", {
                        month: "short", day: "numeric",
                        hour: "2-digit", minute: "2-digit",
                      })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

const formRow = {
  display: "flex", gap: 16, flexWrap: "wrap", alignItems: "flex-end",
};
const fieldGroup = { display: "flex", flexDirection: "column", gap: 4 };
const fieldLabel = {
  fontFamily: "var(--mono)", fontSize: 10, color: "var(--muted)",
  letterSpacing: "0.08em", textTransform: "uppercase",
};
const select = {
  background: "var(--bg)", border: "1px solid var(--border2)",
  color: "var(--text)", fontFamily: "var(--mono)", fontSize: 12,
  padding: "6px 10px", borderRadius: 2, outline: "none",
};
const input = {
  ...select, width: 100,
};
const sideBtn = (active, isBuy) => ({
  fontFamily: "var(--mono)", fontSize: 11, letterSpacing: "0.06em",
  padding: "6px 14px", border: "1px solid var(--border2)",
  borderRadius: isBuy ? "2px 0 0 2px" : "0 2px 2px 0",
  background: active
    ? (isBuy ? "rgba(0,212,170,0.15)" : "rgba(255,77,109,0.15)")
    : "var(--bg)",
  color: active
    ? (isBuy ? "var(--gain)" : "var(--loss)")
    : "var(--muted)",
  borderColor: active
    ? (isBuy ? "var(--gain)" : "var(--loss)")
    : "var(--border2)",
  cursor: "pointer", transition: "all 0.15s",
});
const submitBtn = {
  fontFamily: "var(--mono)", fontSize: 12, letterSpacing: "0.08em",
  padding: "6px 20px", background: "var(--accent)", color: "var(--bg)",
  border: "none", borderRadius: 2, cursor: "pointer",
  fontWeight: 600, alignSelf: "flex-end",
  opacity: 1, transition: "opacity 0.15s",
};
const table = { width: "100%", borderCollapse: "collapse" };
const th = {
  fontFamily: "var(--mono)", fontSize: 10, color: "var(--muted)",
  textAlign: "left", padding: "6px 10px",
  borderBottom: "1px solid var(--border)", textTransform: "uppercase",
  letterSpacing: "0.08em",
};
const td = {
  fontFamily: "var(--mono)", fontSize: 12, textAlign: "left",
  padding: "9px 10px", color: "var(--muted)",
};
