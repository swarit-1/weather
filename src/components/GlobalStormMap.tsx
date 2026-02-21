"use client";

import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { GoogleMap, Marker, Polygon, useJsApiLoader } from "@react-google-maps/api";

export interface LatLng {
  lat: number;
  lng: number;
}

export interface Overlay {
  type: "polygon";
  coordinates: LatLng[];
  risk_level: number;
  label: string;
}

export interface Pin {
  lat: number;
  lng: number;
  type: "crew" | "risk" | "alert";
  label: string;
}

export interface WeatherSnapshotView {
  wind_speed?: number | null;
  alerts?: Array<{ event?: string; headline?: string }>;
}

export interface DerivedScenarioView {
  event_type?: string;
  severity_level?: string;
}

export interface RiskScoresView {
  load_stress?: number;
  outage_likelihood?: number;
  restoration_difficulty?: number;
  crew_urgency?: number;
  public_safety_risk?: number;
}

export interface RunRecord {
  zip?: string;
  weather_snapshot?: WeatherSnapshotView;
  derived_scenario?: DerivedScenarioView;
  risk_scores?: RiskScoresView;
  playbook?: unknown;
  map_widgets?: {
    overlays?: Overlay[];
    pins?: Pin[];
  };
}

const DEFAULT_CENTER: LatLng = { lat: 20, lng: 0 };
const DEFAULT_ZOOM = 2;

const MAP_CONTAINER_STYLE = {
  width: "100%",
  height: "100vh",
} as const;

const MAP_OPTIONS: google.maps.MapOptions = {
  zoomControl: true,
  mapTypeControl: false,
  streetViewControl: false,
  fullscreenControl: true,
  clickableIcons: false,
};

const GOOGLE_MAPS_LIBRARIES: ("places" | "geometry")[] = [];

const MARKER_ICON_URL: Record<Pin["type"], string> = {
  crew: "https://maps.google.com/mapfiles/ms/icons/blue-dot.png",
  risk: "https://maps.google.com/mapfiles/ms/icons/red-dot.png",
  alert: "https://maps.google.com/mapfiles/ms/icons/orange-dot.png",
};

export function getRiskColor(risk: number): string {
  if (risk >= 80) return "#ef4444";
  if (risk >= 60) return "#f97316";
  if (risk >= 30) return "#eab308";
  return "#22c55e";
}

function darkenHexColor(hex: string, factor = 0.7): string {
  const clean = hex.replace("#", "");
  if (clean.length !== 6) return hex;
  const channel = (start: number) => Math.max(0, Math.min(255, Math.floor(parseInt(clean.slice(start, start + 2), 16) * factor)));
  const r = channel(0).toString(16).padStart(2, "0");
  const g = channel(2).toString(16).padStart(2, "0");
  const b = channel(4).toString(16).padStart(2, "0");
  return `#${r}${g}${b}`;
}

function formatScore(value: number | undefined): string {
  if (value === undefined) return "—";
  return `${Math.round(value)}`;
}

function hasMeaningfulBounds(overlays: Overlay[]): boolean {
  let pointCount = 0;
  for (const overlay of overlays) {
    pointCount += overlay.coordinates.length;
  }
  return pointCount >= 3;
}

function markerKey(pin: Pin, index: number): string {
  return `${pin.type}-${pin.lat}-${pin.lng}-${pin.label}-${index}`;
}

function polygonKey(overlay: Overlay, index: number): string {
  const first = overlay.coordinates[0];
  return `${overlay.label}-${overlay.risk_level}-${first?.lat ?? "x"}-${first?.lng ?? "y"}-${index}`;
}

const MemoMarker = memo(function MemoMarker({ pin }: { pin: Pin }) {
  const icon = useMemo<google.maps.Icon | undefined>(() => {
    if (typeof window === "undefined" || !window.google?.maps) return undefined;
    return {
      url: MARKER_ICON_URL[pin.type],
      scaledSize: new window.google.maps.Size(30, 30),
    };
  }, [pin.type]);

  return <Marker position={{ lat: pin.lat, lng: pin.lng }} title={pin.label} icon={icon} />;
});

const MemoPolygon = memo(function MemoPolygon({
  overlay,
  faded,
}: {
  overlay: Overlay;
  faded: boolean;
}) {
  const fillColor = getRiskColor(overlay.risk_level);
  const strokeColor = darkenHexColor(fillColor);
  return (
    <Polygon
      path={overlay.coordinates}
      options={{
        fillColor,
        fillOpacity: faded ? 0.14 : 0.4,
        strokeColor,
        strokeWeight: 2,
        clickable: true,
      }}
    />
  );
});

export default function GlobalStormMap() {
  const [zip, setZip] = useState("78701");
  const [runRecord, setRunRecord] = useState<RunRecord | null>(null);
  const [polygons, setPolygons] = useState<Overlay[]>([]);
  const [markers, setMarkers] = useState<Pin[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fadeTransition, setFadeTransition] = useState(false);

  const mapRef = useRef<google.maps.Map | null>(null);
  const fadeTimerRef = useRef<number | null>(null);

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const googleMapsApiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY ?? "";

  const { isLoaded, loadError } = useJsApiLoader({
    id: "stormops-global-map-script",
    googleMapsApiKey,
    libraries: GOOGLE_MAPS_LIBRARIES,
  });

  const updateMapWidgets = useCallback((nextRunRecord: RunRecord | null) => {
    if (fadeTimerRef.current !== null) {
      window.clearTimeout(fadeTimerRef.current);
    }
    setFadeTransition(true);

    fadeTimerRef.current = window.setTimeout(() => {
      setPolygons(nextRunRecord?.map_widgets?.overlays ?? []);
      setMarkers(nextRunRecord?.map_widgets?.pins ?? []);
      setFadeTransition(false);
    }, 180);
  }, []);

  useEffect(() => {
    updateMapWidgets(runRecord);
  }, [runRecord, updateMapWidgets]);

  useEffect(() => {
    return () => {
      if (fadeTimerRef.current !== null) {
        window.clearTimeout(fadeTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!mapRef.current || !isLoaded || !hasMeaningfulBounds(polygons)) return;

    const bounds = new window.google.maps.LatLngBounds();
    for (const overlay of polygons) {
      for (const point of overlay.coordinates) {
        bounds.extend(point);
      }
    }
    mapRef.current.fitBounds(bounds, 60);
  }, [isLoaded, polygons]);

  const onMapLoad = useCallback((map: google.maps.Map) => {
    mapRef.current = map;
  }, []);

  const onMapUnmount = useCallback(() => {
    mapRef.current = null;
  }, []);

  const runAnalysis = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/api/analyze?zip=${encodeURIComponent(zip.trim())}`);
      if (!response.ok) {
        throw new Error(`Analyze request failed: ${response.status}`);
      }
      const payload = (await response.json()) as RunRecord;
      setRunRecord(payload);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to analyze live conditions.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl, zip]);

  const activeAlerts = runRecord?.weather_snapshot?.alerts ?? [];

  if (loadError) {
    return (
      <div className="global-map-shell">
        <div className="global-map-error">Unable to load Google Maps script.</div>
      </div>
    );
  }

  if (!googleMapsApiKey) {
    return (
      <div className="global-map-shell">
        <div className="global-map-error">Set NEXT_PUBLIC_GOOGLE_MAPS_API_KEY to render the operational map.</div>
      </div>
    );
  }

  return (
    <section className="global-map-shell">
      {isLoaded ? (
        <GoogleMap
          mapContainerStyle={MAP_CONTAINER_STYLE}
          center={DEFAULT_CENTER}
          zoom={DEFAULT_ZOOM}
          options={MAP_OPTIONS}
          onLoad={onMapLoad}
          onUnmount={onMapUnmount}
        >
          {polygons.map((overlay, index) => (
            <MemoPolygon key={polygonKey(overlay, index)} overlay={overlay} faded={fadeTransition} />
          ))}
          {markers.map((pin, index) => (
            <MemoMarker key={markerKey(pin, index)} pin={pin} />
          ))}
        </GoogleMap>
      ) : (
        <div className="global-map-loading">Loading global map…</div>
      )}

      <div className="global-map-panel global-map-panel-left">
        <h3 className="global-map-panel-title">Live Weather Intelligence</h3>
        <div className="global-map-meta-row">
          <span className="global-map-label">Event</span>
          <span>{runRecord?.derived_scenario?.event_type ?? "normal"}</span>
        </div>
        <div className="global-map-meta-row">
          <span className="global-map-label">Severity</span>
          <span>{runRecord?.derived_scenario?.severity_level ?? "low"}</span>
        </div>
        <div className="global-map-meta-row">
          <span className="global-map-label">Wind</span>
          <span>{runRecord?.weather_snapshot?.wind_speed ?? "—"} mph</span>
        </div>
        <div className="global-map-meta-row">
          <span className="global-map-label">Alerts</span>
          <span>{activeAlerts.length}</span>
        </div>

        <div className="global-map-score-grid">
          <div>
            <div className="global-map-label">Load</div>
            <div>{formatScore(runRecord?.risk_scores?.load_stress)}</div>
          </div>
          <div>
            <div className="global-map-label">Outage</div>
            <div>{formatScore(runRecord?.risk_scores?.outage_likelihood)}</div>
          </div>
          <div>
            <div className="global-map-label">Restore</div>
            <div>{formatScore(runRecord?.risk_scores?.restoration_difficulty)}</div>
          </div>
          <div>
            <div className="global-map-label">Crew</div>
            <div>{formatScore(runRecord?.risk_scores?.crew_urgency)}</div>
          </div>
          <div>
            <div className="global-map-label">Safety</div>
            <div>{formatScore(runRecord?.risk_scores?.public_safety_risk)}</div>
          </div>
        </div>
      </div>

      <div className="global-map-panel global-map-panel-right">
        <div className="global-map-analyze-row">
          <input
            className="global-map-input"
            value={zip}
            onChange={(event) => setZip(event.target.value)}
            placeholder="ZIP"
            aria-label="Zip for analysis"
          />
          <button className="btn btn-primary" onClick={runAnalysis} disabled={loading || zip.trim().length === 0}>
            Analyze
          </button>
        </div>
        {loading && <div className="global-map-loading-note">Analyzing live conditions…</div>}
      </div>

      {error && <div className="global-map-error-banner">{error}</div>}
    </section>
  );
}
