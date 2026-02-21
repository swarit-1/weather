"use client";

import { useMemo, useState, useEffect } from "react";
import { useStore, formatTimestamp } from "@/lib/store";
import { AppStatus, RunSnapshot } from "@/lib/types";

const STATUS_CONFIG: Record<AppStatus, { label: string; dotClass: string }> = {
  booting: { label: "Connecting", dotClass: "status-dot status-dot-degraded" },
  monitoring: { label: "Monitoring", dotClass: "status-dot status-dot-live" },
  triggered: { label: "Triggered", dotClass: "status-dot status-dot-triggered" },
  degraded: { label: "Degraded", dotClass: "status-dot status-dot-degraded" },
  offline: { label: "Offline", dotClass: "status-dot status-dot-offline" },
};

const socialLinks = [
  { label: "NWS", href: "https://www.weather.gov/" },
  { label: "ERCOT", href: "https://www.ercot.com/" },
  { label: "DOE", href: "https://www.energy.gov/" },
];

function getRunQuality(run: RunSnapshot | null): { score: number; label: "Good" | "Degraded" | "Poor"; missingFeeds: number; stalenessMin: number; completeness: number } {
  if (!run) {
    return { score: 0, label: "Poor", missingFeeds: 3, stalenessMin: 999, completeness: 0 };
  }

  const missingFeeds = run.traces.filter((t) => t.status === "error").length;
  const stalenessMin = Math.max(0, Math.round((Date.now() - new Date(run.weather.timestamp).getTime()) / 60000));
  const completeness = Math.min(100, (run.citations.length >= 2 ? 50 : 25) + (run.actions.length >= 2 ? 50 : 25));

  let score = 100;
  score -= missingFeeds * 18;
  score -= stalenessMin > 30 ? 18 : stalenessMin > 15 ? 10 : 0;
  score -= run.status === "degraded" ? 10 : run.status === "error" ? 28 : 0;
  score -= Math.max(0, 100 - completeness) / 5;
  score = Math.max(0, Math.min(100, Math.round(score)));

  const label: "Good" | "Degraded" | "Poor" = score >= 85 ? "Good" : score >= 65 ? "Degraded" : "Poor";
  return { score, label, missingFeeds, stalenessMin, completeness };
}

export default function TopBar() {
  const { state, togglePause, exitReplay } = useStore();
  const cfg = STATUS_CONFIG[state.status];
  const [showQuality, setShowQuality] = useState(false);
  const [uiTime, setUiTime] = useState(() => new Date().toISOString());

  useEffect(() => {
    const timer = setInterval(() => setUiTime(new Date().toISOString()), 1000);
    return () => clearInterval(timer);
  }, []);

  const quality = useMemo(() => getRunQuality(state.currentRun), [state.currentRun]);

  return (
    <header
      className="flex flex-col border-b shrink-0"
      style={{
        minHeight: 56,
        padding: "8px 24px",
        background: "var(--color-surface)",
        borderColor: "var(--color-border)",
        gap: 8,
      }}
    >
      <div className="flex flex-col xl:flex-row xl:items-center xl:justify-between" style={{ gap: 8 }}>
        <div className="flex flex-col md:flex-row md:items-center" style={{ gap: 8 }}>
          <div className="flex items-center" style={{ gap: 8 }}>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <rect x="1" y="1" width="18" height="18" rx="8" stroke="var(--color-accent)" strokeWidth="1.5" />
              <path d="M6 10h8M10 6v8" stroke="var(--color-accent)" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            <span className="type-h3" style={{ color: "var(--color-text-primary)" }}>
              AI Grid Operations Copilot
            </span>
          </div>
          <div
            style={{
              height: 32,
              padding: "0 16px",
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              borderRadius: "var(--radius)",
              border: "1px solid var(--color-border)",
              background: "var(--color-surface-elevated)",
            }}
            aria-label="Utility account"
          >
            <span className="type-small" style={{ color: "var(--color-text-secondary)" }}>
              Gulf Coast Transmission Authority
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center xl:justify-end" style={{ gap: 8 }}>
          {socialLinks.map((link) => (
            <a
              key={link.label}
              href={link.href}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-ghost"
              aria-label={`Open ${link.label} website`}
              title={`Open ${link.label}`}
            >
              {link.label}
            </a>
          ))}

          {state.isReplay ? (
            <button className="btn btn-primary" onClick={exitReplay} aria-label="Resume live monitoring">
              Resume Live
            </button>
          ) : (
            <button
              className="btn btn-secondary"
              onClick={togglePause}
              aria-label={state.isPaused ? "Resume monitoring" : "Pause monitoring"}
            >
              {state.isPaused ? "Resume" : "Pause"}
            </button>
          )}
        </div>
      </div>

      <div
        className="panel"
        style={{
          padding: 8,
          background: "var(--color-surface-elevated)",
          borderColor: "var(--color-border-subtle)",
        }}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4" style={{ gap: 8 }}>
          <div className="inset-section">
            <div className="type-micro" style={{ color: "var(--color-text-tertiary)" }}>State</div>
            <div className="flex items-center" style={{ gap: 8, marginTop: 4 }}>
              <span className={cfg.dotClass} />
              <span className="type-small" style={{ color: "var(--color-text-primary)", fontWeight: 500 }}>{cfg.label}</span>
              {state.isReplay && <span className="badge badge-info">Replay</span>}
            </div>
          </div>

          <div className="inset-section">
            <div className="type-micro" style={{ color: "var(--color-text-tertiary)" }}>Data Timestamp</div>
            <div className="type-small" style={{ color: "var(--color-text-primary)", marginTop: 4 }}>
              {state.currentRun ? formatTimestamp(state.currentRun.timestamp) : "No snapshot"}
            </div>
          </div>

          <div className="inset-section">
            <div className="type-micro" style={{ color: "var(--color-text-tertiary)" }}>UI Timestamp</div>
            <div className="type-small" style={{ color: "var(--color-text-primary)", marginTop: 4 }}>{formatTimestamp(uiTime)}</div>
          </div>

          <div className="inset-section">
            <div className="type-micro" style={{ color: "var(--color-text-tertiary)" }}>Run Quality</div>
            <button
              className="btn btn-ghost"
              onClick={() => setShowQuality((v) => !v)}
              aria-expanded={showQuality}
              aria-label="Toggle run quality details"
              title="Toggle run quality details"
              style={{
                height: 24,
                marginTop: 4,
                padding: 0,
                justifyContent: "flex-start",
                color: "var(--color-text-primary)",
              }}
            >
              {quality.score}/100 · {quality.label}
            </button>
          </div>
        </div>

        {showQuality && (
          <div className="fade-in" style={{ marginTop: 8, paddingTop: 8, borderTop: "1px solid var(--color-border-subtle)" }}>
            <div className="grid grid-cols-1 md:grid-cols-3" style={{ gap: 8 }}>
              <div className="inset-section">
                <div className="type-micro" style={{ color: "var(--color-text-tertiary)" }}>Missing feeds</div>
                <div className="type-small" style={{ color: "var(--color-text-primary)", marginTop: 4 }}>{quality.missingFeeds}</div>
              </div>
              <div className="inset-section">
                <div className="type-micro" style={{ color: "var(--color-text-tertiary)" }}>Staleness</div>
                <div className="type-small" style={{ color: "var(--color-text-primary)", marginTop: 4 }}>{quality.stalenessMin} min</div>
              </div>
              <div className="inset-section">
                <div className="type-micro" style={{ color: "var(--color-text-tertiary)" }}>Completeness</div>
                <div className="type-small" style={{ color: "var(--color-text-primary)", marginTop: 4 }}>{quality.completeness}%</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
