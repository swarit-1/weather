"use client";

import { useState } from "react";
import { useStore, formatTimestamp, getTopRiskScore, scoreToSeverity } from "@/lib/store";
import { RunSnapshot } from "@/lib/types";

export default function RunStream() {
  const { state, enterReplay } = useStore();
  const [collapsed, setCollapsed] = useState(false);

  if (state.status === "booting") return null;

  const runs = state.runHistory;

  return (
    <div
      style={{
        borderTop: "1px solid var(--color-border)",
        background: "var(--color-surface)",
        flexShrink: 0,
      }}
    >
      <div
        className="flex items-center justify-between"
        style={{
          padding: "8px 24px",
          cursor: "pointer",
        }}
        onClick={() => setCollapsed(!collapsed)}
        role="button"
        tabIndex={0}
        aria-expanded={!collapsed}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setCollapsed(!collapsed);
          }
        }}
      >
        <div className="flex items-center" style={{ gap: 8 }}>
          <span className="type-micro" style={{ color: "var(--color-text-secondary)" }}>
            Audit Timeline
          </span>
          <span className="type-small" style={{ color: "var(--color-text-tertiary)" }}>
            {runs.length} runs
          </span>
        </div>
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          style={{
            transform: collapsed ? "rotate(0deg)" : "rotate(180deg)",
            transition: "transform var(--transition-fast)",
            color: "var(--color-text-tertiary)",
          }}
        >
          <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>

      {!collapsed && (
        <div className="flex overflow-x-auto" style={{ padding: "0 24px 16px 24px", gap: 8 }}>
          {runs.map((run) => (
            <TimelineRow
              key={run.id}
              run={run}
              isActive={state.isReplay && state.currentRun?.id === run.id}
              onClick={() => enterReplay(run)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function TimelineRow({ run, isActive, onClick }: { run: RunSnapshot; isActive: boolean; onClick: () => void }) {
  const topScore = getTopRiskScore(run.riskScores);
  const severity = scoreToSeverity(topScore);

  return (
    <button
      onClick={onClick}
      className="panel"
      style={{
        minWidth: 280,
        padding: 8,
        background: isActive ? "var(--color-surface-elevated)" : "var(--color-surface)",
        border: isActive ? "1px solid var(--color-accent)" : "1px solid var(--color-border)",
        textAlign: "left",
        display: "grid",
        gridTemplateColumns: "120px minmax(0,1fr) auto auto",
        gap: 8,
        alignItems: "center",
        flexShrink: 0,
      }}
      aria-label={`Run ${run.id} at ${formatTimestamp(run.timestamp)}`}
    >
      <span className="type-small" style={{ color: "var(--color-text-primary)", fontWeight: 500 }}>
        {formatTimestamp(run.timestamp)}
      </span>
      <span className="type-small" style={{ color: "var(--color-text-secondary)" }}>
        {run.detectedEvent?.type ?? "No event"}
      </span>
      <span className={`badge badge-${severity}`}>{topScore}</span>
      <div className="flex items-center" style={{ gap: 8 }}>
        <span className={`badge ${run.status === "error" ? "badge-critical" : run.status === "degraded" ? "badge-medium" : "badge-low"}`}>
          {run.status}
        </span>
        {isActive && <span className="badge badge-info">Replay Lock</span>}
      </div>
    </button>
  );
}
