"""IGNIS AI Streamlit landing page."""

import sys
from pathlib import Path

import streamlit as st

# Streamlit may execute this file with only the app directory on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.components import honesty_banner, inject_css


st.set_page_config(page_title="IGNIS AI", page_icon="🔥", layout="wide")
inject_css()
honesty_banner()

st.title("IGNIS AI")
st.subheader("Mission-control workspace for NASA combustion research")
st.write("The IGNIS AI dashboard scaffold is ready for evidence-grounded research workflows.")
