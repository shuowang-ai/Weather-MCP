import os
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("knowair-weather", dependencies=["mcp[cli]"])

# Environment validation
api_token = os.getenv("CAIYUN_WEATHER_API_TOKEN")
if not api_token:
    logger.warning("CAIYUN_WEATHER_API_TOKEN environment variable not set")


async def make_request(client: httpx.AsyncClient, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Make HTTP request with proper error handling."""
    try:
        response = await client.get(url, params=params, timeout=30.0)
        response.raise_for_status()
        return response.json()
    except httpx.TimeoutException:
        logger.error(f"Request timeout for URL: {url}")
        raise Exception("Request timeout - please try again")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error {e.response.status_code} for URL: {url}")
        if e.response.status_code == 401:
            raise Exception("Invalid API token - please check your CAIYUN_WEATHER_API_TOKEN")
        elif e.response.status_code == 429:
            raise Exception("API rate limit exceeded - please try again later")
        else:
            raise Exception(f"API request failed with status {e.response.status_code}")
    except Exception as e:
        logger.error(f"Unexpected error for URL: {url} - {str(e)}")
        raise Exception(f"Weather data request failed: {str(e)}")


def validate_api_token() -> str:
    """Validate that API token is available."""
    if not api_token:
        raise Exception("API token not configured. Please set CAIYUN_WEATHER_API_TOKEN environment variable.")
    return api_token


@mcp.tool()
async def get_realtime_weather(
    lng: float = Field(
        description="The longitude of the location (-180 to 180)",
        ge=-180.0,
        le=180.0
    ),
    lat: float = Field(
        description="The latitude of the location (-90 to 90)",
        ge=-90.0,
        le=90.0
    ),
) -> str:
    """Get comprehensive real-time weather data including temperature, humidity, wind, air quality, and life indices."""
    try:
        token = validate_api_token()
        logger.info(f"Getting real-time weather for coordinates: {lng}, {lat}")
        
        async with httpx.AsyncClient() as client:
            result = await make_request(
                client,
                f"https://api.caiyunapp.com/v2.6/{token}/{lng},{lat}/realtime",
                {"lang": "en_US"},
            )
            result = result["result"]["realtime"]
            
            return f"""Temperature: {result["temperature"]}°C
Humidity: {result["humidity"]}%
Wind: {result["wind"]["speed"]} m/s, From north clockwise {result["wind"]["direction"]}°
Precipitation: {result["precipitation"]["local"]["intensity"]}%
Air Quality:
    PM2.5: {result["air_quality"]["pm25"]} μg/m³
    PM10: {result["air_quality"]["pm10"]} μg/m³
    O3: {result["air_quality"]["o3"]} μg/m³
    SO2: {result["air_quality"]["so2"]} μg/m³
    NO2: {result["air_quality"]["no2"]} μg/m³
    CO: {result["air_quality"]["co"]} mg/m³
    AQI:
        China: {result["air_quality"]["aqi"]["chn"]}
        USA: {result["air_quality"]["aqi"]["usa"]}
    Life Index:
        UV: {result["life_index"]["ultraviolet"]["desc"]}
        Comfort: {result["life_index"]["comfort"]["desc"]}"""
        
    except Exception as e:
        logger.error(f"Error getting real-time weather: {str(e)}")
        raise Exception(f"Failed to get real-time weather: {str(e)}")


@mcp.tool()
async def get_hourly_forecast(
    lng: float = Field(
        description="The longitude of the location (-180 to 180)",
        ge=-180.0,
        le=180.0
    ),
    lat: float = Field(
        description="The latitude of the location (-90 to 90)",
        ge=-90.0,
        le=90.0
    ),
) -> str:
    """Get detailed hourly weather forecast for the next 72 hours including temperature, apparent temperature, weather conditions, precipitation probability, and wind data."""
    try:
        token = validate_api_token()
        logger.info(f"Getting hourly forecast for coordinates: {lng}, {lat}")
        
        async with httpx.AsyncClient() as client:
            result = await make_request(
                client,
                f"https://api.caiyunapp.com/v2.6/{token}/{lng},{lat}/hourly",
                {"hourlysteps": "72", "lang": "en_US"},
            )
            hourly = result["result"]["hourly"]
            forecast = "72-Hour Forecast:\n"
            
            for i in range(len(hourly["temperature"])):
                time = hourly["temperature"][i]["datetime"].split("+")[0]
                temp = hourly["temperature"][i]["value"]
                skycon = hourly["skycon"][i]["value"]
                rain_prob = hourly["precipitation"][i]["probability"]
                # Get precipitation intensity (mm/h)
                precip_intensity = hourly["precipitation"][i].get("value", 0)
                wind_speed = hourly["wind"][i]["speed"]
                wind_dir = hourly["wind"][i]["direction"]
                
                # Add apparent temperature if available
                apparent_temp = ""
                if "apparent_temperature" in hourly and i < len(hourly["apparent_temperature"]):
                    apparent_temp = f"Feels Like: {hourly['apparent_temperature'][i]['value']}°C\n"

                forecast += f"""
Time: {time}
Temperature: {temp}°C
{apparent_temp}Weather: {skycon}
Rain Probability: {rain_prob}%
Precipitation: {precip_intensity}mm/h
Wind: {wind_speed}m/s, {wind_dir}°
------------------------"""
            return forecast
            
    except Exception as e:
        logger.error(f"Error getting hourly forecast: {str(e)}")
        raise Exception(f"Failed to get hourly forecast: {str(e)}")


@mcp.tool()
async def get_weekly_forecast(
    lng: float = Field(
        description="The longitude of the location (-180 to 180)",
        ge=-180.0,
        le=180.0
    ),
    lat: float = Field(
        description="The latitude of the location (-90 to 90)",
        ge=-90.0,
        le=90.0
    ),
) -> str:
    """Get daily weather forecast for the next 7 days including temperature range, weather conditions, and precipitation probability."""
    try:
        token = validate_api_token()
        logger.info(f"Getting weekly forecast for coordinates: {lng}, {lat}")
        
        async with httpx.AsyncClient() as client:
            result = await make_request(
                client,
                f"https://api.caiyunapp.com/v2.6/{token}/{lng},{lat}/daily",
                {"dailysteps": "7", "lang": "en_US"},
            )
            daily = result["result"]["daily"]
            forecast = "7-Day Forecast:\n"
            
            for i in range(min(7, len(daily["temperature"]))):
                date = daily["temperature"][i]["date"].split("T")[0]
                temp_max = daily["temperature"][i]["max"]
                temp_min = daily["temperature"][i]["min"]
                skycon = daily["skycon"][i]["value"]
                rain_prob = daily["precipitation"][i]["probability"]

                forecast += f"""
Date: {date}
Temperature: {temp_min}°C ~ {temp_max}°C
Weather: {skycon}
Rain Probability: {rain_prob}%
------------------------"""
            return forecast
            
    except Exception as e:
        logger.error(f"Error getting weekly forecast: {str(e)}")
        raise Exception(f"Failed to get weekly forecast: {str(e)}")


@mcp.tool()
async def get_historical_weather(
    lng: float = Field(
        description="The longitude of the location (-180 to 180)",
        ge=-180.0,
        le=180.0
    ),
    lat: float = Field(
        description="The latitude of the location (-90 to 90)",
        ge=-90.0,
        le=90.0
    ),
) -> str:
    """Get historical weather data for the past 24 hours including temperature and weather conditions."""
    try:
        token = validate_api_token()
        logger.info(f"Getting historical weather for coordinates: {lng}, {lat}")
        
        # Calculate timestamp for 24 hours ago
        timestamp = int((datetime.now() - timedelta(hours=24)).timestamp())

        async with httpx.AsyncClient() as client:
            result = await make_request(
                client,
                f"https://api.caiyunapp.com/v2.6/{token}/{lng},{lat}/hourly",
                {"hourlysteps": "24", "begin": str(timestamp), "lang": "en_US"},
            )
            hourly = result["result"]["hourly"]
            history = "Past 24-Hour Weather:\n"
            
            for i in range(len(hourly["temperature"])):
                time = hourly["temperature"][i]["datetime"].split("+")[0]
                temp = hourly["temperature"][i]["value"]
                skycon = hourly["skycon"][i]["value"]

                history += f"""
Time: {time}
Temperature: {temp}°C
Weather: {skycon}
------------------------"""
            return history
            
    except Exception as e:
        logger.error(f"Error getting historical weather: {str(e)}")
        raise Exception(f"Failed to get historical weather: {str(e)}")


@mcp.tool()
async def get_minute_precipitation(
    lng: float = Field(
        description="The longitude of the location (-180 to 180)",
        ge=-180.0,
        le=180.0
    ),
    lat: float = Field(
        description="The latitude of the location (-90 to 90)",
        ge=-90.0,
        le=90.0
    ),
) -> str:
    """Get minute-level precipitation forecast for the next 2 hours (available for major cities in China)."""
    try:
        token = validate_api_token()
        logger.info(f"Getting minute precipitation for coordinates: {lng}, {lat}")
        
        async with httpx.AsyncClient() as client:
            result = await make_request(
                client,
                f"https://api.caiyunapp.com/v2.6/{token}/{lng},{lat}/minutely",
                {"lang": "en_US"},
            )
            
            # Check if minutely data is available
            if "minutely" not in result["result"]:
                return f"Minute-level precipitation data not available for this location ({lng}, {lat}). This feature is primarily available for major cities in China."
            
            minutely = result["result"]["minutely"]
            
            # Get summary and datasource
            summary = minutely.get("description", "No description available")
            datasource = minutely.get("datasource", "Unknown")
            
            forecast = f"2-Hour Minute-level Precipitation Forecast:\n"
            forecast += f"Summary: {summary}\n"
            forecast += f"Data Source: {datasource}\n\n"
            
            # Show precipitation data in 10-minute intervals for readability
            if "precipitation_2h" in minutely:
                precipitation_data = minutely["precipitation_2h"]
                for i in range(0, len(precipitation_data), 10):
                    time_offset = i
                    intensity = precipitation_data[i]
                    forecast += f"T+{time_offset:2d}min: {intensity:.2f}mm/h\n"
            else:
                forecast += "No precipitation forecast data available.\n"
            
            return forecast
            
    except Exception as e:
        logger.error(f"Error getting minute precipitation: {str(e)}")
        return f"Minute-level precipitation data not available for this location. This feature is primarily available for major cities in China. Error: {str(e)}"


@mcp.tool()
async def get_comprehensive_weather(
    lng: float = Field(
        description="The longitude of the location (-180 to 180)",
        ge=-180.0,
        le=180.0
    ),
    lat: float = Field(
        description="The latitude of the location (-90 to 90)",
        ge=-90.0,
        le=90.0
    ),
) -> str:
    """Get comprehensive weather report including current conditions, air quality, today's forecast, and active alerts."""
    try:
        token = validate_api_token()
        logger.info(f"Getting comprehensive weather for coordinates: {lng}, {lat}")
        
        async with httpx.AsyncClient() as client:
            result = await make_request(
                client,
                f"https://api.caiyunapp.com/v2.6/{token}/{lng},{lat}/weather",
                {"lang": "en_US"},
            )
            
            weather_data = result["result"]
            comprehensive_report = "🌤️ Comprehensive Weather Report:\n\n"
            
            # Realtime data
            if "realtime" in weather_data:
                rt = weather_data["realtime"]
                comprehensive_report += f"📍 Current Conditions:\n"
                comprehensive_report += f"Temperature: {rt['temperature']}°C\n"
                if "apparent_temperature" in rt:
                    comprehensive_report += f"Feels Like: {rt['apparent_temperature']}°C\n"
                comprehensive_report += f"Humidity: {rt['humidity']}%\n"
                comprehensive_report += f"Wind: {rt['wind']['speed']}m/s @ {rt['wind']['direction']}°\n"
                comprehensive_report += f"Pressure: {rt.get('pressure', 'N/A')} Pa\n"
                comprehensive_report += f"Visibility: {rt.get('visibility', 'N/A')} km\n"
                comprehensive_report += f"Cloud Cover: {rt.get('cloudrate', 'N/A')}%\n"
                comprehensive_report += f"UV Index: {rt.get('dswrf', 'N/A')}\n\n"
                
                # Air Quality
                if "air_quality" in rt:
                    aq = rt["air_quality"]
                    comprehensive_report += f"🏭 Air Quality:\n"
                    comprehensive_report += f"PM2.5: {aq['pm25']}μg/m³ | PM10: {aq['pm10']}μg/m³\n"
                    comprehensive_report += f"O3: {aq['o3']}μg/m³ | NO2: {aq['no2']}μg/m³\n"
                    comprehensive_report += f"SO2: {aq['so2']}μg/m³ | CO: {aq['co']}mg/m³\n"
                    comprehensive_report += f"AQI (CN): {aq['aqi']['chn']} | AQI (US): {aq['aqi']['usa']}\n\n"
            
            # Today's forecast summary
            if "daily" in weather_data and len(weather_data["daily"]["temperature"]) > 0:
                today = weather_data["daily"]
                comprehensive_report += f"📅 Today's Forecast:\n"
                comprehensive_report += f"High: {today['temperature'][0]['max']}°C | Low: {today['temperature'][0]['min']}°C\n"
                comprehensive_report += f"Weather: {today['skycon'][0]['value']}\n"
                comprehensive_report += f"Rain Chance: {today['precipitation'][0]['probability']}%\n\n"
            
            # Alerts
            if "alert" in weather_data and weather_data["alert"]["content"]:
                alerts = weather_data["alert"]["content"]
                comprehensive_report += f"⚠️ Active Weather Alerts: {len(alerts)}\n"
                for alert in alerts[:3]:  # Show first 3 alerts
                    comprehensive_report += f"• {alert.get('title', 'Alert')}: {alert.get('status', 'Unknown')}\n"
                comprehensive_report += "\n"
            
            return comprehensive_report
            
    except Exception as e:
        logger.error(f"Error getting comprehensive weather: {str(e)}")
        raise Exception(f"Failed to get comprehensive weather: {str(e)}")


@mcp.tool()
async def get_astronomy_info(
    lng: float = Field(
        description="The longitude of the location (-180 to 180)",
        ge=-180.0,
        le=180.0
    ),
    lat: float = Field(
        description="The latitude of the location (-90 to 90)",
        ge=-90.0,
        le=90.0
    ),
) -> str:
    """Get astronomy information including sunrise, sunset times for the next 7 days."""
    try:
        token = validate_api_token()
        logger.info(f"Getting astronomy info for coordinates: {lng}, {lat}")
        
        async with httpx.AsyncClient() as client:
            result = await make_request(
                client,
                f"https://api.caiyunapp.com/v2.6/{token}/{lng},{lat}/daily",
                {"dailysteps": "7", "lang": "en_US"},
            )
            daily = result["result"]["daily"]
            
            astro_info = "🌅 Astronomy Information (Next 7 Days):\n\n"
            
            available_days = min(7, len(daily.get("astro", [])))
            if available_days == 0:
                return "Astronomy data not available for this location."
            
            for i in range(available_days):
                date = daily["astro"][i]["date"].split("T")[0]
                astro = daily["astro"][i]
                
                astro_info += f"📅 {date}:\n"
                
                # Sun info - these should be available
                if "sunrise" in astro and "sunset" in astro:
                    sunrise = astro["sunrise"]["time"] if isinstance(astro["sunrise"], dict) else astro["sunrise"]
                    sunset = astro["sunset"]["time"] if isinstance(astro["sunset"], dict) else astro["sunset"]
                    astro_info += f"☀️ Sun: Rise {sunrise} | Set {sunset}\n"
                
                # Moon info - may not be available for all locations
                if "moonrise" in astro and "moonset" in astro:
                    try:
                        moonrise = astro["moonrise"]["time"] if isinstance(astro["moonrise"], dict) else astro["moonrise"]
                        moonset = astro["moonset"]["time"] if isinstance(astro["moonset"], dict) else astro["moonset"]
                        astro_info += f"🌙 Moon: Rise {moonrise} | Set {moonset}\n"
                    except:
                        astro_info += f"🌙 Moon: Data not available\n"
                
                # Moon phase
                if "moon_phase" in astro:
                    moon_phase = astro["moon_phase"]
                    phase_names = {
                        "new": "New Moon 🌑",
                        "waxing_crescent": "Waxing Crescent 🌒", 
                        "first_quarter": "First Quarter 🌓",
                        "waxing_gibbous": "Waxing Gibbous 🌔",
                        "full": "Full Moon 🌕",
                        "waning_gibbous": "Waning Gibbous 🌖",
                        "last_quarter": "Last Quarter 🌗",
                        "waning_crescent": "Waning Crescent 🌘"
                    }
                    phase_name = phase_names.get(moon_phase, f"Unknown ({moon_phase})")
                    astro_info += f"🌙 Phase: {phase_name}\n"
                
                astro_info += "------------------------\n"
            
            return astro_info
            
    except Exception as e:
        logger.error(f"Error getting astronomy info: {str(e)}")
        raise Exception(f"Failed to get astronomy info: {str(e)}")


@mcp.tool()
async def get_weather_alerts(
    lng: float = Field(
        description="The longitude of the location (-180 to 180)",
        ge=-180.0,
        le=180.0
    ),
    lat: float = Field(
        description="The latitude of the location (-90 to 90)",
        ge=-90.0,
        le=90.0
    ),
) -> str:
    """Get active weather alerts and warnings for the specified location."""
    try:
        token = validate_api_token()
        logger.info(f"Getting weather alerts for coordinates: {lng}, {lat}")
        
        async with httpx.AsyncClient() as client:
            result = await make_request(
                client,
                f"https://api.caiyunapp.com/v2.6/{token}/{lng},{lat}/weather",
                {"alert": "true", "lang": "en_US"},
            )
            alerts = result["result"].get("alert", {}).get("content", [])
            
            if not alerts:
                return "No active weather alerts."

            alert_text = "Weather Alerts:\n"
            for alert in alerts:
                alert_text += f"""
Title: {alert.get("title", "N/A")}
Code: {alert.get("code", "N/A")}
Status: {alert.get("status", "N/A")}
Description: {alert.get("description", "N/A")}
------------------------"""
            return alert_text
            
    except Exception as e:
        logger.error(f"Error getting weather alerts: {str(e)}")
        raise Exception(f"Failed to get weather alerts: {str(e)}")


def main():
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()