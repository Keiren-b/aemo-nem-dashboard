# NEM Electricity Price & Demand Dashboard

Interactive dashboard of wholesale electricity price and demand across Australia's
National Electricity Market (NEM), built from AEMO dispatch data. A Python pipeline
ingests and cleans the raw AEMO feeds and the cleaned data drives a live Streamlit
dashboard.

**▶ Live dashboard:** https://aemo-nem-app.streamlit.app/

![Dashboard overview](https://github.com/Keiren-b/aemo-nem-dashboard/blob/main/dashboard_screenshot.png)

---

## What the dashboard does

Wholesale NEM prices are extraordinarily volatile. Within a single day a region
can swing from *negative* prices (more generation than demand) to the market price
cap. But underneath that volatility, price and demand follow structural, repeatable
patterns, and those patterns are what shape decisions about investment in renewables
and storage.

This dashboard is a tool for exploring these patterns. It lets you examine price and demand at different levels of aggregation, overlay moving averages across multiple time scales,
and split any chart out by NEM region to compare patterns between states. You can also
set your own spike thresholds and date ranges to probe how often extreme-price events
occur, and when.

![Price volatility by hour of day](assets/price-by-hour.png)

## How it works 

https://www.aemo.com.au/aemo/data/nem/priceanddemand/

**Data source.** public dispatch data in 5-min intervals for the 5 NEM regions (NSW1, QLD1, SA1, TAS1, VIC1) between 01-Jan_2024 and 01-Jan-2026

**Pipeline.**

```
AEMO NEMWEB  →  ingest (src/)  →  clean + reshape  →  data snapshot (data/)  →  Streamlit app
```

**Stack.** Python (pandas), Streamlit, Power BI. Exploratory analysis lives in
`notebooks/`; the reusable ingestion-and-cleaning code in `src/`.

## Running it locally

```bash
git clone https://github.com/keiren-b/aemo-nem-dashboard.git
cd aemo-nem-dashboard
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Repository layout

```
.streamlit/        Streamlit configuration
data/              cleaned data snapshot(s)
notebooks/         exploratory analysis (EDA, findings)
src/               ingestion + cleaning pipeline
streamlit_app.py   dashboard entry point
requirements.txt   dependencies
```


---

*Built by Keiren Brandt-Sawdy. [Portfolio](https://keiren-b.github.io) · LinkedIn [https://www.linkedin.com/in/keiren-brandt-sawdy-90779bb0/] · Email keiren.james18@gmail.com