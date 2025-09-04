import os
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List

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
    logger.warning("CAIYUN_WEATHER_API_TOKEN environment variable not set. Please configure your API token.")

# Weather phenomenon mapping
WEATHER_PHENOMENA = {
    "CLEAR_DAY": "晴（白天）",
    "CLEAR_NIGHT": "晴（夜间）", 
    "PARTLY_CLOUDY_DAY": "多云（白天）",
    "PARTLY_CLOUDY_NIGHT": "多云（夜间）",
    "CLOUDY": "阴",
    "LIGHT_HAZE": "轻度雾霾",
    "MODERATE_HAZE": "中度雾霾", 
    "HEAVY_HAZE": "重度雾霾",
    "LIGHT_RAIN": "小雨",
    "MODERATE_RAIN": "中雨",
    "HEAVY_RAIN": "大雨",
    "STORM_RAIN": "暴雨",
    "FOG": "雾",
    "LIGHT_SNOW": "小雪",
    "MODERATE_SNOW": "中雪",
    "HEAVY_SNOW": "大雪",
    "STORM_SNOW": "暴雪",
    "DUST": "浮尘",
    "SAND": "沙尘",
    "WIND": "大风"
}

def translate_weather_phenomenon(skycon: str) -> str:
    """Translate weather phenomenon code to Chinese description."""
    return WEATHER_PHENOMENA.get(skycon, skycon)

def format_precipitation_intensity(intensity: float) -> str:
    """Format precipitation intensity with proper description."""
    if intensity < 0.031:
        return f"{intensity:.3f} (无雨/雪)"
    elif intensity < 0.25:
        return f"{intensity:.3f} (小雨/雪)"
    elif intensity < 0.35:
        return f"{intensity:.3f} (中雨/雪)"
    elif intensity < 0.48:
        return f"{intensity:.3f} (大雨/雪)"
    else:
        return f"{intensity:.3f} (暴雨/雪)"


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
                {"lang": "zh_CN"},
            )
            rt = result["result"]["realtime"]
            
            # Format weather report
            weather_desc = translate_weather_phenomenon(rt["skycon"])
            precip_intensity = format_precipitation_intensity(rt["precipitation"]["local"]["intensity"])
            
            report = f"""🌤️ 实时天气数据:
📍 位置: {lng}, {lat}
🌡️  温度: {rt["temperature"]}°C
🤔 体感温度: {rt.get("apparent_temperature", "N/A")}°C
💧 湿度: {int(rt["humidity"] * 100)}%
☁️  云量: {int(rt["cloudrate"] * 100)}%
🌦️  天气: {weather_desc}
👁️  能见度: {rt["visibility"]}km
☀️  辐射通量: {rt["dswrf"]}W/M²
💨 风速: {rt["wind"]["speed"]}m/s, 风向: {rt["wind"]["direction"]}°
📊 气压: {rt["pressure"]}Pa
🌧️  降水强度: {precip_intensity}
📍 最近降水距离: {rt["precipitation"]["nearest"]["distance"]/1000:.1f}km

🏭 空气质量:
    PM2.5: {rt["air_quality"]["pm25"]}μg/m³
    PM10: {rt["air_quality"]["pm10"]}μg/m³
    臭氧: {rt["air_quality"]["o3"]}μg/m³
    二氧化硫: {rt["air_quality"]["so2"]}μg/m³
    二氧化氮: {rt["air_quality"]["no2"]}μg/m³
    一氧化碳: {rt["air_quality"]["co"]}mg/m³
    中国AQI: {rt["air_quality"]["aqi"]["chn"]} ({rt["air_quality"]["description"]["chn"]})
    美国AQI: {rt["air_quality"]["aqi"]["usa"]} ({rt["air_quality"]["description"]["usa"]})

📋 生活指数:
    紫外线: {rt["life_index"]["ultraviolet"]["desc"]} (指数: {rt["life_index"]["ultraviolet"]["index"]})
    舒适度: {rt["life_index"]["comfort"]["desc"]} (指数: {rt["life_index"]["comfort"]["index"]})"""
            
            return report
        
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
    hours: int = Field(
        description="Number of hours to forecast (1-72)",
        ge=1,
        le=72,
        default=24
    ),
) -> str:
    """Get detailed hourly weather forecast including temperature, apparent temperature, weather conditions, precipitation, wind, air quality, and more."""
    try:
        token = validate_api_token()
        logger.info(f"Getting {hours}-hour forecast for coordinates: {lng}, {lat}")
        
        async with httpx.AsyncClient() as client:
            result = await make_request(
                client,
                f"https://api.caiyunapp.com/v2.6/{token}/{lng},{lat}/hourly",
                {"hourlysteps": str(hours), "lang": "zh_CN"},
            )
            hourly = result["result"]["hourly"]
            description = hourly.get("description", f"未来{hours}小时天气预报")
            keypoint = result["result"].get("forecast_keypoint", "")
            
            forecast = f"🕒 {description}\n"
            if keypoint:
                forecast += f"🎯 关键信息: {keypoint}\n\n"
            
            # Show every 3 hours for better readability if more than 24 hours
            step = 3 if hours > 24 else 1
            
            for i in range(0, min(hours, len(hourly["temperature"])), step):
                time = hourly["temperature"][i]["datetime"]
                temp = hourly["temperature"][i]["value"]
                skycon = translate_weather_phenomenon(hourly["skycon"][i]["value"])
                
                # Precipitation data
                rain_prob = int(hourly["precipitation"][i]["probability"] * 100)
                precip_value = hourly["precipitation"][i].get("value", 0)
                
                # Wind data
                wind_speed = hourly["wind"][i]["speed"]
                wind_dir = hourly["wind"][i]["direction"]
                
                # Additional data
                humidity = int(hourly["humidity"][i]["value"] * 100) if "humidity" in hourly else "N/A"
                cloudrate = int(hourly["cloudrate"][i]["value"] * 100) if "cloudrate" in hourly else "N/A"
                visibility = hourly["visibility"][i]["value"] if "visibility" in hourly else "N/A"
                pressure = hourly["pressure"][i]["value"] if "pressure" in hourly else "N/A"
                
                # Apparent temperature
                apparent_temp = ""
                if "apparent_temperature" in hourly and i < len(hourly["apparent_temperature"]):
                    apparent_temp = f"🤔 体感: {hourly['apparent_temperature'][i]['value']}°C\n"
                
                # Air quality (if available)
                air_quality_info = ""
                if "air_quality" in hourly:
                    if "pm25" in hourly["air_quality"] and i < len(hourly["air_quality"]["pm25"]):
                        pm25 = hourly["air_quality"]["pm25"][i]["value"]
                        air_quality_info += f"🏭 PM2.5: {pm25}μg/m³\n"
                    if "aqi" in hourly["air_quality"] and i < len(hourly["air_quality"]["aqi"]):
                        chn_aqi = hourly["air_quality"]["aqi"][i]["value"]["chn"]
                        air_quality_info += f"📊 AQI: {chn_aqi}\n"
                
                forecast += f"""⏰ {time}
🌡️  温度: {temp}°C
{apparent_temp}🌦️  天气: {skycon}
🌧️  降水概率: {rain_prob}%
💧 降水量: {precip_value}mm/h
💨 风速: {wind_speed}km/h, 风向: {wind_dir}°
💧 湿度: {humidity}%
☁️  云量: {cloudrate}%
👁️  能见度: {visibility}km
📊 气压: {pressure}Pa
{air_quality_info}------------------------\n"""
                
            return forecast
            
    except Exception as e:
        logger.error(f"Error getting hourly forecast: {str(e)}")
        raise Exception(f"Failed to get hourly forecast: {str(e)}")


@mcp.tool()
async def get_daily_forecast(
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
    days: int = Field(
        description="Number of days to forecast (1-7)",
        ge=1,
        le=7,
        default=7
    ),
) -> str:
    """Get comprehensive daily weather forecast including temperature ranges, weather conditions, precipitation, wind, air quality, and life indices."""
    try:
        token = validate_api_token()
        logger.info(f"Getting {days}-day forecast for coordinates: {lng}, {lat}")
        
        async with httpx.AsyncClient() as client:
            result = await make_request(
                client,
                f"https://api.caiyunapp.com/v2.6/{token}/{lng},{lat}/daily",
                {"dailysteps": str(days), "lang": "zh_CN"},
            )
            daily = result["result"]["daily"]
            
            forecast = f"📅 未来{days}天天气预报:\n\n"
            
            for i in range(min(days, len(daily["temperature"]))):
                date = daily["temperature"][i]["date"].split("T")[0]
                
                # Temperature data
                temp_max = daily["temperature"][i]["max"]
                temp_min = daily["temperature"][i]["min"]
                temp_avg = daily["temperature"][i]["avg"]
                
                # Day/night temperature if available
                day_temp = ""
                night_temp = ""
                if "temperature_08h_20h" in daily and i < len(daily["temperature_08h_20h"]):
                    day_max = daily["temperature_08h_20h"][i]["max"]
                    day_min = daily["temperature_08h_20h"][i]["min"]
                    day_temp = f"🌞 白天: {day_min}°C~{day_max}°C\n"
                
                if "temperature_20h_32h" in daily and i < len(daily["temperature_20h_32h"]):
                    night_max = daily["temperature_20h_32h"][i]["max"]
                    night_min = daily["temperature_20h_32h"][i]["min"]
                    night_temp = f"🌙 夜间: {night_min}°C~{night_max}°C\n"
                
                # Weather phenomena
                skycon = translate_weather_phenomenon(daily["skycon"][i]["value"])
                day_skycon = ""
                night_skycon = ""
                if "skycon_08h_20h" in daily and i < len(daily["skycon_08h_20h"]):
                    day_skycon = f"🌞 白天天气: {translate_weather_phenomenon(daily['skycon_08h_20h'][i]['value'])}\n"
                if "skycon_20h_32h" in daily and i < len(daily["skycon_20h_32h"]):
                    night_skycon = f"🌙 夜间天气: {translate_weather_phenomenon(daily['skycon_20h_32h'][i]['value'])}\n"
                
                # Precipitation data
                rain_prob = int(daily["precipitation"][i]["probability"] * 100)
                precip_avg = daily["precipitation"][i]["avg"]
                
                # Day/night precipitation
                day_precip = ""
                night_precip = ""
                if "precipitation_08h_20h" in daily and i < len(daily["precipitation_08h_20h"]):
                    day_prob = int(daily["precipitation_08h_20h"][i]["probability"] * 100)
                    day_precip = f"🌞 白天降水: {day_prob}%\n"
                if "precipitation_20h_32h" in daily and i < len(daily["precipitation_20h_32h"]):
                    night_prob = int(daily["precipitation_20h_32h"][i]["probability"] * 100)
                    night_precip = f"🌙 夜间降水: {night_prob}%\n"
                
                # Wind data
                wind_info = ""
                if "wind" in daily and i < len(daily["wind"]):
                    wind_max_speed = daily["wind"][i]["max"]["speed"]
                    wind_avg_speed = daily["wind"][i]["avg"]["speed"]
                    wind_info = f"💨 风速: 平均{wind_avg_speed}km/h, 最大{wind_max_speed}km/h\n"
                
                # Humidity
                humidity_info = ""
                if "humidity" in daily and i < len(daily["humidity"]):
                    humidity_avg = int(daily["humidity"][i]["avg"] * 100)
                    humidity_info = f"💧 湿度: {humidity_avg}%\n"
                
                # Air quality
                air_quality_info = ""
                if "air_quality" in daily:
                    if "aqi" in daily["air_quality"] and i < len(daily["air_quality"]["aqi"]):
                        aqi_avg = daily["air_quality"]["aqi"][i]["avg"]["chn"]
                        air_quality_info += f"🏭 AQI: {aqi_avg}\n"
                    if "pm25" in daily["air_quality"] and i < len(daily["air_quality"]["pm25"]):
                        pm25_avg = daily["air_quality"]["pm25"][i]["avg"]
                        air_quality_info += f"🏭 PM2.5: {pm25_avg}μg/m³\n"
                
                # Sunrise/sunset
                sun_info = ""
                if "astro" in daily and i < len(daily["astro"]):
                    astro = daily["astro"][i]
                    if "sunrise" in astro and "sunset" in astro:
                        sunrise = astro["sunrise"]["time"] if isinstance(astro["sunrise"], dict) else astro["sunrise"]
                        sunset = astro["sunset"]["time"] if isinstance(astro["sunset"], dict) else astro["sunset"]
                        sun_info = f"🌅 日出: {sunrise} | 🌇 日落: {sunset}\n"
                
                # Life index
                life_info = ""
                if "life_index" in daily:
                    for key, name in [("ultraviolet", "紫外线"), ("carWashing", "洗车"), 
                                     ("dressing", "穿衣"), ("comfort", "舒适度"), ("coldRisk", "感冒")]:
                        if key in daily["life_index"] and i < len(daily["life_index"][key]):
                            desc = daily["life_index"][key][i]["desc"]
                            life_info += f"{name}: {desc} | "
                    if life_info:
                        life_info = f"📋 生活指数: {life_info.rstrip(' | ')}\n"
                
                forecast += f"""📅 {date}
🌡️  温度: {temp_min}°C ~ {temp_max}°C (平均: {temp_avg}°C)
{day_temp}{night_temp}🌦️  全天天气: {skycon}
{day_skycon}{night_skycon}🌧️  降水概率: {rain_prob}% (平均降水量: {precip_avg}mm/h)
{day_precip}{night_precip}{wind_info}{humidity_info}{air_quality_info}{sun_info}{life_info}========================\n\n"""
            
            return forecast
            
    except Exception as e:
        logger.error(f"Error getting daily forecast: {str(e)}")
        raise Exception(f"Failed to get daily forecast: {str(e)}")


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
    hours_back: int = Field(
        description="Number of hours to look back (1-72)",
        ge=1,
        le=72,
        default=24
    ),
) -> str:
    """Get historical weather data including temperature, weather conditions, precipitation and air quality."""
    try:
        token = validate_api_token()
        logger.info(f"Getting historical weather for coordinates: {lng}, {lat}, {hours_back} hours back")
        
        # Calculate timestamp for hours ago
        begin_time = datetime.now() - timedelta(hours=hours_back)
        timestamp = int(begin_time.timestamp())

        async with httpx.AsyncClient() as client:
            result = await make_request(
                client,
                f"https://api.caiyunapp.com/v2.6/{token}/{lng},{lat}/hourly",
                {"hourlysteps": str(hours_back), "begin": str(timestamp), "lang": "zh_CN"},
            )
            
            if "hourly" not in result["result"]:
                return f"❌ 无法获取历史天气数据 (位置: {lng}, {lat})"
            
            hourly = result["result"]["hourly"]
            history = f"📊 过去{hours_back}小时天气历史数据:\n\n"
            
            # Show data in 3-hour intervals for better readability if more than 24 hours
            step = 3 if hours_back > 24 else 2
            
            for i in range(0, len(hourly["temperature"]), step):
                time = hourly["temperature"][i]["datetime"]
                temp = hourly["temperature"][i]["value"]
                skycon = translate_weather_phenomenon(hourly["skycon"][i]["value"])
                
                # Precipitation data
                precip_value = hourly["precipitation"][i].get("value", 0)
                precip_prob = int(hourly["precipitation"][i]["probability"] * 100)
                
                # Wind data
                wind_speed = hourly["wind"][i]["speed"]
                wind_dir = hourly["wind"][i]["direction"]
                
                # Additional data if available
                additional_info = ""
                if "humidity" in hourly and i < len(hourly["humidity"]):
                    humidity = int(hourly["humidity"][i]["value"] * 100)
                    additional_info += f"💧 湿度: {humidity}% | "
                
                if "apparent_temperature" in hourly and i < len(hourly["apparent_temperature"]):
                    feels_like = hourly["apparent_temperature"][i]["value"]
                    additional_info += f"🤔 体感: {feels_like}°C | "
                
                # Air quality if available
                air_info = ""
                if "air_quality" in hourly:
                    if "pm25" in hourly["air_quality"] and i < len(hourly["air_quality"]["pm25"]):
                        pm25 = hourly["air_quality"]["pm25"][i]["value"]
                        air_info += f"🏭 PM2.5: {pm25}μg/m³ | "
                    if "aqi" in hourly["air_quality"] and i < len(hourly["air_quality"]["aqi"]):
                        aqi = hourly["air_quality"]["aqi"][i]["value"]["chn"]
                        air_info += f"📊 AQI: {aqi} | "
                
                if additional_info:
                    additional_info = additional_info.rstrip(" | ")
                if air_info:
                    air_info = air_info.rstrip(" | ")
                
                history += f"""⏰ {time}
🌡️  温度: {temp}°C | 🌦️  天气: {skycon}
💨 风速: {wind_speed}km/h, 风向: {wind_dir}° | 🌧️  降水: {precip_value}mm/h ({precip_prob}%)"""
                
                if additional_info:
                    history += f"\n{additional_info}"
                if air_info:
                    history += f"\n{air_info}"
                
                history += "\n------------------------\n"
            
            return history
            
    except Exception as e:
        logger.error(f"Error getting historical weather: {str(e)}")
        raise Exception(f"Failed to get historical weather: {str(e)}")


@mcp.tool()
async def get_minutely_precipitation(
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
                {"lang": "zh_CN"},
            )
            
            # Check if minutely data is available
            if "minutely" not in result["result"] or result["result"]["minutely"]["status"] != "ok":
                return f"⚠️  分钟级降水数据不可用 (位置: {lng}, {lat})\n此功能主要适用于中国主要城市。"
            
            minutely = result["result"]["minutely"]
            
            # Get summary and datasource
            description = minutely.get("description", "暂无描述")
            datasource = minutely.get("datasource", "未知数据源")
            forecast_keypoint = result["result"].get("forecast_keypoint", "")
            
            forecast = f"🌧️  未来2小时分钟级降水预报:\n"
            forecast += f"📝 预报描述: {description}\n"
            if forecast_keypoint:
                forecast += f"🎯 关键信息: {forecast_keypoint}\n"
            forecast += f"📊 数据源: {datasource}\n\n"
            
            # Show 1-hour precipitation data in 5-minute intervals
            if "precipitation" in minutely and minutely["precipitation"]:
                forecast += "⏰ 未来1小时每5分钟降水强度:\n"
                precipitation_data = minutely["precipitation"]
                for i in range(0, min(60, len(precipitation_data)), 5):
                    time_offset = i
                    intensity = precipitation_data[i] if i < len(precipitation_data) else 0
                    intensity_desc = format_precipitation_intensity(intensity)
                    forecast += f"T+{time_offset:2d}分钟: {intensity_desc}\n"
            
            # Show 2-hour precipitation probability
            if "probability" in minutely and minutely["probability"]:
                forecast += "\n📊 未来2小时降水概率 (每30分钟):\n"
                for i, prob in enumerate(minutely["probability"]):
                    forecast += f"未来{(i+1)*30}分钟: {int(prob * 100)}%\n"
            
            return forecast
            
    except Exception as e:
        logger.error(f"Error getting minute precipitation: {str(e)}")
        return f"⚠️  分钟级降水数据获取失败。此功能主要适用于中国主要城市。\n错误信息: {str(e)}"


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
    include_hourly: bool = Field(
        description="Include 24-hour hourly forecast",
        default=False
    ),
    include_alerts: bool = Field(
        description="Include weather alerts",
        default=True
    ),
) -> str:
    """Get the most comprehensive weather report including all available data: current conditions, forecasts, air quality, alerts, and astronomical data."""
    try:
        token = validate_api_token()
        logger.info(f"Getting comprehensive weather for coordinates: {lng}, {lat}")
        
        async with httpx.AsyncClient() as client:
            # Prepare query parameters
            params = {"dailysteps": "3", "lang": "zh_CN"}
            if include_hourly:
                params["hourlysteps"] = "24"
            if include_alerts:
                params["alert"] = "true"
            
            result = await make_request(
                client,
                f"https://api.caiyunapp.com/v2.6/{token}/{lng},{lat}/weather",
                params,
            )
            
            weather_data = result["result"]
            server_time = datetime.fromtimestamp(result["server_time"]).strftime("%Y-%m-%d %H:%M:%S")
            timezone = result.get("timezone", "未知时区")
            
            report = f"🌍 综合天气报告\n📍 位置: {lng}, {lat}\n⏰ 更新时间: {server_time} ({timezone})\n\n"
            
            # === 实时天气数据 ===
            if "realtime" in weather_data:
                rt = weather_data["realtime"]
                weather_desc = translate_weather_phenomenon(rt["skycon"])
                precip_intensity = format_precipitation_intensity(rt["precipitation"]["local"]["intensity"])
                
                report += f"""🌤️  === 实时天气 ===
🌡️  温度: {rt["temperature"]}°C
🤔 体感温度: {rt.get("apparent_temperature", "N/A")}°C
💧 湿度: {int(rt["humidity"] * 100)}%
☁️  云量: {int(rt["cloudrate"] * 100)}%
🌦️  天气现象: {weather_desc}
👁️  能见度: {rt["visibility"]}km
☀️  辐射通量: {rt["dswrf"]}W/M²
💨 风速: {rt["wind"]["speed"]}m/s, 风向: {rt["wind"]["direction"]}°
📊 气压: {rt["pressure"]}Pa
🌧️  本地降水强度: {precip_intensity}
📍 最近降水距离: {rt["precipitation"]["nearest"]["distance"]/1000:.1f}km
\n"""
                
                # 空气质量
                if "air_quality" in rt:
                    aq = rt["air_quality"]
                    report += f"""🏭 === 空气质量 ===
PM2.5: {aq["pm25"]}μg/m³ | PM10: {aq["pm10"]}μg/m³
臭氧: {aq["o3"]}μg/m³ | 二氧化氮: {aq["no2"]}μg/m³
二氧化硫: {aq["so2"]}μg/m³ | 一氧化碳: {aq["co"]}mg/m³
中国AQI: {aq["aqi"]["chn"]} ({aq["description"]["chn"]})
美国AQI: {aq["aqi"]["usa"]} ({aq["description"]["usa"]})
\n"""
                
                # 生活指数
                if "life_index" in rt:
                    li = rt["life_index"]
                    report += f"""📋 === 生活指数 ===
紫外线: {li["ultraviolet"]["desc"]} (指数: {li["ultraviolet"]["index"]})
舒适度: {li["comfort"]["desc"]} (指数: {li["comfort"]["index"]})
\n"""
            
            # === 分钟级降水预报 ===
            if "minutely" in weather_data and weather_data["minutely"]["status"] == "ok":
                minutely = weather_data["minutely"]
                description = minutely.get("description", "")
                keypoint = weather_data.get("forecast_keypoint", "")
                report += f"""🌧️  === 分钟级降水预报 ===
预报描述: {description}
关键信息: {keypoint}
数据源: {minutely.get("datasource", "雷达数据")}
\n"""
            
            # === 逐小时预报 ===
            if include_hourly and "hourly" in weather_data:
                hourly = weather_data["hourly"]
                report += f"""🕒 === 未来24小时预报 ===
{hourly.get("description", "未来24小时天气预报")}
\n"""
                
                # 显示未来6小时的详细预报
                for i in range(0, min(6, len(hourly["temperature"]))):
                    time = hourly["temperature"][i]["datetime"]
                    temp = hourly["temperature"][i]["value"]
                    skycon = translate_weather_phenomenon(hourly["skycon"][i]["value"])
                    rain_prob = int(hourly["precipitation"][i]["probability"] * 100)
                    wind_speed = hourly["wind"][i]["speed"]
                    
                    report += f"{time}: {temp}°C, {skycon}, 降水概率{rain_prob}%, 风速{wind_speed}km/h\n"
                
                report += "\n"
            
            # === 未来3天预报 ===
            if "daily" in weather_data:
                daily = weather_data["daily"]
                report += "📅 === 未来3天预报 ===\n"
                
                for i in range(min(3, len(daily["temperature"]))):
                    date = daily["temperature"][i]["date"].split("T")[0]
                    temp_max = daily["temperature"][i]["max"]
                    temp_min = daily["temperature"][i]["min"]
                    skycon = translate_weather_phenomenon(daily["skycon"][i]["value"])
                    rain_prob = int(daily["precipitation"][i]["probability"] * 100)
                    
                    # 日出日落时间
                    sun_info = ""
                    if "astro" in daily and i < len(daily["astro"]):
                        astro = daily["astro"][i]
                        if "sunrise" in astro and "sunset" in astro:
                            sunrise = astro["sunrise"]["time"] if isinstance(astro["sunrise"], dict) else astro["sunrise"]
                            sunset = astro["sunset"]["time"] if isinstance(astro["sunset"], dict) else astro["sunset"]
                            sun_info = f" | 日出:{sunrise} 日落:{sunset}"
                    
                    day_name = ["今天", "明天", "后天"][i] if i < 3 else f"第{i+1}天"
                    report += f"{day_name} ({date}): {temp_min}°C~{temp_max}°C, {skycon}, 降水概率{rain_prob}%{sun_info}\n"
                
                report += "\n"
            
            # === 天气预警 ===
            if include_alerts and "alert" in weather_data:
                alert_data = weather_data["alert"]
                alerts = alert_data.get("content", [])
                
                if alerts:
                    report += f"⚠️  === 天气预警 (共{len(alerts)}条) ===\n"
                    for i, alert in enumerate(alerts[:3], 1):  # 显示前3条预警
                        report += f"{i}. {alert.get('title', '未知预警')}: {alert.get('status', '未知状态')}\n"
                    if len(alerts) > 3:
                        report += f"...还有{len(alerts) - 3}条预警\n"
                    report += "\n"
                else:
                    report += "✅ 暂无天气预警\n\n"
            
            report += f"""📊 === 数据来源信息 ===
API版本: {result.get("api_version", "未知")}
API状态: {result.get("api_status", "未知")}
数据单位: {result.get("unit", "metric")}
服务状态: {result.get("status", "未知")}
\n🔄 数据每小时更新，分钟级降水数据实时更新"""
            
            return report
            
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
    days: int = Field(
        description="Number of days to get astronomy info (1-7)",
        ge=1,
        le=7,
        default=7
    ),
) -> str:
    """Get comprehensive astronomy information including sunrise, sunset, moonrise, moonset times and moon phases."""
    try:
        token = validate_api_token()
        logger.info(f"Getting astronomy info for coordinates: {lng}, {lat} for {days} days")
        
        async with httpx.AsyncClient() as client:
            result = await make_request(
                client,
                f"https://api.caiyunapp.com/v2.6/{token}/{lng},{lat}/daily",
                {"dailysteps": str(days), "lang": "zh_CN"},
            )
            daily = result["result"]["daily"]
            
            astro_info = f"🌌 天文信息 (未来{days}天):\n📍 位置: {lng}, {lat}\n\n"
            
            available_days = min(days, len(daily.get("astro", [])))
            if available_days == 0:
                return f"❌ 该位置暂无天文数据 ({lng}, {lat})"
            
            for i in range(available_days):
                date = daily["astro"][i]["date"].split("T")[0]
                astro = daily["astro"][i]
                
                day_name = ["今天", "明天", "后天"][i] if i < 3 else f"第{i+1}天"
                astro_info += f"📅 {day_name} ({date}):\n"
                
                # 日出日落信息
                if "sunrise" in astro and "sunset" in astro:
                    sunrise = astro["sunrise"]["time"] if isinstance(astro["sunrise"], dict) else astro["sunrise"]
                    sunset = astro["sunset"]["time"] if isinstance(astro["sunset"], dict) else astro["sunset"]
                    
                    # 计算日照时长
                    try:
                        from datetime import datetime
                        sunrise_dt = datetime.strptime(sunrise, "%H:%M")
                        sunset_dt = datetime.strptime(sunset, "%H:%M")
                        daylight_duration = sunset_dt - sunrise_dt
                        hours, remainder = divmod(daylight_duration.total_seconds(), 3600)
                        minutes = remainder // 60
                        daylight_info = f" (日照时长: {int(hours)}小时{int(minutes)}分钟)"
                    except:
                        daylight_info = ""
                    
                    astro_info += f"☀️ 日出: {sunrise} | 🌅 日落: {sunset}{daylight_info}\n"
                
                # 月出月落信息 - 可能不是所有地区都有
                moon_info = ""
                if "moonrise" in astro and "moonset" in astro:
                    try:
                        moonrise = astro["moonrise"]["time"] if isinstance(astro["moonrise"], dict) else astro["moonrise"]
                        moonset = astro["moonset"]["time"] if isinstance(astro["moonset"], dict) else astro["moonset"]
                        moon_info = f"🌙 月出: {moonrise} | 🌛 月落: {moonset}\n"
                    except:
                        moon_info = "🌙 月出月落: 数据不可用\n"
                else:
                    moon_info = "🌙 月出月落: 数据不可用\n"
                
                astro_info += moon_info
                
                # 月相信息
                if "moon_phase" in astro:
                    moon_phase = astro["moon_phase"]
                    phase_names = {
                        "new": "新月 🌑",
                        "waxing_crescent": "蛾眉月(上弦) 🌒", 
                        "first_quarter": "上弦月 🌓",
                        "waxing_gibbous": "盈凸月 🌔",
                        "full": "满月 🌕",
                        "waning_gibbous": "亏凸月 🌖",
                        "last_quarter": "下弦月 🌗",
                        "waning_crescent": "蛾眉月(下弦) 🌘"
                    }
                    phase_name = phase_names.get(moon_phase, f"未知月相 ({moon_phase})")
                    astro_info += f"🌙 月相: {phase_name}\n"
                
                # 如果有额外的天文数据
                if "moon_illumination" in astro:
                    illumination = astro["moon_illumination"]
                    astro_info += f"🌙 月亮照度: {illumination:.1%}\n"
                
                astro_info += "========================\n"
            
            # 添加天文小贴士
            astro_info += f"""\n📖 天文小贴士:
• 日出日落时间因地理位置和季节而异
• 月出月落时间每天推迟约50分钟
• 满月时月出约在日落时，新月时月出约在日出时
• 观星最佳时间通常是月落后到日出前的时段"""
            
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
                {"alert": "true", "lang": "zh_CN"},
            )
            
            alert_data = result["result"].get("alert", {})
            alerts = alert_data.get("content", [])
            adcodes = alert_data.get("adcodes", [])
            
            if not alerts:
                location_info = ""
                if adcodes:
                    locations = " → ".join([area["name"] for area in adcodes])
                    location_info = f" (区域: {locations})"
                return f"✅ 暂无生效的天气预警{location_info}"

            alert_text = f"⚠️  天气预警信息 (共{len(alerts)}条):\n\n"
            
            # Show area coverage
            if adcodes:
                locations = " → ".join([area["name"] for area in adcodes])
                alert_text += f"📍 覆盖区域: {locations}\n\n"
            
            for i, alert in enumerate(alerts, 1):
                # Parse publication time
                pub_time = ""
                if "pubtimestamp" in alert:
                    try:
                        pub_dt = datetime.fromtimestamp(alert["pubtimestamp"])
                        pub_time = pub_dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        pub_time = "未知时间"
                
                alert_text += f"""🚨 预警 {i}:
📢 标题: {alert.get("title", "未知预警")}
📝 状态: {alert.get("status", "未知状态")}
🏷️  代码: {alert.get("code", "N/A")}
📍 发布机构: {alert.get("source", "未知机构")}
🌍 地区: {alert.get("location", "未知地区")}
⏰ 发布时间: {pub_time}
📄 详细描述:
{alert.get("description", "暂无详细描述")}
========================\n\n"""
            
            return alert_text
            
    except Exception as e:
        logger.error(f"Error getting weather alerts: {str(e)}")
        raise Exception(f"Failed to get weather alerts: {str(e)}")


def main():
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()