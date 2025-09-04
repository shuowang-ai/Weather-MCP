"""Configuration management for the weather MCP server."""

import os
from typing import Optional


class WeatherConfig:
    """Configuration class for weather API settings."""
    
    def __init__(self):
        self.api_token: Optional[str] = os.getenv("CAIYUN_WEATHER_API_TOKEN")
        self.api_base_url: str = "https://api.caiyunapp.com/v2.6"
        self.default_timeout: float = 30.0
        self.default_lang: str = "zh_CN"
        self.max_retries: int = 3
        
        # API limits - enhanced based on API documentation
        self.max_hourly_hours: int = 360  # Enhanced to support 15-day hourly forecasts
        self.max_daily_days: int = 15     # Enhanced to support 15-day daily forecasts
        self.max_minutely_hours: int = 2
        
        # Data display settings
        self.use_emoji: bool = True
        self.show_air_quality_trends: bool = True
        self.show_life_indices: bool = True
        
    def validate_token(self) -> str:
        """Validate that API token is available."""
        if not self.api_token:
            raise ValueError(
                "API token not configured. Please set CAIYUN_WEATHER_API_TOKEN environment variable."
            )
        return self.api_token
    
    def get_api_url(self, endpoint: str) -> str:
        """Get full API URL for endpoint."""
        return f"{self.api_base_url}/{self.api_token}/{endpoint}"


# Global config instance
config = WeatherConfig()