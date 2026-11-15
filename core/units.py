"""Conversions from source units to the display units used by the app.

All factors here are team-documented conventions. Original NASA values are kept
alongside converted ones, so rounding here never loses source information.
"""

ATM_TO_PSI_FACTOR = 14.696  # documented factor used throughout IGNIS AI
MMHG_TO_PSI_FACTOR = 14.696 / 760.0
BAR_TO_PSI_FACTOR = 14.5037738
MMHG_TO_ATM_FACTOR = 1.0 / 760.0
BAR_TO_ATM_FACTOR = 0.986923
O2_FRACTION_TO_PCT = 100.0


def oxygen_mole_fraction_to_pct(value: float) -> float:
    """Convert an oxygen mole fraction (0 to 1) to percent, rounded to 4 places."""
    return round(value * O2_FRACTION_TO_PCT, 4)


def atm_to_psi(value: float) -> float:
    """Convert atmospheres to psi (factor 14.696), rounded to 2 places."""
    return round(value * ATM_TO_PSI_FACTOR, 2)


def mmhg_to_atm(value: float) -> float:
    """Convert millimetres of mercury to atmospheres."""
    return value * MMHG_TO_ATM_FACTOR


def bar_to_atm(value: float) -> float:
    """Convert bar to atmospheres using the documented PSI factor."""
    return value * BAR_TO_ATM_FACTOR


def mmhg_to_psi(value: float) -> float:
    """Convert millimetres of mercury to psi, rounded to 2 places."""
    return round(value * MMHG_TO_PSI_FACTOR, 2)


def bar_to_psi(value: float) -> float:
    """Convert bar to psi, rounded to 2 places."""
    return round(value * BAR_TO_PSI_FACTOR, 2)