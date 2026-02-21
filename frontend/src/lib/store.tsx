"use client";

import { createContext, useContext, useReducer, useCallback, useEffect, useRef, ReactNode } from "react";
import { AppState, AppStatus, RunSnapshot } from "./types";
import { MOCK_RUNS } from "@/data/mock";

export function getTopRiskScore(r: RunSnapshot["riskScores"]): number {
  return Math.max(r.loadStress, r.outageLikelihood, r.restorationDifficulty, r.crewUrgency, r.publicSafetyRisk);
}

export function scoreToSeverity(score: number): "critical" | "high" | "medium" | "low" | "info" {
  if (score >= 80) return "critical";
  if (score >= 60) return "high";
  if (score >= 40) return "medium";
  if (score >= 20) return "low";
  return "info";
}

export function formatTimestamp(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  } catch {
    return iso;
  }
}

type Action =
  | { type: "SET_STATUS"; status: AppStatus }
  | { type: "SET_RUN"; run: RunSnapshot }
  | { type: "SELECT_REGION"; regionId: string | null }
  | { type: "TOGGLE_PAUSE" }
  | { type: "ENTER_REPLAY"; run: RunSnapshot }
  | { type: "EXIT_REPLAY" }
  | { type: "RETRY_CONNECTION_START" }
  | { type: "RETRY_CONNECTION_COMPLETE" }
  | { type: "BOOT_COMPLETE" };

const initialState: AppState = {
  status: "booting",
  isPaused: false,
  isReplay: false,
  retryingConnection: false,
  selectedRegionId: null,
  currentRun: null,
  runHistory: [],
  lastUpdated: null,
};

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case "SET_STATUS":
      return { ...state, status: action.status };

    case "SET_RUN": {
      const history = [action.run, ...state.runHistory].slice(0, 50);
      let status: AppStatus;
      if (action.run.status === "error") status = "offline";
      else if (action.run.status === "degraded") status = "degraded";
      else status = action.run.detectedEvent ? "triggered" : "monitoring";

      return {
        ...state,
        currentRun: action.run,
        runHistory: history,
        lastUpdated: new Date().toISOString(),
        status: state.isReplay ? state.status : status,
        retryingConnection: false,
      };
    }

    case "SELECT_REGION":
      return { ...state, selectedRegionId: action.regionId };

    case "TOGGLE_PAUSE":
      return { ...state, isPaused: !state.isPaused };

    case "ENTER_REPLAY":
      return { ...state, isReplay: true, currentRun: action.run, retryingConnection: false };

    case "EXIT_REPLAY": {
      const latest = state.runHistory[0] ?? null;
      const status: AppStatus = latest?.detectedEvent ? "triggered" : "monitoring";
      return { ...state, isReplay: false, currentRun: latest, status, retryingConnection: false };
    }

    case "RETRY_CONNECTION_START":
      return { ...state, retryingConnection: true };

    case "RETRY_CONNECTION_COMPLETE": {
      if (!state.currentRun) {
        return { ...state, status: "monitoring", lastUpdated: new Date().toISOString(), retryingConnection: false };
      }
      const status: AppStatus = state.currentRun.detectedEvent ? "triggered" : "monitoring";
      return { ...state, status, lastUpdated: new Date().toISOString(), retryingConnection: false };
    }

    case "BOOT_COMPLETE": {
      const run = MOCK_RUNS[0];
      const history = [...MOCK_RUNS].slice(0, 50);
      return {
        ...state,
        status: run.detectedEvent ? "triggered" : "monitoring",
        currentRun: run,
        runHistory: history,
        selectedRegionId: run.regionId,
        lastUpdated: new Date().toISOString(),
      };
    }

    default:
      return state;
  }
}

interface StoreContext {
  state: AppState;
  dispatch: React.Dispatch<Action>;
  selectRegion: (id: string | null) => void;
  togglePause: () => void;
  enterReplay: (run: RunSnapshot) => void;
  exitReplay: () => void;
  retryConnection: () => void;
  getRegionRun: () => RunSnapshot | null;
  getPreviousRegionRun: () => RunSnapshot | null;
}

const Ctx = createContext<StoreContext | null>(null);

export function StoreProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const runIndexRef = useRef(0);

  useEffect(() => {
    const timer = setTimeout(() => dispatch({ type: "BOOT_COMPLETE" }), 1800);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (state.status === "booting" || state.isPaused || state.isReplay) return;
    const interval = setInterval(() => {
      runIndexRef.current = (runIndexRef.current + 1) % MOCK_RUNS.length;
      const run = { ...MOCK_RUNS[runIndexRef.current], id: `run-live-${Date.now()}`, timestamp: new Date().toISOString() };
      dispatch({ type: "SET_RUN", run });
    }, 15000);
    return () => clearInterval(interval);
  }, [state.status, state.isPaused, state.isReplay]);

  const selectRegion = useCallback((id: string | null) => dispatch({ type: "SELECT_REGION", regionId: id }), []);
  const togglePause = useCallback(() => dispatch({ type: "TOGGLE_PAUSE" }), []);
  const enterReplay = useCallback((run: RunSnapshot) => dispatch({ type: "ENTER_REPLAY", run }), []);
  const exitReplay = useCallback(() => dispatch({ type: "EXIT_REPLAY" }), []);

  const retryConnection = useCallback(() => {
    dispatch({ type: "RETRY_CONNECTION_START" });
    setTimeout(() => dispatch({ type: "RETRY_CONNECTION_COMPLETE" }), 1200);
  }, []);

  const getRegionRun = useCallback((): RunSnapshot | null => {
    if (!state.currentRun) return null;
    if (!state.selectedRegionId) return state.currentRun;
    if (state.currentRun.regionId === state.selectedRegionId) return state.currentRun;
    const found = state.runHistory.find((r) => r.regionId === state.selectedRegionId);
    return found ?? null;
  }, [state.currentRun, state.selectedRegionId, state.runHistory]);

  const getPreviousRegionRun = useCallback((): RunSnapshot | null => {
    const targetRegion = state.selectedRegionId ?? state.currentRun?.regionId;
    if (!targetRegion) return null;
    const current = getRegionRun();
    if (!current) return null;
    const currentIndex = state.runHistory.findIndex((r) => r.id === current.id);
    if (currentIndex < 0) return null;
    for (let i = currentIndex + 1; i < state.runHistory.length; i += 1) {
      const candidate = state.runHistory[i];
      if (candidate.regionId === targetRegion) return candidate;
    }
    return null;
  }, [state.selectedRegionId, state.currentRun, state.runHistory, getRegionRun]);

  return (
    <Ctx.Provider
      value={{ state, dispatch, selectRegion, togglePause, enterReplay, exitReplay, retryConnection, getRegionRun, getPreviousRegionRun }}
    >
      {children}
    </Ctx.Provider>
  );
}

export function useStore(): StoreContext {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useStore must be used within StoreProvider");
  return ctx;
}
