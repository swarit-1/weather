/* ── Core domain types for AI Grid Operations Copilot ── */

export type AppStatus = "booting" | "monitoring" | "triggered" | "degraded" | "offline";

export type SeverityLevel = "critical" | "high" | "medium" | "low" | "info";

export interface Region {
  id: string;
  name: string;
  lat: number;
  lng: number;
  riskLevel: SeverityLevel;
}

export interface WeatherAlert {
  id: string;
  title: string;
  severity: SeverityLevel;
  source: string;
  issuedAt: string;
}

export interface WeatherData {
  windGustMph: number;
  heatIndexF: number;
  precipProbability: number;
  alerts: WeatherAlert[];
  source: string;
  timestamp: string;
}

export interface DetectedEvent {
  type: string;
  severity: SeverityLevel;
  triggerConfidence: number;
  startTime: string;
  endTime: string | null;
}

export interface RiskScores {
  loadStress: number;
  outageLikelihood: number;
  restorationDifficulty: number;
  crewUrgency: number;
  publicSafetyRisk: number;
}

export interface RecommendedAction {
  id: string;
  title: string;
  ownerRole: string;
  timeWindow: string;
  rationale: string;
  evidence: string;
  riskKeys: (keyof RiskScores)[];
  citationIds: string[];
  traceAgents: string[];
}

export interface Citation {
  id: string;
  title: string;
  source: string;
  url: string;
}

export interface AgentTrace {
  agentName: string;
  status: "complete" | "running" | "error";
  summary: string;
}

export interface RunSnapshot {
  id: string;
  timestamp: string;
  regionId: string;
  status: "success" | "degraded" | "error";
  weather: WeatherData;
  detectedEvent: DetectedEvent | null;
  riskScores: RiskScores;
  actions: RecommendedAction[];
  citations: Citation[];
  traces: AgentTrace[];
  regions: Region[];
}

export interface AppState {
  status: AppStatus;
  isPaused: boolean;
  isReplay: boolean;
  retryingConnection: boolean;
  selectedRegionId: string | null;
  currentRun: RunSnapshot | null;
  runHistory: RunSnapshot[];
  lastUpdated: string | null;
}
