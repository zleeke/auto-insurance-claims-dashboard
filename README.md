# Auto Insurance Claims Dashboard

This project is a polished Streamlit dashboard for exploring an auto insurance claims dataset. It is designed as a portfolio-ready analytics app that demonstrates data cleaning, interactive visualizations, and user-driven filtering in a clear, presentation-friendly interface.

## What the app does

The dashboard allows you to explore insurance claim patterns through:

- KPI cards for average insured tenure, average insured age, and average claim amount
- Interactive bar charts for incident type and gender distributions
- A time-series view of incidents by month, week, or day
- Sidebar filters for date range, policy state, incident severity, and selected chart dimensions

## Dataset

The app uses the Auto Insurance Claims dataset.

- Source: Kaggle dataset
- Local expected file: data/insurance_claims.csv

If the CSV is not already present locally, the app will attempt to download the dataset through KaggleHub. For the smoothest local experience, place the CSV in the data folder before running the app.

## Tech stack

- Python
- Streamlit
- Plotly
- Pandas
- KaggleHub

## Current project structure

- app.py — main Streamlit dashboard application
- data/insurance_claims.csv — local dataset file
- README.md — project overview and setup instructions
- portfolio_project_plan.md — original planning notes

## Notes

This project is intended to be a simple but polished MVP for a data portfolio. The focus is on clarity, storytelling, and making the analysis easy to understand for hiring managers, recruiters, and other stakeholders.
