import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config import PROCESSED_DIR
import transform
import requests
import logging as log

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
    return pd.read_parquet(transform.CLEAN_STORE)

df_full = load_data()

# Define filter variables
SPIKE_THRESHOLD = 300
ALL_STATES = df_full["State"].unique()
MAX_PRICE = max(df_full["Price ($/MWh)"])
MIN_PRICE = min(df_full["Price ($/MWh)"])

TAB_LABELS = ["📈 Price Trends", "⚡ Demand Trends", "🕐 Daily & Seasonal Patterns", "🚨 Price Spikes"]
TREND_TABS = {"📈 Price Trends", "⚡ Demand Trends"}

if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = TAB_LABELS[0]

is_trend_tab = st.session_state["active_tab"] in TREND_TABS
is_price_tab = st.session_state["active_tab"] == "📈 Price Trends"

#---Sidebar-------------------------------------------

st.sidebar.header("Filters", divider=True)

selected_states = st.sidebar.multiselect("Select which States you want to see data for:", options=ALL_STATES, default=ALL_STATES)

separate_plot = st.sidebar.toggle("Select to place each state's graph on a separate plot", value=False, key="sep_plot", disabled=not is_trend_tab)
st.sidebar.divider()

selected_agg = st.sidebar.segmented_control("Select which time aggregation you want", ["5 Min", "1 Hour", "1 Day", "1 Month"],
                                            selection_mode="single",
                                            required=True,
                                            default="1 Month",
                                            key="time_agg_selector",
                                            disabled=not is_trend_tab)

selected_smooth = st.sidebar.segmented_control("Select which smoothing you want", ["1 Day", "7 Days", "30 Days", "90 Days"],
                                            selection_mode="single",
                                            required=False,
                                            default=None,
                                            key="smoothselector",
                                            disabled=not is_price_tab)

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
st.text(
    "5-minute settlement intervals from the Australian Energy Market Operator (AEMO) · 2024–2026"
    )
st.space("small")
#--KPIS-------------------------------------------------------
st.subheader("Live Electricity Prices")
kpi_cols = st.columns(len(ALL_STATES))


@st.cache_data(ttl=300)
def fetch_live_prices() -> dict:
    headers = {"User-Agent": "aemo-portfolio-project/1.0 (learning)"}
    for attempt in range(3):
        try:
            resp = requests.get("https://visualisations.aemo.com.au/aemo/apps/api/report/ELEC_NEM_SUMMARY",
                                headers=headers, 
                                timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            log.warning("Attempt %d failed: %s", attempt + 1, e)
    raise RuntimeError("Could not fetch endpoint after 3 attempts")

live_data_raw = fetch_live_prices()
live_data_raw = live_data_raw["ELEC_NEM_SUMMARY"]
live_data_raw = pd.DataFrame(live_data_raw)

keep = [
        "SETTLEMENTDATE", "REGIONID", "PRICE", "PRICE_STATUS",
        "TOTALDEMAND", "NETINTERCHANGE",
        "SCHEDULEDGENERATION", "SEMISCHEDULEDGENERATION",
    ]

numeric = ["PRICE", "TOTALDEMAND", "NETINTERCHANGE",
            "SCHEDULEDGENERATION", "SEMISCHEDULEDGENERATION"]

live_data = live_data_raw[keep]
live_data[numeric] = live_data[numeric].apply(pd.to_numeric, errors="coerce")

live_data["REGIONID"] = live_data["REGIONID"].map({
    "NSW1": "NSW",
    "VIC1": "VIC",
    "TAS1": "TAS",
    "SA1": "SA",
    "QLD1": "QLD"
})

for state in ALL_STATES:
    state_data = live_data[live_data["REGIONID"] == state]

for num, state in enumerate(ALL_STATES):
    state_data = live_data[live_data["REGIONID"] == state]
    kpi_cols[num].metric(label=state, value=f"${state_data['PRICE'].iloc[0]:,.2f}")


st.divider()


#--Tabs-------------------------------------------------------

@st.cache_data
def compute_aggs(df: pd.DataFrame) -> dict:
    return {
        "5 Min": (
            df.groupby(["Settlement Date", "Date", "State"], observed=True)[["Price ($/MWh)",
                                                                             "Demand (MW)",
                                                                             "Rolling 24h Mean Price ($/MWh)",
                                                                             "Rolling 7d Mean Price ($/MWh)",
                                                                             "Rolling 30d Mean Price ($/MWh)",
                                                                             "Rolling 90d Mean Price ($/MWh)",
                                                                             "National Rolling 24h Mean Price ($/MWh)",
                                                                             "National Rolling 7d Mean Price ($/MWh)",
                                                                             "National Rolling 30d Mean Price ($/MWh)",
                                                                             "National Rolling 90d Mean Price ($/MWh)"]]
            .mean()
            .reset_index()
        ),
        "1 Hour": (
            df.groupby(["Date", "Hour of Day", "State"], observed=True)[["Price ($/MWh)", 
                                                                        "Demand (MW)",
                                                                        "Rolling 24h Mean Price ($/MWh)",
                                                                        "Rolling 7d Mean Price ($/MWh)",
                                                                        "Rolling 30d Mean Price ($/MWh)",
                                                                        "Rolling 90d Mean Price ($/MWh)",
                                                                        "National Rolling 24h Mean Price ($/MWh)",
                                                                        "National Rolling 7d Mean Price ($/MWh)",
                                                                        "National Rolling 30d Mean Price ($/MWh)",
                                                                        "National Rolling 90d Mean Price ($/MWh)"]]
            .mean()
            .reset_index()
        ),
        "1 Day": (
            df.groupby(["Date", "State"], observed=True)[["Price ($/MWh)",
                                                        "Demand (MW)",
                                                        "Rolling 24h Mean Price ($/MWh)",
                                                        "Rolling 7d Mean Price ($/MWh)",
                                                        "Rolling 30d Mean Price ($/MWh)",
                                                        "Rolling 90d Mean Price ($/MWh)",
                                                        "National Rolling 24h Mean Price ($/MWh)",
                                                        "National Rolling 7d Mean Price ($/MWh)",
                                                        "National Rolling 30d Mean Price ($/MWh)",
                                                        "National Rolling 90d Mean Price ($/MWh)"]]
            .mean()
            .reset_index()
        ),
        "1 Month": (
            df.groupby(["Month Start", "State"], observed=True)[["Price ($/MWh)", 
                                                                "Demand (MW)",
                                                                "Rolling 24h Mean Price ($/MWh)",
                                                                "Rolling 7d Mean Price ($/MWh)",
                                                                "Rolling 30d Mean Price ($/MWh)",
                                                                "Rolling 90d Mean Price ($/MWh)",
                                                                "National Rolling 24h Mean Price ($/MWh)",
                                                                "National Rolling 7d Mean Price ($/MWh)",
                                                                "National Rolling 30d Mean Price ($/MWh)",
                                                                "National Rolling 90d Mean Price ($/MWh)"]]
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

SMOOTH_X = {
    "1 Day": "Rolling 24h Mean Price ($/MWh)",
    "7 Days": "Rolling 7d Mean Price ($/MWh)",
    "30 Days": "Rolling 30d Mean Price ($/MWh)",
    "90 Days": "Rolling 90d Mean Price ($/MWh)"
}

aggs = compute_aggs(df)
# x = pd.DataFrame(aggs["1 Month"]["Rolling 30d Mean Price ($/MWh)"])
# y = df["Rolling 30d Mean Price ($/MWh)"]

# st.dataframe(x.head())
# st.dataframe(y.head())


tab_price, tab_demand, tab_patterns, tab_spikes = st.tabs(
    TAB_LABELS, key="active_tab", on_change="rerun"
)

with tab_price:
    # st.dataframe(df.head())
    
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
    if selected_smooth:
        df_smooth = aggs[selected_agg]
        if separate_plot:
            states = sorted(df_smooth["State"].unique())
            n_states = len(states)
            for i, state in enumerate(states):
                state_df = df_smooth[df_smooth["State"] == state]
                fig.add_trace(
                    go.Scatter(
                        x=state_df[AGG_X_COL[selected_agg]],
                        y=state_df[SMOOTH_X[selected_smooth]],
                        mode="lines",
                        name=f"{state} {SMOOTH_X[selected_smooth]}",
                        line=dict(color="gold", dash="dot"),
                        showlegend=False,
                    ),
                    row=n_states - i,
                    col=1,
                )
        else:
            fig.add_trace(go.Scatter(
                x = df_smooth[AGG_X_COL[selected_agg]],
                y = df_smooth[f'National {SMOOTH_X[selected_smooth]}'],
                mode = "lines",
                name = f"National {SMOOTH_X[selected_smooth]}",
                line = dict(color="gold", dash="dot")
            ))

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

    st.plotly_chart(fig, width="stretch", key="price_chart")

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

    st.plotly_chart(fig, width="stretch", key="demand_chart")

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
        st.plotly_chart(fig, width="stretch")

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
        st.plotly_chart(fig, width="stretch")


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
    st.plotly_chart(fig, width="stretch")

    st.subheader(f"Spike Events — {len(spikes):,} intervals above ${spike_threshold}/MWh")
    display_cols = ["Settlement Date", "State", "Price ($/MWh)", "Demand (MW)", "Season", "Hour of Day"]
    st.dataframe(
        spikes[display_cols]
        .sort_values("Price ($/MWh)", ascending=False)
        .reset_index(drop=True),
        width="stretch",
    )