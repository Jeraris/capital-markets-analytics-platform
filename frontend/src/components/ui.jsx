const s = {
  card: {
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: 4,
    padding: "20px 24px",
  },
  cardTitle: {
    fontFamily: "var(--mono)",
    fontSize: 11,
    letterSpacing: "0.12em",
    color: "var(--muted)",
    textTransform: "uppercase",
    marginBottom: 16,
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  dot: (color) => ({
    width: 6, height: 6, borderRadius: "50%",
    background: color, flexShrink: 0,
  }),
};

export function Card({ title, accent = "var(--accent)", children, style, action }) {
  return (
    <div style={{ ...s.card, ...style }} className="fade-up">
      {title && (
        <div style={s.cardTitle}>
          <span style={s.dot(accent)} />
          {title}
          {action && <span style={{ marginLeft: "auto" }}>{action}</span>}
        </div>
      )}
      {children}
    </div>
  );
}

export function Badge({ children, color = "var(--accent)" }) {
  return (
    <span style={{
      fontFamily: "var(--mono)", fontSize: 11,
      padding: "2px 8px", borderRadius: 2,
      border: `1px solid ${color}`, color,
      letterSpacing: "0.06em",
    }}>
      {children}
    </span>
  );
}

export function Spinner() {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: 48, color: "var(--muted)" }}>
      <div style={{
        width: 20, height: 20, borderRadius: "50%",
        border: "2px solid var(--border2)",
        borderTopColor: "var(--accent)",
        animation: "spin 0.7s linear infinite",
      }} />
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
    </div>
  );
}

export function ErrorState({ message }) {
  return (
    <div style={{
      padding: 24, textAlign: "center",
      color: "var(--loss)", fontFamily: "var(--mono)", fontSize: 11,
      border: "1px solid rgba(255,77,109,0.2)", borderRadius: 3,
      background: "rgba(255,77,109,0.05)",
    }}>
      ✗ {message ?? "Failed to load data — is the backend running?"}
    </div>
  );
}

export function EmptyState({ message = "No data available" }) {
  return (
    <div style={{ padding: 40, textAlign: "center", color: "var(--muted)", fontFamily: "var(--mono)", fontSize: 12 }}>
      {message}
    </div>
  );
}

export function Num({ value, decimals = 2, prefix = "", suffix = "", colored = false }) {
  const n = typeof value === "number" ? value : parseFloat(value);
  if (isNaN(n)) return <span style={{ color: "var(--muted)" }}>—</span>;
  const formatted = `${prefix}${Math.abs(n).toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}${suffix}`;
  const color = !colored ? "inherit"
    : n > 0 ? "var(--gain)"
    : n < 0 ? "var(--loss)"
    : "var(--muted)";
  const sign = colored && n > 0 ? "+" : colored && n < 0 ? "−" : "";
  return <span style={{ fontFamily: "var(--mono)", color }}>{sign}{formatted}</span>;
}
