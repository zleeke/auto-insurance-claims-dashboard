# Insurance Claims Dashboard

This project is a beginner-friendly data analytics portfolio dashboard built around auto insurance claims data. The goal is to turn insurance industry knowledge into a clear, interactive analysis that can be shared on LinkedIn and shown to employers.

## Project Overview

This dashboard will explore auto insurance claims data to answer questions such as:
- Which factors are associated with higher claim amounts?
- Are certain vehicle types or regions linked to more frequent claims?
- How do claim characteristics vary across different policy segments?

The project is designed to demonstrate data cleaning, analysis, visualization, and presentation skills using Python.

## Dataset

The project uses the following dataset:
- Source: Kaggle - Auto Insurance Claims Data
- Local file: data/insurance_claims.csv

This file contains insurance-related records that can be used to build charts, metrics, and filters for an interactive dashboard.

## Tools Used

- Python
- Pandas
- Plotly
- Streamlit
- GitHub

## Planned Dashboard Features

- KPI cards for total claims, average claim amount, and claim frequency
- Interactive charts for claim trends and distributions
- Filters for vehicle type, region, or other relevant fields
- A short summary section explaining key insights

## Local Setup

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install required packages:
   ```bash
   pip install streamlit pandas plotly
   ```

3. Run the dashboard locally:
   ```bash
   streamlit run app.py
   ```

## Project Structure

- data/insurance_claims.csv
- README.md
- portfolio_project_plan.md

## Notes

This project is intended to be a simple but polished MVP for a data portfolio. The focus is on clarity, storytelling, and making the analysis easy to understand for hiring managers and recruiters.
