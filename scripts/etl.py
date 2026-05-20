"""
etl.py — Metro Manila Transportation Dashboard
Step 1: Extract, Transform, Load
Cleans MMDA traffic incident data and MRT-3 ridership data,
then saves clean outputs to /data/processed/.
"""

import pandas as pd
import numpy as np
import os
import sqlite3

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR   = os.path.join(BASE_DIR, "data")
PROC_DIR   = os.path.join(DATA_DIR, "processed")
DB_PATH    = os.path.join(DATA_DIR, "metro_manila.db")
os.makedirs(PROC_DIR, exist_ok=True)

# =============================================================================
# 1. MMDA TRAFFIC INCIDENTS
# =============================================================================
print("=" * 60)
print("CLEANING MMDA TRAFFIC INCIDENTS ...")
print("=" * 60)

mmda_raw = pd.read_csv(os.path.join(DATA_DIR, "data_mmda_traffic_spatial.csv"))
print(f"  Raw shape: {mmda_raw.shape}")

mmda = mmda_raw.copy()

# --- Date & Time -------------------------------------------------------------
mmda["Date"] = pd.to_datetime(mmda["Date"], errors="coerce")
mmda.dropna(subset=["Date"], inplace=True)

# Parse time → 24-hour integer hour
mmda["Time_Clean"] = pd.to_datetime(mmda["Time"], format="%I:%M %p", errors="coerce")
mmda["Hour"]       = mmda["Time_Clean"].dt.hour
mmda["DayOfWeek"]  = mmda["Date"].dt.day_name()
mmda["Month"]      = mmda["Date"].dt.month
mmda["Year"]       = mmda["Date"].dt.year
mmda["YearMonth"]  = mmda["Date"].dt.to_period("M").astype(str)

# --- Incident type bucketing -------------------------------------------------
def bucket_type(t):
    t = str(t).upper()
    if "ACCIDENT" in t or "COLLISION" in t or "SELF ACCIDENT" in t:
        return "Accident"
    if "STALLED" in t:
        return "Stalled Vehicle"
    if "OBSTRUCTION" in t or "ROAD BLOCK" in t:
        return "Obstruction"
    if "FALLEN" in t or "DEBRIS" in t:
        return "Road Hazard"
    return "Other"

mmda["Incident_Category"] = mmda["Type"].apply(bucket_type)

# --- City cleanup ------------------------------------------------------------
mmda["City"] = mmda["City"].str.strip().str.title()
# Fix encoding artifact
mmda["City"] = mmda["City"].str.replace("ParaÃ±aque", "Parañaque", regex=False)
mmda["City"] = mmda["City"].str.replace("Paranaque", "Parañaque", regex=False)

# --- Lanes blocked -----------------------------------------------------------
mmda["Lanes_Blocked"] = pd.to_numeric(mmda["Lanes_Blocked"], errors="coerce").fillna(0)

# --- Drop helper cols --------------------------------------------------------
mmda_clean = mmda.drop(columns=["Time_Clean", "Tweet", "Source", "High_Accuracy"], errors="ignore")

print(f"  Clean shape: {mmda_clean.shape}")
print(f"  Date range : {mmda_clean['Date'].min().date()} → {mmda_clean['Date'].max().date()}")
print(f"  Cities     : {mmda_clean['City'].nunique()}")
print(f"  Categories : {mmda_clean['Incident_Category'].value_counts().to_dict()}")

mmda_clean.to_csv(os.path.join(PROC_DIR, "mmda_clean.csv"), index=False)
print("  ✓ Saved mmda_clean.csv")

# =============================================================================
# 2. MRT-3 DAILY RIDERSHIP
# =============================================================================
print()
print("=" * 60)
print("CLEANING MRT-3 RIDERSHIP ...")
print("=" * 60)

ride_raw = pd.read_csv(os.path.join(DATA_DIR, "cleaned_ridership_data.csv"))
print(f"  Raw shape : {ride_raw.shape}")

# Wide → long
month_cols = ["January","February","March","April","May","June",
              "July","August","September","October","November","December"]

ride_long = ride_raw.melt(
    id_vars=["Date", "Year"],
    value_vars=month_cols,
    var_name="Month_Name",
    value_name="Ridership"
)

# Build a proper date from Year, Month_Name, Day (Date col = day)
ride_long.rename(columns={"Date": "Day"}, inplace=True)
ride_long["Date_Str"] = ride_long["Year"].astype(str) + "-" + ride_long["Month_Name"] + "-" + ride_long["Day"].astype(str)
ride_long["Date"]     = pd.to_datetime(ride_long["Date_Str"], format="%Y-%B-%d", errors="coerce")

# Drop invalid dates (e.g. Feb 30) and zero-ridership rows
ride_long.dropna(subset=["Date"], inplace=True)
ride_long = ride_long[ride_long["Ridership"] > 0].copy()

# Add time columns
ride_long["Year"]       = ride_long["Date"].dt.year
ride_long["Month"]      = ride_long["Date"].dt.month
ride_long["Month_Name"] = ride_long["Date"].dt.month_name()
ride_long["DayOfWeek"]  = ride_long["Date"].dt.day_name()
ride_long["YearMonth"]  = ride_long["Date"].dt.to_period("M").astype(str)

# Monthly aggregates (used by charts)
ride_monthly = (
    ride_long
    .groupby(["Year", "Month", "Month_Name", "YearMonth"], as_index=False)
    .agg(Total_Ridership=("Ridership", "sum"),
         Avg_Daily=("Ridership", "mean"),
         Days=("Ridership", "count"))
)
ride_monthly.sort_values(["Year","Month"], inplace=True)

print(f"  Daily rows : {ride_long.shape[0]}")
print(f"  Years      : {ride_long['Year'].min()} – {ride_long['Year'].max()}")
print(f"  Monthly rows: {ride_monthly.shape[0]}")

ride_long.to_csv(os.path.join(PROC_DIR, "ridership_daily.csv"), index=False)
ride_monthly.to_csv(os.path.join(PROC_DIR, "ridership_monthly.csv"), index=False)
print("  ✓ Saved ridership_daily.csv")
print("  ✓ Saved ridership_monthly.csv")

# =============================================================================
# 3. LOAD INTO SQLITE
# =============================================================================
print()
print("=" * 60)
print("LOADING INTO SQLITE ...")
print("=" * 60)

conn = sqlite3.connect(DB_PATH)

mmda_clean.to_sql("mmda_incidents", conn, if_exists="replace", index=False)
print(f"  ✓ mmda_incidents  → {len(mmda_clean):,} rows")

ride_long.to_sql("ridership_daily", conn, if_exists="replace", index=False)
print(f"  ✓ ridership_daily → {len(ride_long):,} rows")

ride_monthly.to_sql("ridership_monthly", conn, if_exists="replace", index=False)
print(f"  ✓ ridership_monthly → {len(ride_monthly):,} rows")

conn.close()
print(f"  ✓ Database saved → {DB_PATH}")

print()
print("=" * 60)
print("ETL COMPLETE ✓")
print("=" * 60)
