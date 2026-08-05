import streamlit as st

st.title("Plotly Import Test")

try:
    import plotly
    st.success(f"Plotly imported successfully: {plotly.__version__}")
except Exception as exc:
    st.error("Plotly import failed")
    st.write(repr(exc))