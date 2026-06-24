# AEMO National Electricity Market Dashboard

An end-to-end data pipeline and interactive dashboard for Australian electricity market data from the [Australian Energy Market Operator (AEMO)](https://www.aemo.com.au/).

## What it does

- **Ingests** 5-minute settlement data from AEMO's public API (2024–2026, all 5 NEM regions)
- **Cleans & transforms** raw data: column renaming, type casting, AEST timezone standardisation, temporal feature engineering, and price spike detection
- **Visualises** price trends, demand patterns, hourly/seasonal profiles, and spike events via an interactive Streamlit dashboard

## Running locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run streamlit_app.py
```

To regenerate the processed data from scratch:

```bash
python src/ingest_historical.py   # downloads raw CSVs from AEMO
python src/transform.py           # cleans and feature-engineers the dataset
```

## Project structure

```
├── src/
│   ├── config.py              # path constants and region list
│   ├── ingest_historical.py   # backfill 2024–2026 from AEMO API
│   ├── ingest_live.py         # 5-minute live snapshot capture (runs via cron)
│   └── transform.py           # cleaning and feature engineering pipeline
├── notebooks/
│   ├── 01_exploration.ipynb   # exploratory analysis
│   └── 02_cleaning.ipynb      # pipeline walkthrough
├── data/
│   └── processed/
│       └── historical_price_demand.parquet  # committed for deployment
├── streamlit_app.py           # dashboard entry point
└── requirements.txt
```

## Data

- **Source**: [AEMO Price and Demand](https://www.aemo.com.au/energy-systems/electricity/national-electricity-market-nem/data-nem/aggregated-data)
- **Coverage**: Jan 2024 – Jan 2026 · ~1M 5-minute intervals · 5 regions (NSW, QLD, SA, TAS, VIC)
- **Live feed**: `ingest_live.py` captures the real-time NEM summary every 5 minutes via cron
