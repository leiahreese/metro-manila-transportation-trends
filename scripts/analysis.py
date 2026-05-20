"""
analysis.py — Metro Manila Transportation Dashboard
Step 2: SQL Analysis Queries
Runs all analytical queries against the SQLite DB and saves results to /data/processed/.
Run this AFTER etl.py.
"""

import sqlite3
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "data", "metro_manila.db")
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")

conn = sqlite3.connect(DB_PATH)

def run(label, sql):
    df = pd.read_sql_query(sql, conn)
    print(f"  ✓ {label} → {df.shape[0]} rows")
    return df

print("=" * 60)
print("RUNNING SQL ANALYSIS ...")
print("=" * 60)

# ── TAB 1: TRAFFIC INCIDENTS ──────────────────────────────────────────────────

# 1a. Incidents per month (trend line)
incidents_monthly = run("Incidents per month", """
    SELECT
        YearMonth,
        Year,
        Month,
        COUNT(*)                                    AS Total_Incidents,
        SUM(CASE WHEN Incident_Category = 'Accident'         THEN 1 ELSE 0 END) AS Accidents,
        SUM(CASE WHEN Incident_Category = 'Stalled Vehicle'  THEN 1 ELSE 0 END) AS Stalled,
        SUM(CASE WHEN Incident_Category = 'Other'            THEN 1 ELSE 0 END) AS Other,
        AVG(Lanes_Blocked)                          AS Avg_Lanes_Blocked
    FROM mmda_incidents
    GROUP BY YearMonth, Year, Month
    ORDER BY Year, Month
""")

# 1b. Incidents by city
incidents_by_city = run("Incidents by city", """
    SELECT
        City,
        COUNT(*)                                    AS Total_Incidents,
        SUM(CASE WHEN Incident_Category = 'Accident' THEN 1 ELSE 0 END) AS Accidents,
        ROUND(AVG(Lanes_Blocked), 2)                AS Avg_Lanes_Blocked
    FROM mmda_incidents
    WHERE City IS NOT NULL
    GROUP BY City
    ORDER BY Total_Incidents DESC
""")

# 1c. Incidents by type (donut chart)
incidents_by_type = run("Incidents by type", """
    SELECT
        Incident_Category,
        COUNT(*) AS Count,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS Pct
    FROM mmda_incidents
    GROUP BY Incident_Category
    ORDER BY Count DESC
""")

# ── TAB 2: PEAK HOURS ─────────────────────────────────────────────────────────

# 2a. Heatmap: incidents by Hour × DayOfWeek
peak_heatmap = run("Peak hour heatmap", """
    SELECT
        Hour,
        DayOfWeek,
        COUNT(*) AS Incidents
    FROM mmda_incidents
    WHERE Hour IS NOT NULL
    GROUP BY Hour, DayOfWeek
    ORDER BY Hour, DayOfWeek
""")

# 2b. Hourly totals (bar chart)
peak_hourly = run("Hourly totals", """
    SELECT
        Hour,
        COUNT(*) AS Incidents,
        ROUND(AVG(Lanes_Blocked), 2) AS Avg_Lanes_Blocked
    FROM mmda_incidents
    WHERE Hour IS NOT NULL
    GROUP BY Hour
    ORDER BY Hour
""")

# 2c. Busiest locations
peak_locations = run("Busiest locations", """
    SELECT
        Location,
        City,
        COUNT(*) AS Incidents
    FROM mmda_incidents
    WHERE Location IS NOT NULL
    GROUP BY Location, City
    ORDER BY Incidents DESC
    LIMIT 15
""")

# ── TAB 3: MRT-3 RIDERSHIP ───────────────────────────────────────────────────

# 3a. Annual totals (bar chart + KPIs)
ridership_annual = run("Annual ridership", """
    SELECT
        Year,
        SUM(Total_Ridership)        AS Annual_Total,
        AVG(Avg_Daily)              AS Avg_Daily,
        MAX(Total_Ridership)        AS Peak_Month_Riders
    FROM ridership_monthly
    GROUP BY Year
    ORDER BY Year
""")

# 3b. Monthly averages across all years (seasonality)
ridership_seasonality = run("Monthly seasonality", """
    SELECT
        Month,
        Month_Name,
        ROUND(AVG(Total_Ridership), 0)  AS Avg_Monthly,
        ROUND(AVG(Avg_Daily), 0)        AS Avg_Daily
    FROM ridership_monthly
    WHERE Year BETWEEN 2010 AND 2025
    GROUP BY Month, Month_Name
    ORDER BY Month
""")

# 3c. Year-over-year growth
ridership_yoy = run("Year-over-year growth", """
    SELECT
        Year,
        SUM(Total_Ridership) AS Annual_Total,
        LAG(SUM(Total_Ridership)) OVER (ORDER BY Year) AS Prev_Year,
        ROUND(
            (SUM(Total_Ridership) - LAG(SUM(Total_Ridership)) OVER (ORDER BY Year))
            * 100.0 / LAG(SUM(Total_Ridership)) OVER (ORDER BY Year), 1
        ) AS YoY_Growth_Pct
    FROM ridership_monthly
    GROUP BY Year
    ORDER BY Year
""")

# 3d. Monthly ridership 2019–2025 (COVID impact visible)
ridership_recent = run("Recent monthly ridership", """
    SELECT YearMonth, Year, Month, Month_Name, Total_Ridership, Avg_Daily
    FROM ridership_monthly
    WHERE Year >= 2019
    ORDER BY Year, Month
""")

conn.close()

# ── Save all ─────────────────────────────────────────────────────────────────
outputs = {
    "incidents_monthly.csv":     incidents_monthly,
    "incidents_by_city.csv":     incidents_by_city,
    "incidents_by_type.csv":     incidents_by_type,
    "peak_heatmap.csv":          peak_heatmap,
    "peak_hourly.csv":           peak_hourly,
    "peak_locations.csv":        peak_locations,
    "ridership_annual.csv":      ridership_annual,
    "ridership_seasonality.csv": ridership_seasonality,
    "ridership_yoy.csv":         ridership_yoy,
    "ridership_recent.csv":      ridership_recent,
}

print()
print("SAVING CSVs ...")
for fname, df in outputs.items():
    df.to_csv(os.path.join(PROC_DIR, fname), index=False)
    print(f"  ✓ {fname}")

print()
print("=" * 60)
print("ANALYSIS COMPLETE ✓")
print("=" * 60)
