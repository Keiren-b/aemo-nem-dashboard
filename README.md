# NEM Electricity Price & Demand Dashboard

Interactive dashboard of wholesale electricity price and demand across Australia's
National Electricity Market (NEM), built from AEMO dispatch data. A Python pipeline
ingests and cleans the raw AEMO feeds and the cleaned data drives a live Streamlit
dashboard.

**▶ Live dashboard:** [https://aemo-nem-app.streamlit.app/]


![Dashboard overview](https://aemo-nem-app.dashboard_screenshot.png)

---

## The question

Wholesale NEM prices are extraordinarily volatile — within a single day a region can
swing from *negative* prices (more generation than demand) to the market price cap.
That volatility isn't noise: it drives real decisions about battery storage, hedging
contracts, and demand response. This project asks a simple question with a non-obvious
answer: **when and why do prices spike, and how does that differ across the five NEM
regions?**

## Key findings

> Replace these with your real figures. This section is what a reviewer remembers, and
> the numbers are what make it stick — lead each point with the number, not the setup.

- **[Finding 1 — the headline.]** e.g. "Evening peak (5–8pm) prices averaged **X×** the
  midday trough across the two-year window."
- **[Finding 2 — concentration.]** e.g. "**X%** of the year's total price spikes occurred
  in just **N** hours — the tail dominates the average."
- **[Finding 3 — regional contrast.]** e.g. "**South Australia** recorded negative prices
  **X%** of intervals, roughly **N×** more often than NSW, reflecting its rooftop-solar
  penetration."
- **[Finding 4 — a relationship.]** e.g. "Demand alone explained only **R²** of price
  variation — supply-side factors (generator outages, interconnector limits) drive the
  extremes."

<!-- Put your single most convincing chart right here, next to the findings. -->
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

## What I learned / tradeoffs

> This is the section that signals judgment rather than just execution. Be specific — a
> named limitation makes everything above it *more* credible, not less. Prompts to draw from:

- The live-vs-snapshot decision: what you chose, and what it cost you.
- A cleaning call that could have gone another way (handling the interval-ending timestamp
  convention, negative prices, or gaps in the dispatch record).
- Something the data *couldn't* tell you — a spike you couldn't fully attribute.
- What you'd build next with more time (interconnector flows? a price-forecast model?
  FCAS markets?).

---

*Built by Keiren Brandt-Sawdy. [Portfolio](https://keiren-b.github.io) · LinkedIn [https://www.linkedin.com/in/keiren-brandt-sawdy-90779bb0/] · Email keiren.james18@gmail.com