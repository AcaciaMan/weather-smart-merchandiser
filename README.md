# weather-smart-merchandiser

Weather-driven merchandising tool that analyses historical sales-weather data,
forecasts demand by temperature bucket, and generates store layout-change
suggestions. Exposed as an **MCP server** so AI assistants (Claude Desktop,
VS Code Copilot, etc.) can call the tools directly.

Short introduction video:
https://github.com/user-attachments/assets/bdb07f87-5e2a-4974-be23-12ba47560132

Notion project page:
https://neighborly-fridge-ea2.notion.site/Weather-smart-merchandiser-31a4fffb13a880618b7fd4198be66b30

Notion DIY dashboard page:
https://neighborly-fridge-ea2.notion.site/DIY-Weather-Smart-Merchandising-fffb7fe844f841bda431202321e29ac9

## Project structure

| File | Purpose |
|------|---------|
| `first_python_module.py` | Core library — reusable functions for data loading, demand signals, forecasting, and action generation |
| `server.py` | MCP server entry point — wraps the core functions as MCP tools |
| `sales_weather_daily.csv` | Input dataset (Date, Store, Temp °C, Weather, Category, Units Sold, Revenue €) |
| `requirements.txt` | Python dependencies |

## MCP tools

| Tool | Description |
|------|-------------|
| `list_stores` | List unique store names in the dataset |
| `demand_signals` | Average units sold per temperature bucket and category |
| `top_categories` | Top-selling categories for a given temp bucket (cold/mild/warm) |
| `classify_temperature` | Classify a °C value into cold / mild / warm |
| `forecast` | Simple temperature forecast for upcoming days |
| `layout_actions` | End-to-end layout-change suggestions based on weather forecast |

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### Run as MCP server (Claude Desktop)

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "weather-smart-merchandiser": {
      "command": "python",
      "args": ["path/to/server.py"]
    }
  }
}
```

Then restart Claude Desktop. The tools appear under the hammer icon.

### Run with MCP Inspector (dev/test)

```bash
mcp dev server.py
```

### Run as standalone script

```bash
python first_python_module.py
```

Reads `sales_weather_daily.csv`, prints demand signals and layout actions,
and saves results to `layout_actions_suggested.csv`.

## CSV format

The input CSV expects these columns:

| Column | Example |
|--------|---------|
| Date | 2025-03-01 |
| Store | Riga 1 |
| Temp °C | 12.5 |
| Weather | Cloudy |
| Category | Beverages |
| Units Sold | 45 |
| Revenue € | 120.50 |

## Configuration

Default temperature thresholds (tunable per tool call):

- **Cold**: ≤ 8 °C
- **Warm**: ≥ 15 °C
- **Mild**: everything in between
