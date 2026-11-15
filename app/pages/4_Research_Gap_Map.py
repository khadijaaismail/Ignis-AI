"""Research Gap Map placeholder page."""

import streamlit as st

from app.components import honesty_banner, inject_css
from core.data import load_experiment_records
from core.gaps import partition_gap_records


inject_css()
honesty_banner()
st.title("Research Gap Map")
groups = partition_gap_records(load_experiment_records())
st.subheader("Placeable flight evidence")
st.dataframe(
    [{"investigation": record.name, "psi_ref": record.psi_ref} for record in groups["placeable"]],
    use_container_width=True,
)
st.subheader("Ground-based modelling (not flight evidence)")
st.dataframe(
    [{"investigation": record.name, "psi_ref": record.psi_ref} for record in groups["ground"]],
    use_container_width=True,
)
st.subheader("Unplaceable")
st.dataframe(
    [
        {
            "investigation": record.name,
            "psi_ref": record.psi_ref,
            "reason": record.conditions_status,
        }
        for record in groups["unplaceable"]
    ],
    use_container_width=True,
)
