"""Transform raw AEMO historical price/demand into the analysis-ready dataset."""
import pandas as pd
import logging
from config import PROCESSED_DIR

# Path constants
HISTORICAL_RAW   = PROCESSED_DIR / "historical_price_demand.parquet"
CLEAN_STORE      = PROCESSED_DIR / "nem_clean.parquet"
CLEAN_STORE_CSV  = PROCESSED_DIR / "nem_clean.csv"

log = logging.getLogger(__name__)

# ---- Stage 1: ----------------------------------------------------------------

def rename_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Rename AEMO source columns to more intuitive names used downstream."""
    names = {
        "REGION":         "State",
        "SETTLEMENTDATE": "Settlement Date",
        "TOTALDEMAND":    "Demand (MW)",
        "RRP":            "Price ($/MWh)",
    }
    return df.rename(columns=names)

def drop_redundant_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Drops redundant columns"""
    return df.drop(columns="PERIODTYPE")

def cast_types(df: pd.DataFrame) -> pd.DataFrame:
    """Explicitly cast each column to its intended type."""
    df = df.copy()
    df["Settlement Date"] = pd.to_datetime(df["Settlement Date"])
    df["State"]           = df["State"].astype("category")
    df["Demand (MW)"]     = pd.to_numeric(df["Demand (MW)"], errors="coerce")
    df["Price ($/MWh)"]   = pd.to_numeric(df["Price ($/MWh)"], errors="coerce")
    return df

def standardise_timezone(df:pd.DataFrame) -> pd.DataFrame:
    """NEM publishes in AEST time but without Daylight Saving Time. 
    This explicitly localises the time to Australia/Brisbane which is the tz that 
    corresponponds to AEMO's"""

    df["Settlement Date"] = df["Settlement Date"].dt.tz_localize("Australia/Brisbane", ambiguous=False)
    return df

# ---- Orchestration ----------------------------------------------------------

def run() -> pd.DataFrame:
    """Run the full cleaning pipeline and write the clean dataset to disk."""
    df = pd.read_parquet(HISTORICAL_RAW)
    df = rename_cols(df)
    df = drop_redundant_cols(df)
    df = standardise_timezone(df)
    
    # df = add_calendar_features(df)    # added once that function exists
    # df = add_price_classification(df) # added once that function exists
    # ... etc
    df.to_parquet(CLEAN_STORE, index=False)
    df.to_csv(CLEAN_STORE_CSV, index=False)
    log.info("Wrote %d rows to %s", len(df), CLEAN_STORE.name)

    return df

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()