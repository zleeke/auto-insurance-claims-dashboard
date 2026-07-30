from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import kagglehub


st.set_page_config(page_title="Auto Insurance Claims Explorer", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: #003f5c;
        color: white;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    [data-testid="stSidebar"] {
        background-color: #594e90;
    }
    [data-testid="stSidebar"] * {
        color: white;
    }
    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #dfe6ee;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.18);
    }
    div[data-testid="stMetric"] [data-testid="stMetricLabel"],
    div[data-testid="stMetric"] [data-testid="stMetricValue"],
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        color: #003f5c;
    }
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] {
        font-weight: 700;
        text-transform: capitalize;
    }
    div[data-testid="stInfo"] {
        background-color: white;
        border: 1px solid #dfe6ee;
        border-radius: 10px;
        padding: 0.7rem 1rem;
        color: #003f5c;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.14);
    }
    .stPlotlyChart > div {
        background-color: white !important;
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.16);
        border-radius: 12px;
        overflow: hidden;
    }
    .stPlotlyChart iframe {
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data() -> pd.DataFrame:
    """Load the insurance claims data from a local CSV first, then fall back to Kaggle."""
    data_path = Path("data/insurance_claims.csv")

    if data_path.exists():
        df = pd.read_csv(data_path)
    else:
        try:
            kagglehub.dataset_download("buntyshah/auto-insurance-claims-data")
            st.info("Kaggle dataset downloaded successfully. Please place the CSV in the data folder to use it locally.")
            st.stop()
        except Exception as exc:
            st.error(f"Failed to load data from both local CSV and Kaggle: {exc}")
            st.stop()

    numeric_columns = [
        "total_claim_amount",
        "injury_claim",
        "property_claim",
        "vehicle_claim",
        "policy_annual_premium",
        "policy_deductable",
        "capital-gains",
        "capital-loss",
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    if "incident_date" in df.columns:
        df["incident_date"] = pd.to_datetime(df["incident_date"], errors="coerce")

    if "months_as_customer" in df.columns:
        df["tenure_years"] = pd.to_numeric(df["months_as_customer"], errors="coerce") / 12

    if "insured_sex" in df.columns:
        df["gender"] = df["insured_sex"].fillna("Unknown").astype(str).str.title()

    return df


def main() -> None:
    df = load_data()

    st.sidebar.header("Filters")
    filtered_df = df.copy()

    if "policy_state" in filtered_df.columns:
        states = sorted(filtered_df["policy_state"].dropna().astype(str).unique())
        selected_states = st.sidebar.multiselect("Policy state", states)
        if selected_states:
            filtered_df = filtered_df[filtered_df["policy_state"].astype(str).isin(selected_states)]

    if "incident_severity" in filtered_df.columns:
        severities = sorted(filtered_df["incident_severity"].dropna().astype(str).unique())
        selected_severities = st.sidebar.multiselect("Incident severity", severities)
        if selected_severities:
            filtered_df = filtered_df[filtered_df["incident_severity"].astype(str).isin(selected_severities)]

    selected_date_range = None
    if "incident_date" in filtered_df.columns:
        date_values = pd.to_datetime(filtered_df["incident_date"], errors="coerce").dropna()
        if not date_values.empty:
            min_date = date_values.min().date()
            max_date = date_values.max().date()
            date_input_value = st.sidebar.date_input(
                "Incident date range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="incident_date_range",
            )
            if isinstance(date_input_value, tuple) and len(date_input_value) == 2:
                start_date, end_date = date_input_value
            else:
                start_date = end_date = date_input_value

            if start_date is not None and end_date is not None:
                filtered_df = filtered_df[
                    (filtered_df["incident_date"] >= pd.Timestamp(start_date))
                    & (filtered_df["incident_date"] <= pd.Timestamp(end_date))
                ]
                selected_date_range = (start_date, end_date)

    if "selected_incident_type" not in st.session_state:
        st.session_state.selected_incident_type = None
    if "selected_gender" not in st.session_state:
        st.session_state.selected_gender = None
    if "selected_claim_range" not in st.session_state:
        st.session_state.selected_claim_range = None

    if st.session_state.selected_incident_type:
        filtered_df = filtered_df[filtered_df["incident_type"].astype(str).isin([st.session_state.selected_incident_type])]

    if st.session_state.selected_gender:
        filtered_df = filtered_df[filtered_df["gender"].astype(str).isin([st.session_state.selected_gender])]

    if st.session_state.selected_claim_range is not None:
        filtered_df = filtered_df[
            (filtered_df["total_claim_amount"] >= st.session_state.selected_claim_range[0])
            & (filtered_df["total_claim_amount"] <= st.session_state.selected_claim_range[1])
        ]

    date_range_text = ""

    if "incident_date" in filtered_df.columns:
        valid_dates = filtered_df["incident_date"].dropna()
        if not valid_dates.empty:
            date_start = valid_dates.min()
            date_end = valid_dates.max()
            date_range_text = f"{date_start.month}/{date_start.day}/{date_start.year} - {date_end.month}/{date_end.day}/{date_end.year}"

    if date_range_text:
        st.title(f"Auto Insurance Claims Explorer ({date_range_text})")
    else:
        st.title("Auto Insurance Claims Explorer")

    metric_col1, metric_col2, metric_col3 = st.columns(3)

    if "tenure_years" in filtered_df.columns:
        metric_col1.metric("Average Insured Tenure", f"{filtered_df['tenure_years'].mean():.1f} years")
    else:
        metric_col1.metric("Average Insured Tenure", "N/A")

    if "age" in filtered_df.columns:
        metric_col2.metric("Average Insured Age", f"{filtered_df['age'].mean():.0f} years")
    else:
        metric_col2.metric("Average Insured Age", "N/A")

    if "total_claim_amount" in filtered_df.columns:
        metric_col3.metric("Average Claim Amount", f"${filtered_df['total_claim_amount'].mean():,.0f}")
    else:
        metric_col3.metric("Average Claim Amount", "N/A")

    col1, col2 = st.columns(2)
    selected_incident_types = []
    selected_genders = []
    selected_claim_range = None

    if "incident_type" in filtered_df.columns:
        incident_counts = filtered_df["incident_type"].dropna().value_counts().reset_index()
        incident_counts.columns = ["incident_type", "count"]
        incident_chart = px.pie(
            incident_counts,
            names="incident_type",
            values="count",
            hole=0.45,
            title="Accidents by incident type",
        )
        incident_chart.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(color="#003f5c"),
            title=dict(
                text="Accidents by incident type",
                x=0,
                xanchor="left",
                font=dict(color="#003f5c", size=16, family="Arial Black"),
            ),
            legend=dict(font=dict(color="#003f5c")),
            xaxis=dict(tickfont=dict(color="#003f5c")),
            yaxis=dict(tickfont=dict(color="#003f5c")),
        )
        with col1:
            incident_selection = st.plotly_chart(
                incident_chart,
                use_container_width=True,
                on_select="rerun",
                selection_mode="points",
                key="incident_chart",
            )
            if isinstance(incident_selection, dict):
                labels = [str(point.get("label")) for point in incident_selection.get("points", []) if point.get("label")]
                if labels:
                    st.session_state.selected_incident_type = labels[0]
                else:
                    st.session_state.selected_incident_type = None
    else:
        col1.info("The incident_type column is not available.")

    if "gender" in filtered_df.columns:
        gender_counts = filtered_df["gender"].dropna().value_counts().reset_index()
        gender_counts.columns = ["gender", "count"]
        gender_chart = px.pie(
            gender_counts,
            names="gender",
            values="count",
            hole=0.45,
            title="Accidents by gender",
        )
        gender_chart.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(color="#003f5c"),
            title=dict(
                text="Accidents by gender",
                x=0,
                xanchor="left",
                font=dict(color="#003f5c", size=16, family="Arial Black"),
            ),
            legend=dict(font=dict(color="#003f5c")),
            xaxis=dict(tickfont=dict(color="#003f5c")),
            yaxis=dict(tickfont=dict(color="#003f5c")),
        )
        with col2:
            gender_selection = st.plotly_chart(
                gender_chart,
                use_container_width=True,
                on_select="rerun",
                selection_mode="points",
                key="gender_chart",
            )
            if isinstance(gender_selection, dict):
                labels = [str(point.get("label")) for point in gender_selection.get("points", []) if point.get("label")]
                if labels:
                    st.session_state.selected_gender = labels[0]
                else:
                    st.session_state.selected_gender = None
    else:
        col2.info("The insured_sex column is not available.")

    if "total_claim_amount" in filtered_df.columns:
        claim_hist = go.Figure(
            go.Histogram(
                x=filtered_df["total_claim_amount"],
                histnorm="percent",
                nbinsx=20,
                texttemplate="%{y:.1f}%",
                textposition="outside",
            )
        )
        claim_hist.update_layout(
            title=dict(
                text="Percentage of accidents by total claim amount",
                x=0,
                xanchor="left",
                font=dict(color="#003f5c", size=16, family="Arial Black"),
            ),
            xaxis_title=dict(text="Total claim amount", font=dict(color="#003f5c", size=16)),
            yaxis_title=dict(text="Percent of accidents", font=dict(color="#003f5c", size=16)),
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(family="Arial", size=13, color="#003f5c"),
            bargap=0.1,
            legend=dict(font=dict(color="#003f5c")),
            xaxis=dict(tickfont=dict(color="#003f5c")),
            yaxis=dict(tickfont=dict(color="#003f5c")),
        )
        claim_hist.update_traces(marker_color="#4c78a8")
        histogram_selection = st.plotly_chart(
            claim_hist,
            use_container_width=True,
            on_select="rerun",
            selection_mode="points",
            key="claim_hist_chart",
        )
        if isinstance(histogram_selection, dict):
            histogram_points = histogram_selection.get("points", [])
            if histogram_points:
                first_point = histogram_points[0]
                x_value = first_point.get("x")
                if x_value is not None:
                    claim_amount_values = filtered_df["total_claim_amount"].dropna()
                    if not claim_amount_values.empty:
                        value_min = claim_amount_values.min()
                        value_max = claim_amount_values.max()
                        if value_max > value_min:
                            bin_width = (value_max - value_min) / 20
                        else:
                            bin_width = 1000
                        st.session_state.selected_claim_range = (x_value - bin_width / 2, x_value + bin_width / 2)
                    else:
                        st.session_state.selected_claim_range = None
                else:
                    st.session_state.selected_claim_range = None
            else:
                st.session_state.selected_claim_range = None
    else:
        st.info("The total_claim_amount column is not available.")

    if "incident_date" in filtered_df.columns:
        valid_dates = filtered_df["incident_date"].dropna()
        if not valid_dates.empty:
            date_start = valid_dates.min()
            date_end = valid_dates.max()
            date_range_text = f"{date_start.month}/{date_start.day}/{date_start.year} - {date_end.month}/{date_end.day}/{date_end.year}"
        else:
            date_range_text = ""
    else:
        date_range_text = ""


if __name__ == "__main__":
    main()
