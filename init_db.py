"""
Load sales_weather_daily.csv into a local SQLite database.

Run once:  python init_db.py
"""

import os
import sqlite3
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(_HERE, "sales_weather_daily.csv")
DB_PATH = os.path.join(_HERE, "sales_weather.db")
TABLE_NAME = "sales_weather_daily"


def init_db(csv_path: str = CSV_PATH, db_path: str = DB_PATH) -> None:
    df = pd.read_csv(csv_path)
    with sqlite3.connect(db_path) as conn:
        df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
    print(f"Loaded {len(df)} rows into {db_path} (table: {TABLE_NAME})")


if __name__ == "__main__":
    init_db()
