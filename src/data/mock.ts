import { Region, RunSnapshot, WeatherData, DetectedEvent, RiskScores, RecommendedAction, Citation, AgentTrace, WeatherAlert } from "@/lib/types";

/* ── Regions ── */
export const REGIONS: Region[] = [
  { id: "us-south", name: "US South (Texas Grid)", lat: 31.0, lng: -97.0, riskLevel: "high" },
  { id: "us-northeast", name: "US Northeast", lat: 42.0, lng: -73.0, riskLevel: "medium" },
  { id: "eu-west", name: "Western Europe", lat: 48.5, lng: 2.5, riskLevel: "low" },
  { id: "south-asia", name: "South Asia", lat: 22.0, lng: 78.0, riskLevel: "medium" },
  { id: "east-africa", name: "East Africa", lat: -1.0, lng: 37.0, riskLevel: "low" },
  { id: "au-east", name: "Eastern Australia", lat: -33.5, lng: 151.0, riskLevel: "info" },
  { id: "jp-kanto", name: "Japan Kanto", lat: 35.7, lng: 139.7, riskLevel: "low" },
  { id: "br-south", name: "Brazil South", lat: -23.5, lng: -46.6, riskLevel: "info" },
];

/* ── Weather ── */
const alertsTexas: WeatherAlert[] = [
  { id: "a1", title: "Extreme Heat Warning", severity: "critical", source: "NWS", issuedAt: "2026-02-21T08:00:00Z" },
  { id: "a2", title: "Wind Advisory", severity: "high", source: "NWS", issuedAt: "2026-02-21T07:30:00Z" },
  { id: "a3", title: "Flash Flood Watch", severity: "medium", source: "NWS", issuedAt: "2026-02-21T06:00:00Z" },
];

const weatherTexas: WeatherData = {
  windGustMph: 58,
  heatIndexF: 112,
  precipProbability: 0.72,
  alerts: alertsTexas,
  source: "NOAA / NWS",
  timestamp: "2026-02-21T08:15:00Z",
};

const weatherCalm: WeatherData = {
  windGustMph: 12,
  heatIndexF: 78,
  precipProbability: 0.15,
  alerts: [],
  source: "NOAA / NWS",
  timestamp: "2026-02-21T08:15:00Z",
};

/* ── Detected event ── */
const eventTexas: DetectedEvent = {
  type: "Compound Heat-Wind Storm",
  severity: "critical",
  triggerConfidence: 0.94,
  startTime: "2026-02-21T06:00:00Z",
  endTime: "2026-02-21T18:00:00Z",
};

/* ── Risk scores ── */
const riskTexas: RiskScores = {
  loadStress: 89,
  outageLikelihood: 76,
  restorationDifficulty: 64,
  crewUrgency: 82,
  publicSafetyRisk: 71,
};

const riskCalm: RiskScores = {
  loadStress: 22,
  outageLikelihood: 8,
  restorationDifficulty: 12,
  crewUrgency: 5,
  publicSafetyRisk: 3,
};

/* ── Actions ── */
const actionsTexas: RecommendedAction[] = [
    {
      id: "act1",
      title: "Pre-stage mobile generation units at substations S-04 and S-11",
      ownerRole: "Field Operations Lead",
      timeWindow: "Within 2 hours",
      rationale: "Substations S-04 and S-11 are within the projected wind corridor and serve critical load centers including two hospitals.",
      evidence: "NWS wind advisory + ERCOT load forecast Q3 2026 Section 4.2",
      riskKeys: ["outageLikelihood", "publicSafetyRisk"],
      citationIds: ["c1", "c2"],
      traceAgents: ["Event Classification Agent", "Playbook Generation Agent"],
    },
  {
    id: "act2",
    title: "Activate demand-response contracts for industrial customers in Zone 3",
    ownerRole: "Grid Dispatch Manager",
    timeWindow: "Within 1 hour",
    rationale: "Reducing peak load by 400MW in Zone 3 will maintain reserve margin above 6% during the heat index peak.",
    evidence: "ERCOT demand-response protocol DR-7 + real-time load telemetry",
    riskKeys: ["loadStress", "crewUrgency"],
    citationIds: ["c1"],
    traceAgents: ["Risk Scoring Agent", "Playbook Generation Agent"],
  },
  {
    id: "act3",
    title: "Issue public conservation appeal for residential areas",
    ownerRole: "Communications Lead",
    timeWindow: "Within 30 minutes",
    rationale: "Historical data shows a 3-5% demand reduction when conservation appeals are issued 4+ hours before peak.",
    evidence: "PUCT conservation effectiveness report 2025, Table 3",
    riskKeys: ["loadStress", "publicSafetyRisk"],
    citationIds: ["c3"],
    traceAgents: ["Risk Scoring Agent", "Playbook Generation Agent"],
  },
  {
    id: "act4",
    title: "Deploy additional line crews to sectors with vegetation encroachment risk",
    ownerRole: "Vegetation Management Supervisor",
    timeWindow: "Within 3 hours",
    rationale: "Wind gusts above 55 mph combined with recent rainfall increase tree-related outage probability by 340%.",
    evidence: "Internal vegetation risk model v2.3 + satellite imagery analysis",
    riskKeys: ["outageLikelihood", "restorationDifficulty", "crewUrgency"],
    citationIds: ["c4"],
    traceAgents: ["Weather Ingest Agent", "Risk Scoring Agent"],
  },
];

/* ── Citations ── */
const citationsTexas: Citation[] = [
  { id: "c1", title: "ERCOT Seasonal Assessment of Resource Adequacy", source: "ERCOT", url: "https://www.ercot.com/gridmktinfo/dashboards" },
  { id: "c2", title: "NWS Extreme Heat Warning - South Texas", source: "National Weather Service", url: "https://www.weather.gov/ewx/" },
  { id: "c3", title: "PUCT Conservation Effectiveness Analysis 2025", source: "Public Utility Commission of Texas", url: "https://www.puc.texas.gov/" },
    { id: "c4", title: "Vegetation Management and Reliability Guidance", source: "U.S. Department of Energy", url: "https://www.energy.gov/oe/activities/technology-development/grid-modernization-and-smart-grid" },
];

/* ── Traces ── */
const tracesTexas: AgentTrace[] = [
  { agentName: "Weather Ingest Agent", status: "complete", summary: "Fetched 14 data sources; 3 alerts flagged above threshold." },
  { agentName: "Event Classification Agent", status: "complete", summary: "Classified compound heat-wind event with 94% confidence." },
  { agentName: "Risk Scoring Agent", status: "complete", summary: "Computed 5 risk dimensions using ensemble model v4.1." },
  { agentName: "Playbook Generation Agent", status: "complete", summary: "Generated 4 recommended actions with evidence links." },
  { agentName: "Citation Verification Agent", status: "complete", summary: "Verified 4/4 citations; all sources accessible." },
];

/* ── Run snapshots ── */
function makeTimestamp(hoursAgo: number): string {
  const d = new Date("2026-02-21T08:15:00Z");
  d.setHours(d.getHours() - hoursAgo);
  return d.toISOString();
}

export const MOCK_RUNS: RunSnapshot[] = [
  {
    id: "run-001",
    timestamp: makeTimestamp(0),
    regionId: "us-south",
    status: "success",
    weather: weatherTexas,
    detectedEvent: eventTexas,
    riskScores: riskTexas,
    actions: actionsTexas,
    citations: citationsTexas,
    traces: tracesTexas,
    regions: REGIONS,
  },
  {
    id: "run-002",
    timestamp: makeTimestamp(1),
    regionId: "us-south",
    status: "success",
    weather: { ...weatherTexas, windGustMph: 52, timestamp: makeTimestamp(1) },
    detectedEvent: { ...eventTexas, triggerConfidence: 0.87 },
    riskScores: { ...riskTexas, loadStress: 82, outageLikelihood: 68 },
    actions: actionsTexas.slice(0, 3),
    citations: citationsTexas.slice(0, 3),
    traces: tracesTexas,
    regions: REGIONS,
  },
  {
    id: "run-003",
    timestamp: makeTimestamp(2),
    regionId: "us-northeast",
    status: "success",
    weather: weatherCalm,
    detectedEvent: null,
    riskScores: riskCalm,
    actions: [],
    citations: [],
    traces: [
      { agentName: "Weather Ingest Agent", status: "complete", summary: "Fetched 14 data sources; no alerts above threshold." },
      { agentName: "Event Classification Agent", status: "complete", summary: "No significant weather event detected." },
    ],
    regions: REGIONS,
  },
  {
    id: "run-004",
    timestamp: makeTimestamp(3),
    regionId: "us-south",
    status: "degraded",
    weather: { ...weatherTexas, windGustMph: 45, heatIndexF: 105, timestamp: makeTimestamp(3) },
    detectedEvent: { ...eventTexas, severity: "high", triggerConfidence: 0.72 },
    riskScores: { ...riskTexas, loadStress: 68, outageLikelihood: 52, crewUrgency: 61, publicSafetyRisk: 48 },
    actions: actionsTexas.slice(0, 2),
    citations: citationsTexas.slice(0, 2),
    traces: [
      ...tracesTexas.slice(0, 3),
      { agentName: "Playbook Generation Agent", status: "complete", summary: "Generated 2 actions; limited confidence due to partial data." },
      { agentName: "Citation Verification Agent", status: "error", summary: "1/2 citations could not be verified; source timeout." },
    ],
    regions: REGIONS,
  },
  {
      id: "run-005",
      timestamp: makeTimestamp(5),
      regionId: "eu-west",
      status: "success",
      weather: { ...weatherCalm, windGustMph: 18, heatIndexF: 65, precipProbability: 0.42, timestamp: makeTimestamp(5) },
      detectedEvent: null,
      riskScores: { loadStress: 15, outageLikelihood: 6, restorationDifficulty: 8, crewUrgency: 3, publicSafetyRisk: 2 },
      actions: [],
      citations: [],
      traces: [
        { agentName: "Weather Ingest Agent", status: "complete", summary: "Fetched 11 data sources; normal conditions." },
        { agentName: "Event Classification Agent", status: "complete", summary: "No event detected." },
      ],
      regions: REGIONS,
    },
    {
      id: "run-006",
      timestamp: makeTimestamp(7),
      regionId: "jp-kanto",
      status: "error",
      weather: { ...weatherCalm, windGustMph: 0, heatIndexF: 0, precipProbability: 0, timestamp: makeTimestamp(7) },
      detectedEvent: null,
      riskScores: { loadStress: 0, outageLikelihood: 0, restorationDifficulty: 0, crewUrgency: 0, publicSafetyRisk: 0 },
      actions: [],
      citations: [],
      traces: [
        { agentName: "Weather Ingest Agent", status: "error", summary: "Upstream data source timeout. Last known values retained." },
      ],
      regions: REGIONS,
    },
];
