"""Capture a live 5-minute NEM snapshot from AEMO's public summary endpoint."""
import json
import logging
from datetime import datetime, timezone

import requests
import pandas as pd

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import RAW_DIR, PROCESSED_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

ENDPOINT = "https://visualisations.aemo.com.au/aemo/apps/api/report/ELEC_NEM_SUMMARY"
SNAPSHOT_STORE = PROCESSED_DIR / "live_snapshots.parquet"
SNAPSHOT_STORE_CSV = PROCESSED_DIR / "live_snapshots.csv"


def fetch_raw() -> dict:
    """GET the endpoint with a timeout, a couple of retries, and a UA header."""
    headers = {"User-Agent": "aemo-portfolio-project/1.0 (learning)"}
    for attempt in range(3):
        try:
            resp = requests.get(ENDPOINT, headers=headers, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            log.warning("Attempt %d failed: %s", attempt + 1, e)
    raise RuntimeError("Could not fetch endpoint after 3 attempts")


def save_raw(payload: dict) -> None:
    """Archive the untouched response for provenance, stamped with capture time."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = RAW_DIR / f"nem_summary_{stamp}.json"
    out.write_text(json.dumps(payload))
    log.info("Saved raw response -> %s", out.name)


def parse_summary(payload: dict) -> pd.DataFrame:
    """Flatten the ELEC_NEM_SUMMARY section into a tidy one-row-per-region frame."""
    records = payload["ELEC_NEM_SUMMARY"]
    df = pd.DataFrame(records)

    keep = [
        "SETTLEMENTDATE", "REGIONID", "PRICE", "PRICE_STATUS",
        "TOTALDEMAND", "NETINTERCHANGE",
        "SCHEDULEDGENERATION", "SEMISCHEDULEDGENERATION",
    ]
    df = df[keep].copy()

    df["SETTLEMENTDATE"] = pd.to_datetime(df["SETTLEMENTDATE"])
    df["captured_at_utc"] = datetime.now(timezone.utc)

    numeric = ["PRICE", "TOTALDEMAND", "NETINTERCHANGE",
               "SCHEDULEDGENERATION", "SEMISCHEDULEDGENERATION"]
    df[numeric] = df[numeric].apply(pd.to_numeric, errors="coerce")
    return df


def append_to_store(df: pd.DataFrame) -> None:
    """Append the new snapshot to a growing Parquet store, de-duplicating."""
    if SNAPSHOT_STORE.exists():
        existing = pd.read_parquet(SNAPSHOT_STORE)
        combined = pd.concat([existing, df], ignore_index=True)
    else:
        combined = df
    # One row per region per settlement interval
    combined = combined.drop_duplicates(subset=["SETTLEMENTDATE", "REGIONID"], keep="last")
    combined.to_parquet(SNAPSHOT_STORE, index=False)
    combined.to_csv(SNAPSHOT_STORE_CSV, index=False)
    log.info("Store now holds %d rows", len(combined))


def main() -> None:
    payload = fetch_raw()
    save_raw(payload)
    df = parse_summary(payload)
    append_to_store(df)
    log.info("Latest snapshot:\n%s", df[["REGIONID", "PRICE", "TOTALDEMAND"]].to_string(index=False))


if __name__ == "__main__":
    main()