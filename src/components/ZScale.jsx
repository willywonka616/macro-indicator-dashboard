import React, { useEffect, useState } from "react";
import { c, pct, zColor, THRESH } from "../theme.js";

/* The signature element: the Z-score vitals scale.
 * Carried over unchanged from the legacy dashboard. */
export default function ZScale({ z, animate = true, height = 8 }) {
  const [p, setP] = useState(animate ? pct(0) : pct(z));
  useEffect(() => {
    const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (!animate || reduce) {
      setP(pct(z));
      return;
    }
    const t = setTimeout(() => setP(pct(z)), 60);
    return () => clearTimeout(t);
  }, [z, animate]);
  return (
    <div className="w-full">
      <div
        className="relative w-full rounded-full"
        style={{
          height,
          background: `linear-gradient(90deg, ${c.calm} 0%, ${c.panel2} 46%, ${c.caution} 74%, ${c.alarm} 100%)`,
          opacity: 0.5,
        }}
      >
        <div
          className="absolute top-0 bottom-0"
          style={{ left: `${pct(THRESH)}%`, width: 1, background: c.alarm, opacity: 0.7 }}
        />
        <div
          className="absolute"
          style={{
            left: `${p}%`,
            top: "50%",
            transform: "translate(-50%,-50%)",
            transition: "left 900ms cubic-bezier(.22,1,.36,1)",
          }}
        >
          <div
            style={{
              width: height + 6,
              height: height + 6,
              borderRadius: "50%",
              background: zColor(z),
              boxShadow: `0 0 0 3px ${c.bg}, 0 0 12px ${zColor(z)}66`,
            }}
          />
        </div>
      </div>
      <div className="flex justify-between mt-1" style={{ fontSize: 9, color: c.faint }}>
        <span>−3</span>
        <span>0</span>
        <span style={{ color: c.alarm }}>+2</span>
        <span>+3</span>
      </div>
    </div>
  );
}
