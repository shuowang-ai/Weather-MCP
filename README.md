<div align="center">
  <img src="knowair_logo.png" alt="KnowAir Logo" width="400"/>
  
  # KnowAir Weather MCP Server
  
  A comprehensive Model Context Protocol (MCP) server providing real-time weather data, air quality monitoring, forecasts, and astronomical information.
  
  [![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
  [![FastMCP](https://img.shields.io/badge/MCP-FastMCP-green.svg)](https://github.com/jlowin/FastMCP)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
</div>

## Setup Instructions

> Before anything, ensure you have access to the API. You can apply for it at [https://docs.caiyunapp.com/weather-api/](https://docs.caiyunapp.com/weather-api/).

Install uv first.

MacOS/Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows:

```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Setup with Claude Desktop

```
# claude_desktop_config.json
# Can find location through:
# Hamburger Menu -> File -> Settings -> Developer -> Edit Config
{
  "mcpServers": {
    "knowair-weather": {
      "command": "uvx",
      "args": ["mcp-knowair-weather"],
      "env": {
        "CAIYUN_WEATHER_API_TOKEN": "YOUR_API_KEY_HERE"
      }
    }
  }
}
```

### Ask Claude a question requiring weather
e.g. "What's the weather in Beijing Now?"

## Local/Dev Setup Instructions

### Setup with Claude Desktop

```
# claude_desktop_config.json
# Can find location through:
# Hamburger Menu -> File -> Settings -> Developer -> Edit Config
{
  "mcpServers": {
    "knowair-weather": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/PARENT/FOLDER/Weather-MCP",
        "run",
        "mcp-knowair-weather"
      ],
      "env": {
        "CAIYUN_WEATHER_API_TOKEN": "YOUR_API_TOKEN_HERE"
      }
    }
  }
}
```

### Debugging

Run:
```bash
npx @modelcontextprotocol/inspector \
      uv \
      --directory /ABSOLUTE/PATH/TO/PARENT/FOLDER/Weather-MCP \
      run \
      mcp-knowair-weather
```

## Available Tools

### Core Weather Tools

- **`get_realtime_weather`**: Get comprehensive real-time weather data
  - **Parameters**: `lng` (longitude, -180 to 180), `lat` (latitude, -90 to 90)
  - **Returns**: Current temperature, humidity, wind, precipitation, air quality (PM2.5, PM10, O3, SO2, NO2, CO), AQI (China and USA standards), UV index, and comfort level

- **`get_hourly_forecast`**: Get detailed 72-hour weather forecast
  - **Parameters**: `lng` (longitude, -180 to 180), `lat` (latitude, -90 to 90)
  - **Returns**: Hourly temperature, apparent temperature (feels like), weather conditions, precipitation probability, and wind data

- **`get_weekly_forecast`**: Get 7-day weather forecast
  - **Parameters**: `lng` (longitude, -180 to 180), `lat` (latitude, -90 to 90)
  - **Returns**: Daily temperature range (min/max), weather conditions, and precipitation probability

- **`get_historical_weather`**: Get past 24-hour weather data
  - **Parameters**: `lng` (longitude, -180 to 180), `lat` (latitude, -90 to 90)
  - **Returns**: Historical temperature and weather conditions for each hour

### Advanced Weather Tools

- **`get_comprehensive_weather`**: Get complete weather report in one call
  - **Parameters**: `lng` (longitude, -180 to 180), `lat` (latitude, -90 to 90)
  - **Returns**: Current conditions, air quality, today's forecast, and active alerts all in one comprehensive report

- **`get_minute_precipitation`**: Get minute-level precipitation forecast (2 hours)
  - **Parameters**: `lng` (longitude, -180 to 180), `lat` (latitude, -90 to 90)
  - **Returns**: Minute-by-minute precipitation intensity for next 2 hours (available for major cities in China)

- **`get_astronomy_info`**: Get astronomical information
  - **Parameters**: `lng` (longitude, -180 to 180), `lat` (latitude, -90 to 90)
  - **Returns**: Sunrise and sunset times for the next 7 days

- **`get_weather_alerts`**: Get active weather alerts and warnings
  - **Parameters**: `lng` (longitude, -180 to 180), `lat` (latitude, -90 to 90)
  - **Returns**: Current weather alerts with title, code, status, and description

## Tool Comparison

| Tool | Time Span | Data Type | Best For |
|------|-----------|-----------|----------|
| `get_realtime_weather` | Current | Weather + Air Quality | Current conditions & air quality check |
| `get_hourly_forecast` | Next 72h | Detailed hourly | Short-term planning |
| `get_weekly_forecast` | Next 7 days | Daily summary | Week planning |
| `get_historical_weather` | Past 24h | Historical | Weather analysis |
| `get_comprehensive_weather` | Current + Today | All-in-one | Complete weather overview |
| `get_minute_precipitation` | Next 2h | Precipitation | Rain/snow timing |
| `get_astronomy_info` | Next 7 days | Sun/Moon | Outdoor activities |
| `get_weather_alerts` | Active | Warnings | Safety alerts |

## Features

✅ **Comprehensive Air Quality Data** - PM2.5, PM10, O3, SO2, NO2, CO levels with both Chinese and US AQI standards
✅ **Detailed Forecasts** - Up to 72-hour forecasts with apparent temperature
✅ **Minute-level Precipitation** - Precise precipitation forecasting for major cities
✅ **Astronomy Information** - Sunrise/sunset times and moon phases
✅ **Weather Alerts** - Real-time weather warnings and alerts
✅ **Proper Error Handling** - Robust error handling with informative messages
✅ **Input Validation** - Coordinate validation and API token checking
✅ **Logging** - Comprehensive logging for debugging and monitoring

## Requirements

- Python 3.12+
- Valid Caiyun Weather API token (set as `CAIYUN_WEATHER_API_TOKEN` environment variable)
- All coordinate parameters must be valid: longitude (-180 to 180), latitude (-90 to 90)

## Quick Start

1. **Get your API key** from [Caiyun Weather API](https://docs.caiyunapp.com/weather-api/)

2. **Install and run**:
```bash
# Set your API token
export CAIYUN_WEATHER_API_TOKEN=your_api_token_here

# Run with uv (recommended)
uv run mcp-knowair-weather

# Or test with MCP Inspector
npx @modelcontextprotocol/inspector uv --directory /path/to/Weather-MCP run mcp-knowair-weather
```

3. **Use in Claude Desktop**: Add the server configuration to your `claude_desktop_config.json`

4. **Ask Claude**: "What's the air quality in Beijing?" or "Get weather forecast for 40.7128,-74.0060"

## Example Usage

```
🤖 You: "Get comprehensive weather data for coordinates 116.4575, 39.9113"

🌤️ Claude: Using KnowAir Weather MCP to get comprehensive weather report...

📍 Current Conditions:
Temperature: 32°C (Feels Like: 33°C)
Humidity: 47%
Wind: 13.4m/s @ 169°
Air Quality: PM2.5: 14μg/m³ | AQI (CN): 49 (优)
```

## API Data Source

This MCP server uses the **Caiyun Weather API** (彩云天气) as its data source, which provides:
- Real-time weather conditions
- High-precision air quality monitoring
- Minute-level precipitation forecasts
- Multi-day weather forecasts
- Weather alerts and warnings

## Development

```bash
# Clone the repository
git clone https://github.com/shuowang/Weather-MCP.git
cd Weather-MCP

# Install dependencies
uv install

# Run tests
export CAIYUN_WEATHER_API_TOKEN=your_token
uv run python -m pytest

# Format code
uv run ruff format src/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Caiyun Weather](https://caiyunapp.com/) for providing the weather API
- [FastMCP](https://github.com/jlowin/FastMCP) for the MCP framework
- [Claude](https://claude.ai/) for AI assistance capabilities

---

<div align="center">
  <p>Built with ❤️ for accurate weather and air quality monitoring</p>
  <p>
    <a href="https://github.com/shuowang/Weather-MCP">GitHub</a> •
    <a href="https://docs.caiyunapp.com/weather-api/">API Docs</a> •
    <a href="https://github.com/shuowang/Weather-MCP/issues">Issues</a>
  </p>
</div>
