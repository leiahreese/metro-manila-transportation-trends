# Metro Manila Transportation Trend Dashboard

A Streamlit dashboard visualizing Metro Manila traffic incidents and MRT-3 ridership trends,
built with Python (ETL), SQL (analysis), and Streamlit + Plotly (visualization).

---

## Project Structure

```
metro_dashboard/
├── data/
│   ├── data_mmda_traffic_spatial.csv     ← MMDA incident raw data
│   ├── cleaned_ridership_data.csv        ← MRT-3 ridership raw data
│   ├── DAILY_RIDERSHIP_FROM_1999.xlsx    ← MRT-3 raw source
│   ├── metro_manila.db                   ← SQLite DB (generated)
│   └── processed/                        ← Cleaned CSVs (generated)
├── scripts/
│   ├── etl.py                            ← Step 1: Extract, Transform, Load
│   └── analysis.py                       ← Step 2: SQL Analysis Queries
├── app/
│   └── app.py                            ← Step 3: Streamlit Dashboard
└── requirements.txt
```

---

## Setup in VS Code

### 1. Install dependencies
Open the terminal in VS Code (`Ctrl + `` ` ``) and run:

```bash
pip install -r requirements.txt
```

### 2. Run ETL (data cleaning)
```bash
python scripts/etl.py
```
✓ This creates `data/metro_manila.db` and `data/processed/*.csv`

### 3. Run SQL analysis
```bash
python scripts/analysis.py
```
✓ This runs all queries and saves 10 analysis CSVs to `data/processed/`

### 4. Launch the dashboard
```bash
streamlit run app/app.py
```
✓ Opens at `http://localhost:8501` in your browser

---

## Dashboard Tabs

| Tab | Content |
|-----|---------|
| 🚗 Traffic Volume & Incidents | Monthly trend, city breakdown, incident types |
| 🕐 Peak Hour Analysis | Hour × Day heatmap, rush hour bars, hotspot locations |
| 🚇 MRT-3 Ridership Trends | Annual totals, YoY growth, COVID recovery, seasonality |

---

## Data Sources

- **MMDA Traffic Incidents** — Kaggle (esparko/mmda-traffic-incident-data), 2018–2020
- **MRT-3 Daily Ridership** — Kaggle (franksebastiancayaco/mrt-3-ridership-1999-2025)
