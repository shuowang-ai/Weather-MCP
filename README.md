<div align="center">
  <img src="knowair_logo.png" alt="KnowAir Logo" width="400"/>
  
  # KnowAir Weather MCP Server
  
  A comprehensive Model Context Protocol (MCP) server providing real-time weather data, air quality monitoring, forecasts, and astronomical information powered by Caiyun Weather API.
  
  [![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
  [![FastMCP](https://img.shields.io/badge/MCP-FastMCP-green.svg)](https://github.com/jlowin/FastMCP)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
</div>

## 🌟 Features

✅ **实时天气数据** - 温度、体感温度、湿度、风速、能见度等完整气象信息  
✅ **全方位空气质量监测** - PM2.5/PM10/O3/SO2/NO2/CO 及中美AQI标准  
✅ **小时级空气质量预报** - 1-72小时逐小时AQI/PM2.5趋势预测，彩色分级显示  
✅ **空气质量趋势分析** - 自动分析空气质量改善/恶化趋势，提供健康建议  
✅ **分钟级降水预报** - 未来2小时逐分钟降水强度预测  
✅ **多时间尺度预报** - 1-72小时 / 1-7天预报，灵活时间范围  
✅ **天气预警系统** - 实时预警信息推送  
✅ **天文信息** - 日出日落、月相、月出月落时间  
✅ **历史天气数据** - 过去72小时历史天气查询  
✅ **中文本地化** - 天气现象、生活指数全面中文化  
✅ **智能格式化** - 降水强度分级、emoji图标、用户友好显示  

## 🚀 Quick Start

### 1. 获取API密钥
访问 [彩云天气API](https://docs.caiyunapp.com/weather-api/) 申请API密钥

### 2. 安装uv包管理器

**MacOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 3. 配置Claude Desktop

在 `claude_desktop_config.json` 中添加配置：
```json
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

### 4. 开始使用
向Claude提问："北京现在的天气怎么样？" 或 "上海明天会下雨吗？"

## 🛠️ Available Tools

### 📍 核心天气工具

#### `get_realtime_weather`
获取实时天气数据
- **参数**: `lng`(经度), `lat`(纬度)
- **返回**: 温度、体感温度、湿度、风速、气压、能见度、空气质量、生活指数等

#### `get_hourly_forecast`
小时级天气预报
- **参数**: `lng`, `lat`, `hours`(1-72小时，默认24)
- **返回**: 逐小时温度、天气现象、降水概率、风速、完整空气质量数据(AQI/PM2.5/PM10/O3/NO2/SO2/CO)及趋势分析

#### `get_daily_forecast`
日级天气预报
- **参数**: `lng`, `lat`, `days`(1-7天，默认7)
- **返回**: 每日温度范围、天气现象、降水概率、风速、日出日落、生活指数等

#### `get_air_quality_forecast`
空气质量预报和分析
- **参数**: `lng`, `lat`, `days`(1-7天，默认7)
- **返回**: 未来1-7天空气质量预报、AQI/PM2.5趋势分析、健康建议

### 🌧️ 高级天气工具

#### `get_minutely_precipitation`
分钟级降水预报
- **参数**: `lng`, `lat`
- **返回**: 未来2小时逐分钟降水强度、降水概率预测

#### `get_comprehensive_weather`
综合天气报告
- **参数**: `lng`, `lat`, `include_hourly`(可选), `include_alerts`(可选)
- **返回**: 实时+预报+预警的完整天气报告

#### `get_weather_alerts`
天气预警信息
- **参数**: `lng`, `lat`
- **返回**: 当前生效的天气预警详情

#### `get_astronomy_info`
天文信息
- **参数**: `lng`, `lat`, `days`(1-7天，默认7)
- **返回**: 日出日落、月出月落、月相信息

#### `get_historical_weather`
历史天气数据
- **参数**: `lng`, `lat`, `hours_back`(1-72小时，默认24)
- **返回**: 过去指定时间的天气历史数据

## 📊 工具对比表

| 工具 | 时间范围 | 数据类型 | 最佳用途 |
|------|----------|----------|----------|
| `get_realtime_weather` | 当前 | 实时天气+空气质量 | 当前状况查询 |
| `get_hourly_forecast` | 未来1-72小时 | 逐小时详细预报 | 短期规划 |
| `get_daily_forecast` | 未来1-7天 | 日级汇总预报 | 周计划安排 |
| `get_air_quality_forecast` | 未来1-7天 | 空气质量预报+趋势 | 空气质量分析 |
| `get_minutely_precipitation` | 未来2小时 | 分钟级降水 | 精确降雨预测 |
| `get_comprehensive_weather` | 当前+预报 | 综合报告 | 完整天气概览 |
| `get_weather_alerts` | 当前生效 | 预警信息 | 安全提醒 |
| `get_astronomy_info` | 未来1-7天 | 天文数据 | 户外活动规划 |
| `get_historical_weather` | 过去1-72小时 | 历史数据 | 天气分析 |

## 🌈 天气现象支持

系统支持完整的天气现象识别和中文翻译：

**晴朗天气**: 晴（白天/夜间）、多云（白天/夜间）、阴  
**降水天气**: 小雨/中雨/大雨/暴雨、小雪/中雪/大雪/暴雪  
**特殊天气**: 雾、轻度/中度/重度雾霾、浮尘、沙尘、大风

## 💡 降水强度分级

系统根据不同数据类型使用相应的降水强度标准：

### 🔴 雷达降水强度 (实时数据，0-1范围)
- **< 0.031**: 无雨/雪
- **0.031-0.25**: 小雨/雪  
- **0.25-0.35**: 中雨/雪
- **0.35-0.48**: 大雨/雪
- **≥ 0.48**: 暴雨/雪

### ⏰ 小时级降水量 (mm/h)
- **< 0.0606**: 无雨/雪
- **0.0606-0.8989**: 小雨/雪
- **0.8989-2.87**: 中雨/雪
- **2.87-12.8638**: 大雨/雪
- **≥ 12.8638**: 暴雨/雪

### ⏱️ 分钟级降水量 (mm/h)
- **< 0.08**: 无雨/雪
- **0.08-3.44**: 小雨/雪
- **3.44-11.33**: 中雨/雪
- **11.33-51.30**: 大雨/雪
- **≥ 51.30**: 暴雨/雪

## 📋 生活指数说明

### ☀️ 紫外线指数
**实况级别 (0-11)**：无(0) → 很弱(1-2) → 弱(3-4) → 中等(5-6) → 强(7-9) → 很强(10) → 极强(11)  
**天级别 (1-5)**：最弱(1) → 弱(2) → 中等(3) → 强(4) → 很强(5)

### 👕 穿衣指数 (0-8)
极热(0-1) → 很热(2) → 热(3) → 温暖(4) → 凉爽(5) → 冷(6) → 寒冷(7) → 极冷(8)

### 🌡️ 舒适度指数 (0-13)
闷热(0) → 酷热(1) → 很热(2) → 热(3) → 温暖(4) → 舒适(5) → 凉爽(6) → 冷(7) → 很冷(8) → 寒冷(9) → 极冷(10) → 刺骨的冷(11) → 湿冷(12) → 干冷(13)

### 🤧 感冒指数 (1-4) 
少发(1) → 较易发(2) → 易发(3) → 极易发(4)

### 🚗 洗车指数 (1-4)
适宜(1) → 较适宜(2) → 较不适宜(3) → 不适宜(4)

## 🔧 开发调试

### 本地开发配置
```json
{
  "mcpServers": {
    "knowair-weather": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/Weather-MCP",
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

### MCP Inspector调试
```bash
npx @modelcontextprotocol/inspector \
      uv \
      --directory /ABSOLUTE/PATH/TO/Weather-MCP \
      run \
      mcp-knowair-weather
```

### 命令行测试
```bash
# 设置API密钥
export CAIYUN_WEATHER_API_TOKEN=your_api_token_here

# 运行服务器
uv run mcp-knowair-weather
```

## 🎯 使用示例

### 实时天气查询
```
🤖 用户: "北京现在的天气怎么样？"

🌤️ Claude: 让我查询北京当前的天气情况...

📍 北京实时天气数据:
🌡️  温度: 28°C
🤔 体感温度: 31°C  
💧 湿度: 65%
☁️  云量: 40%
🌦️  天气: 多云（白天）
👁️  能见度: 15km
💨 风速: 12m/s, 风向: 180°
🏭 空气质量:
    PM2.5: 35μg/m³
    中国AQI: 89 (良)
📋 生活指数:
    紫外线: 中等
    舒适度: 闷热
```

### 综合天气报告
```
🤖 用户: "给我上海的完整天气报告"

🌐 综合天气报告
📍 位置: 121.4737, 31.2304
⏰ 更新时间: 2024-09-04 19:07:21

🌤️  === 实时天气 ===
🌡️  温度: 32°C, 体感: 35°C
💧 湿度: 58%, ☁️  云量: 20%
🌦️  天气现象: 晴（白天）
💨 风速: 8m/s, 风向: 45°

🏭 === 空气质量 ===
PM2.5: 42μg/m³ | PM10: 65μg/m³
中国AQI: 96 (良)

📅 === 未来3天预报 ===
今天: 26°C~35°C, 晴, 降水概率5%
明天: 28°C~36°C, 多云, 降水概率15%  
后天: 25°C~32°C, 小雨, 降水概率80%
```

### 空气质量预报分析
```
🤖 用户: "北京接下来一周的空气质量怎么样？"

🏭 空气质量预报 (未来7天)
📍 位置: 116.3885, 39.9066

🔄 当前空气质量 (实时):
🟡 AQI: 89 (良)
🟡 PM2.5: 32μg/m³ (良好)
📊 完整数据:
    PM10: 45μg/m³
    臭氧: 127μg/m³
    二氧化硫: 6μg/m³
    二氧化氮: 38μg/m³
    一氧化碳: 0.8mg/m³
💡 健康建议: 空气质量可接受，但某些污染物可能对极少数异常敏感人群健康有较弱影响

📅 === 未来空气质量预报 ===

🟡 今天 (2025-09-04):
📊 AQI: 平均44 (范围: 40~109) - 优
🟢 PM2.5: 平均15μg/m³ (范围: 10~74μg/m³) - 优秀
🌫️ PM10: 22μg/m³
💨 臭氧: 85μg/m³
💡 健康建议: 空气质量令人满意，基本无空气污染
------------------------

🟢 明天 (2025-09-05):
📊 AQI: 平均35 (范围: 25~51) - 优
🟢 PM2.5: 平均12μg/m³ (范围: 8~25μg/m³) - 优秀
💡 健康建议: 空气质量令人满意，基本无空气污染
------------------------

📈 === 趋势分析 ===
AQI变化: 44 → 35 (📉 空气质量呈改善趋势)
PM2.5变化: 15 → 12μg/m³ (📉 PM2.5浓度下降)

🌟 空气质量最好: 明天 (AQI: 35)
⚠️ 空气质量最差: 今天 (AQI: 44)

🏥 === 一周健康建议 ===
平均AQI: 40
✅ 空气质量优良，适合各类户外活动
```

### 小时级空气质量预报
```
🤖 用户: "北京今天晚上空气质量怎么样？"

🕒 未来24小时阴
🎯 关键信息: 未来24小时阴

🏭 === 空气质量趋势 ===
📉 空气质量趋势：改善 (AQI: 77→43)
PM2.5变化: 16→25μg/m³

⏰ 2025-09-04T19:00+08:00
🌡️  温度: 28°C
🤔 体感: 31°C
🌦️  天气: 阴
🌧️  降水概率: 5%
💧 降水量: 0.0mm/h
💨 风速: 12km/h, 风向: 180°
💧 湿度: 65%
☁️  云量: 80%
👁️  能见度: 15km
📊 气压: 101325Pa
🟡 AQI: 77 (美标:59)
🟢 PM2.5: 16μg/m³
------------------------

⏰ 2025-09-04T22:00+08:00
🌡️  温度: 25°C
🤔 体感: 27°C
🌦️  天气: 阴
💨 风速: 8km/h, 风向: 90°
🟢 AQI: 41 (美标:71)
🟢 PM2.5: 22μg/m³
------------------------
```

## 📋 系统要求

- Python 3.12+
- 有效的彩云天气API密钥
- 经纬度坐标: 经度(-180至180), 纬度(-90至90)

## 🌍 数据来源

本MCP服务器使用**彩云天气API**作为数据源，提供：
- 全球实时天气数据  
- 高精度空气质量监测
- 分钟级降水预报（中国主要城市）
- 多日天气预报
- 官方天气预警信息

## 🤝 贡献指南

欢迎贡献！请随时提交Pull Request。对于重大更改，请先开issue讨论。

```bash
# 克隆仓库
git clone https://github.com/shuowang/Weather-MCP.git
cd Weather-MCP

# 安装依赖
uv install

# 设置环境变量
export CAIYUN_WEATHER_API_TOKEN=your_token

# 格式化代码
uv run ruff format src/
```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [彩云天气](https://caiyunapp.com/) - 提供API服务
- [FastMCP](https://github.com/jlowin/FastMCP) - MCP框架支持
- [Claude](https://claude.ai/) - AI助手能力

---

<div align="center">
  <p>Built with ❤️ for accurate weather and air quality monitoring</p>
  <p>
    <a href="https://github.com/shuowang/Weather-MCP">GitHub</a> •
    <a href="https://docs.caiyunapp.com/weather-api/">API Docs</a> •
    <a href="https://github.com/shuowang/Weather-MCP/issues">Issues</a>
  </p>
</div>

