# StormOps Console

Live weather detection and risk triggering for the StormOps Console. Stateless, no database, target &lt;3s for weather.

## Environment variables

**Backend** (e.g. `.env` or export):

- `NWS_BASE_URL` — default `https://api.weather.gov`
- `USER_AGENT` — **required by NWS**; use `StormOpsConsole`

**Frontend** (`web/.env.local`):

- `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` — Google Maps JavaScript API key (do not hardcode)
- `NEXT_PUBLIC_API_URL` — backend URL, e.g. `http://localhost:8000`

Copy `web/.env.local.example` to `web/.env.local` and set values.

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
