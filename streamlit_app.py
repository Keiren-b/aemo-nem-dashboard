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

# Define filter variables
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

def compute_aggs(df: pd.DataFrame) -> dict:
    return {
        "5 Min": (
            df.groupby(["Settlement Date", "Date", "State"], observed=True)[["Price ($/MWh)", "Demand (MW)"]]
            .mean()
            .reset_index()
        ),
        "1 Hour": (
            df.groupby(["Date", "Hour of Day", "State"], observed=True)[["Price ($/MWh)", "Demand (MW)"]]
            .mean()
            .reset_index()
        ),
        "1 Day": (
            df.groupby(["Date", "State"], observed=True)[["Price ($/MWh)", "Demand (MW)"]]
            .mean()
            .reset_index()
        ),
        "1 Month": (
            df.groupby(["Month Start", "State"], observed=True)[["Price ($/MWh)", "Demand (MW)"]]
            .mean()
            .reset_index()
        ),
    }

AGG_X_COL = {
    "5 Min": "Settlement Date",
    "1 Hour": "Date",
    "1 Day": "Date",
    "1 Month": "Month Start",
}

aggs = compute_aggs(df)

tab_price, tab_demand, tab_patterns, tab_spikes = st.tabs(
    ["📈 Price Trends", "⚡ Demand Trends", "🕐 Daily & Seasonal Patterns", "🚨 Price Spikes"]
)

with tab_price:

    fig = px.line(
        aggs[selected_agg],
        x=AGG_X_COL[selected_agg],
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
        n = aggs[selected_agg]["State"].nunique()
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
    fig = px.line(
        aggs[selected_agg],
        x=AGG_X_COL[selected_agg],
        y="Demand (MW)",
        color="State",
        title="Average Price by Region",
        labels={"Demand (MW)": "Avg Demand (MW)", "Date":"Date"},
        facet_row="State" if separate_plot else None,
        facet_row_spacing=0.09,
        height=1200 if separate_plot else 600,
        width=800,
    )
    if separate_plot:
        n = aggs[selected_agg]["State"].nunique()
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