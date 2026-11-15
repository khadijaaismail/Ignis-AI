"""Mission Ranking placeholder page."""

import streamlit as st

from app.components import honesty_banner, inject_css
from core.data import load_experiment_records
from core.ranking import rank_experiments


inject_css()
honesty_banner()
st.title("Mission Ranking")
experiments = load_experiment_records()
if not experiments:
    st.info("No processed investigations are available.")
else:
    ranked = rank_experiments(experiments)
    if not ranked:
        st.info("No eligible measured flight evidence is available for ranking.")
    else:
        st.dataframe(
            [
                {
                    "investigation": result.experiment.name,
                    "score": result.score,
                    "evidence": "; ".join(result.reasons),
                }
                for result in ranked
            ],
            use_container_width=True,
        )
