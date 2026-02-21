# StormOps Console

Live weather detection and risk triggering for the StormOps Console. Stateless, no database, target &lt;3s for weather.

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
