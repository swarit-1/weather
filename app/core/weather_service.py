"""NWS API integration for fetching weather data."""

import httpx
from app.config import NWS_API_BASE_URL
from app.core.models import WeatherSnapshot
from typing import Optional

class WeatherService:
    """Service for interacting with National Weather Service API."""
    
    def __init__(self, base_url: str = NWS_API_BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def get_forecast(self, latitude: float, longitude: float) -> Optional[dict]:
        """Fetch forecast data from NWS API."""
        try:
            url = f"{self.base_url}/points/{latitude},{longitude}"
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error fetching forecast: {e}")
            return None
    
    async def get_weather_snapshot(self, latitude: float, longitude: float) -> Optional[WeatherSnapshot]:
        """Get current weather conditions as WeatherSnapshot."""
        forecast = await self.get_forecast(latitude, longitude)
        if not forecast:
            return None
        
        # TODO: Parse forecast data into WeatherSnapshot
        # This is a placeholder for actual weather data parsing
        return None
