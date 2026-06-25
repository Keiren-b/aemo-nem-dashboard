import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st
import pandas as pd
import plotly.express as px
from config import PROCESSED_DIR
import transform

# streamlit page config
st.set_page_config(
    page_title="AEMO Dashboard",
    page_icon="⚡",
    layout="wide",
)
# Add title
st.title("⚡ AEMO Price and Demand Dashboard")

#Define default Spike Threshold
SPIKE_THRESHOLD = 300

@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_parquet(PROCESSED_DIR / "historical_price_demand.parquet")
    df = transform.rename_cols(df)
    df = transform.drop_redundant_cols(df)
    df = transform.cast_types(df)
    df = transform.standardise_timezone(df)
    df = transform.date_features(df)
    df = transform.spike(df, spike_threshold=SPIKE_THRESHOLD)
    return df

df_full = load_data()
all_states = df_full["State"].unique()
print(all_states)
