"""Utility functions for weather data processing."""

import math
import httpx
from typing import Dict, Any, Optional, Tuple, Union
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)


def translate_weather_phenomenon(skycon: str) -> str:
    """Translate weather phenomenon code to Chinese description."""
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
    return WEATHER_PHENOMENA.get(skycon, skycon)


def get_precipitation_type(temperature: float = None) -> str:
    """根据温度判断降水类型（雨或雪）"""
    if temperature is None:
        return "雨/雪"  # 温度未知时保持原样
    elif temperature > 0:
        return "雨"
    else:
        return "雪"


def format_precipitation_intensity(intensity: float, data_type: str = "radar", temperature: float = None) -> str:
    """Format precipitation intensity with proper description based on data type.
    
    Args:
        intensity: 降水强度值
        data_type: 数据类型（radar, hourly, minutely, daily等）
        temperature: 温度（摄氏度），用于判断雨雪类型，>0为雨，≤0为雪
    
    综合优化降水强度分级标准：
    - 融合API官方、中国气象标准和实际体感
    - 雷达数据保持API原始标准以确保兼容性
    - mm/h数据采用优化标准，更符合实际感受
    - 根据温度自动判断雨雪类型
    
    雷达降水强度 (0-1 范围) - API官方标准:
    - < 0.031: 无降水
    - 0.031~0.25: 小雨/雪  
    - 0.25~0.35: 中雨/雪
    - 0.35~0.48: 大雨/雪
    - >= 0.48: 暴雨/雪
    
    官方mm/h分级标准 (逐小时预报):
    - < 0.0606: 无降水
    - 0.0606~0.8989: 小雨/雪
    - 0.8989~2.8700: 中雨/雪
    - 2.8700~12.8638: 大雨/雪
    - >= 12.8638: 暴雨/雪
    
    官方mm/h分级标准 (分钟级预报):
    - < 0.08: 无降水
    - 0.08~3.44: 小雨/雪
    - 3.44~11.33: 中雨/雪
    - 11.33~51.30: 大雨/雪
    - >= 51.30: 暴雨/雪
    """
    precip_type = get_precipitation_type(temperature)
    if data_type == "radar":
        # 雷达降水强度 (0-1 范围) - 保持API官方标准以确保兼容性
        if intensity < 0.031:
            return f"{intensity:.3f} (无{precip_type})"
        elif intensity < 0.25:
            return f"{intensity:.3f} (小{precip_type})"
        elif intensity < 0.35:
            return f"{intensity:.3f} (中{precip_type})"
        elif intensity < 0.48:
            return f"{intensity:.3f} (大{precip_type})"
        else:
            return f"{intensity:.3f} (暴{precip_type})"
    elif data_type == "hourly":
        # 逐小时预报降水量 - 使用官方mm/h分级标准
        if intensity < 0.0606:
            return f"{intensity:.4f}mm/h (无{precip_type})"
        elif intensity < 0.8989:
            return f"{intensity:.4f}mm/h (小{precip_type})"
        elif intensity < 2.8700:
            return f"{intensity:.4f}mm/h (中{precip_type})"
        elif intensity < 12.8638:
            return f"{intensity:.4f}mm/h (大{precip_type})"
        else:
            return f"{intensity:.4f}mm/h (暴{precip_type})"
    elif data_type == "hourly_radar":
        # 逐小时预报降水量 - unit=metric:v1时的雷达强度格式
        if intensity < 0.031:
            return f"{intensity:.3f} (无{precip_type})"
        elif intensity < 0.25:
            return f"{intensity:.3f} (小{precip_type})"
        elif intensity < 0.35:
            return f"{intensity:.3f} (中{precip_type})"
        elif intensity < 0.48:
            return f"{intensity:.3f} (大{precip_type})"
        else:
            return f"{intensity:.3f} (暴{precip_type})"
    elif data_type == "minutely":
        # 分钟级降水短临预报 - 默认返回雷达降水强度（0-1），使用API官方标准
        if intensity < 0.031:
            return f"{intensity:.3f} (无{precip_type})"
        elif intensity < 0.25:
            return f"{intensity:.3f} (小{precip_type})"
        elif intensity < 0.35:
            return f"{intensity:.3f} (中{precip_type})"
        elif intensity < 0.48:
            return f"{intensity:.3f} (大{precip_type})"
        else:
            return f"{intensity:.3f} (暴{precip_type})"
    elif data_type == "minutely_mm":
        # 分钟级预报 - unit=metric:v2时的mm/h格式，使用官方分钟级mm/h分级标准
        if intensity < 0.08:
            return f"{intensity:.2f}mm/h (无{precip_type})"
        elif intensity < 3.44:
            return f"{intensity:.2f}mm/h (小{precip_type})"
        elif intensity < 11.33:
            return f"{intensity:.2f}mm/h (中{precip_type})"
        elif intensity < 51.30:
            return f"{intensity:.2f}mm/h (大{precip_type})"
        else:
            return f"{intensity:.2f}mm/h (暴{precip_type})"
    elif data_type == "daily":
        # 逐日预报降水量 - 注意：应使用avg*2再用逐小时阈值判断
        # 这里假设传入的intensity已经是处理过的值
        if intensity < 0.0606:
            return f"{intensity:.4f}mm/h (无{precip_type})"
        elif intensity < 0.8989:
            return f"{intensity:.4f}mm/h (小{precip_type})"
        elif intensity < 2.8700:
            return f"{intensity:.4f}mm/h (中{precip_type})"
        elif intensity < 12.8638:
            return f"{intensity:.4f}mm/h (大{precip_type})"
        else:
            return f"{intensity:.4f}mm/h (暴{precip_type})"
    elif data_type == "daily_radar":
        # 逐日预报降水量 - unit=metric:v1时的雷达强度格式
        if intensity < 0.031:
            return f"{intensity:.3f} (无{precip_type})"
        elif intensity < 0.25:
            return f"{intensity:.3f} (小{precip_type})"
        elif intensity < 0.35:
            return f"{intensity:.3f} (中{precip_type})"
        elif intensity < 0.48:
            return f"{intensity:.3f} (大{precip_type})"
        else:
            return f"{intensity:.3f} (暴{precip_type})"
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


def get_aqi_level_description(aqi: int) -> tuple[str, str, str]:
    """Get AQI level description with icon."""
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


def get_pm25_level_description(pm25: int) -> tuple[str, str]:
    """Get PM2.5 level description with icon."""
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


def safe_precipitation_probability(probability) -> int:
    """Safely convert precipitation probability to percentage."""
    # Handle None or invalid data
    if probability is None:
        return 0
    
    try:
        prob_float = float(probability)
    except (ValueError, TypeError):
        return 0
    
    # Handle different API response formats
    if prob_float <= 1.0:
        # Probability is in 0-1 range, convert to percentage
        return int(prob_float * 100)
    elif prob_float <= 100.0:
        # Probability is already in percentage
        return int(prob_float)
    else:
        # Invalid data, cap at 100%
        return 100


def format_air_quality_data(air_quality_data: Dict[str, Any], data_type: str = "realtime") -> str:
    """Format air quality data into a consistent string format.
    
    Args:
        air_quality_data: Air quality data dictionary
        data_type: Type of data ("realtime", "hourly", "daily")
    
    Returns:
        Formatted air quality string
    """
    if not air_quality_data:
        return ""
    
    air_info = ""
    
    # AQI information
    if "aqi" in air_quality_data:
        aqi_data = air_quality_data["aqi"]
        if isinstance(aqi_data, dict):
            chn_aqi = aqi_data.get("chn", "N/A")
            usa_aqi = aqi_data.get("usa", "N/A")
            level, desc, icon = get_aqi_level_description(chn_aqi)
            air_info += f"{icon} AQI: {chn_aqi} (美标:{usa_aqi})\n"
        else:
            air_info += f"🏭 AQI: {aqi_data}\n"
    
    # PM2.5 information
    if "pm25" in air_quality_data:
        pm25 = air_quality_data["pm25"]
        level, icon = get_pm25_level_description(pm25)
        air_info += f"{icon} PM2.5: {pm25}μg/m³\n"
    
    # PM10 information
    if "pm10" in air_quality_data:
        pm10 = air_quality_data["pm10"]
        air_info += f"🌫️ PM10: {pm10}μg/m³\n"
    
    # O3 information
    if "o3" in air_quality_data:
        o3 = air_quality_data["o3"]
        air_info += f"💨 臭氧: {o3}μg/m³\n"
    
    # Additional pollutants
    pollutants = [
        ("no2", "🌬️ NO2", "μg/m³"),
        ("so2", "☁️ SO2", "μg/m³"),
        ("co", "💨 CO", "mg/m³")
    ]
    
    for pollutant, icon, unit in pollutants:
        if pollutant in air_quality_data:
            value = air_quality_data[pollutant]
            air_info += f"{icon}: {value}{unit}\n"
    
    return air_info


def get_air_quality_summary(air_quality_data: Dict[str, Any]) -> str:
    """Get a concise air quality summary for display in compact formats."""
    if not air_quality_data:
        return ""
    
    summary_parts = []
    
    if "aqi" in air_quality_data:
        aqi_data = air_quality_data["aqi"]
        if isinstance(aqi_data, dict):
            chn_aqi = aqi_data.get("chn", "N/A")
            summary_parts.append(f"AQI:{chn_aqi}")
        else:
            summary_parts.append(f"AQI:{aqi_data}")
    
    for pollutant in ["pm25", "pm10", "o3"]:
        if pollutant in air_quality_data:
            value = air_quality_data[pollutant]
            unit = "μg/m³"
            summary_parts.append(f"{pollutant.upper()}:{value}{unit}")
    
    return " ".join(summary_parts)


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two coordinates in km using Haversine formula."""
    R = 6371  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def handle_detail_level_parameter(detail_level: Any) -> int:
    """Handle potential FastMCP parameter issue for detail_level parameter."""
    if hasattr(detail_level, 'default'):
        return detail_level.default
    elif not isinstance(detail_level, int):
        return 0  # fallback to auto-select
    return detail_level


def get_display_interval(hours: int, detail_level: int) -> Tuple[int, str]:
    """
    Determine display interval and description based on forecast duration and user preference.
    
    Args:
        hours: Number of hours to forecast
        detail_level: User preference (0=auto-select, 1=hourly, 2=every 2h, etc.)
    
    Returns:
        Tuple of (step_size, description)
    """
    if detail_level == 0:
        # Auto-select based on forecast duration
        if hours <= 12:
            step = 1  # Every hour for short forecasts
        elif hours <= 48:
            step = 2  # Every 2 hours for 1-2 day forecasts
        elif hours <= 120:
            step = 3  # Every 3 hours for up to 5 days
        else:
            step = 6  # Every 6 hours for long forecasts
    else:
        # Use user-specified detail level
        step = detail_level
    
    # Generate description
    if step == 1:
        description = "每小时"
    else:
        description = f"每{step}小时"
    
    return step, description


async def fetch_station_data(client: httpx.AsyncClient, token: str, lng: float, lat: float, hours: int) -> Optional[Dict[str, Any]]:
    """
    Fetch station air quality data with proper error handling.
    
    Returns None if station data is not available.
    """
    try:
        from .server import make_request  # Import here to avoid circular import
        return await make_request(
            client,
            "https://singer.caiyunhub.com/v3/aqi/forecast/station",
            {
                "token": token,
                "longitude": lng,
                "latitude": lat,
                "hours": str(hours)
            },
        )
    except Exception as e:
        logger.warning(f"Station data not available: {str(e)}")
        return None


def process_station_daily_data(station_result: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, list]], str]:
    """
    Process station result into daily aggregated data.
    
    Returns:
        Tuple of (daily_data_dict, station_info_string)
    """
    station_daily_data = {}
    station_info = ""
    
    if station_result and "data" in station_result and station_result["data"]:
        # Group station data by day for easier access
        station_forecast = station_result["data"][0]["data"]  # Use nearest station
        station_id = station_result["data"][0]["station_id"]
        station_info = f"💡 PM10和O3数据来自监测站: {station_id}\n\n"
        
        for data_point in station_forecast:
            day_key = data_point["date"][:10]  # Extract date (YYYY-MM-DD)
            if day_key not in station_daily_data:
                station_daily_data[day_key] = {
                    "pm10_values": [],
                    "o3_values": [],
                    "pm25_values": [],
                    "aqi_values": []
                }
            station_daily_data[day_key]["pm10_values"].append(data_point["pm10"])
            station_daily_data[day_key]["o3_values"].append(data_point["o3"])
            station_daily_data[day_key]["pm25_values"].append(data_point["pm25"])
            station_daily_data[day_key]["aqi_values"].append(data_point["aqi"])
    
    return station_daily_data, station_info


def convert_utc_to_china_time(utc_datetime_str: str) -> str:
    """
    Convert UTC datetime string to China Standard Time (UTC+8).
    
    Args:
        utc_datetime_str: UTC datetime string in ISO format
        
    Returns:
        China time string in format "YYYY-MM-DD HH:MM+08:00"
    """
    try:
        # Parse UTC datetime string
        if utc_datetime_str.endswith('Z'):
            # Replace Z with +00:00 for proper parsing
            utc_datetime_str = utc_datetime_str.replace('Z', '+00:00')
        elif not ('+' in utc_datetime_str or utc_datetime_str.endswith('Z')):
            # Assume UTC if no timezone info
            utc_datetime_str += '+00:00'
            
        dt_utc = datetime.fromisoformat(utc_datetime_str)
        
        # Convert to China Standard Time (UTC+8)
        china_tz = timezone(timedelta(hours=8))
        dt_china = dt_utc.astimezone(china_tz)
        
        # Format as YYYY-MM-DD HH:MM+08:00
        return dt_china.strftime('%Y-%m-%d %H:%M+08:00')
        
    except (ValueError, TypeError) as e:
        # Fallback: return original string if conversion fails
        logger.warning(f"Failed to convert UTC time '{utc_datetime_str}': {e}")
        return utc_datetime_str


def utc_timestamp_to_china_time(timestamp: int) -> str:
    """
    Convert UTC timestamp to China Standard Time string.
    
    Args:
        timestamp: UTC timestamp (seconds since epoch)
        
    Returns:
        China time string in format "YYYY-MM-DD HH:MM+08:00"
    """
    try:
        # Create datetime from timestamp (assumes UTC)
        dt_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        
        # Convert to China Standard Time (UTC+8)
        china_tz = timezone(timedelta(hours=8))
        dt_china = dt_utc.astimezone(china_tz)
        
        # Format as YYYY-MM-DD HH:MM+08:00
        return dt_china.strftime('%Y-%m-%d %H:%M+08:00')
        
    except (ValueError, TypeError, OSError) as e:
        # Fallback: return timestamp as string if conversion fails
        logger.warning(f"Failed to convert timestamp '{timestamp}': {e}")
        return str(timestamp)


def is_china_location(lng: float, lat: float) -> bool:
    """
    Determine if coordinates are within China's approximate boundaries.
    
    Args:
        lng: Longitude
        lat: Latitude
        
    Returns:
        True if coordinates are likely in China
    """
    # Approximate boundaries of China (including Taiwan, Hong Kong, Macau)
    # Longitude: 73°E to 135°E
    # Latitude: 18°N to 54°N
    return 73 <= lng <= 135 and 18 <= lat <= 54


def convert_station_timestamp_for_matching(station_timestamp: int, lng: float, lat: float) -> int:
    """
    Convert station UTC timestamp for proper matching with API datetime strings.
    For China locations, API datetimes are in local time (UTC+8).
    
    Args:
        station_timestamp: UTC timestamp from station data
        lng: Longitude to determine if in China
        lat: Latitude to determine if in China
        
    Returns:
        Adjusted timestamp for matching
    """
    if is_china_location(lng, lat):
        # For China locations, API returns local time (UTC+8)
        # So we need to add 8 hours to UTC timestamp for matching
        return station_timestamp + (8 * 3600)
    else:
        # For non-China locations, assume timestamps match directly
        return station_timestamp