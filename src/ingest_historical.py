"""Backfill historical 5-minute price & demand from AEMO monthly CSVs."""
import logging
import time

import requests
import pandas as pd

from config import RAW_DIR, PROCESSED_DIR, REGIONS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# check this

BASE_URL = "https://www.aemo.com.au/aemo/data/nem/priceanddemand/"
HISTORICAL_STORE = PROCESSED_DIR / "historical_price_demand.parquet"
HISTORICAL_STORE_CSV = PROCESSED_DIR / "historical_price_demand.csv"

def month_range(start: str, end: str):
    """Yield 'YYYYMM' strings inclusive, e.g. month_range('2024-01', '2025-12')."""
    periods = pd.period_range(start=start, end=end, freq="M")
    return [p.strftime("%Y%m") for p in periods]

def download_month_region(yyyymm: str, region: str) -> pd.DataFrame | None:
    fname = f"PRICE_AND_DEMAND_{yyyymm}_{region}.csv"
    url = f"{BASE_URL}/{fname}"
    raw_path = RAW_DIR / fname

    if raw_path.exists():                       # cache: skip re-downloading
        log.info("Cached %s", fname)
        return pd.read_csv(raw_path)
    
    try:
        resp = requests.get(url, timeout=30,
                                headers={"User-Agent": "aemo-portfolio-project/1.0"})
        resp.raise_for_status()

    except requests.RequestException as e:
            log.warning("Skip %s (%s)", fname, e)
            return None

    raw_path.write_bytes(resp.content)          # archive raw to data/raw
    log.info("Downloaded %s", fname)
    time.sleep(1)                               # be polite between requests
    return pd.read_csv(raw_path)

def build_historical(start="2024-01", end="2025-12") -> pd.DataFrame:
    frames = []
    for yyyymm in month_range(start, end):
        for region in REGIONS:
            df = download_month_region(yyyymm, region)
            if df is not None:
                frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    # Typical columns: REGION, SETTLEMENTDATE, TOTALDEMAND, RRP, PERIODTYPE
    combined["SETTLEMENTDATE"] = pd.to_datetime(combined["SETTLEMENTDATE"])
    combined.to_parquet(HISTORICAL_STORE, index=False)
    combined.to_csv(HISTORICAL_STORE_CSV, index=False)
    log.info("Historical store: %d rows -> %s", len(combined), HISTORICAL_STORE.name)
    return combined


if __name__ == "__main__":
    build_historical()

