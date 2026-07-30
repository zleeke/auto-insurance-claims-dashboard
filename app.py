from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="Insurance Claims Explorer", layout="wide")


@st.cache_data
def load_data() -> pd.DataFrame:
    """Load the insurance claims CSV and clean a few basic columns."""
    data_path = Path("data/insurance_claims.csv")

    if not data_path.exists():
        st.error(f"Could not find the dataset at {data_path}")
        st.stop()

    df = pd.read_csv(data_path)

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

    return df


def main() -> None:
    st.title("Insurance Claims Explorer")
    st.write(
        "This starter app helps you inspect the dataset before turning it into a polished portfolio dashboard."
    )

    df = load_data()

    st.caption(f"Loaded {df.shape[0]} rows and {df.shape[1]} columns.")

    st.subheader("Sample of the data")
    st.dataframe(df.head(10), use_container_width=True)

    st.subheader("Quick summary")
    col1, col2, col3 = st.columns(3)

    if "total_claim_amount" in df.columns:
        col1.metric("Average claim amount", f"${df['total_claim_amount'].mean():,.0f}")
        col2.metric("Total claim amount", f"${df['total_claim_amount'].sum():,.0f}")
    else:
        col1.metric("Average claim amount", "N/A")
        col2.metric("Total claim amount", "N/A")

    if "policy_state" in df.columns:
        col3.metric("Unique policy states", df["policy_state"].nunique())
    else:
        col3.metric("Unique policy states", "N/A")

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

    st.subheader("Claim amount by policy state")
    if "policy_state" in filtered_df.columns and "total_claim_amount" in filtered_df.columns:
        state_summary = (
            filtered_df.groupby("policy_state", dropna=False)["total_claim_amount"].mean().reset_index()
        )
        state_chart = px.bar(
            state_summary,
            x="policy_state",
            y="total_claim_amount",
            title="Average total claim amount by policy state",
            color="policy_state",
        )
        st.plotly_chart(state_chart, use_container_width=True)
    else:
        st.info("The expected columns for this chart are not available in the dataset.")

    st.subheader("Distribution of claim amounts")
    if "total_claim_amount" in filtered_df.columns:
        histogram = px.histogram(
            filtered_df,
            x="total_claim_amount",
            nbins=20,
            title="Distribution of total claim amount",
        )
        st.plotly_chart(histogram, use_container_width=True)
    else:
        st.info("The total_claim_amount column is not available.")

    st.subheader("Incident type breakdown")
    if "incident_type" in filtered_df.columns:
        incident_counts = filtered_df["incident_type"].value_counts().reset_index()
        incident_counts.columns = ["incident_type", "count"]
        incident_chart = px.bar(
            incident_counts,
            x="incident_type",
            y="count",
            title="Count of incidents by type",
            color="incident_type",
        )
        st.plotly_chart(incident_chart, use_container_width=True)
    else:
        st.info("The incident_type column is not available.")


if __name__ == "__main__":
    main()
