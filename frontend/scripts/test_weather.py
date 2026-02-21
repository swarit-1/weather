#!/usr/bin/env python3
"""Quick test that NWS weather fetching works. Run from repo root: python scripts/test_weather.py"""

import asyncio
import os
import sys

# Ensure app is on path when run from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.weather_service import fetch_live_weather, zip_to_lat_lon


async def main():
    zip_code = "78701"
    print(f"Testing weather fetch for ZIP {zip_code}...")
    print(f"  Lat/lon: {zip_to_lat_lon(zip_code)}")
    try:
        snapshot = await fetch_live_weather(zip_code)
        print("  OK – got WeatherSnapshot")
        print(f"  Temperature: {snapshot.temperature}°F")
        print(f"  Wind: {snapshot.wind_speed} mph (gust {snapshot.wind_gust})")
        print(f"  Precip prob: {snapshot.precipitation_probability}%")
        print(f"  Heat index: {snapshot.heat_index}°F")
        print(f"  Forecast: {snapshot.forecast_summary or '(none)'}")
        print(f"  Alerts: {len(snapshot.alerts)}")
        print(f"  Timestamp: {snapshot.timestamp}")
    except Exception as e:
        print(f"  FAILED: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
