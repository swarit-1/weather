"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const AUSTIN_CENTER = { lat: 30.2672, lng: -97.7431 };
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const MAP_SCRIPT_URL = "https://maps.googleapis.com/maps/api/js";

export type AnalyzeResponse = {
  weather_snapshot: {
    temperature: number | null;
    wind_speed: number | null;
    wind_gust: number | null;
    precipitation_probability: number | null;
    heat_index: number | null;
    alerts: Array<{ event?: string; severity?: string; headline?: string }>;
    forecast_summary: string | null;
    timestamp: string;
    zip_code: string | null;
  };
  derived_scenario: {
    event_type: string;
    severity_level: string;
    trigger_reason: string;
    confidence_score: number;
  };
  risk_scores: {
    load_stress: number;
    outage_likelihood: number;
    restoration_difficulty: number;
    crew_urgency: number;
    public_safety_risk: number;
  };
};

function riskColor(score: number): string {
  if (score >= 80) return "risk-red";
  if (score >= 60) return "risk-orange";
  if (score >= 30) return "risk-yellow";
  return "risk-green";
}

function riskFillColor(score: number): string {
  if (score >= 80) return "rgba(239, 68, 68, 0.35)";
  if (score >= 60) return "rgba(249, 115, 22, 0.35)";
  if (score >= 30) return "rgba(234, 179, 8, 0.35)";
  return "rgba(34, 197, 94, 0.35)";
}

export default function StormOpsMap() {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<google.maps.Map | null>(null);
  const layersRef = useRef<google.maps.Data | null>(null);
  const [scriptLoaded, setScriptLoaded] = useState(false);
  const [data, setData] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedZip, setSelectedZip] = useState<string | null>(null);
  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

  const loadScript = useCallback(() => {
    if (!apiKey || typeof window === "undefined") return;
    if ((window as unknown as { __gmLoaded?: boolean }).__gmLoaded) {
      setScriptLoaded(true);
      return;
    }
    const existing = document.querySelector(`script[src^="${MAP_SCRIPT_URL}"]`);
    if (existing) {
      setScriptLoaded(true);
      return;
    }
    const script = document.createElement("script");
    script.src = `${MAP_SCRIPT_URL}?key=${apiKey}`;
    script.async = true;
    script.defer = true;
    script.onload = () => {
      (window as unknown as { __gmLoaded?: boolean }).__gmLoaded = true;
      setScriptLoaded(true);
    };
    document.head.appendChild(script);
  }, [apiKey]);

  useEffect(() => {
    loadScript();
  }, [loadScript]);

  const fetchGeoJson = useCallback(() => {
    return fetch("/austin-zips.geojson").then((r) => r.json());
  }, []);

  const initMap = useCallback(() => {
    if (!containerRef.current || !scriptLoaded || mapRef.current) return;
    const map = new google.maps.Map(containerRef.current, {
      center: AUSTIN_CENTER,
      zoom: 11,
      mapTypeId: "roadmap",
      styles: [
        { featureType: "poi", stylers: [{ visibility: "off" }] },
        { featureType: "transit", stylers: [{ visibility: "off" }] },
      ],
    });
    mapRef.current = map;

    const dataLayer = new google.maps.Data();
    dataLayer.setStyle((feature) => {
      const zip = feature.getProperty("zip") as string | undefined;
      const fill = selectedZip === zip && data?.risk_scores
        ? riskFillColor(
            Math.max(
              data.risk_scores.load_stress,
              data.risk_scores.outage_likelihood,
              data.risk_scores.public_safety_risk
            )
          )
        : "rgba(59, 130, 246, 0.2)";
      return {
        fillColor: fill,
        strokeColor: "#3b82f6",
        strokeWeight: 2,
        clickable: true,
      };
    });
    dataLayer.addListener("click", (e: google.maps.Data.MouseEvent) => {
      const zip = (e.feature.getProperty("zip") as string) || "";
      if (!zip) return;
      setSelectedZip(zip);
      setError(null);
      setLoading(true);
      fetch(`${API_URL}/api/analyze?zip=${encodeURIComponent(zip)}`)
        .then((res) => {
          if (!res.ok) throw new Error(res.statusText || "Analysis failed");
          return res.json();
        })
        .then((json: AnalyzeResponse) => {
          setData(json);
          dataLayer.revertStyle();
          dataLayer.setStyle((feature) => {
            const z = feature.getProperty("zip") as string | undefined;
            const fill = selectedZip === z && json?.risk_scores
              ? riskFillColor(
                  Math.max(
                    json.risk_scores.load_stress,
                    json.risk_scores.outage_likelihood,
                    json.risk_scores.public_safety_risk
                  )
                )
              : "rgba(59, 130, 246, 0.2)";
            return {
              fillColor: fill,
              strokeColor: "#3b82f6",
              strokeWeight: 2,
              clickable: true,
            };
          });
        })
        .catch((err) => setError(err.message || "Request failed"))
        .finally(() => setLoading(false));
    });

    fetchGeoJson().then((geojson) => {
      dataLayer.addGeoJson(geojson);
      dataLayer.setMap(map);
      layersRef.current = dataLayer;
    });
  }, [scriptLoaded, selectedZip, data, fetchGeoJson]);

  useEffect(() => {
    initMap();
  }, [initMap]);

  if (!apiKey) {
    return (
      <div className="map-container" ref={containerRef}>
        <div className="risk-panel">
          <p className="error">Set NEXT_PUBLIC_GOOGLE_MAPS_API_KEY in .env.local</p>
        </div>
      </div>
    );
  }

  return (
    <div className="map-container">
      <div ref={containerRef} style={{ width: "100%", height: "100%" }} />
      <div className="risk-panel">
        <h2>StormOps Risk</h2>
        {loading && <p className="loading">Loading analysis…</p>}
        {error && <p className="error">{error}</p>}
        {!data && !loading && !error && (
          <p className="zip-placeholder">Click a ZIP on the map to analyze.</p>
        )}
        {data && !loading && (
          <>
            <section>
              <div className="label">ZIP</div>
              <div className="value">{data.weather_snapshot.zip_code ?? selectedZip ?? "—"}</div>
            </section>
            <section>
              <div className="label">Detected event</div>
              <div className="value">
                <span className={`event-badge ${data.derived_scenario.event_type}`}>
                  {data.derived_scenario.event_type}
                </span>
                {" — "}
                {data.derived_scenario.trigger_reason}
              </div>
            </section>
            <section>
              <div className="label">Current wind</div>
              <div className="value">
                {data.weather_snapshot.wind_speed != null
                  ? `${data.weather_snapshot.wind_speed} mph`
                  : "—"}
                {data.weather_snapshot.wind_gust != null &&
                  data.weather_snapshot.wind_gust !== data.weather_snapshot.wind_speed && (
                    <> (gust {data.weather_snapshot.wind_gust} mph)</>
                  )}
              </div>
            </section>
            <section>
              <div className="label">Risk scores (0–100)</div>
              {[
                { name: "Load stress", v: data.risk_scores.load_stress },
                { name: "Outage likelihood", v: data.risk_scores.outage_likelihood },
                { name: "Restoration difficulty", v: data.risk_scores.restoration_difficulty },
                { name: "Crew urgency", v: data.risk_scores.crew_urgency },
                { name: "Public safety", v: data.risk_scores.public_safety_risk },
              ].map(({ name, v }) => (
                <div key={name} className="risk-bar">
                  <span className="name">{name}</span>
                  <div className="bar-wrap">
                    <div
                      className={`bar ${riskColor(v)}`}
                      style={{ width: `${Math.min(100, v)}%` }}
                    />
                  </div>
                  <span className="num">{v.toFixed(0)}</span>
                </div>
              ))}
            </section>
            <section>
              <div className="label">Active alerts</div>
              {data.weather_snapshot.alerts?.length ? (
                <ul className="alerts-list">
                  {data.weather_snapshot.alerts.map((a, i) => (
                    <li key={i}>
                      <div className="alert-headline">{a.headline ?? a.event ?? "Alert"}</div>
                      {a.event && <div className="alert-event">{a.event}</div>}
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="value">None</div>
              )}
            </section>
            {data.weather_snapshot.forecast_summary && (
              <section>
                <div className="label">Forecast</div>
                <div className="value" style={{ fontSize: "0.875rem" }}>
                  {data.weather_snapshot.forecast_summary}
                </div>
              </section>
            )}
          </>
        )}
      </div>
    </div>
  );
}
