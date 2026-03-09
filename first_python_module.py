"""
weather_smart_merchandiser.core
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Reusable functions for weather-driven merchandising analysis.
"""

import os
import sqlite3
import pandas as pd
from datetime import timedelta

# ---- DEFAULT CONFIG ----
_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(_HERE, "sales_weather.db")
DEFAULT_TABLE = "sales_weather_daily"
DEFAULT_COLD_MAX = 8    # <= 8 °C  → cold
DEFAULT_WARM_MIN = 15   # >= 15 °C → warm


# ---- helpers ----

def temp_bucket(temp: float, cold_max: int = DEFAULT_COLD_MAX, warm_min: int = DEFAULT_WARM_MIN) -> str:
    """Classify a temperature into cold / mild / warm."""
    if temp <= cold_max:
        return "cold"
    elif temp >= warm_min:
        return "warm"
    return "mild"


def load_data(db_path: str = DEFAULT_DB_PATH, store: str | None = None) -> pd.DataFrame:
    """Load the sales-weather data from SQLite, parse dates, and optionally filter by store."""
    with sqlite3.connect(db_path) as conn:
        if store:
            df = pd.read_sql_query(
                f"SELECT * FROM {DEFAULT_TABLE} WHERE Store = ?",
                conn,
                params=(store,),
            )
        else:
            df = pd.read_sql_query(f"SELECT * FROM {DEFAULT_TABLE}", conn)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def get_demand_signals(
    df: pd.DataFrame,
    cold_max: int = DEFAULT_COLD_MAX,
    warm_min: int = DEFAULT_WARM_MIN,
) -> pd.DataFrame:
    """Return average units sold per (TempBucket, Category)."""
    df = df.copy()
    df["TempBucket"] = df["Temp °C"].apply(lambda t: temp_bucket(t, cold_max, warm_min))
    avg_units = (
        df.groupby(["TempBucket", "Category"])["Units Sold"]
          .mean()
          .reset_index()
    )
    return avg_units


def get_top_categories(
    avg_units: pd.DataFrame,
    bucket: str,
    top_n: int = 2,
) -> list[str]:
    """Return the *top_n* best-selling categories for a temperature bucket."""
    sub = avg_units[avg_units["TempBucket"] == bucket]
    if sub.empty:
        return []
    sub = sub.sort_values("Units Sold", ascending=False)
    return list(sub["Category"].head(top_n))


def forecast_temperatures(
    last_temp: float,
    days_ahead: int = 3,
    delta_per_day: float = 2.0,
) -> list[float]:
    """Toy forecast: increase *delta_per_day* °C per future day."""
    return [round(last_temp + delta_per_day * i, 1) for i in range(1, days_ahead + 1)]


def generate_layout_actions(
    df: pd.DataFrame,
    store: str = "Riga 1",
    days_ahead: int = 3,
    top_n: int = 2,
    cold_max: int = DEFAULT_COLD_MAX,
    warm_min: int = DEFAULT_WARM_MIN,
) -> list[dict]:
    """
    End-to-end: compute demand signals, forecast temps, and return a list
    of suggested layout-change actions for the next *days_ahead* days.
    """
    avg_units = get_demand_signals(df, cold_max, warm_min)

    last_date = df["Date"].max()
    last_temp = float(df.loc[df["Date"] == last_date, "Temp °C"].mean())
    forecasts = forecast_temperatures(last_temp, days_ahead)

    actions: list[dict] = []
    for i, ftemp in enumerate(forecasts, start=1):
        fdate = last_date + timedelta(days=i)
        bucket = temp_bucket(ftemp, cold_max, warm_min)
        cats = get_top_categories(avg_units, bucket, top_n)
        if not cats:
            continue

        for cat in cats:
            if bucket == "warm":
                suggestion = f"Move {cat} to front/endcap for warm spell"
                expected_uplift = 15
            elif bucket == "cold":
                suggestion = f"Highlight {cat} near entrance for cold days"
                expected_uplift = 12
            else:
                suggestion = f"Keep {cat} in standard aisle for mild weather"
                expected_uplift = 5

            actions.append({
                "Action": f"{bucket.capitalize()} layout – {cat} – {fdate.date().isoformat()}",
                "Store": store,
                "Start Date": fdate.date().isoformat(),
                "End Date": fdate.date().isoformat(),
                "Category": cat,
                "Suggested Move": suggestion,
                "Status": "Planned",
                "Expected Uplift %": expected_uplift,
                "Forecast Temp °C": ftemp,
                "Temp Bucket": bucket,
            })
    return actions


# ---- CLI entry-point (preserves original behaviour) ----

if __name__ == "__main__":
    STORE_NAME = "Riga 1"
    df = load_data(DEFAULT_DB_PATH, store=STORE_NAME)

    avg = get_demand_signals(df)
    print("Average units by temp bucket and category:\n")
    print(avg)

    for b in ("cold", "mild", "warm"):
        print(f"\nTop categories ({b}):", get_top_categories(avg, b))

    actions = generate_layout_actions(df, store=STORE_NAME)
    actions_df = pd.DataFrame(actions)
    print("\nSuggested layout actions:\n")
    print(actions_df)

    actions_df.to_json("layout_actions_suggested.json", orient="records", indent=2)
    print("\nSaved to layout_actions_suggested.json")
