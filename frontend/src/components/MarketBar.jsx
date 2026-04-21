import { useEffect, useRef } from "react";
import { useData } from "../useData.js";
import { api } from "../api.js";
import { Num } from "./ui.jsx";

export default function MarketBar() {
  const { data } = useData(api.getAllMarketData);
  const trackRef = useRef(null);

  // Animate the ticker by translating the track leftward in a loop
  useEffect(() => {
    const el = trackRef.current;
    if (!el || !data?.length) return;

    let frame;
    let pos = 0;
    const speed = 0.4; // px per frame
    const halfWidth = el.scrollWidth / 2; // data is doubled so half = one full set

    const tick = () => {
      pos += speed;
      if (pos >= halfWidth) pos = 0;
      el.style.transform = `translateX(-${pos}px)`;
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [data]);

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
      <div style={outer}>
        {/* Mask fades at both edges */}
        <div style={mask} />
        <div ref={trackRef} style={track}>
          {/* Doubled so the scroll loops seamlessly */}
          {[...data, ...data].map((d, i) => (
            <span key={i} style={item}>
              <span style={sym}>{d.symbol}</span>
              <Num value={d.price} decimals={2} prefix="$" />
              <Num value={d.change_pct} decimals={2} suffix="%" colored />
              <span style={{ color: "var(--border2)" }}>|</span>
            </span>
          ))}
        </div>
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
  height: 36,
};
const label = {
  fontFamily: "var(--mono)", fontSize: 10,
  letterSpacing: "0.15em", color: "var(--gain)",
  animation: "pulse 2s ease-in-out infinite",
  flexShrink: 0,
};
const outer = { flex: 1, overflow: "hidden", position: "relative" };
const mask = {
  position: "absolute", inset: 0, zIndex: 1, pointerEvents: "none",
  background: "linear-gradient(to right, var(--surface) 0%, transparent 6%, transparent 94%, var(--surface) 100%)",
};
const track = {
  display: "flex", gap: 28, willChange: "transform",
  whiteSpace: "nowrap",
};
const item = {
  display: "inline-flex", gap: 8, alignItems: "center",
  flexShrink: 0, fontFamily: "var(--mono)", fontSize: 12,
};
const sym = { color: "var(--muted)", fontSize: 11, letterSpacing: "0.06em" };
