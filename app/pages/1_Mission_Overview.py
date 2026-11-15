"""Mission Overview placeholder page."""

import streamlit as st

from app.components import honesty_banner, inject_css


inject_css()
honesty_banner()
st.title("Mission Overview")
