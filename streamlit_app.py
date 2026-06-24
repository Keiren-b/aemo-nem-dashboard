import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st
import pandas as pd
import plotly.express as px
from config import PROCESSED_DIR
import transform as t

st.set_page_config(
    page_title="AEMO NEM Dashboard",
    page_icon="⚡",
    layout="wide",
)

SPIKE_THRESHOLD = 300


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_parquet(PROCESSED_DIR / "historical_price_demand.parquet")
    df = t.rename_cols(df)
    df = t.drop_redundant_cols(df)
    df = t.cast_types(df)
    df = t.standardise_timezone(df)
    df = t.date_features(df)
    df = t.spike(df, spike_threshold=SPIKE_THRESHOLD)
    return df


df_full = load_data()
all_states = sorted(df_full["State"].cat.categories.tolist())

# ── Sidebar ──────────────────────────────────────────────────────────────────

st.sidebar.title("Filters")
selected_states = st.sidebar.multiselect("Regions", options=all_states, default=all_states)

min_date = df_full["Settlement Date"].dt.date.min()
max_date = df_full["Settlement Date"].dt.date.max()
date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

st.sidebar.divider()
spike_threshold = st.sidebar.number_input(
    "Spike threshold ($/MWh)", min_value=0, max_value=20000, value=SPIKE_THRESHOLD, step=50
)

# ── Apply filters ─────────────────────────────────────────────────────────────

start_date, end_date = (date_range[0], date_range[1]) if len(date_range) == 2 else (date_range[0], date_range[0])

df = df_full[
    df_full["State"].isin(selected_states)
    & (df_full["Settlement Date"].dt.date >= start_date)
    & (df_full["Settlement Date"].dt.date <= end_date)
].copy()

df["Is Spike"] = df["Price ($/MWh)"] > spike_threshold

# ── Header ────────────────────────────────────────────────────────────────────

st.title("⚡ AEMO National Electricity Market")
st.caption(
    "5-minute settlement intervals from the Australian Energy Market Operator (AEMO) · 2024–2026 · "
    f"{len(df):,} intervals shown"
)

# ── KPI cards ─────────────────────────────────────────────────────────────────

kpi_cols = st.columns(len(all_states))
for col, state in zip(kpi_cols, all_states):
    state_df = df[df["State"] == state]
    if state_df.empty:
        col.metric(state.replace("1", ""), "—")
    else:
        avg = state_df["Price ($/MWh)"].mean()
        col.metric(state.replace("1", ""), f"${avg:.0f}/MWh", help="Average price over selected period")

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_price, tab_demand, tab_patterns, tab_spikes = st.tabs(
    ["📈 Price Trends", "⚡ Demand Trends", "🕐 Daily & Seasonal Patterns", "🚨 Price Spikes"]
)

with tab_price:
    daily_price = (
        df.groupby(["Date", "State"], observed=True)["Price ($/MWh)"]
        .mean()
        .reset_index()
    )
    fig = px.line(
        daily_price,
        x="Date",
        y="Price ($/MWh)",
        color="State",
        title="Average Daily Price by Region",
        labels={"Price ($/MWh)": "Avg Price ($/MWh)"},
    )
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

with tab_demand:
    daily_demand = (
        df.groupby(["Date", "State"], observed=True)["Demand (MW)"]
        .mean()
        .reset_index()
    )
    fig = px.line(
        daily_demand,
        x="Date",
        y="Demand (MW)",
        color="State",
        title="Average Daily Demand by Region",
        labels={"Demand (MW)": "Avg Demand (MW)"},
    )
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

with tab_patterns:
    col_left, col_right = st.columns(2)

    with col_left:
        hourly = (
            df.groupby(["Hour of Day", "State"], observed=True)["Price ($/MWh)"]
            .mean()
            .reset_index()
        )
        fig = px.line(
            hourly,
            x="Hour of Day",
            y="Price ($/MWh)",
            color="State",
            title="Average Price by Hour of Day",
            labels={"Price ($/MWh)": "Avg Price ($/MWh)"},
        )
        fig.update_xaxes(tickmode="linear", dtick=2)
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        seasonal = (
            df.groupby(["Season", "State"], observed=True)["Price ($/MWh)"]
            .mean()
            .reset_index()
        )
        fig = px.bar(
            seasonal,
            x="Season",
            y="Price ($/MWh)",
            color="State",
            barmode="group",
            category_orders={"Season": ["Summer", "Autumn", "Winter", "Spring"]},
            title="Average Price by Season",
            labels={"Price ($/MWh)": "Avg Price ($/MWh)"},
        )
        st.plotly_chart(fig, use_container_width=True)

    monthly = (
        df.groupby(["Month", "Month Name", "State"], observed=True)["Price ($/MWh)"]
        .mean()
        .reset_index()
        .sort_values("Month")
    )
    fig = px.line(
        monthly,
        x="Month Name",
        y="Price ($/MWh)",
        color="State",
        title="Average Price by Month",
        labels={"Price ($/MWh)": "Avg Price ($/MWh)", "Month Name": "Month"},
        markers=True,
    )
    st.plotly_chart(fig, use_container_width=True)

with tab_spikes:
    spikes = df[df["Is Spike"]]

    spike_counts = spikes.groupby("State", observed=True).size().reset_index(name="Spike Count")
    fig = px.bar(
        spike_counts,
        x="State",
        y="Spike Count",
        color="State",
        title=f"Price Spike Count by Region (> ${spike_threshold}/MWh)",
        text_auto=True,
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader(f"Spike Events — {len(spikes):,} intervals above ${spike_threshold}/MWh")
    display_cols = ["Settlement Date", "State", "Price ($/MWh)", "Demand (MW)", "Season", "Hour of Day"]
    st.dataframe(
        spikes[display_cols]
        .sort_values("Price ($/MWh)", ascending=False)
        .reset_index(drop=True),
        use_container_width=True,
    )
