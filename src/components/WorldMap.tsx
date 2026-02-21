"use client";

import { useStore, scoreToSeverity, getTopRiskScore } from "@/lib/store";
import { Region, SeverityLevel } from "@/lib/types";
import { REGIONS } from "@/data/mock";

const RISK_COLORS: Record<SeverityLevel, string> = {
  critical: "var(--color-risk-critical)",
  high: "var(--color-risk-high)",
  medium: "var(--color-risk-medium)",
  low: "var(--color-risk-low)",
  info: "var(--color-text-tertiary)",
};

const RISK_SWATCHES: { key: SeverityLevel; label: string }[] = [
  { key: "critical", label: "Critical" },
  { key: "high", label: "High" },
  { key: "medium", label: "Medium" },
  { key: "low", label: "Low" },
  { key: "info", label: "Info" },
];

function project(lat: number, lng: number): { x: number; y: number } {
  const x = ((lng + 180) / 360) * 1000;
  const y = ((90 - lat) / 180) * 500;
  return { x, y };
}

const CONTINENT_PATHS = [
  "M120,80 L140,72 L180,64 L220,64 L260,72 L280,88 L288,120 L280,152 L264,176 L240,192 L216,208 L184,224 L160,232 L144,216 L136,192 L128,168 L120,144 L112,120 L104,96 Z",
  "M208,232 L232,240 L248,256 L256,288 L264,320 L256,352 L248,384 L232,400 L216,408 L200,400 L192,384 L184,352 L176,320 L184,288 L192,256 Z",
  "M440,64 L464,56 L488,56 L512,64 L528,72 L528,96 L512,112 L488,120 L464,120 L448,104 L440,88 Z",
  "M440,144 L464,136 L488,144 L512,160 L528,184 L536,216 L528,248 L520,280 L504,312 L488,328 L464,336 L448,320 L432,296 L424,264 L424,232 L432,200 Z",
  "M536,56 L576,48 L624,40 L672,40 L720,48 L760,64 L784,88 L792,112 L784,136 L760,160 L728,168 L688,168 L648,160 L608,144 L576,128 L552,112 L536,88 Z",
  "M624,160 L648,168 L664,184 L672,208 L664,232 L648,240 L624,232 L608,216 L600,192 Z",
  "M736,280 L768,272 L800,280 L824,296 L832,320 L824,344 L808,360 L784,360 L752,352 L736,336 L728,312 Z",
  "M792,96 L800,88 L808,96 L816,112 L808,120 L800,128 L792,120 L784,112 Z",
];

function MarkerDot({ region, isSelected, onClick }: { region: Region; isSelected: boolean; onClick: () => void }) {
  const { x, y } = project(region.lat, region.lng);
  const color = RISK_COLORS[region.riskLevel];

  return (
    <g
      onClick={onClick}
      style={{ cursor: "pointer" }}
      role="button"
      tabIndex={0}
      aria-label={`${region.name} - Risk level: ${region.riskLevel}`}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick();
        }
      }}
    >
      {isSelected && <circle cx={x} cy={y} r={12} fill="none" stroke="var(--color-accent)" strokeWidth="1.5" />}
      <circle cx={x} cy={y} r={6} fill={color} stroke="var(--color-bg)" strokeWidth="1.5" />
      <text x={x + 10} y={y - 8} className="type-micro" fill="var(--color-text-tertiary)">
        {region.name.split(" ")[0]}
      </text>
    </g>
  );
}

export default function WorldMap() {
  const { state, selectRegion } = useStore();
  const regions = state.currentRun?.regions ?? REGIONS;
  const isBooting = state.status === "booting";

  const enrichedRegions: Region[] = regions.map((r) => {
    if (!state.currentRun) return r;
    const runForRegion = state.runHistory.find((run) => run.regionId === r.id);
    if (!runForRegion) return r;
    return { ...r, riskLevel: scoreToSeverity(getTopRiskScore(runForRegion.riskScores)) };
  });

  return (
    <div
      className="relative min-h-[320px] flex-1 overflow-hidden"
      style={{
        background: "var(--color-bg)",
        borderRight: "1px solid var(--color-border)",
      }}
    >
      {isBooting && (
        <div className="absolute inset-0 flex items-center justify-center" style={{ zIndex: 10, background: "var(--color-bg)" }}>
          <div className="flex flex-col items-center" style={{ gap: 16 }}>
            <div className="skeleton" style={{ width: 48, height: 48, borderRadius: 8 }} />
            <span className="type-small" style={{ color: "var(--color-text-tertiary)" }}>
              Connecting to grid telemetry...
            </span>
          </div>
        </div>
      )}

      <svg
        viewBox="0 0 1000 500"
        className="h-full w-full"
        preserveAspectRatio="xMidYMid meet"
        style={{ opacity: isBooting ? 0.24 : 1, transition: "opacity var(--transition-normal)" }}
      >
        {Array.from({ length: 9 }, (_, i) => (
          <line
            key={`vg-${i}`}
            x1={i * (1000 / 8)}
            y1={0}
            x2={i * (1000 / 8)}
            y2={500}
            stroke="var(--color-border-subtle)"
            strokeOpacity="0.4"
            strokeWidth="0.5"
          />
        ))}
        {Array.from({ length: 5 }, (_, i) => (
          <line
            key={`hg-${i}`}
            x1={0}
            y1={i * (500 / 4)}
            x2={1000}
            y2={i * (500 / 4)}
            stroke="var(--color-border-subtle)"
            strokeOpacity="0.4"
            strokeWidth="0.5"
          />
        ))}

        {CONTINENT_PATHS.map((d, i) => (
          <path key={`cont-${i}`} d={d} fill="var(--color-surface)" stroke="var(--color-border)" strokeWidth="1" />
        ))}

        {enrichedRegions.map((r) => (
          <MarkerDot
            key={r.id}
            region={r}
            isSelected={state.selectedRegionId === r.id}
            onClick={() => selectRegion(state.selectedRegionId === r.id ? null : r.id)}
          />
        ))}
      </svg>

      <div
        className="absolute panel"
        style={{
          bottom: 16,
          left: 16,
          padding: 8,
          width: 240,
          background: "var(--color-surface-elevated)",
        }}
      >
        <div className="type-micro" style={{ color: "var(--color-text-secondary)", marginBottom: 8 }}>
          Risk posture
        </div>
        <div className="grid grid-cols-2" style={{ gap: 8 }}>
          {RISK_SWATCHES.map((item) => (
            <div key={item.key} className="flex items-center" style={{ gap: 8 }}>
              <span className="status-dot" style={{ background: RISK_COLORS[item.key] }} />
              <span className="type-small" style={{ color: "var(--color-text-secondary)" }}>
                {item.label}
              </span>
            </div>
          ))}
        </div>
        <div className="type-small" style={{ color: "var(--color-text-tertiary)", marginTop: 8 }}>
          Selection overrides map context
        </div>
      </div>
    </div>
  );
}
