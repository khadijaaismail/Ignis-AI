# IGNIS AI: rules for Copilot
Project: AI-powered research analyst over NASA PSI microgravity combustion data (NASA Space Apps, Flame in Freefall).
Stack: Python 3.11, Streamlit, custom CSS, Plotly, pandas, NumPy, SciPy (only where appropriate), a file-based data layer (CSV and Parquet in data/processed), BM25 keyword retrieval (rank-bm25) with optional sentence-transformers embeddings, pydantic.

Architecture rules:
- LLM calls go only through llm/adapter.py. Never hardcode a provider, model or key. Read config from environment.
- All reading and writing of data files lives in core/. Streamlit pages call functions in core/data.py and never open files themselves.
- Chart code lives in app/charts.py. Pages call chart functions.
- Use type hints, short functions, docstrings and logging (no print).
- Add or update a pytest test for every function with scoring or parsing logic.

Scientific integrity rules (highest priority):
- Never invent experimental values, findings, citations or URLs. Missing values are empty/None and displayed as Not reported.
- Every AI answer must cite retrieved chunk ids. If retrieval is weak, return insufficient evidence without calling the LLM.
- Label statements as experimental_evidence, interpretation or research_gap.
- NASA PSI currently has no partial-gravity combustion data (LUCI and FM2 are expected to add it). Never present lunar-gravity results. E-FIELD Flames only mimics partial gravity through an electric field: always label it an analog, never true partial gravity.
- Microgravity and normal-gravity results only bound intermediate gravity.
- Rocket and propellant combustion is out of scope.
- Reference conditions from the challenge (Earth 14.7 psi and 21% O2; spacesuit 4.3 psi and 100% O2; expected lunar habitat 30% O2 or more at 10.2 psi or less) are challenge-provided references, not specifications.
- Relevance scores are not safety certifications. Never claim an experiment proves a habitat is safe.
- Keep the original columns and units from NASA files and add converted columns (O2 mole fraction to percent, atm to psi), documented in core/units.py.

Data accuracy rules:
- CFI-G: the up to 85% O2 value is the oxygen-nitrogen stream flowing from the spherical burner, not the chamber atmosphere. The chamber holds nitrogen and a flammable gas. Store stream O2 separately from chamber O2 and leave chamber O2 empty unless a source states it.
- Never set gravity_regime without source evidence. Unreported means unknown. A value inferred from context is marked inferred in provenance. A PSI folder labeled Reduced Gravity is not partial gravity.
- Never plot or compare stream O2 and chamber O2 as the same quantity. A list of tested values (for example 17, 21, 25 and 30 percent O2) is not a range and does not prove every combination of conditions was tested.
- Never hardcode experimental values from memory, in code or in tests. Derive them from the downloaded files. Tests of parsers and conversions use small synthetic fixtures kept separate from production data.
- Do not assume a fixed number of investigations. Work from experiments.csv.
- Every chart has units, axis labels and a legend, marks reference conditions differently from measured data, and shows missing values explicitly.

Reliability rules:
- Every module works independently. If the LLM is unavailable (or DEMO_MODE is on), show the retrieved sources without a generated answer. If embeddings are missing or fail to load, use BM25 keyword search. Never show fabricated results to fill an empty section.

Workflow rules:
- Before coding, state a short plan and list the files you will change. Change only those files.
- Do not overwrite working functionality without saying why. Run the relevant tests after each task.
- No secrets in code. Use .env and .env.example.
- If something is unclear, ask me instead of guessing.
- Prefer rewriting a function or module over appending patches. - Keep files under 300 lines. No dead code.