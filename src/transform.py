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

def fix_state_names(df:pd.DataFrame) -> pd.DataFrame:
    """Rename State abbreviations eg from NSW1 to NSW"""
    df = df.copy()
    df["State"] = df["State"].map({
        "NSW1": "NSW",
        "VIC1": "VIC",
        "TAS1": "TAS",
        "SA1": "SA",
        "QLD1": "QLD"
    })
    return df

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

def flag_missing_time_intervals(df:pd.DataFrame) -> int:
    pieces = []
    for state in df["State"].unique():
        state_data = df[df["State"]==state]
        full_range = pd.date_range(
        start=state_data["Settlement Date"].min(), 
        end=state_data["Settlement Date"].max(),
        freq = "5min",
        tz=state_data["Settlement Date"].dt.tz
        )
        # missing = full_range.difference(state_time["Settlement Date"])

        reindexed = (
        state_data.set_index("Settlement Date")
            .reindex(full_range)
            .rename_axis("Settlement Date")
            .reset_index()
        )
        reindexed["State"] = state
        reindexed["is_imputed"] = reindexed["Price ($/MWh)"].isna()
        pieces.append(reindexed)
            
    df = pd.concat(pieces, ignore_index=True)
    return df.sort_values(["State", "Settlement Date"]).reset_index(drop=True)

def date_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineering different Time and Date features to aid analysis"""
    df["Date"] = df["Settlement Date"].dt.date
    df["Time"] = df["Settlement Date"].dt.time
    df["Hour of Day"] = df["Settlement Date"].dt.hour
    df["Day Name"] = df["Settlement Date"].dt.day_name()
    df["Weekday"] = df["Settlement Date"].dt.weekday
    df["Month"] = df["Settlement Date"].dt.month
    df["Month Start"] = df["Settlement Date"].dt.to_period("M").dt.to_timestamp()
    df["Month Name"] = df["Settlement Date"].dt.month_name()
    df["Month End"] = df["Settlement Date"].dt.is_month_end
    df["Quarter"] = df["Settlement Date"].dt.quarter
    df["Season"] = df["Month"].map({
        1: "Summer",
        2: "Summer",
        3: "Autumn",
        4: "Autumn",
        5: "Autumn",
        6: "Winter",
        7: "Winter",
        8: "Winter",
        9: "Spring",
        10: "Spring",
        11: "Spring",
        12: "Summer"
    })
    df["Year"] = df["Settlement Date"].dt.year
    return df

def spike(df: pd.DataFrame, spike_threshold: float = 300.00) -> pd.DataFrame:
    """Creates a user defined spike flag to see when electricity prices spike above a threshold"""
    df["Is Spike"] = df["Price ($/MWh)"] > spike_threshold
    return df

def add_rolling_features(df: pd.DataFrame, col: str, windows: dict[str, str], aggs: list[str] = ("mean",),) -> pd.DataFrame:
    """calculates a range of rolling statistics over different time periods"""
    df = df.sort_values(["State", "Settlement Date"]).reset_index(drop=True)
    grouped = df.groupby("State", observed=True)

    for suffix, window in windows.items():
        for agg in aggs:
            rolled = (
                grouped.rolling(window, on="Settlement Date")[col]
                .agg(agg)
                .reset_index(level=0, drop=True)
                .reset_index(drop=True)
            )
            df[f"Rolling {suffix} {agg.title()} {col}"] = rolled
    return df

def add_national_rolling_features(df: pd.DataFrame, col: str, windows: dict[str, str], aggs: list[str] = ("mean",),) -> pd.DataFrame:
    """calculates a range of rolling statistics nationally over different time periods"""
    df = df.sort_values(["Settlement Date", "State"]).reset_index(drop=True)

    national = (
        df.groupby("Settlement Date", observed=True)[col]
        .mean()
        .reset_index()
        .sort_values("Settlement Date")
    )

    for suffix, window in windows.items():
        for agg in aggs:
            rolled = national.rolling(window, on="Settlement Date")[col].agg(agg)
            national[f"National Rolling {suffix} {agg.title()} {col}"] = rolled

    new_cols = [c for c in national.columns if c.startswith("National Rolling")]
    df = df.merge(national[["Settlement Date"] + new_cols], on="Settlement Date", how="left")
    return df

# ---- Orchestration ----------------------------------------------------------

def run() -> pd.DataFrame:
    """Run the full cleaning pipeline and write the clean dataset to disk."""
    df = pd.read_parquet(HISTORICAL_RAW)
    df = rename_cols(df)
    df = fix_state_names(df)
    df = drop_redundant_cols(df)
    df = standardise_timezone(df)
    df = flag_missing_time_intervals(df)
    df = date_features(df)
    df = spike(df)
    df = add_rolling_features(df, "Price ($/MWh)", {"24h": "1D", "7d": "7D", "30d": "30D", "90d":"90D"}, aggs=["mean"])
    df = add_rolling_features(df, "Demand (MW)",   {"24h": "1D", "7d": "7D", "30d":"30D", "90d":"90D"}, aggs=["mean"])
    df = add_national_rolling_features(df, "Price ($/MWh)",   {"24h": "1D", "7d": "7D", "30d":"30D", "90d":"90D"}, aggs=["mean"])

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