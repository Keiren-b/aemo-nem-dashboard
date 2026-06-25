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

# Load data
@st.cache_data
def load_data() -> pd.DataFrame:
    return transform.run()

df_full = load_data()

# Define variables
SPIKE_THRESHOLD = 300
ALL_STATES = df_full["State"].unique()
MAX_PRICE = max(df_full["Price ($/MWh)"])
MIN_PRICE = min(df_full["Price ($/MWh)"])

#---Sidebar-------------------------------------------

st.sidebar.header("Filters", divider=True)

selected_states = st.sidebar.multiselect("Select which States you want to see data for:", options=ALL_STATES, default=ALL_STATES)

separate_plot = st.sidebar.toggle("Select to place each state's graph on a separate plot", value = False)
st.sidebar.divider()

selected_agg = st.sidebar.segmented_control("Select which time aggregation you want",["5 Min", "1 Hour", "1 Day", "1 Month"], selection_mode="single", required=True, default="5 Min")

st.sidebar.divider()

min_date = df_full["Settlement Date"].dt.date.min()
max_date = df_full["Settlement Date"].dt.date.max()

date_range = st.sidebar.slider("Select a Date Range:",
                       value=(min_date, max_date),
                       min_value=min_date,
                       max_value=max_date,
                       format="D MMM YY")

st.sidebar.divider()
spike_threshold = st.sidebar.number_input(
    "Spike threshold ($/MWh)", min_value=0, max_value=20000, value=SPIKE_THRESHOLD, step=50
)

#--Apply Filters-------------------------------------------

start_date, end_date = (date_range[0], date_range[1]) if len(date_range) == 2 else (date_range[0], date_range[0])

df = df_full[
    df_full["State"].isin(selected_states)
    & (df_full["Settlement Date"].dt.date >= start_date)
    & (df_full["Settlement Date"].dt.date <= end_date)
]

df["Is Spike"] = df["Price ($/MWh)"] > spike_threshold

#--Format Sub heading---------------------------------------
st.caption(
    "5-minute settlement intervals from the Australian Energy Market Operator (AEMO) · 2024–2026"
    )

st.caption(
    f"{len(df)} intervals shown"
    )

#--KPIS-------------------------------------------------------



#--Tabs-------------------------------------------------------

tab_price, tab_demand, tab_patterns, tab_spikes = st.tabs(
    ["📈 Price Trends", "⚡ Demand Trends", "🕐 Daily & Seasonal Patterns", "🚨 Price Spikes"]
)
with tab_price:
    if selected_agg == "5 Min":
        price = (
            df.groupby(["Settlement Date", "Date", "State"], observed=True)["Price ($/MWh)"]
            .mean()
            .reset_index()
        )
    elif selected_agg == "1 Hour":
        price = (
            df.groupby(["Date", "Hour of Day", "State"], observed=True)["Price ($/MWh)"]
            .mean()
            .reset_index()
        )
    elif selected_agg == "1 Day":
        price = (
            df.groupby(["Date", "State"], observed=True)["Price ($/MWh)"]
            .mean()
            .reset_index()
        )
    elif selected_agg == "1 Month":
        price = (
            df.groupby([df["Settlement Date"].dt.to_period("M").rename("Month"), "State"], observed=True)["Price ($/MWh)"]
            .mean()
            .reset_index()
        )
        price["Date"] = price["Month"].dt.to_timestamp()

    x_col = "Settlement Date" if selected_agg == "5 Min" else "Date"
    fig = px.line(
        price,
        x=x_col,
        y="Price ($/MWh)",
        color="State",
        title="Average Price by Region",
        labels={"Price ($/MWh)": "Avg Price ($/MWh)", "Date":"Date"},
        facet_row="State" if separate_plot else None,
        facet_row_spacing=0.09,
        height=1200 if separate_plot else 600,
        width=800,
    )
    if separate_plot:
        n = price["State"].nunique()
        fig.for_each_annotation(lambda a: a.update(
            text=a.text.split("=")[-1],
            x=0.5,
            xanchor="center",
            textangle=0,
            yanchor="bottom",
            y=a.y + 0.3 / n,
        ))
    fig.update_layout(hovermode="x unified",
                    showlegend=False if separate_plot else True)
    fig.update_xaxes(matches=None, 
                     showticklabels=True)

    st.plotly_chart(fig, use_container_width=True, key="price_chart")

with tab_demand:
    if selected_agg == "5 Min":
        price = (
            df.groupby(["Settlement Date", "Date", "State"], observed=True)["Demand (MW)"]
            .mean()
            .reset_index()
        )
    elif selected_agg == "1 Hour":
        price = (
            df.groupby(["Date", "Hour of Day", "State"], observed=True)["Demand (MW)"]
            .mean()
            .reset_index()
        )
    elif selected_agg == "1 Day":
        price = (
            df.groupby(["Date", "State"], observed=True)["Demand (MW)"]
            .mean()
            .reset_index()
        )
    elif selected_agg == "1 Month":
        price = (
            df.groupby([df["Settlement Date"].dt.to_period("M").rename("Month"), "State"], observed=True)["Demand (MW)"]
            .mean()
            .reset_index()
        )
        price["Date"] = price["Month"].dt.to_timestamp()

    x_col = "Settlement Date" if selected_agg == "5 Min" else "Date"
    fig = px.line(
        price,
        x=x_col,
        y="Demand (MW)",
        color="State",
        title="Average Price by Region",
        labels={"Demand (MW)": "Avg Demand (MW)"},
        facet_row="State" if separate_plot else None,
        facet_row_spacing=0.09,
        height=1200 if separate_plot else 600,
        width=800,
    )
    if separate_plot:
        n = price["State"].nunique()
        fig.for_each_annotation(lambda a: a.update(
            text=a.text.split("=")[-1],
            x=0.5,
            xanchor="center",
            textangle=0,
            yanchor="bottom",
            y=a.y + 0.3 / n,
        ))
    fig.update_layout(hovermode="x unified",
                    showlegend=False if separate_plot else True)
    fig.update_xaxes(matches=None, 
                     showticklabels=True)

    st.plotly_chart(fig, use_container_width=True, key="demand_chart")