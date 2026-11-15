# Data discrepancies

| Investigation | Field | Curated value | Table value | Curated source | Table source |
| PSI-159 | o2_stream_max_pct | 85.0 | 39.97 | data/raw/curated/investigations.csv | CFI-G_Normal_Flames_PSI-159.csv; PSI id PSI-159 |
| PSI-68 | o2_chamber_max_pct | 40.0 | 30.0 | data/raw/curated/investigations.csv | Flex2_PSI-68.csv; PSI id PSI-68 |
| PSI-68 | o2_chamber_min_pct | 10.0 | 17.0 | data/raw/curated/investigations.csv | Flex2_PSI-68.csv; PSI id PSI-68 |
| PSI-39 | pressure_min_psi | 3.67 | 7.35 | data/raw/curated/investigations.csv | CFI_PSI-39.csv; PSI id PSI-39 |
| PSI-69 | pressure_min_psi | 7.35 | 0.0 | data/raw/curated/investigations.csv | FLEX_PSI-69.csv; PSI id PSI-69 |
| PSI-69 | pressure_max_psi | 22.04 | 44.86 | data/raw/curated/investigations.csv | FLEX_PSI-69.csv; PSI id PSI-69 |

## Scenario configuration differences
- Scenario `iss` name differs: curated `International Space Station`; configured `ISS`.
- Scenario `lunar_rover` name differs: curated `Lunar pressurized rover`; configured `Lunar rover`.
- Scenario `mars_rover` name differs: curated `Mars pressurized rover`; configured `Mars rover`.
