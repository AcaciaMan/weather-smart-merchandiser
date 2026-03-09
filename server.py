"""
Weather-Smart Merchandiser – MCP Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Exposes merchandising-analysis tools over the Model Context Protocol
so AI assistants can query demand signals and generate layout actions.

Run in dev mode:   mcp dev server.py
Install for Claude: mcp install server.py
"""

from mcp.server.fastmcp import FastMCP
import json
import pandas as pd

from first_python_module import (
    load_data,
    get_demand_signals,
    get_top_categories,
    forecast_temperatures,
    generate_layout_actions,
    temp_bucket,
    DEFAULT_DB_PATH,
    DEFAULT_COLD_MAX,
    DEFAULT_WARM_MIN,
)

# ---- initialise MCP server ----
mcp = FastMCP("weather-smart-merchandiser")


# ---- tools ----

@mcp.tool()
def list_stores(db_path: str = DEFAULT_DB_PATH) -> list[str]:
    """Return a list of unique store names in the dataset."""
    df = load_data(db_path)
    return sorted(df["Store"].unique().tolist())


@mcp.tool()
def demand_signals(
    store: str = "Riga 1",
    db_path: str = DEFAULT_DB_PATH,
    cold_max: int = DEFAULT_COLD_MAX,
    warm_min: int = DEFAULT_WARM_MIN,
) -> str:
    """
    Compute average units sold per temperature bucket (cold/mild/warm)
    and product category for a given store.

    Returns a list of records with columns:
    TempBucket, Category, Units Sold (avg).
    """
    df = load_data(db_path, store=store)
    avg = get_demand_signals(df, cold_max, warm_min)
    return json.dumps(avg.to_dict(orient="records"), indent=2)


@mcp.tool()
def top_categories(
    temp_bucket_name: str,
    store: str = "Riga 1",
    top_n: int = 2,
    db_path: str = DEFAULT_DB_PATH,
    cold_max: int = DEFAULT_COLD_MAX,
    warm_min: int = DEFAULT_WARM_MIN,
) -> list[str]:
    """
    Return the top-selling product categories for a temperature bucket.

    Parameters
    ----------
    temp_bucket_name : one of "cold", "mild", "warm"
    store            : store name to filter on
    top_n            : how many top categories to return
    """
    df = load_data(db_path, store=store)
    avg = get_demand_signals(df, cold_max, warm_min)
    return get_top_categories(avg, temp_bucket_name, top_n)


@mcp.tool()
def classify_temperature(temp: float) -> str:
    """Classify a temperature (°C) into cold / mild / warm."""
    return temp_bucket(temp)


@mcp.tool()
def forecast(
    store: str = "Riga 1",
    days_ahead: int = 3,
    delta_per_day: float = 2.0,
    db_path: str = DEFAULT_DB_PATH,
) -> str:
    """
    Return a simple toy forecast for a store:
    each future day is *delta_per_day* °C warmer than the last observed temp.

    Returns a list of {day, date, forecast_temp, temp_bucket}.
    """
    df = load_data(db_path, store=store)
    last_date = df["Date"].max()
    last_temp = float(df.loc[df["Date"] == last_date, "Temp °C"].mean())
    temps = forecast_temperatures(last_temp, days_ahead, delta_per_day)

    results = []
    for i, t in enumerate(temps, start=1):
        fdate = last_date + pd.Timedelta(days=i)
        results.append({
            "day": i,
            "date": fdate.date().isoformat(),
            "forecast_temp": t,
            "temp_bucket": temp_bucket(t),
        })
    return json.dumps(results, indent=2)


@mcp.tool()
def layout_actions(
    store: str = "Riga 1",
    days_ahead: int = 3,
    top_n: int = 2,
    db_path: str = DEFAULT_DB_PATH,
    cold_max: int = DEFAULT_COLD_MAX,
    warm_min: int = DEFAULT_WARM_MIN,
) -> str:
    """
    Generate merchandising layout-change suggestions for the next
    *days_ahead* days based on historical sales-weather data.

    Each action contains: Action, Store, Start/End Date, Category,
    Suggested Move, Status, Expected Uplift %, Forecast Temp °C,
    and Temp Bucket.
    """
    df = load_data(db_path, store=store)
    actions = generate_layout_actions(
        df,
        store=store,
        days_ahead=days_ahead,
        top_n=top_n,
        cold_max=cold_max,
        warm_min=warm_min,
    )
    return json.dumps(actions, indent=2)


# ---- resources (read-only data exposed to the AI) ----

@mcp.resource("config://defaults")
def get_defaults() -> str:
    """Return the default configuration values."""
    return (
        f"DB_PATH={DEFAULT_DB_PATH}\n"
        f"COLD_MAX={DEFAULT_COLD_MAX}\n"
        f"WARM_MIN={DEFAULT_WARM_MIN}\n"
    )


# ---- entry point ----

if __name__ == "__main__":
    mcp.run()
