"""Configuration management for the weather MCP server."""

import os
from typing import Optional
from datetime import datetime, timedelta


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
        
        # Performance monitoring
        self.enable_monitoring: bool = True
        self.request_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_response_time": 0.0
        }
        
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
    
    def record_request(self, success: bool, response_time: float) -> None:
        """Record request statistics."""
        if not self.enable_monitoring:
            return
        
        self.request_stats["total_requests"] += 1
        if success:
            self.request_stats["successful_requests"] += 1
        else:
            self.request_stats["failed_requests"] += 1
        
        # Update average response time
        total_requests = self.request_stats["successful_requests"] + self.request_stats["failed_requests"]
        if total_requests > 0:
            current_avg = self.request_stats["average_response_time"]
            self.request_stats["average_response_time"] = (
                (current_avg * (total_requests - 1) + response_time) / total_requests
            )
    
    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        if self.enable_monitoring:
            self.request_stats["cache_hits"] += 1
    
    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        if self.enable_monitoring:
            self.request_stats["cache_misses"] += 1
    
    def get_stats(self) -> dict:
        """Get current statistics."""
        stats = self.request_stats.copy()
        if stats["total_requests"] > 0:
            stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]
            stats["cache_hit_rate"] = (
                stats["cache_hits"] / (stats["cache_hits"] + stats["cache_misses"])
                if (stats["cache_hits"] + stats["cache_misses"]) > 0 else 0
            )
        return stats


# Global config instance
config = WeatherConfig()