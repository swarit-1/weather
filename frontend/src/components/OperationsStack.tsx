"use client";

import { useMemo, useState } from "react";
import { useStore, formatTimestamp, scoreToSeverity } from "@/lib/store";
import {
  RunSnapshot,
  SeverityLevel,
  RiskScores,
  WeatherAlert,
  DetectedEvent,
  RecommendedAction,
  Citation,
  AgentTrace,
} from "@/lib/types";

function PanelHeader({ title, trailing }: { title: string; trailing?: React.ReactNode }) {
  return (
    <div className="panel-header-rail flex items-center justify-between" style={{ padding: "16px 16px", borderBottom: "1px solid var(--color-border-subtle)" }}>
      <span className="type-micro" style={{ color: "var(--color-text-secondary)" }}>{title}</span>
      {trailing}
    </div>
  );
}

function SeverityBadge({ severity }: { severity: SeverityLevel }) {
  return <span className={`badge badge-${severity}`}>{severity}</span>;
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="inset-section" style={{ padding: 16 }}>
      <span className="type-small" style={{ color: "var(--color-text-tertiary)" }}>{message}</span>
    </div>
  );
}

function SkeletonBlock({ lines = 3 }: { lines?: number }) {
  return (
    <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 8 }}>
      {Array.from({ length: lines }, (_, i) => (
        <div key={i} className="skeleton" style={{ height: 16, width: i === lines - 1 ? "64%" : "100%" }} />
      ))}
    </div>
  );
}

function formatDelta(current: number, prev: number | null, suffix = ""): string {
  if (prev === null) return "—";
  const delta = current - prev;
  if (delta === 0) return `0${suffix}`;
  return `${delta > 0 ? "+" : ""}${delta}${suffix}`;
}

function WeatherPanel({ run, previousRun }: { run: RunSnapshot | null; previousRun: RunSnapshot | null }) {
  if (!run) return <SkeletonBlock lines={4} />;
  const w = run.weather;
  const prev = previousRun?.weather ?? null;

  return (
    <div className="panel fade-in">
      <PanelHeader
        title="Live Weather & Alerts"
        trailing={<span className="type-small" style={{ color: "var(--color-text-tertiary)" }}>{w.source} · {formatTimestamp(w.timestamp)}</span>}
      />
      <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 16 }}>
        <div className="grid grid-cols-1 md:grid-cols-3" style={{ gap: 8 }}>
          <MetricTile
            label="Wind Gust"
            value={`${w.windGustMph} mph`}
            delta={formatDelta(w.windGustMph, prev ? prev.windGustMph : null)}
            warn={w.windGustMph > 50}
          />
          <MetricTile
            label="Heat Index"
            value={`${w.heatIndexF}°F`}
            delta={formatDelta(w.heatIndexF, prev ? prev.heatIndexF : null)}
            warn={w.heatIndexF > 105}
          />
          <MetricTile
            label="Precip. Prob."
            value={`${Math.round(w.precipProbability * 100)}%`}
            delta={formatDelta(Math.round(w.precipProbability * 100), prev ? Math.round(prev.precipProbability * 100) : null, "%")}
            warn={w.precipProbability > 0.6}
          />
        </div>
        {w.alerts.length > 0 ? (
          <div className="inset-section" style={{ display: "flex", flexDirection: "column", gap: 8, padding: 8 }}>
            {w.alerts.slice(0, 5).map((a) => (
              <AlertRow key={a.id} alert={a} />
            ))}
          </div>
        ) : (
          <span className="type-small" style={{ color: "var(--color-text-tertiary)" }}>No active alerts.</span>
        )}
      </div>
    </div>
  );
}

function MetricTile({ label, value, delta, warn }: { label: string; value: string; delta: string; warn?: boolean }) {
  return (
    <div className="inset-section" style={{ padding: 8 }}>
      <div className="type-micro" style={{ color: "var(--color-text-tertiary)", marginBottom: 8 }}>{label}</div>
      <div className="type-h2" style={{ color: warn ? "var(--color-risk-high)" : "var(--color-text-primary)" }}>{value}</div>
      <div className="type-small" style={{ color: "var(--color-text-tertiary)", marginTop: 8 }}>since last run {delta}</div>
    </div>
  );
}

function AlertRow({ alert }: { alert: WeatherAlert }) {
  return (
    <div className="flex items-center justify-between" style={{ padding: "8px 0", borderBottom: "1px solid var(--color-border-subtle)" }}>
      <div className="flex items-center" style={{ gap: 8 }}>
        <SeverityBadge severity={alert.severity} />
        <span className="type-small" style={{ color: "var(--color-text-primary)" }}>{alert.title}</span>
      </div>
      <span className="type-small" style={{ color: "var(--color-text-tertiary)" }}>{alert.source}</span>
    </div>
  );
}

function DetectedEventPanel({ event, previousEvent }: { event: DetectedEvent | null; previousEvent: DetectedEvent | null }) {
  return (
    <div className="panel fade-in">
      <PanelHeader title="Detected Event" />
      {event ? (
        <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 16 }}>
          <div className="flex items-center" style={{ gap: 8 }}>
            <SeverityBadge severity={event.severity} />
            <span className="type-h3" style={{ color: "var(--color-text-primary)" }}>{event.type}</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2" style={{ gap: 8 }}>
            <div className="inset-section" style={{ padding: 8 }}>
              <div className="type-micro" style={{ color: "var(--color-text-tertiary)", marginBottom: 8 }}>Confidence</div>
              <div className="type-body" style={{ color: "var(--color-text-primary)", fontWeight: 500 }}>{Math.round(event.triggerConfidence * 100)}%</div>
              <div className="type-small" style={{ color: "var(--color-text-tertiary)", marginTop: 8 }}>
                since last run {formatDelta(Math.round(event.triggerConfidence * 100), previousEvent ? Math.round(previousEvent.triggerConfidence * 100) : null, "%")}
              </div>
            </div>
            <div className="inset-section" style={{ padding: 8 }}>
              <div className="type-micro" style={{ color: "var(--color-text-tertiary)", marginBottom: 8 }}>Window</div>
              <div className="type-small" style={{ color: "var(--color-text-primary)" }}>
                {formatTimestamp(event.startTime)} — {event.endTime ? formatTimestamp(event.endTime) : "Ongoing"}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <EmptyState message="No active event detected. Monitoring live weather signals." />
      )}
    </div>
  );
}

const RISK_LABELS: { key: keyof RiskScores; label: string; policy: number }[] = [
  { key: "loadStress", label: "Load Stress", policy: 55 },
  { key: "outageLikelihood", label: "Outage Likelihood", policy: 55 },
  { key: "restorationDifficulty", label: "Restoration Difficulty", policy: 50 },
  { key: "crewUrgency", label: "Crew Urgency", policy: 60 },
  { key: "publicSafetyRisk", label: "Public Safety Risk", policy: 45 },
];

function RiskScoresPanel({ scores, previousScores, linkedRiskKeys }: { scores: RiskScores | null; previousScores: RiskScores | null; linkedRiskKeys: (keyof RiskScores)[] }) {
  return (
    <div className="panel fade-in">
      <PanelHeader title="Risk Scores" />
      {scores ? (
        <div className="grid grid-cols-2 lg:grid-cols-5" style={{ padding: 16, gap: 8 }}>
          {RISK_LABELS.map(({ key, label, policy }) => {
            const value = scores[key];
            const severity = scoreToSeverity(value);
            const prev = previousScores ? previousScores[key] : null;
            const linked = linkedRiskKeys.includes(key);
            const outOfPolicy = value > policy;

            return (
              <div
                key={key}
                className="inset-section"
                style={{
                  padding: 8,
                  borderRadius: "var(--radius)",
                  border: linked ? "1px solid var(--color-accent)" : "1px solid var(--color-border-subtle)",
                  textAlign: "center",
                }}
              >
                <div className="type-micro" style={{ color: "var(--color-text-tertiary)", marginBottom: 8 }}>{label}</div>
                <div className="type-h1" style={{ color: `var(--color-risk-${severity})`, fontVariantNumeric: "tabular-nums" }}>{value}</div>
                <div className="type-small" style={{ color: "var(--color-text-tertiary)", marginTop: 8 }}>Δ {formatDelta(value, prev)}</div>
                <div className="type-small" style={{ color: "var(--color-text-tertiary)", marginTop: 4 }}>Policy {policy}</div>
                {outOfPolicy && <div className="type-small" style={{ color: "var(--color-risk-medium)", marginTop: 4 }}>Out of policy</div>}
              </div>
            );
          })}
        </div>
      ) : (
        <SkeletonBlock lines={2} />
      )}
    </div>
  );
}

function ActionsPanel({ actions, onSelectAction, activeActionId }: { actions: RecommendedAction[]; onSelectAction: (action: RecommendedAction | null) => void; activeActionId: string | null }) {
  const [openId, setOpenId] = useState<string | null>(null);

  return (
    <div className="panel fade-in">
      <PanelHeader
        title="Recommended Actions"
        trailing={actions.length > 0 ? <span className="type-small" style={{ color: "var(--color-text-tertiary)" }}>{actions.length} actions</span> : null}
      />
      {actions.length > 0 ? (
        <div>
          {actions.map((action, index) => {
            const active = activeActionId === action.id;
            return (
              <div
                key={action.id}
                onClick={() => onSelectAction(active ? null : action)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    onSelectAction(active ? null : action);
                  }
                }}
                style={{
                  padding: 16,
                  borderBottom: index < actions.length - 1 ? "1px solid var(--color-border-subtle)" : "none",
                  background: active ? "var(--color-surface-elevated)" : "transparent",
                  cursor: "pointer",
                }}
              >
                <div className="flex items-start justify-between" style={{ gap: 8 }}>
                  <div style={{ flex: 1 }}>
                    <div className="flex items-center" style={{ gap: 8, marginBottom: 8 }}>
                      <span className="badge badge-info">{index + 1}</span>
                      <span className="type-body" style={{ color: "var(--color-text-primary)", fontWeight: 500 }}>{action.title}</span>
                    </div>
                    <div className="flex flex-wrap items-center type-small" style={{ gap: 8, color: "var(--color-text-secondary)" }}>
                      <span>{action.ownerRole}</span>
                      <span>•</span>
                      <span>{action.timeWindow}</span>
                    </div>
                    <p className="type-small" style={{ color: "var(--color-text-secondary)", marginTop: 8, marginBottom: 0 }}>{action.rationale}</p>
                  </div>
                  <button
                    className="btn btn-ghost btn-icon"
                    onClick={(e) => {
                      e.stopPropagation();
                      setOpenId(openId === action.id ? null : action.id);
                    }}
                    aria-expanded={openId === action.id}
                    aria-label="Show evidence"
                    title="Show evidence"
                  >
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 16 16"
                      fill="none"
                      style={{ transform: openId === action.id ? "rotate(180deg)" : "rotate(0deg)", transition: "transform var(--transition-fast)" }}
                    >
                      <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </button>
                </div>
                {openId === action.id && (
                  <div className="fade-in inset-section" style={{ marginTop: 8, padding: "8px 16px" }}>
                    <div className="type-micro" style={{ color: "var(--color-text-tertiary)", marginBottom: 8 }}>Evidence</div>
                    <p className="type-small" style={{ color: "var(--color-text-secondary)", margin: 0 }}>{action.evidence}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <EmptyState message="No actions recommended for current conditions." />
      )}
    </div>
  );
}

function CitationsPanel({ citations, activeCitationIds }: { citations: Citation[]; activeCitationIds: string[] }) {
  return (
    <div className="panel fade-in">
      <PanelHeader title="Evidence & Citations" />
      {citations.length > 0 ? (
        <div>
          {citations.map((citation, index) => {
            const linked = activeCitationIds.includes(citation.id);
            return (
              <div
                key={citation.id}
                className="flex items-center justify-between"
                style={{
                  padding: "16px 16px",
                  borderBottom: index < citations.length - 1 ? "1px solid var(--color-border-subtle)" : "none",
                  background: linked ? "var(--color-surface-elevated)" : "transparent",
                }}
              >
                <div>
                  <div className="type-small" style={{ color: "var(--color-text-primary)", fontWeight: 500 }}>{citation.title}</div>
                  <div className="type-small" style={{ color: "var(--color-text-tertiary)" }}>{citation.source}</div>
                </div>
                <a href={citation.url} target="_blank" rel="noopener noreferrer" className="btn btn-ghost" aria-label={`Open ${citation.title}`} title="Open source">
                  Open
                </a>
              </div>
            );
          })}
        </div>
      ) : (
        <EmptyState message="No citations available." />
      )}
    </div>
  );
}

function TracePanel({ traces, activeTraceAgents }: { traces: AgentTrace[]; activeTraceAgents: string[] }) {
  const [open, setOpen] = useState(false);

  const statusColor: Record<string, string> = {
    complete: "var(--color-risk-low)",
    running: "var(--color-accent)",
    error: "var(--color-risk-critical)",
  };

  return (
    <div className="panel fade-in">
      <div
        className="panel-header-rail flex items-center justify-between"
        style={{ padding: "16px 16px", cursor: "pointer" }}
        onClick={() => setOpen(!open)}
        role="button"
        tabIndex={0}
        aria-expanded={open}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setOpen(!open);
          }
        }}
      >
        <span className="type-micro" style={{ color: "var(--color-text-secondary)" }}>Trace · Agent Audit Trail</span>
        <div className="flex items-center" style={{ gap: 8 }}>
          <span className="type-small" style={{ color: "var(--color-text-tertiary)" }}>{traces.length} agents</span>
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            style={{ transform: open ? "rotate(180deg)" : "rotate(0deg)", transition: "transform var(--transition-fast)", color: "var(--color-text-tertiary)" }}
          >
            <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </div>
      {open && (
        <div style={{ borderTop: "1px solid var(--color-border-subtle)" }}>
          {traces.map((trace, index) => {
            const linked = activeTraceAgents.includes(trace.agentName);
            return (
              <div
                key={index}
                className="flex items-start"
                style={{
                  padding: "16px 16px",
                  gap: 8,
                  borderBottom: index < traces.length - 1 ? "1px solid var(--color-border-subtle)" : "none",
                  background: linked ? "var(--color-surface-elevated)" : "transparent",
                }}
              >
                <span className="status-dot" style={{ background: statusColor[trace.status] ?? "var(--color-text-tertiary)" }} />
                <div>
                  <div className="type-small" style={{ color: "var(--color-text-primary)", fontWeight: 500 }}>{trace.agentName}</div>
                  <div className="type-small" style={{ color: "var(--color-text-secondary)" }}>{trace.summary}</div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function MonitoringReasoning({ run, previousRun }: { run: RunSnapshot | null; previousRun: RunSnapshot | null }) {
  if (!run || run.detectedEvent) return null;

  const confidence = previousRun?.detectedEvent?.triggerConfidence ?? 0.61;
  return (
    <div className="panel fade-in">
      <PanelHeader title="Trigger Reasoning" />
      <div className="inset-section" style={{ padding: 16 }}>
        <div className="type-small" style={{ color: "var(--color-text-primary)" }}>No active event detected.</div>
        <div className="type-small" style={{ color: "var(--color-text-secondary)", marginTop: 8 }}>
          Closest candidate: Heat event — confidence {confidence.toFixed(2)} &lt; 0.70 threshold.
        </div>
        <div className="type-small" style={{ color: "var(--color-text-secondary)", marginTop: 8 }}>
          Would trigger if: Heat index &gt; 110°F for 30m.
        </div>
      </div>
    </div>
  );
}

export default function OperationsStack() {
  const { state, getRegionRun, getPreviousRegionRun } = useStore();
  const run = getRegionRun();
  const previousRun = getPreviousRegionRun();
  const isBooting = state.status === "booting";
  const [activeActionId, setActiveActionId] = useState<string | null>(null);

  if (isBooting) {
    return (
      <div className="flex flex-col overflow-y-auto w-full lg:w-[448px] shrink-0" style={{ padding: 16, gap: 16, background: "var(--color-bg)" }}>
        {Array.from({ length: 4 }, (_, i) => (
          <div key={i} className="panel">
            <div style={{ padding: "16px 16px", borderBottom: "1px solid var(--color-border-subtle)" }}>
              <div className="skeleton" style={{ height: 16, width: 160 }} />
            </div>
            <SkeletonBlock lines={3} />
          </div>
        ))}
      </div>
    );
  }

  const selectedRegion = state.selectedRegionId;
  const noDataForRegion = selectedRegion && !run;
  const selectedAction = run?.actions.find((a) => a.id === activeActionId) ?? null;
  const linkedRiskKeys = selectedAction?.riskKeys ?? [];
  const linkedCitations = selectedAction?.citationIds ?? [];
  const linkedTraces = selectedAction?.traceAgents ?? [];

  return (
    <div className="flex flex-col overflow-y-auto w-full lg:w-[448px] shrink-0" style={{ padding: 16, gap: 16, background: "var(--color-bg)" }}>
      {selectedRegion && (
        <div className="type-small" style={{ color: "var(--color-text-tertiary)" }}>
          Region: <span style={{ color: "var(--color-text-primary)", fontWeight: 500 }}>{state.currentRun?.regions.find((r) => r.id === selectedRegion)?.name ?? selectedRegion}</span>
        </div>
      )}

      {noDataForRegion ? (
        <div className="panel">
          <EmptyState message="No run data available for this region." />
        </div>
      ) : (
        <>
          <WeatherPanel run={run} previousRun={previousRun} />
          <DetectedEventPanel event={run?.detectedEvent ?? null} previousEvent={previousRun?.detectedEvent ?? null} />
          <RiskScoresPanel scores={run?.riskScores ?? null} previousScores={previousRun?.riskScores ?? null} linkedRiskKeys={linkedRiskKeys} />
          <MonitoringReasoning run={run} previousRun={previousRun} />
          <ActionsPanel actions={run?.actions ?? []} onSelectAction={(action) => setActiveActionId(action?.id ?? null)} activeActionId={activeActionId} />
          <CitationsPanel citations={run?.citations ?? []} activeCitationIds={linkedCitations} />
          <TracePanel traces={run?.traces ?? []} activeTraceAgents={linkedTraces} />
        </>
      )}
    </div>
  );
}
