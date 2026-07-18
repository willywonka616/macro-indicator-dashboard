import React, { useEffect, useState } from "react";
import { c, zColor } from "./theme.js";
import { commentary, footerCaveats } from "./content/commentary.js";
import HeadlineGauge from "./components/HeadlineGauge.jsx";
import Panel from "./components/Panel.jsx";
import GaugeRow from "./components/GaugeRow.jsx";
import Sparkline from "./components/Sparkline.jsx";
import Tag from "./components/Tag.jsx";
import { toneColor } from "./theme.js";

/* Countries planned but not yet wired up. Kept out of data.json because
 * they have no data yet — purely a UI affordance. */
const PLANNED = ["Euro area · ECB", "Japan", "China"];

const dotColor = (tag) => (tag === "live" ? c.calm : tag === "model" ? c.mitig : c.caution);
const commentaryTone = (t) => (t === "alarm" ? c.alarm : t === "calm" ? c.calm : t === "mitig" ? c.mitig : c.text);

function fmtTimestamp(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toISOString().replace("T", " ").slice(0, 16) + " UTC";
}

export default function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [code, setCode] = useState(null);

  useEffect(() => {
    const url = `${import.meta.env.BASE_URL}data.json`;
    fetch(url, { cache: "no-cache" })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status} loading data.json`);
        return r.json();
      })
      .then((json) => {
        setData(json);
        setCode((prev) => prev || Object.keys(json.countries || {})[0] || null);
      })
      .catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <Shell>
        <p style={{ color: c.alarm, fontSize: 14 }}>Couldn't load data.json — {error}</p>
      </Shell>
    );
  }
  if (!data || !code) {
    return (
      <Shell>
        <p style={{ color: c.muted, fontSize: 14 }}>Loading…</p>
      </Shell>
    );
  }

  const d = data.countries[code];
  const cm = commentary[code] || {};
  const codes = Object.keys(data.countries);

  return (
    <Shell>
      <header className="mb-6">
        <div style={{ fontSize: 11, letterSpacing: "0.18em", textTransform: "uppercase", color: c.calm }}>
          Sovereign Debt Vitals
        </div>
        <h1 className="mt-1" style={{ fontSize: 26, fontWeight: 700, letterSpacing: "-0.01em" }}>
          {d.name}
        </h1>
        <p className="mt-1" style={{ fontSize: 12.5, color: c.muted, lineHeight: 1.5, maxWidth: 620 }}>
          Central-government and central-bank debt risk, after Ray Dalio's{" "}
          <span style={{ fontStyle: "italic" }}>How Countries Go Broke</span> (Ch. 17). Baseline snapshot:{" "}
          {d.baseline}. Read it like a medical chart — these gauges flag vulnerability, not timing.
        </p>
        <div className="flex flex-wrap gap-2 mt-4">
          {codes.map((cc) => (
            <button
              key={cc}
              onClick={() => setCode(cc)}
              className="rounded-md px-3 py-1.5"
              style={{
                fontSize: 12,
                fontWeight: 600,
                color: code === cc ? c.bg : c.text,
                background: code === cc ? c.calm : "transparent",
                border: `1px solid ${code === cc ? c.calm : c.line}`,
              }}
            >
              {data.countries[cc].name}
            </button>
          ))}
          {PLANNED.map((p) => (
            <button
              key={p}
              disabled
              className="rounded-md px-3 py-1.5"
              style={{
                fontSize: 12,
                color: c.faint,
                background: "transparent",
                border: `1px dashed ${c.line}`,
                cursor: "not-allowed",
              }}
            >
              {p} · planned
            </button>
          ))}
        </div>
      </header>

      {/* headline gauges */}
      <div className="grid gap-3 mb-3" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))" }}>
        <HeadlineGauge g={d.headline.govLT} />
        <HeadlineGauge g={d.headline.cbLT} />
      </div>
      <div
        className="rounded-lg p-4 mb-3 flex items-center justify-between"
        style={{ background: c.panel2, border: `1px solid ${c.line}` }}
      >
        <div>
          <div style={{ fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase", color: c.muted }}>
            Short-term (imminent) risk
          </div>
          <div style={{ fontSize: 11.5, color: c.muted, marginTop: 2 }}>{d.headline.shortTerm.note}</div>
        </div>
        <span className="font-mono" style={{ fontSize: 18, fontWeight: 700, color: c.calm }}>
          {d.headline.shortTerm.level}
        </span>
      </div>

      {/* commentary */}
      {cm.reads && (
        <div className="rounded-lg p-4 mb-5" style={{ background: c.panel, border: `1px solid ${c.line}` }}>
          <h3
            style={{
              fontSize: 11,
              letterSpacing: "0.12em",
              textTransform: "uppercase",
              color: c.muted,
              fontWeight: 600,
              marginBottom: 8,
            }}
          >
            What Dalio reads here
          </h3>
          {cm.reads.map((para, i) => (
            <p
              key={i}
              style={{ fontSize: 13, lineHeight: 1.6, color: c.text, marginTop: i === 0 ? 0 : 10 }}
            >
              {para.map((seg, j) => (
                <span key={j} style={{ color: commentaryTone(seg.tone) }}>
                  {seg.t}
                </span>
              ))}
            </p>
          ))}
        </div>
      )}

      {/* four vital signs */}
      <div className="mb-5">
        <div className="flex items-center justify-between mb-2">
          <h2 style={{ fontSize: 12, letterSpacing: "0.12em", textTransform: "uppercase", color: c.text, fontWeight: 700 }}>
            Four vital signs
          </h2>
          <span style={{ fontSize: 11, color: c.faint }}>the four Dalio calls most important</span>
        </div>
        <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
          {d.vitals.map((v, i) => (
            <div
              key={v.key || i}
              className="rounded-lg p-3.5 flex flex-col"
              style={{ background: c.panel, border: `1px solid ${c.line}` }}
            >
              <div className="flex items-start justify-between gap-2">
                <span style={{ fontSize: 11.5, color: c.muted, lineHeight: 1.3 }}>{v.label}</span>
                <span style={{ fontSize: 9, color: dotColor(v.tag) }}>{v.tag === "live" ? "●" : "○"}</span>
              </div>
              <div className="mt-1.5 mb-1 flex items-baseline gap-1">
                <span className="font-mono" style={{ fontSize: 22, fontWeight: 600, color: toneColor(v.tone) }}>
                  {v.display ?? v.value}
                </span>
                <span className="font-mono" style={{ fontSize: 10, color: c.faint }}>
                  {v.unit}
                </span>
              </div>
              {v.history && v.history.length > 1 && (
                <div className="mb-2">
                  <Sparkline data={v.history} color={toneColor(v.tone)} />
                </div>
              )}
              <p style={{ fontSize: 11, lineHeight: 1.45, color: c.muted }}>{v.read}</p>
            </div>
          ))}
        </div>
      </div>

      {/* panels */}
      <div className="grid gap-3 mb-3" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))" }}>
        {d.panels.map((p, i) => (
          <Panel key={i} p={p} />
        ))}
      </div>

      {/* gov / cb gauges */}
      <div className="grid gap-3 mb-3" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))" }}>
        {[d.govGauge, d.cbGauge].map((g, i) => (
          <section key={i} className="rounded-lg p-4" style={{ background: c.panel, border: `1px solid ${c.line}` }}>
            <div className="flex items-center justify-between mb-1">
              <h3
                style={{
                  fontSize: 11,
                  letterSpacing: "0.12em",
                  textTransform: "uppercase",
                  color: c.muted,
                  fontWeight: 600,
                }}
              >
                {g.eyebrow}
              </h3>
              <Tag kind="model" />
            </div>
            <div className="flex items-baseline gap-2 mb-3">
              <span className="font-mono" style={{ fontSize: 24, fontWeight: 700, color: zColor(g.overall) }}>
                {g.overall > 0 ? "+" : ""}
                {g.overall.toFixed(1)}z
              </span>
              <span style={{ fontSize: 11, color: c.faint }}>overall</span>
            </div>
            <div>
              {g.rows.map((r, j) => (
                <GaugeRow key={j} r={r} />
              ))}
            </div>
            <p className="mt-3" style={{ fontSize: 11.5, lineHeight: 1.5, color: c.muted }}>
              {g.note}
            </p>
          </section>
        ))}
      </div>

      {/* red flags */}
      <div
        className="rounded-lg p-4 mb-6"
        style={{ background: c.panel, border: `1px solid ${c.alarm}44`, borderLeft: `2px solid ${c.alarm}` }}
      >
        <h3
          style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: c.alarm, fontWeight: 600, marginBottom: 8 }}
        >
          Two red flags to watch
        </h3>
        {cm.redFlagsIntro && (
          <p style={{ fontSize: 12, color: c.muted, marginBottom: 8 }}>{cm.redFlagsIntro}</p>
        )}
        {d.redFlags.map((f, i) => (
          <div key={i} className="flex gap-2 py-1" style={{ fontSize: 13, color: c.text }}>
            <span style={{ color: c.alarm }}>›</span>
            <span>{f}</span>
          </div>
        ))}
      </div>

      <footer style={{ borderTop: `1px solid ${c.line}`, paddingTop: 16 }}>
        <p style={{ fontSize: 11, lineHeight: 1.6, color: c.faint }}>
          <span style={{ color: c.muted }}>Graphs.</span> Sparklines show real historical series at native
          frequency from the source feed; model gauges and short-history shares carry no sparkline.
        </p>
        <p style={{ fontSize: 11, lineHeight: 1.6, color: c.faint, marginTop: 6 }}>
          <span style={{ color: c.muted }}>Updating.</span> Metrics tagged{" "}
          <span style={{ color: c.calm }}>Live data</span> come from public sources (FRED, IMF, BIS) and refresh
          monthly via a GitHub Actions job. Metrics tagged <span style={{ color: c.mitig }}>Dalio model</span> are
          Z-scores from his proprietary historical model and change only when he republishes;{" "}
          <span style={{ color: c.caution }}>Manual</span> figures are hand-updated with a checked date.
        </p>
        <p style={{ fontSize: 11, lineHeight: 1.6, color: c.faint, marginTop: 6 }}>
          <span style={{ color: c.muted }}>Caveats.</span> {footerCaveats}
        </p>
        <p style={{ fontSize: 10.5, color: c.faint, marginTop: 8 }}>
          Source: Ray Dalio, How Countries Go Broke: The Big Cycle, Ch. 17 (snapshot {d.baseline}). Z-score
          convention: up = more vulnerable; +2 and above is "quite bad".
          {data.generatedAt ? ` · Data generated ${fmtTimestamp(data.generatedAt)}` : ""}
        </p>
      </footer>
    </Shell>
  );
}

function Shell({ children }) {
  return (
    <div
      style={{
        background: c.bg,
        color: c.text,
        minHeight: "100vh",
        fontFamily: "system-ui, -apple-system, sans-serif",
      }}
    >
      <div className="mx-auto px-5 py-8" style={{ maxWidth: 960 }}>
        {children}
      </div>
    </div>
  );
}
