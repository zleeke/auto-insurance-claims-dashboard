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
        background-color: #346888;
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
        selected_states = st.sidebar.multiselect("Policy State", states)
        if selected_states:
            filtered_df = filtered_df[filtered_df["policy_state"].astype(str).isin(selected_states)]

    if "incident_severity" in filtered_df.columns:
        severities = sorted(filtered_df["incident_severity"].dropna().astype(str).unique())
        selected_severities = st.sidebar.multiselect("Incident Severity", severities)
        if selected_severities:
            filtered_df = filtered_df[filtered_df["incident_severity"].astype(str).isin(selected_severities)]

    selected_date_range = None
    if "incident_date" in filtered_df.columns:
        date_values = pd.to_datetime(filtered_df["incident_date"], errors="coerce").dropna()
        if not date_values.empty:
            min_date = date_values.min().date()
            max_date = date_values.max().date()
            if "incident_date_range" not in st.session_state:
                st.session_state["incident_date_range"] = (min_date, max_date)

            stored_range = st.session_state["incident_date_range"]
            date_filter_mode = st.sidebar.radio(
                "Incident Date Filter",
                ["All dates", "Custom range"],
                index=0 if stored_range == (min_date, max_date) else 1,
                key="incident_date_filter_mode",
                horizontal=True,
            )

            if date_filter_mode == "Custom range":
                date_input_value = st.sidebar.date_input(
                    "Select Date Range",
                    value=stored_range,
                    min_value=min_date,
                    max_value=max_date,
                    format="MM/DD/YYYY",
                    key="incident_date_range_widget",
                )

                def normalize_date_input(value):
                    if isinstance(value, (tuple, list)):
                        flattened = []
                        for item in value:
                            if isinstance(item, (tuple, list)):
                                flattened.extend(normalize_date_input(item))
                            else:
                                flattened.append(item)
                        return flattened
                    return [value]

                values = normalize_date_input(date_input_value)
                if len(values) >= 2:
                    start_date, end_date = values[0], values[1]
                else:
                    start_date = end_date = None

                if start_date is not None and end_date is not None:
                    st.session_state["incident_date_range"] = (start_date, end_date)
                    filtered_df = filtered_df[
                        (filtered_df["incident_date"] >= pd.Timestamp(start_date))
                        & (filtered_df["incident_date"] <= pd.Timestamp(end_date))
                    ]
                    selected_date_range = (start_date, end_date)
            else:
                st.session_state["incident_date_range"] = (min_date, max_date)
                start_date, end_date = min_date, max_date

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
            title="Accidents by Incident Type",
            height=320,
        )
        incident_chart.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(color="#003f5c"),
            title=dict(
                text="Accidents by Incident Type",
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
                height=320,
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
            title="Incidents by Gender",
            height=320,
        )
        gender_chart.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(color="#003f5c"),
            title=dict(
                text="Incidents by Gender",
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
                height=320,
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

    if "incident_date" in filtered_df.columns:
        incident_dates = filtered_df["incident_date"].dropna().copy()
        if not incident_dates.empty:
            date_df = pd.DataFrame({"incident_date": pd.to_datetime(incident_dates, errors="coerce")})
            date_df = date_df.dropna(subset=["incident_date"]).set_index("incident_date")

            grouped_month = date_df.resample("MS").size().rename("count").reset_index()
            grouped_week = date_df.resample("W-SUN").size().rename("count").reset_index()
            grouped_day = date_df.resample("D").size().rename("count").reset_index()

            month_trace = go.Scatter(
                x=grouped_month["incident_date"],
                y=grouped_month["count"],
                mode="lines+markers+text",
                name="Month",
                line=dict(shape="spline", color="#4c78a8"),
                marker=dict(size=8, color="#4c78a8"),
                text=grouped_month["count"],
                textposition="top center",
                hovertemplate="%{x|%b-%Y}: %{y}<extra></extra>",
                visible=False,
            )
            week_trace = go.Scatter(
                x=grouped_week["incident_date"],
                y=grouped_week["count"],
                mode="lines+markers+text",
                name="Week",
                line=dict(shape="spline", color="#4c78a8"),
                marker=dict(size=8, color="#4c78a8"),
                text=grouped_week["count"],
                textposition="top center",
                hovertemplate="%{x|%m/%d/%Y}: %{y}<extra></extra>",
                visible=True,
            )
            day_trace = go.Scatter(
                x=grouped_day["incident_date"],
                y=grouped_day["count"],
                mode="lines+markers+text",
                name="Day",
                line=dict(shape="spline", color="#4c78a8"),
                marker=dict(size=8, color="#4c78a8"),
                text=grouped_day["count"],
                textposition="top center",
                hovertemplate="%{x|%m/%d/%Y}: %{y}<extra></extra>",
                visible=False,
            )

            line_chart = go.Figure(data=[month_trace, week_trace, day_trace])
            line_chart.update_layout(
                title=dict(
                    text="Count of Auto Incidents by Week",
                    x=0,
                    xanchor="left",
                    font=dict(color="#003f5c", size=16, family="Arial Black"),
                ),
                updatemenus=[
                    dict(
                        type="buttons",
                        direction="right",
                        x=0.5,
                        y=-0.18,
                        xanchor="center",
                        yanchor="top",
                        pad=dict(t=10, b=10, l=12, r=12),
                        bgcolor="white",
                        bordercolor="#003f5c",
                        borderwidth=1,
                        font=dict(color="#003f5c", size=13),
                        showactive=True,
                        active=1,
                        buttons=[
                            dict(
                                label="Month",
                                method="update",
                                args=[
                                    {"visible": [True, False, False]},
                                    {
                                        "title": "Count of Auto Incidents by Month",
                                        "xaxis": {
                                            "tickmode": "array",
                                            "tickvals": grouped_month["incident_date"].tolist(),
                                            "ticktext": [d.strftime("%b-%Y") for d in grouped_month["incident_date"]],
                                            "tickfont": {"color": "#003f5c"},
                                            "title": {"text": "", "font": {"color": "#003f5c"}},
                                            "color": "#003f5c",
                                        },
                                    },
                                ],
                            ),
                            dict(
                                label="Week",
                                method="update",
                                args=[
                                    {"visible": [False, True, False]},
                                    {
                                        "title": "Count of Auto Incidents by Week",
                                        "xaxis": {
                                            "tickformat": "%m/%d/%Y",
                                            "tickfont": {"color": "#003f5c"},
                                            "title": {"text": "", "font": {"color": "#003f5c"}},
                                            "color": "#003f5c",
                                        },
                                    },
                                ],
                            ),
                            dict(
                                label="Day",
                                method="update",
                                args=[
                                    {"visible": [False, False, True]},
                                    {
                                        "title": "Count of Auto Incidents by Day",
                                        "xaxis": {
                                            "tickformat": "%m/%d/%Y",
                                            "tickfont": {"color": "#003f5c"},
                                            "title": {"text": "", "font": {"color": "#003f5c"}},
                                            "color": "#003f5c",
                                        },
                                    },
                                ],
                            ),
                        ],
                    )
                ],
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(family="Arial", size=13, color="#003f5c"),
                legend=dict(font=dict(color="#003f5c")),
                xaxis=dict(tickfont=dict(color="#003f5c"), tickformat="%m/%d/%Y", title="", color="#003f5c"),
                yaxis=dict(title=dict(text="Count of Incidents", font=dict(color="#003f5c", size=16)), tickfont=dict(color="#003f5c")),
                margin=dict(t=100, b=100),
                height=350,
            )
            st.plotly_chart(
                line_chart,
                use_container_width=True,
                height=350,
                key="incident_line_chart",
            )
        else:
            st.info("No incident dates are available to build the time series.")
    else:
        st.info("The incident_date column is not available.")

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
