# StormOps Console

Live weather detection and risk triggering for the StormOps Console. Stateless, no database, target &lt;3s for weather.

## Environment variables

**Backend** (e.g. `.env` or export):

- `NWS_BASE_URL` — default `https://api.weather.gov`
- `USER_AGENT` — **required by NWS**; use `StormOpsConsole`
## Setup

### Backend

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd web
npm install
npm run dev
```

## Environment variables

**Backend** (e.g. `app/.env` or export):

- `NWS_BASE_URL` — default `https://api.weather.gov`
- `USER_AGENT` — **required by NWS**; use `StormOpsConsole`
- `OPENAI_API_KEY` — required for RAG embeddings and LLM playbook generation
- `LLM_API_KEY` — fallback for `OPENAI_API_KEY`

**Frontend** (`web/.env.local`):

- `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` — Google Maps JavaScript API key (do not hardcode)
- `NEXT_PUBLIC_API_URL` — backend URL, e.g. `http://localhost:8000`

Copy `web/.env.local.example` to `web/.env.local` and set values.

<<<<<<< HEAD
## Backend (FastAPI)

```bash
# From repo root; use a venv if you prefer
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: `GET /health`
- Analyze: `GET /api/analyze?zip=78701` → `{ weather_snapshot, derived_scenario, risk_scores }`

## Frontend (Next.js)

```bash
cd web
cp .env.local.example .env.local
# Edit .env.local: set NEXT_PUBLIC_GOOGLE_MAPS_API_KEY and NEXT_PUBLIC_API_URL
npm install
npm run dev
```

Open http://localhost:3000. Map is centered on Austin; load ZIP GeoJSON polygons; click a ZIP to call `/api/analyze?zip=XXXXX` and show risk panel, current wind, active alerts, event type, and risk color overlay (0–30 green, 30–60 yellow, 60–80 orange, 80+ red).

## Structure

- **PART 1** — `app/config.py`, `.env.example`, `web/.env.local.example`
- **PART 2** — `app/core/weather_service.py` (ZIP→lat/lng, NWS points + forecast + alerts, WeatherSnapshot, httpx async, timeout)
- **PART 3** — `app/core/trigger_engine.py` (WeatherSnapshot → DerivedScenario: event_type, severity_level, trigger_reason, confidence_score)
- **PART 4** — `app/core/risk_engine.py` (WeatherSnapshot + DerivedScenario → RiskScores 0–100)
- **PART 5** — `app/api/routes.py` (`/analyze` flow: fetch weather → derive scenario → compute risk → return JSON)
- **PART 6** — `web/` Next.js app with Google Maps JS API, Austin-centered map, ZIP GeoJSON, risk panel, no persistence
=======
## Endpoints

- Health: `GET /health`
- Analyze: `GET /api/analyze?zip=78701` — live weather + risk scores (optional `include_decision=true` for RAG + LLM agents)
- Autonomous Cycle: `POST /api/run-autonomous-cycle` — full pipeline: trigger + risk + RAG + LLM playbook

### POST /api/run-autonomous-cycle

```bash
curl -X POST http://localhost:8000/api/run-autonomous-cycle \
  -H "Content-Type: application/json" \
  -d '{
    "weather_snapshot": {
      "temperature": 98,
      "wind_speed": 25,
      "wind_gust": 48,
      "precipitation_probability": 75,
      "heat_index": 112,
      "alerts": [{"event": "Severe Thunderstorm Warning", "severity": "Severe", "headline": "Severe Thunderstorm Warning for Travis County", "id": "1"}],
      "forecast_summary": "Severe thunderstorms expected.",
      "timestamp": "2025-07-01T12:00:00Z",
      "lat": 30.267,
      "lon": -97.743,
      "zip_code": "78701"
    }
  }'
```

Returns `RunRecord` with: `weather_snapshot`, `derived_scenario`, `risk_scores`, `top_risk_driver`, `rag_snippets`, `playbook`.

### Simulation Mode

Override weather values for testing without waiting for real conditions:

```bash
curl -X POST http://localhost:8000/api/run-autonomous-cycle \
  -H "Content-Type: application/json" \
  -d '{
    "weather_snapshot": { ... },
    "simulate": "high_wind"
  }'
```

Options: `high_wind` (wind_gust=65, wind_speed=50), `extreme_heat` (heat_index=115, temperature=108).

## Architecture

```
Weather (NWS) → Trigger Engine → Risk Engine → RAG Retrieval → LLM Playbook → RunRecord
```

## Structure

- **app/config.py** — environment and constants
- **app/core/weather_service.py** — NWS API integration (ZIP → lat/lng → WeatherSnapshot)
- **app/core/trigger_engine.py** — deterministic WeatherSnapshot → DerivedScenario
- **app/core/risk_engine.py** — deterministic RiskScores 0–100
- **app/core/rag_adapter.py** — bridges core models to RAG schema
- **app/core/rag.py** — RAG retrieval wrapper (vector store + embeddings)
- **app/core/llm.py** — LLM playbook generation (gpt-4o-mini, structured JSON)
- **app/core/orchestration.py** — full autonomous cycle with simulation support
- **app/api/routes.py** — `/analyze` and `/run-autonomous-cycle` endpoints
- **app/retrieval/** — vector store, embeddings, protocol retrieval, schemas
- **app/llm/** — agent orchestration (GridOps, FieldOps, Comms, Aggregator)
- **app/schemas/** — consolidated Pydantic schemas (Playbook, RunRecord, etc.)
- **web/** — Next.js frontend with Google Maps, ZIP GeoJSON, risk panel
>>>>>>> origin/main
