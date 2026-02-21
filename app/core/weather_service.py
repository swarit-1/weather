"""NWS API integration — live weather, ZIP → lat/lng, WeatherSnapshot."""

from datetime import datetime
from typing import Any

import httpx

from app.config import NWS_BASE_URL, USER_AGENT
from app.core.models import WeatherSnapshot

# Hackathon: simple ZIP → (lat, lon) for Austin area and fallback
ZIP_TO_LAT_LON: dict[str, tuple[float, float]] = {
    "78701": (30.2672, -97.7431),
    "78702": (30.2650, -97.7150),
    "78703": (30.2950, -97.7550),
    "78704": (30.2450, -97.7650),
    "78705": (30.2850, -97.7400),
    "78712": (30.2820, -97.7380),
    "78717": (30.4950, -97.7850),
    "78719": (30.1550, -97.6680),
    "78721": (30.2650, -97.6900),
    "78722": (30.2900, -97.7100),
    "78723": (30.3000, -97.6900),
    "78724": (30.2950, -97.6400),
    "78725": (30.1550, -97.6400),
    "78726": (30.4350, -97.8500),
    "78727": (30.4250, -97.7200),
    "78728": (30.4550, -97.6950),
    "78729": (30.4550, -97.7550),
    "78730": (30.3550, -97.8950),
    "78731": (30.3550, -97.7650),
    "78732": (30.3850, -97.8850),
    "78733": (30.4350, -97.8350),
    "78734": (30.3950, -97.9850),
    "78735": (30.2650, -97.9050),
    "78736": (30.2550, -97.9350),
    "78737": (30.2350, -97.9450),
    "78738": (30.3250, -97.9450),
    "78739": (30.1850, -97.8700),
    "78741": (30.2300, -97.7150),
    "78742": (30.2450, -97.6550),
    "78744": (30.1950, -97.7550),
    "78745": (30.2150, -97.8000),
    "78746": (30.3350, -97.8150),
    "78747": (30.1550, -97.7550),
    "78748": (30.1750, -97.8250),
    "78749": (30.2150, -97.8350),
    "78750": (30.4250, -97.8050),
    "78751": (30.3050, -97.7250),
    "78752": (30.3350, -97.7150),
    "78753": (30.3750, -97.6900),
    "78754": (30.3550, -97.6650),
    "78756": (30.3150, -97.7400),
    "78757": (30.3450, -97.7350),
    "78758": (30.3850, -97.7050),
    "78759": (30.4050, -97.7450),
}
AUSTIN_CENTER = (30.267153, -97.7430608)
WEATHER_TIMEOUT = 8.0  # target <3s; allow some buffer


def zip_to_lat_lon(zip_code: str) -> tuple[float, float]:
    """Convert ZIP to (lat, lon). Hackathon: lookup table + Austin fallback."""
    key = str(zip_code).strip()
    return ZIP_TO_LAT_LON.get(key, AUSTIN_CENTER)


async def fetch_live_weather(zip_code: str) -> WeatherSnapshot:
    """
    Fetch live weather from NWS for ZIP.
    Flow: ZIP → lat/lng → /points/{lat},{lon} → grid forecast URL → forecast + alerts.
    """
    lat, lon = zip_to_lat_lon(zip_code)
    headers = {"User-Agent": USER_AGENT}

    async with httpx.AsyncClient(
        base_url=NWS_BASE_URL,
        headers=headers,
        timeout=WEATHER_TIMEOUT,
    ) as client:
        points_resp = await client.get(f"/points/{lat:.4f},{lon:.4f}")
        points_resp.raise_for_status()
        points = points_resp.json()

        props = points.get("properties", {})
        forecast_url = props.get("forecast")

        forecast_data: dict[str, Any] = {}
        if forecast_url:
            forecast_resp = await client.get(forecast_url)
            forecast_resp.raise_for_status()
            forecast_data = forecast_resp.json()

        alerts_resp = await client.get(f"/alerts?point={lat:.4f},{lon:.4f}")
        alerts_resp.raise_for_status()
        alerts_payload = alerts_resp.json()

    return _normalize_to_snapshot(
        zip_code=zip_code,
        lat=lat,
        lon=lon,
        points=points,
        forecast=forecast_data,
        alerts_payload=alerts_payload,
    )


def _normalize_to_snapshot(
    zip_code: str,
    lat: float,
    lon: float,
    points: dict,
    forecast: dict,
    alerts_payload: dict,
) -> WeatherSnapshot:
    """Build WeatherSnapshot from NWS points, forecast, and alerts."""
    periods = forecast.get("properties", {}).get("periods", [])
    first = periods[0] if periods else {}

    temperature = _num(first.get("temperature"))
    wind_speed = _wind_mph(first.get("windSpeed"))
    wind_gust = _wind_mph(first.get("windGust")) or wind_speed
    pop_raw = first.get("probabilityOfPrecipitation")
    precipitation_probability = _num(pop_raw.get("value") if isinstance(pop_raw, dict) else pop_raw)
    forecast_summary = first.get("shortForecast") or first.get("detailedForecast") or ""

    features = alerts_payload.get("features", [])
    alerts = [
        {
            "id": f.get("id"),
            "event": f.get("properties", {}).get("event"),
            "severity": f.get("properties", {}).get("severity"),
            "headline": f.get("properties", {}).get("headline"),
        }
        for f in features
    ]

    heat_index = _compute_heat_index(temperature, _relative_humidity_from_period(first))
    if heat_index is None and temperature is not None:
        heat_index = temperature

    return WeatherSnapshot(
        temperature=temperature,
        wind_speed=wind_speed,
        wind_gust=wind_gust,
        precipitation_probability=precipitation_probability,
        heat_index=heat_index,
        alerts=alerts,
        forecast_summary=forecast_summary or None,
        timestamp=datetime.utcnow(),
        lat=lat,
        lon=lon,
        zip_code=zip_code,
    )


def _num(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _wind_mph(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v.split()[0])
        except (ValueError, IndexError):
            pass
    return None


def _relative_humidity_from_period(period: dict) -> float | None:
    return _num(period.get("relativeHumidity", {}).get("value") if isinstance(period.get("relativeHumidity"), dict) else period.get("relativeHumidity"))


def _compute_heat_index(temp_f: float | None, relative_humidity: float | None) -> float | None:
    """Compute heat index °F from temperature and RH. Simple formula for hackathon."""
    if temp_f is None or relative_humidity is None:
        return None
    if temp_f < 80:
        return temp_f
    # Rothfusz regression approximation (NOAA)
    t, r = temp_f, relative_humidity
    hi = -42.379 + 2.04901523 * t + 10.14333127 * r - 0.22475541 * t * r
    hi -= 6.83783e-3 * t * t - 5.481717e-2 * r * r
    hi += 1.22874e-3 * t * t * r + 8.5282e-4 * t * r * r - 1.99e-6 * t * t * r * r
    return round(hi, 1)
