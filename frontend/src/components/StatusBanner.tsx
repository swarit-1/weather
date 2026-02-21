"use client";

import { useStore, formatTimestamp } from "@/lib/store";

export default function StatusBanner() {
  const { state, retryConnection } = useStore();
  const retryingConnection = state.retryingConnection;

  if (state.status === "degraded") {
    const ts = state.lastUpdated ? formatTimestamp(state.lastUpdated) : "unknown";
    return (
      <div
        className="flex flex-col md:flex-row md:items-center"
        style={{
          padding: "8px 24px",
          gap: 8,
          background: "rgba(210,153,34,0.1)",
          borderBottom: "1px solid rgba(210,153,34,0.3)",
        }}
      >
        <div className="flex items-center" style={{ gap: 8 }}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path d="M8 2L2 14h12L8 2z" stroke="var(--color-risk-medium)" strokeWidth="1.5" strokeLinejoin="round" />
            <path d="M8 6v3M8 11v1" stroke="var(--color-risk-medium)" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <span className="type-small" style={{ color: "var(--color-risk-medium)" }}>
            Data delayed. Showing last known snapshot from {ts}.
          </span>
        </div>
      </div>
    );
  }

  if (state.status === "offline") {
    return (
      <div
        className="flex flex-col md:flex-row md:items-center md:justify-between"
        style={{
          padding: "8px 24px",
          gap: 8,
          background: "rgba(248,81,73,0.08)",
          borderBottom: "1px solid rgba(248,81,73,0.2)",
        }}
      >
        <div className="flex items-center" style={{ gap: 8 }}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <circle cx="8" cy="8" r="6.5" stroke="var(--color-risk-critical)" strokeWidth="1.5" />
            <path d="M6 6l4 4M10 6l-4 4" stroke="var(--color-risk-critical)" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <span className="type-small" style={{ color: "var(--color-risk-critical)" }}>
            Connection lost. Showing last known snapshot.
          </span>
        </div>
        <button
          className="btn btn-secondary"
          onClick={retryConnection}
          disabled={retryingConnection}
          aria-busy={retryingConnection}
        >
          {retryingConnection ? (
            <>
              <span className="loading-spinner" aria-hidden="true" />
              Retrying
            </>
          ) : (
            "Retry connection"
          )}
        </button>
      </div>
    );
  }

  return null;
}
