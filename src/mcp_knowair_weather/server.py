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

def format_precipitation_intensity(intensity: float, data_type: str = "radar") -> str:
    """Format precipitation intensity with proper description based on data type."""
    if data_type == "radar":
        # 雷达降水强度 (0-1 范围)
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
    elif data_type == "hourly":
        # 逐小时降水量 mm/h
        if intensity < 0.0606:
            return f"{intensity:.2f}mm/h (无雨/雪)"
        elif intensity < 0.8989:
            return f"{intensity:.2f}mm/h (小雨/雪)"
        elif intensity < 2.87:
            return f"{intensity:.2f}mm/h (中雨/雪)"
        elif intensity < 12.8638:
            return f"{intensity:.2f}mm/h (大雨/雪)"
        else:
            return f"{intensity:.2f}mm/h (暴雨/雪)"
    elif data_type == "minutely":
        # 分钟级降水量 mm/h
        if intensity < 0.08:
            return f"{intensity:.2f}mm/h (无雨/雪)"
        elif intensity < 3.44:
            return f"{intensity:.2f}mm/h (小雨/雪)"
        elif intensity < 11.33:
            return f"{intensity:.2f}mm/h (中雨/雪)"
        elif intensity < 51.30:
            return f"{intensity:.2f}mm/h (大雨/雪)"
        else:
            return f"{intensity:.2f}mm/h (暴雨/雪)"
    else:
        return f"{intensity:.3f}"

def get_life_index_description(index_type: str, level: int) -> str:
    """Get life index description in Chinese."""
    descriptions = {
        "ultraviolet": {
            0: "无", 1: "很弱", 2: "很弱", 3: "弱", 4: "弱", 5: "中等",
            6: "中等", 7: "强", 8: "强", 9: "强", 10: "很强", 11: "极强"
        },
        "ultraviolet_daily": {
            1: "最弱", 2: "弱", 3: "中等", 4: "强", 5: "很强"
        },
        "dressing": {
            0: "极热", 1: "极热", 2: "很热", 3: "热", 4: "温暖",
            5: "凉爽", 6: "冷", 7: "寒冷", 8: "极冷"
        },
        "comfort": {
            0: "闷热", 1: "酷热", 2: "很热", 3: "热", 4: "温暖",
            5: "舒适", 6: "凉爽", 7: "冷", 8: "很冷", 9: "寒冷",
            10: "极冷", 11: "刺骨的冷", 12: "湿冷", 13: "干冷"
        },
        "coldRisk": {
            1: "少发", 2: "较易发", 3: "易发", 4: "极易发"
        },
        "carWashing": {
            1: "适宜", 2: "较适宜", 3: "较不适宜", 4: "不适宜"
        }
    }
    
    if index_type in descriptions:
        return descriptions[index_type].get(level, f"未知等级({level})")
    return f"未知指数({index_type}: {level})"


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
            precip_intensity = format_precipitation_intensity(rt["precipitation"]["local"]["intensity"], "radar")
            
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
🌧️  降水强度: {precip_intensity} (雷达数据)
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

📋 生活指数:"""
            
            # Enhanced life index
            if "life_index" in rt:
                for key, name, emoji in [("ultraviolet", "紫外线", "☀️"), ("comfort", "舒适度", "🌡️")]:
                    if key in rt["life_index"]:
                        index_value = rt["life_index"][key]["index"]
                        desc = rt["life_index"][key]["desc"]
                        
                        # 尝试用标准描述替代API描述
                        if key == "ultraviolet":
                            try:
                                uv_level = int(float(index_value))
                                standard_desc = get_life_index_description("ultraviolet", uv_level)
                                if standard_desc != f"未知等级({uv_level})":
                                    desc = standard_desc
                            except:
                                pass
                        elif key == "comfort":
                            try:
                                comfort_level = int(index_value)
                                standard_desc = get_life_index_description("comfort", comfort_level)
                                if standard_desc != f"未知等级({comfort_level})":
                                    desc = standard_desc
                            except:
                                pass
                        
                        report += f"\n    {emoji} {name}: {desc} (等级: {index_value})"
            else:
                report += "\n    暂无生活指数数据"
            
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
            
            # Air quality trend analysis (if available)
            air_quality_trend = ""
            if "air_quality" in hourly and "aqi" in hourly["air_quality"]:
                aqi_values = []
                pm25_values = []
                for data in hourly["air_quality"]["aqi"][:min(hours, len(hourly["air_quality"]["aqi"]))]:
                    aqi_values.append(data["value"]["chn"])
                if "pm25" in hourly["air_quality"]:
                    for data in hourly["air_quality"]["pm25"][:min(hours, len(hourly["air_quality"]["pm25"]))]:
                        pm25_values.append(data["value"])
                
                if len(aqi_values) >= 2:
                    aqi_start = aqi_values[0]
                    aqi_end = aqi_values[-1]
                    aqi_change = aqi_end - aqi_start
                    
                    if aqi_change > 10:
                        trend_desc = "📈 空气质量趋势：恶化"
                    elif aqi_change < -10:
                        trend_desc = "📉 空气质量趋势：改善"
                    else:
                        trend_desc = "➡️ 空气质量趋势：稳定"
                    
                    air_quality_trend = f"{trend_desc} (AQI: {aqi_start}→{aqi_end})\n"
                    
                    if pm25_values and len(pm25_values) >= 2:
                        pm25_change = pm25_values[-1] - pm25_values[0]
                        air_quality_trend += f"PM2.5变化: {pm25_values[0]}→{pm25_values[-1]}μg/m³\n"
                    
                    air_quality_trend += "\n"
            
            if air_quality_trend:
                forecast += f"🏭 === 空气质量趋势 ===\n{air_quality_trend}"
            
            # Show every 3 hours for better readability if more than 24 hours
            step = 3 if hours > 24 else 1
            
            for i in range(0, min(hours, len(hourly["temperature"])), step):
                time = hourly["temperature"][i]["datetime"]
                temp = hourly["temperature"][i]["value"]
                skycon = translate_weather_phenomenon(hourly["skycon"][i]["value"])
                
                # Precipitation data
                rain_prob = int(hourly["precipitation"][i]["probability"] * 100)
                precip_value = hourly["precipitation"][i].get("value", 0)
                precip_desc = format_precipitation_intensity(precip_value, "hourly")
                
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
                    # Helper functions for air quality levels
                    def get_aqi_icon(aqi):
                        if aqi <= 50: return "🟢"
                        elif aqi <= 100: return "🟡"
                        elif aqi <= 150: return "🟠"
                        elif aqi <= 200: return "🔴"
                        elif aqi <= 300: return "🟣"
                        else: return "⚫"
                    
                    def get_pm25_icon(pm25):
                        if pm25 <= 35: return "🟢"
                        elif pm25 <= 75: return "🟡"
                        elif pm25 <= 115: return "🟠"
                        elif pm25 <= 150: return "🔴"
                        elif pm25 <= 250: return "🟣"
                        else: return "⚫"
                    
                    # AQI information
                    if "aqi" in hourly["air_quality"] and i < len(hourly["air_quality"]["aqi"]):
                        aqi_data = hourly["air_quality"]["aqi"][i]["value"]
                        chn_aqi = aqi_data["chn"]
                        usa_aqi = aqi_data.get("usa", "N/A")
                        aqi_icon = get_aqi_icon(chn_aqi)
                        air_quality_info += f"{aqi_icon} AQI: {chn_aqi} (美标:{usa_aqi})\n"
                    
                    # PM2.5 information
                    if "pm25" in hourly["air_quality"] and i < len(hourly["air_quality"]["pm25"]):
                        pm25 = hourly["air_quality"]["pm25"][i]["value"]
                        pm25_icon = get_pm25_icon(pm25)
                        air_quality_info += f"{pm25_icon} PM2.5: {pm25}μg/m³\n"
                    
                    # Additional pollutants
                    if "pm10" in hourly["air_quality"] and i < len(hourly["air_quality"]["pm10"]):
                        pm10 = hourly["air_quality"]["pm10"][i]["value"]
                        air_quality_info += f"🌫️ PM10: {pm10}μg/m³\n"
                    
                    if "o3" in hourly["air_quality"] and i < len(hourly["air_quality"]["o3"]):
                        o3 = hourly["air_quality"]["o3"][i]["value"]
                        air_quality_info += f"💨 臭氧: {o3}μg/m³\n"
                    
                    if "no2" in hourly["air_quality"] and i < len(hourly["air_quality"]["no2"]):
                        no2 = hourly["air_quality"]["no2"][i]["value"]
                        air_quality_info += f"🌬️ NO2: {no2}μg/m³\n"
                    
                    if "so2" in hourly["air_quality"] and i < len(hourly["air_quality"]["so2"]):
                        so2 = hourly["air_quality"]["so2"][i]["value"]
                        air_quality_info += f"☁️ SO2: {so2}μg/m³\n"
                    
                    if "co" in hourly["air_quality"] and i < len(hourly["air_quality"]["co"]):
                        co = hourly["air_quality"]["co"][i]["value"]
                        air_quality_info += f"💨 CO: {co}mg/m³\n"
                
                forecast += f"""⏰ {time}
🌡️  温度: {temp}°C
{apparent_temp}🌦️  天气: {skycon}
🌧️  降水概率: {rain_prob}%
💧 降水量: {precip_desc}
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
                
                # Life index with enhanced descriptions
                life_info = ""
                if "life_index" in daily:
                    life_items = []
                    for key, name, emoji in [("ultraviolet", "紫外线", "☀️"), ("carWashing", "洗车", "🚗"), 
                                           ("dressing", "穿衣", "👕"), ("comfort", "舒适度", "🌡️"), ("coldRisk", "感冒", "🤧")]:
                        if key in daily["life_index"] and i < len(daily["life_index"][key]):
                            data = daily["life_index"][key][i]
                            desc = data["desc"]
                            
                            # Try to use standard descriptions
                            if "index" in data:
                                try:
                                    level = int(data["index"])
                                    if key == "ultraviolet":
                                        standard_desc = get_life_index_description("ultraviolet_daily", level)
                                    else:
                                        standard_desc = get_life_index_description(key, level)
                                    
                                    if standard_desc != f"未知等级({level})" and standard_desc != f"未知指数({key}: {level})":
                                        desc = standard_desc
                                except:
                                    pass
                            
                            life_items.append(f"{emoji}{name}:{desc}")
                    
                    if life_items:
                        life_info = f"📋 生活指数: {' | '.join(life_items)}\n"
                
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
                    intensity_desc = format_precipitation_intensity(intensity, "minutely")
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
async def get_air_quality_forecast(
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
        description="Number of days to forecast air quality (1-7)",
        ge=1,
        le=7,
        default=7
    ),
) -> str:
    """Get comprehensive air quality forecast including PM2.5, PM10, AQI trends and health recommendations for the next 1-7 days."""
    try:
        token = validate_api_token()
        logger.info(f"Getting air quality forecast for coordinates: {lng}, {lat} for {days} days")
        
        async with httpx.AsyncClient() as client:
            # Get both current air quality and forecast
            current_result = await make_request(
                client,
                f"https://api.caiyunapp.com/v2.6/{token}/{lng},{lat}/realtime",
                {"lang": "zh_CN"},
            )
            
            forecast_result = await make_request(
                client,
                f"https://api.caiyunapp.com/v2.6/{token}/{lng},{lat}/daily",
                {"dailysteps": str(days), "lang": "zh_CN"},
            )
            
            current_air = current_result["result"]["realtime"]["air_quality"]
            daily = forecast_result["result"]["daily"]
            
            def get_aqi_level_description(aqi):
                """Get AQI level description in Chinese"""
                if aqi <= 50:
                    return "优", "空气质量令人满意，基本无空气污染", "🟢"
                elif aqi <= 100:
                    return "良", "空气质量可接受，但某些污染物可能对极少数异常敏感人群健康有较弱影响", "🟡"
                elif aqi <= 150:
                    return "轻度污染", "易感人群症状有轻度加剧，健康人群出现刺激症状", "🟠"
                elif aqi <= 200:
                    return "中度污染", "进一步加剧易感人群症状，可能对健康人群心脏、呼吸系统有影响", "🔴"
                elif aqi <= 300:
                    return "重度污染", "心脏病和肺病患者症状显著加剧，运动耐受力降低，健康人群普遍出现症状", "🟣"
                else:
                    return "严重污染", "健康人群运动耐受力降低，有明显强烈症状，提前出现某些疾病", "⚫"
            
            def get_pm25_level(pm25):
                """Get PM2.5 level description"""
                if pm25 <= 35:
                    return "优秀", "🟢"
                elif pm25 <= 75:
                    return "良好", "🟡"
                elif pm25 <= 115:
                    return "轻度污染", "🟠"
                elif pm25 <= 150:
                    return "中度污染", "🔴"
                elif pm25 <= 250:
                    return "重度污染", "🟣"
                else:
                    return "严重污染", "⚫"
            
            report = f"🏭 空气质量预报 (未来{days}天)\n📍 位置: {lng}, {lat}\n\n"
            
            # Current air quality
            current_aqi = current_air["aqi"]["chn"]
            current_pm25 = current_air["pm25"]
            current_level, current_desc, current_icon = get_aqi_level_description(current_aqi)
            pm25_level, pm25_icon = get_pm25_level(current_pm25)
            
            report += f"""🔄 当前空气质量 (实时):
{current_icon} AQI: {current_aqi} ({current_level})
{pm25_icon} PM2.5: {current_pm25}μg/m³ ({pm25_level})
📊 完整数据:
    PM10: {current_air["pm10"]}μg/m³
    臭氧: {current_air["o3"]}μg/m³  
    二氧化硫: {current_air["so2"]}μg/m³
    二氧化氮: {current_air["no2"]}μg/m³
    一氧化碳: {current_air["co"]}mg/m³
💡 健康建议: {current_desc}

"""
            
            # Daily air quality forecast
            if "air_quality" in daily:
                report += "📅 === 未来空气质量预报 ===\n\n"
                
                # Track trends
                aqi_trend = []
                pm25_trend = []
                
                for i in range(min(days, len(daily["air_quality"]["aqi"]))):
                    date = daily["air_quality"]["aqi"][i]["date"].split("T")[0]
                    
                    # AQI data
                    aqi_data = daily["air_quality"]["aqi"][i]
                    aqi_avg = aqi_data["avg"]["chn"]
                    aqi_max = aqi_data["max"]["chn"] 
                    aqi_min = aqi_data["min"]["chn"]
                    
                    # PM2.5 data
                    pm25_data = daily["air_quality"]["pm25"][i] if "pm25" in daily["air_quality"] and i < len(daily["air_quality"]["pm25"]) else None
                    
                    level, desc, icon = get_aqi_level_description(aqi_avg)
                    day_name = ["今天", "明天", "后天"][i] if i < 3 else f"第{i+1}天"
                    
                    report += f"""{icon} {day_name} ({date}):
📊 AQI: 平均{aqi_avg} (范围: {aqi_min}~{aqi_max}) - {level}
"""
                    
                    if pm25_data:
                        pm25_avg = pm25_data["avg"]
                        pm25_max = pm25_data["max"]
                        pm25_min = pm25_data["min"]
                        pm25_level, pm25_icon = get_pm25_level(pm25_avg)
                        report += f"{pm25_icon} PM2.5: 平均{pm25_avg}μg/m³ (范围: {pm25_min}~{pm25_max}μg/m³) - {pm25_level}\n"
                    
                    # Additional pollutants if available
                    if "pm10" in daily["air_quality"] and i < len(daily["air_quality"]["pm10"]):
                        pm10_avg = daily["air_quality"]["pm10"][i]["avg"]
                        report += f"🌫️ PM10: {pm10_avg}μg/m³\n"
                    
                    if "o3" in daily["air_quality"] and i < len(daily["air_quality"]["o3"]):
                        o3_avg = daily["air_quality"]["o3"][i]["avg"]  
                        report += f"💨 臭氧: {o3_avg}μg/m³\n"
                    
                    report += f"💡 健康建议: {desc}\n"
                    report += "------------------------\n"
                    
                    # Collect trend data
                    aqi_trend.append(aqi_avg)
                    if pm25_data:
                        pm25_trend.append(pm25_avg)
                
                # Trend analysis
                report += "\n📈 === 趋势分析 ===\n"
                
                if len(aqi_trend) >= 2:
                    aqi_change = aqi_trend[-1] - aqi_trend[0]
                    if aqi_change > 10:
                        trend_desc = "📈 空气质量呈恶化趋势"
                    elif aqi_change < -10:
                        trend_desc = "📉 空气质量呈改善趋势"
                    else:
                        trend_desc = "➡️ 空气质量相对稳定"
                    
                    report += f"AQI变化: {aqi_trend[0]} → {aqi_trend[-1]} ({trend_desc})\n"
                
                if len(pm25_trend) >= 2:
                    pm25_change = pm25_trend[-1] - pm25_trend[0]
                    if pm25_change > 5:
                        pm25_trend_desc = "📈 PM2.5浓度上升"
                    elif pm25_change < -5:
                        pm25_trend_desc = "📉 PM2.5浓度下降"
                    else:
                        pm25_trend_desc = "➡️ PM2.5浓度稳定"
                    
                    report += f"PM2.5变化: {pm25_trend[0]} → {pm25_trend[-1]}μg/m³ ({pm25_trend_desc})\n"
                
                # Best and worst days
                if len(aqi_trend) > 1:
                    best_day_idx = aqi_trend.index(min(aqi_trend))
                    worst_day_idx = aqi_trend.index(max(aqi_trend))
                    
                    best_day_name = ["今天", "明天", "后天"][best_day_idx] if best_day_idx < 3 else f"第{best_day_idx+1}天"
                    worst_day_name = ["今天", "明天", "后天"][worst_day_idx] if worst_day_idx < 3 else f"第{worst_day_idx+1}天"
                    
                    report += f"\n🌟 空气质量最好: {best_day_name} (AQI: {min(aqi_trend)})\n"
                    report += f"⚠️ 空气质量最差: {worst_day_name} (AQI: {max(aqi_trend)})\n"
                
                # Health recommendations
                avg_aqi = sum(aqi_trend) / len(aqi_trend) if aqi_trend else current_aqi
                report += f"\n🏥 === 一周健康建议 ===\n"
                report += f"平均AQI: {avg_aqi:.0f}\n"
                
                if avg_aqi <= 50:
                    report += "✅ 空气质量优良，适合各类户外活动\n"
                elif avg_aqi <= 100:
                    report += "⚠️ 总体空气质量可接受，敏感人群应适当减少户外运动\n"
                elif avg_aqi <= 150:
                    report += "🚫 空气轻度污染，建议减少户外活动，敏感人群避免户外运动\n"
                elif avg_aqi <= 200:
                    report += "🚫 空气中度污染，建议避免户外运动，外出时佩戴口罩\n"
                else:
                    report += "🚨 空气重度污染，建议尽量待在室内，必要时使用空气净化器\n"
                
            else:
                report += "⚠️ 未来空气质量预报数据不可用\n"
            
            return report
            
    except Exception as e:
        logger.error(f"Error getting air quality forecast: {str(e)}")
        raise Exception(f"Failed to get air quality forecast: {str(e)}")


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