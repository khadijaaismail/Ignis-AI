from core.units import atm_to_psi, bar_to_psi, mmhg_to_psi, oxygen_mole_fraction_to_pct


def test_oxygen_mole_fraction_to_pct_rounds_to_four_places():
    assert oxygen_mole_fraction_to_pct(0.29) == 29.0
    assert oxygen_mole_fraction_to_pct(0.07) == 7.0


def test_atm_to_psi_rounds_to_two_places():
    assert atm_to_psi(0.5) == 7.35


def test_table_pressure_conversions_use_declared_units():
    assert mmhg_to_psi(760) == 14.7
    assert bar_to_psi(1) == 14.5
