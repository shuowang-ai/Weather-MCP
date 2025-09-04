"""Data models for weather API responses."""

from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field


class WeatherCoordinate(BaseModel):
    """Weather coordinate model."""
    lng: float = Field(ge=-180.0, le=180.0, description="Longitude")
    lat: float = Field(ge=-90.0, le=90.0, description="Latitude")


class AirQualityData(BaseModel):
    """Air quality data model."""
    pm25: int
    pm10: int
    o3: int
    so2: int
    no2: int
    co: float
    aqi: Dict[str, int]
    description: Dict[str, str]


class PrecipitationData(BaseModel):
    """Precipitation data model."""
    local: Dict[str, Any]
    nearest: Dict[str, Any]


class RealtimeWeatherData(BaseModel):
    """Realtime weather data model."""
    temperature: float
    apparent_temperature: Optional[float] = None
    humidity: float
    cloudrate: float
    skycon: str
    visibility: float
    dswrf: float
    wind: Dict[str, float]
    pressure: float
    precipitation: PrecipitationData
    air_quality: AirQualityData
    life_index: Optional[Dict[str, Any]] = None


class WeatherAlert(BaseModel):
    """Weather alert model."""
    title: str
    code: str
    status: str
    description: str
    location: str
    source: str
    pubtimestamp: Optional[int] = None


class WeatherAPIResponse(BaseModel):
    """Base weather API response model."""
    status: str
    api_version: str
    api_status: str
    lang: str
    unit: str
    server_time: int
    location: List[float]
    result: Dict[str, Any]