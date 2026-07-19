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

## What the dashboard shows

- **Regional contrast.** Split by region, **South Australia** dips into negative prices
  **X%** of intervals — roughly **N×** more often than NSW — the visible fingerprint of
  its rooftop-solar penetration.
- **Concentration of extremes.** Set the spike threshold to **$X/MWh** and **N%** of the
  year's high-price hours collapse into just **M** days — the tail is concentrated, not
  spread evenly.
- **Structure under the noise.** Overlay a 7-day moving average and the seasonal peak
  separates cleanly from the daily cycle in **[region]**, showing **[pattern]**.
- **Why granularity matters.** At 5-minute resolution the evening ramp (5–8pm) shows
  **[pattern]** that washes out entirely once aggregated to daily — detail a summary table
  would hide.

![Price volatility by hour of day](assets/price-by-hour.png)

## How it works

**Data source.** [AEMO NEMWEB](https://nemweb.com.au) — public dispatch data for the five
NEM regions (NSW1, QLD1, SA1, TAS1, VIC1). <!-- Confirm the specifics: which tables
(e.g. dispatch price / RRP and regional demand), the resolution (5-minute dispatch vs
30-minute trading), and the date range you covered. -->

**Pipeline.**

```
AEMO NEMWEB  →  ingest (src/)  →  clean + reshape  →  data snapshot (data/)  →  Streamlit app
```

<!-- One or two sentences per stage: what the ingest pulls, what cleaning was needed
(missing dispatch intervals? the NEM interval-ending timestamp convention? timezone
handling?), and how the app consumes the result. The *why* behind a choice reads as more
senior than the *what*. -->

**Live vs snapshot.** <!-- State honestly which you shipped. Either:
"The app fetches AEMO's live feed on load, cached with @st.cache_data(ttl=300) so it
doesn't hammer the endpoint." — or — "The app reads a committed data snapshot, current
as of <date>." See tradeoffs below. -->

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

## Design decisions & tradeoffs

> For a tool, this is the section that signals judgment rather than just execution — the
> choices you made about *what to build and what to expose* are the seniority signal. Be
> specific; a named tradeoff makes everything above it more credible. Prompts to draw from:

- **Why the spike threshold is a user control, not a fixed number.** <!-- The strong one:
  the "right" threshold depends on the question being asked, so hard-coding a single cutoff
  would claim an authority the data doesn't support — exposing it is the more honest design.
  Say this in your own words; it's the most senior sentence in the file. -->
- **Live vs snapshot** — what you chose, and what it cost you (freshness vs reliability,
  and the Streamlit Community Cloud constraints).
- **A cleaning call that could have gone another way** — the interval-ending timestamp
  convention, how you treated negative prices, or gaps in the dispatch record.
- **A performance tradeoff** — Streamlit re-runs top to bottom on every interaction, so
  what you cached, and how much data the app can hold before it feels sluggish.
- **What you'd build next** — interconnector flows? a price-forecast model? FCAS markets?

---

*Built by Keiren Brandt-Sawdy. [Portfolio](https://keiren-b.github.io) · LinkedIn [https://www.linkedin.com/in/keiren-brandt-sawdy-90779bb0/] · Email keiren.james18@gmail.com