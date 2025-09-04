"""Utility functions for weather data processing."""

from typing import Dict


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