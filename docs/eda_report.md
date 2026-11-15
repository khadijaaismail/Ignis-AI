# EDA report

Generated read-only from `data/processed/experiments.csv` and each discovered CSV under `data/raw/psi_tables/`. Blank cells and explicit markers (`NA`, `N/A`, `null`, `not reported`) are missing; numeric zero is never missing. Source rows are not removed or rewritten.

## Source-file integrity

| Source path | Investigation reference | Rows | Duplicate rows | Issues |
| --- | --- | --- | --- | --- |
| ACME_BRE_PSI-20.csv | PSI-20 | 18 | 0 | none |
| BASS-II_PSI-25.csv | PSI-25 | 129 | 0 | none |
| BASS_PSI-26.csv | PSI-26 | 122 | 0 | none |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | 179 | 0 | none |
| CFI_PSI-39.csv | PSI-39 | 87 | 8 | none |
| Flex2_PSI-68.csv | PSI-68 | 8 | 0 | none |
| FLEX_PSI-69.csv | PSI-69 | 274 | 0 | none |
| PSI-68_Experimental table_Flex2.csv | PSI-68 | 8 | 0 | none |
| Saffire-I_PSI-98.csv | PSI-98 | 4 | 0 | none |
| Saffire-II_PSI-99.csv | PSI-99 | 15 | 0 | none |
| Saffire-III_PSI-100.csv | PSI-100 | 2 | 0 | none |
| SAME-R_PSI-101.csv | PSI-101 | 109 | 0 | none |
| SAME_PSI-102.csv | PSI-102 | 8 | 0 | none |
| Slice_PSI-106.csv | PSI-106 | 12 | 0 | none |
| Spice_PSI-107.csv | PSI-107 | 469 | 34 | none |

## Completeness matrix

| Investigation | Investigation type | Include in ranking | Chamber O2 | Burner-stream O2 | Pressure | Airflow | Gravity regime | Safety focus | Conditions status | Test rows | Outcome column names | Conflicts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bass | flight | True | Not reported | Not reported | Not reported | Not reported | microgravity | prevention | stated_in_text | BASS_PSI-26.csv: 122 rows | Not reported | no |
| bass-ii | flight | True | 22.2, 21.0, 15.0, 17.3, 17.5, 17.4, 20.8, 20.7, 21.7, 21.8, 18.9, 19.1, 18.0, 20.1, 20.0, 19.2, 18.8, 17.9, 19.0, 14.8, 15.1, 14.2, 16.7, 16.0, 15.7, 15.5, 15.4, 13.6, 15.9, 14.6, 16.3, 17.1, 14.5, 15.2, 15.3, 16.5, 17.7, 18.5, 19.3, 16.4, 17.6, 17.0, 20.6, 18.4, 18.2, 16.8, 20.9, 17.2, 18.7, 16.9 | Not reported | Not reported | Not reported | microgravity | prevention | reported_table | BASS-II_PSI-25.csv: 129 rows | BASS-II_PSI-25.csv: Final CO (ppm), BASS-II_PSI-25.csv: Final CO2 % by vol, BASS-II_PSI-25.csv: Initial CO (ppm), BASS-II_PSI-25.csv: Initial CO2 % by vol | no |
| saffire-i | flight | True | Not reported | Not reported | Not reported | 20.0 | microgravity | prevention | reported_table | Saffire-I_PSI-98.csv: 4 rows | Saffire-I_PSI-98.csv: Burn Time (s) | no |
| saffire-ii | flight | True | Not reported | Not reported | Not reported | 20.0 | microgravity | prevention | reported_table | Saffire-II_PSI-99.csv: 15 rows | Saffire-II_PSI-99.csv: 1-g Burn Length, Saffire-II_PSI-99.csv: 1-g Spread Rate, Saffire-II_PSI-99.csv: ?-g Burn Length, Saffire-II_PSI-99.csv: ?-g Spread Length, Saffire-II_PSI-99.csv: Burn Time (s) | no |
| saffire-iii | flight | True | Not reported | Not reported | Not reported | 30.0 | microgravity | prevention | unknown | Saffire-III_PSI-100.csv: 2 rows | Not reported | no |
| same | flight | True | Not reported | Not reported | Not reported | 5.0 | microgravity | detection | unknown | SAME_PSI-102.csv: 8 rows | Not reported | no |
| same-r | flight | True | Not reported | Not reported | Not reported | 8.1 | microgravity | detection | unknown | SAME-R_PSI-101.csv: 109 rows | Not reported | no |
| flex | flight | True | 21.0, 34.0, 30.0, 20.0, 18.0, 15.0, 14.0, 13.0, 12.0, 25.0, 24.0, 23.0, 17.0, 16.0, 19.0 | Not reported | 14.65, 14.73, 14.78, 14.7, 14.72, 14.74, 44.86, 44.84, 40.11, 39.75, 39.96, 40.07, 29.89, 30.05, 10.42, 10.43, 10.45, 10.48, 10.5, 10.39, 10.41, 10.46, 10.44, 14.83, 14.87, 14.9, 14.91, 14.84, 14.85, 10.33, 10.34, 10.35, 14.86, 14.88, 14.89, 14.79, 14.92, 10.47, 10.49, 10.52, 10.53, 14.95, 14.96, 14.97, 14.81, 14.8, 14.93, 10.37, 10.32, 10.38, 10.26, 0.0, 10.36, 10.27, 10.3, 10.18, 10.29, 14.77, 14.76, 14.82, 14.71, 14.69, 10.28, 14.67, 14.68, 14.66, 14.54, 14.55, 14.58, 14.62, 14.64, 14.63, 14.75, 14.61, 14.57, 10.24, 10.23, 10.2, 10.21, 10.31, 10.25 | Not reported | microgravity | suppression | reported_table | FLEX_PSI-69.csv: 274 rows | FLEX_PSI-69.csv: Burn time; s, FLEX_PSI-69.csv: Burning rate; mm, FLEX_PSI-69.csv: CO initial ambient composition; mole fraction, FLEX_PSI-69.csv: Visible flame extinction diameter; mm | yes |
| flex-2 | flight | True | 17.0, 21.0, 25.0, 30.0 | Not reported | 7.35, 14.7, 22.04, 29.39, 44.09 | 0.1 | microgravity | Not reported | reported_table | Flex2_PSI-68.csv: 8 rows; PSI-68_Experimental table_Flex2.csv: 8 rows | Not reported | yes |
| cfi | flight | True | 21.0, 17.0 | Not reported | 14.7, 18.37, 29.39, 44.09, 73.48, 11.02, 7.35 | Not reported | microgravity | Not reported | reported_table | CFI_PSI-39.csv: 87 rows | Not reported | yes |
| cfi-g | flight | True | Not reported | 39.39, 38.9823, 38.6321, 38.2905, 38.0427, 37.9858, 37.6135, 37.3392, 36.9578, 36.455, 21.01, 20.9639, 18.02, 17.9686, 39.57, 39.3032, 39.0548, 38.8126, 38.6222, 38.2509, 38.1212, 38.0669, 23.41, 23.3649, 23.3255, 39.26, 38.4639, 37.7171, 36.9281, 35.8532, 35.4241, 35.3757, 35.2938, 20.97, 20.8586, 20.7474, 20.6695, 39.54, 39.4045, 39.1274, 38.6795, 37.9544, 37.7664, 37.7096, 37.6528, 36.6423, 21.25, 21.2225, 21.2005, 21.1798, 21.1592, 21.1403, 39.45, 39.4119, 38.9157, 38.4376, 21.11, 21.1072, 21.1045, 21.07, 21.0685, 21.0654, 21.0623, 21.0616, 21.0503, 21.0241, 21.67, 21.669, 21.6669, 21.6664, 21.6661, 21.6586, 21.6435, 21.6404, 21.6372, 39.96, 39.7259, 39.4769, 38.9509, 37.1242, 35.7499, 35.5684, 35.3678, 35.2403, 21.0, 20.9134, 20.8928, 38.87, 37.59, 36.3879, 34.0808, 33.4934, 33.2446, 39.85, 39.6626, 39.4842, 39.198, 38.8939, 38.4152, 38.3585, 38.2061, 39.97, 39.4967, 39.0018, 37.9326, 37.2086, 20.962, 20.929, 20.8929, 20.839, 20.7541, 20.7221, 38.86, 38.3172, 37.8522, 37.2052, 35.544, 39.6546, 39.5373, 39.4311, 39.2492, 39.0816, 38.9606, 38.9263, 38.5474, 38.475, 38.4056, 39.93, 39.4233, 38.9271, 38.8319, 38.7191, 38.6174, 39.78, 39.4947, 38.8455, 38.5436, 38.2657, 38.0784, 35.8976, 20.9, 17.9392, 37.5721, 21.0194, 35.0765, 20.876, 31.4456, 38.0654, 36.0352, 20.6622, 34.6861, 38.3001, 38.3428, 37.6958 | 13.7, 14.7, 7.35, 29.39, 44.09 | Not reported | microgravity | Not reported | reported_table | CFI-G_Normal_Flames_PSI-159.csv: 179 rows | CFI-G_Normal_Flames_PSI-159.csv: Cool flame?, CFI-G_Normal_Flames_PSI-159.csv: Flame Type, CFI-G_Normal_Flames_PSI-159.csv: burn time (sec) | yes |
| e-field-flames | flight | True | Not reported | Not reported | Not reported | Not reported | microgravity | Not reported | unknown | Not reported | Not reported | no |
| flame-design | flight | True | Not reported | Not reported | Not reported | Not reported | microgravity | Not reported | unknown | Not reported | Not reported | no |
| acme-cld-flame | flight | True | Not reported | Not reported | Not reported | Not reported | microgravity | Not reported | unknown | Not reported | Not reported | no |
| acme-s-flame | flight | True | Not reported | Not reported | Not reported | Not reported | microgravity | Not reported | unknown | Not reported | Not reported | no |
| bre | flight | True | Not reported | Not reported | Not reported | Not reported | microgravity | prevention | planned_not_confirmed | ACME_BRE_PSI-20.csv: 18 rows | Not reported | no |
| spice | flight | True | Not reported | Not reported | Not reported | 5.4 | microgravity | Not reported | unknown | Spice_PSI-107.csv: 469 rows | Spice_PSI-107.csv: GMT  Flame Off | no |
| slice | flight | True | Not reported | Not reported | Not reported | Not reported | microgravity | Not reported | unknown | Slice_PSI-106.csv: 12 rows | Not reported | no |
| daft | flight | True | Not reported | Not reported | Not reported | Not reported | microgravity | detection | unknown | Not reported | Not reported | no |
| psi-117 | ground | False | Not reported | Not reported | Not reported | Not reported | unknown | Not reported | unknown | Not reported | Not reported | no |
| psi-62 | ground | False | Not reported | Not reported | Not reported | Not reported | unknown | Not reported | unknown | Not reported | Not reported | no |
| psi-60 | ground | False | Not reported | Not reported | Not reported | Not reported | unknown | Not reported | unknown | Not reported | Not reported | no |
| psi-142 | ground | False | Not reported | Not reported | Not reported | Not reported | unknown | Not reported | unknown | Not reported | Not reported | no |
| psi-115 | ground | False | Not reported | Not reported | Not reported | Not reported | unknown | Not reported | unknown | Not reported | Not reported | no |

## Column profiles

| Source path | Investigation reference | Column | Type | Count | Missing | Missing % | Unique | Unique values |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ACME_BRE_PSI-20.csv | PSI-20 | Year | numeric | 18 | 0 | 0.0 | 3 | 2019, 2020, 2021 |
| ACME_BRE_PSI-20.csv | PSI-20 | Month | categorical | 18 | 0 | 0.0 | 7 | Feb, March, April, Sept, Oct, Dec, Jan |
| ACME_BRE_PSI-20.csv | PSI-20 | Date | numeric | 18 | 0 | 0.0 | 12 | 8, 20, 25, 4, 7, 11, 28, 1 ... |
| ACME_BRE_PSI-20.csv | PSI-20 | Burner Size (mm) | numeric | 18 | 0 | 0.0 | 2 | 25, 50 |
| ACME_BRE_PSI-20.csv | PSI-20 | Fuel Bottle | categorical | 18 | 0 | 0.0 | 4 | 100% C2H4, 50% C2H4, 100%C2H4, 100% CH4 |
| ACME_BRE_PSI-20.csv | PSI-20 | Oxygen Conc (percent) | categorical | 18 | 0 | 0.0 | 10 | 21; 26.5; 40, 26.5; 34, 21; 26.5; 34; 40, 26.5; 40, 3400%, 2100%, 21; 26.5; 34, 25; 34; 40 ... |
| ACME_BRE_PSI-20.csv | PSI-20 | Flames Ignited | numeric | 18 | 0 | 0.0 | 12 | 10, 8, 6, 7, 0, 9, 13, 21 ... |
| ACME_BRE_PSI-20.csv | PSI-20 | Notes | text | 2 | 16 | 88.89 | 2 | Oxygen Conc. (as diluted with nitrogen on a volume basis) was varied between tests where approximate concentrations for tests that ignited are listed. The chamber pressures were also varied but are not identified in this summary table., Flames Ignited is the number ignited on that day (neglecting the day change on ISS). |
| BASS-II_PSI-25.csv | PSI-25 | PI | categorical | 129 | 0 | 0.0 | 6 | Bhattacharjee, Ferkul, Miller, Olson, Fernandez-Pello, T'ien |
| BASS-II_PSI-25.csv | PSI-25 | Test # | text | 129 | 0 | 0.0 | 129 | B1, B2, B3, B4, B5, B6, B7, B8 ... |
| BASS-II_PSI-25.csv | PSI-25 | Date | text | 129 | 0 | 0.0 | 30 | 2/19/2014, 7/7/2014, 7/2/2014, 8/4/2014, 7/28/2014, 8/1/2014, 6/24/2014, 2/20/2014 ... |
| BASS-II_PSI-25.csv | PSI-25 | GMT | numeric | 129 | 0 | 0.0 | 29 | 50, 188, 183, 216, 209, 213, 175, 51 ... |
| BASS-II_PSI-25.csv | PSI-25 | Sample # | text | 129 | 0 | 0.0 | 107 | 147, 155, 148, 159, 156, 153m, 161, 157m ... |
| BASS-II_PSI-25.csv | PSI-25 | Fuel Sample Material | text | 129 | 0 | 0.0 | 51 | 100 micron PMMA film   2 cm wide, 200 micron PMMA film   2 cm wide, 100 micron film   2 cm wide, 300 micron PMMA film   2 cm wide, 200 micron  2 cm wide, 2 cm 0.1 mm PMMA film, 400 micron film   2 cm wide, 2 cm   0.2 mm PMMA film ... |
| BASS-II_PSI-25.csv | PSI-25 | Flow restrictor | numeric | 129 | 0 | 0.0 | 3 | 2, 0, 1 |
| BASS-II_PSI-25.csv | PSI-25 | Fan display | text | 116 | 13 | 10.08 | 99 | 62, 47, 61, 59, 0.9   1.3   2.75, 1.4    incr to 10.0, 0.6   0.35, 1.7 (52)   1.25   0.9   0.6   0.4   0.35 ... |
| BASS-II_PSI-25.csv | PSI-25 | Air display | text | 125 | 4 | 3.1 | 90 | 5, 2, 3   5   approaching 10, 10   max, 2   <1, 5  4  3  2  1, 5   3   1   <1, 10   5  4  3  2  1 ... |
| BASS-II_PSI-25.csv | PSI-25 | Radiometer gain   (1000   250   50   10) | categorical | 129 | 0 | 0.0 | 14 | 50, 10, 250, 250>50>250, 250>50, 50>250, 50   250, 250  50  250 ... |
| BASS-II_PSI-25.csv | PSI-25 | Total Frames Shot | text | 128 | 1 | 0.78 | 109 | 57, 253, 137, 206, 80, 84, 226, 45 ... |
| BASS-II_PSI-25.csv | PSI-25 | Calibrated  initial O2 % by vol | numeric | 129 | 0 | 0.0 | 50 | 22.2, 21, 15, 17.3, 17.5, 17.4, 20.8, 20.7 ... |
| BASS-II_PSI-25.csv | PSI-25 | Calibrated final O2 % by vol | numeric | 127 | 2 | 1.55 | 65 | 22.2, 1.6, 21.8, 21.9, 20.9, 22.1, 20.5, 20.8 ... |
| BASS-II_PSI-25.csv | PSI-25 | Initial CO2 % by vol | numeric | 127 | 2 | 1.55 | 52 | 0.44, 0.43, 0.33, 0.45, 0.51, 0, 0.47, 0.2 ... |
| BASS-II_PSI-25.csv | PSI-25 | Final CO2 % by vol | numeric | 123 | 6 | 4.65 | 80 | 0.44, 0.49, 0.51, 0.43, 0.41, 0.58, 0.35, 0.47 ... |
| BASS-II_PSI-25.csv | PSI-25 | Initial CO (ppm) | text | 127 | 2 | 1.55 | 66 | 0, 6, 12, -1, 1, 17, 0.2, 103 ... |
| BASS-II_PSI-25.csv | PSI-25 | Final CO (ppm) | text | 124 | 5 | 3.88 | 99 | 6, 19, 10, 12, 0.3, 17, 131, 23 ... |
| BASS_PSI-26.csv | PSI-26 | Date | text | 122 | 0 | 0.0 | 33 | 3/30/2012, 4/5/2012, 4/9/2012, 5/2/2012, 5/10/2012, 5/11/2012, 6/5/2012, 6/11/2012 ... |
| BASS_PSI-26.csv | PSI-26 | GMT | numeric | 122 | 0 | 0.0 | 31 | 90, 96, 100, 123, 131, 132, 157, 163 ... |
| BASS_PSI-26.csv | PSI-26 | As Run Test # | numeric | 121 | 1 | 0.82 | 116 | 1, 2, 3, 4, 5, 6, 7, 8 ... |
| BASS_PSI-26.csv | PSI-26 | Test # | text | 121 | 1 | 0.82 | 117 | 1, 42, 18, 7, 8, 43, 44, 45 ... |
| BASS_PSI-26.csv | PSI-26 | Sample # | numeric | 121 | 1 | 0.82 | 40 | 4, 24, 19, 10, 11, 12, 2, 27 ... |
| BASS_PSI-26.csv | PSI-26 | Fuel Sample Material | text | 122 | 0 | 0.0 | 34 | SIBAL 2 cm, PMMA sphere 2 cm, PMMA sphere 1 cm, SIBAL 1 cm, Nomex blend 2 cm, PMMA 2 cm, PMMA 1 cm, 2 cm sphere ... |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | Flame Type | categorical | 179 | 0 | 0.0 | 1 | Normal |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | Day | numeric | 179 | 0 | 0.0 | 11 | 1, 2, 3, 4, 5, 6, 7, 8 ... |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | Fuel | categorical | 179 | 0 | 0.0 | 6 | ethane, 50% butane, propane, 30% butane, 30% propane, 30% ethane |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | Test | text | 179 | 0 | 0.0 | 179 | 21088A1, 21088 B1, 21088 C1, 21088 D1, 21088 F1, 21088 G1, 21088 H1, 21088 J1 ... |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | Cool flame? | categorical | 8 | 171 | 95.53 | 8 | no, PCI-hot, yes, PCI-D, yes, PCI-B, yes, PCI-C, yes, PCI-E, yes, PCI-A, yes, PCI-G, yes, PCI-F |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | XO2 before test | numeric | 179 | 0 | 0.0 | 139 | 0.3939, 0.389822946, 0.386321188, 0.382905163, 0.380426741, 0.379858042, 0.376135171, 0.373391583 ... |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | XO2  after test | numeric | 179 | 0 | 0.0 | 136 | 0.389822946, 0.386321188, 0.382905163, 0.380426741, 0.379858042, 0.376135171, 0.373391583, 0.369578072 ... |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | approx p (bar) | numeric | 179 | 0 | 0.0 | 5 | 0.9443956, 1.0133, 0.50665, 2.0266, 3.0399 |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | Xf | numeric | 179 | 0 | 0.0 | 14 | 1, 0.5, 0.25, 0.125, 0.02385, 0.031, 0.02717, 0 ... |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | mHC (mg/s) | numeric | 179 | 0 | 0.0 | 25 | 2, 1, 0.5, 1.6, 1.3, 0.8, 1.2, 0.6 ... |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | TFP | boolean-like | 179 | 0 | 0.0 | 2 | No, Yes |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | Tad (K) | text | 179 | 0 | 0.0 | 145 | 2719.323211, 2713.594987, 2708.596221, 2703.647801, 2700.011998, 2639.215662, 2633.824861, 2512.315217 ... |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | Zst | text | 179 | 0 | 0.0 | 145 | 0.102651783, 0.101747543, 0.100968644, 0.100206801, 0.099652813, 0.175931996, 0.174581055, 0.292108087 ... |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | Hot ignition | boolean-like | 179 | 0 | 0.0 | 2 | Yes, No |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | burn time (sec) | numeric | 175 | 4 | 2.23 | 78 | 50, 43, 42, 61, 28, 62, 37, 98 ... |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | Self-ext or flow term | categorical | 179 | 0 | 0.0 | 3 | SE, FT, - |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | Peak burner T (C ) | text | 179 | 0 | 0.0 | 130 | 290.617198, 276.009368, 266.374008, 459.195642, 532.162657, 226.739332, 416.786789, 164.051351 ... |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | Comments | text | 44 | 135 | 75.42 | 32 | hit burner T limit, FC=flow cut, Lowest flow rate for ignition, Manually stopped the flow. No cool flame detected., Extinction detected. Fuel flow stopped in 6 sec after PMT dropped to 0., Igniter voltage: 2V and 2.5V for 10 sec each. No ignition.Retracted too early., Igniter voltage: 2.25V and 2.75V for 10 sec each. No ignition., Igniter voltage: 2V and 2.5V for 10 sec each. No ignition. PMT2 gain 0.04V. ... |
| CFI_PSI-39.csv | PSI-39 | Flex Number | numeric | 87 | 0 | 0.0 | 79 | 1206, 1207, 1208, 1209, 1210, 1211, 1213, 1215 ... |
| CFI_PSI-39.csv | PSI-39 | Test Date | text | 87 | 0 | 0.0 | 23 | 9-Mar-17, 21-Mar-17, 27-Mar-17, 31-Mar-17, 5-Apr-17, 22-Jun-17, 28-Jun-17, 26-Jun-17 ... |
| CFI_PSI-39.csv | PSI-39 | Local Time | text | 87 | 0 | 0.0 | 79 | 02:03:08 pm est, 03:53:26 pm est, 04:25:22 pm est, 04:49:43 pm est, 05:43:01 pm est, 10:17:45 am est, 10:37:21 am est, 11:45:48 am est ... |
| CFI_PSI-39.csv | PSI-39 | CIR | text | 87 | 0 | 0.0 | 79 | f068a03, f068a07, f068a08, f068a09, f068a11, f080a01, f086a04, f086a06 ... |
| CFI_PSI-39.csv | PSI-39 | Pressure | numeric | 87 | 0 | 0.0 | 7 | 1 atm, 1.25 atm, 2 atm, 3 atm, 5 atm, 0.75 atm, 0.5 atm |
| CFI_PSI-39.csv | PSI-39 | Oxygen | numeric | 87 | 0 | 0.0 | 2 | 0.21, 0.17 |
| CFI_PSI-39.csv | PSI-39 | Nitrogen | numeric | 87 | 0 | 0.0 | 5 | 0.79, 0.83, 0.76, 0.5, 0.2 |
| CFI_PSI-39.csv | PSI-39 | Helium | numeric | 87 | 0 | 0.0 | 3 | 0, 0.29, 0.59 |
| CFI_PSI-39.csv | PSI-39 | Fiber | boolean-like | 78 | 9 | 10.34 | 2 | No, Yes |
| CFI_PSI-39.csv | PSI-39 | Fuel | categorical | 87 | 0 | 0.0 | 3 | C12H26, [.75]/[.25] C12H26/iso-dodecane, [.60]/[.40] C12H26/iso-dodecane |
| Flex2_PSI-68.csv | PSI-68 | Sample (Fuel Type) | categorical | 8 | 0 | 0.0 | 8 | IsoOctane (pure), n-Octane (pure), Heptane (pure), Decane (pure), Ethanol (pure), Propanol (95%) Glycerol (5%) (mixture), Heptane (50%) IsoOctane (50%) (mixture), Propanol (80%) Glycerol (20%) (mixture) |
| Flex2_PSI-68.csv | PSI-68 | Initial Droplet Diameter (mm) | categorical | 8 | 0 | 0.0 | 1 | 1.5 - 5 |
| Flex2_PSI-68.csv | PSI-68 | Ambient Gas Mixture | categorical | 8 | 0 | 0.0 | 1 | O2/N2 or O2/He |
| Flex2_PSI-68.csv | PSI-68 | Oxygen Mole Fraction | categorical | 8 | 0 | 0.0 | 1 | 0.17; 0.21;0.25; 0.3 |
| Flex2_PSI-68.csv | PSI-68 | Ambient Pressure (atm) | categorical | 8 | 0 | 0.0 | 1 | 0.5; 1.0; 1.5; 2.0; or 3.0 |
| Flex2_PSI-68.csv | PSI-68 | Ambient Temperature (C) | numeric | 8 | 0 | 0.0 | 1 | 25 |
| Flex2_PSI-68.csv | PSI-68 | Flow Velocity (cm/s) | categorical | 8 | 0 | 0.0 | 1 | 0.1 - 5 |
| FLEX_PSI-69.csv | PSI-69 | FLEX Test # | numeric | 274 | 0 | 0.0 | 274 | 1, 2, 3, 4, 5, 6, 7, 8 ... |
| FLEX_PSI-69.csv | PSI-69 | FLEX Identifier | text | 274 | 0 | 0.0 | 273 | 20CAL08, 20CAL10, 20CAL12, 30CAL02, 30CAL03, 40CAL01, 20CAL13, 30CAL06 ... |
| FLEX_PSI-69.csv | PSI-69 | Test Date | text | 274 | 0 | 0.0 | 80 | 3/5/2009, 3/31/2009, 4/10/2009, 5/22/2009, 6/25/2009, 6/29/2009, 7/1/2009, 8/26/2009 ... |
| FLEX_PSI-69.csv | PSI-69 | Test GMT | text | 273 | 1 | 0.36 | 269 | 17:22:03, 19:20:06, 21:17:46, 17:16:18, 19:00:48, 20:05:49, 13:26:11, 18:07:15 ... |
| FLEX_PSI-69.csv | PSI-69 | Fuel | categorical | 274 | 0 | 0.0 | 2 | Methanol, Heptane |
| FLEX_PSI-69.csv | PSI-69 | Ambient pressure; mmHg | numeric | 274 | 0 | 0.0 | 183 | 757.7, 762, 764.2, 760, 761.3, 762.4, 2319.7, 2318.8 ... |
| FLEX_PSI-69.csv | PSI-69 | O initial ambient composition; mole fraction | numeric | 274 | 0 | 0.0 | 15 | 0.21, 0.34, 0.3, 0.2, 0.18, 0.15, 0.14, 0.13 ... |
| FLEX_PSI-69.csv | PSI-69 | N initial ambient composition; mole fraction | numeric | 274 | 0 | 0.0 | 33 | 0.79, 0.09, 0.66, 0.7, 0.8, 0.82, 0.81, 0.85 ... |
| FLEX_PSI-69.csv | PSI-69 | CO initial ambient composition; mole fraction | numeric | 274 | 0 | 0.0 | 14 | 0, 0.7, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4 ... |
| FLEX_PSI-69.csv | PSI-69 | He initial ambient composition; mole fraction | numeric | 274 | 0 | 0.0 | 10 | 0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35 ... |
| FLEX_PSI-69.csv | PSI-69 | Droplet initial diameter; mm | text | 268 | 6 | 2.19 | 164 | 1.69, 1.86, 1.61, 2.06, 1.92, 2.54, 1.87, 2.95 ... |
| FLEX_PSI-69.csv | PSI-69 | Visible flame extinction diameter; mm | text | 225 | 49 | 17.88 | 146 | 0.89, 0.94, 0.92, 0.81, 1.53, 1, 1.77, 1.56 ... |
| FLEX_PSI-69.csv | PSI-69 | Burning rate; mm | numeric | 258 | 16 | 5.84 | 60 | 0.52, 0.6, 0.58, 0.48, 0.51, 0.67, 0.79, 0.37 ... |
| FLEX_PSI-69.csv | PSI-69 | Burn time; s | text | 268 | 6 | 2.19 | 164 | 4.3, 5, 3.2, 7.64, 6.34, 9.6, 5.3, 14.8 ... |
| FLEX_PSI-69.csv | PSI-69 | Test end | categorical | 274 | 0 | 0.0 | 3 | Disruption, Extinction, Completion |
| PSI-68_Experimental table_Flex2.csv | PSI-68 | Sample (Fuel Type) | categorical | 8 | 0 | 0.0 | 8 | IsoOctane (pure), n-Octane (pure), Heptane (pure), Decane (pure), Ethanol (pure), Propanol (95%) Glycerol (5%) (mixture), Heptane (50%) IsoOctane (50%) (mixture), Propanol (80%) Glycerol (20%) (mixture) |
| PSI-68_Experimental table_Flex2.csv | PSI-68 | Initial Droplet Diameter (mm) | categorical | 8 | 0 | 0.0 | 1 | 1.5 - 5 |
| PSI-68_Experimental table_Flex2.csv | PSI-68 | Ambient Gas Mixture | categorical | 8 | 0 | 0.0 | 1 | O2/N2 or O2/He |
| PSI-68_Experimental table_Flex2.csv | PSI-68 | Oxygen Mole Fraction | categorical | 8 | 0 | 0.0 | 1 | 0.17; 0.21;0.25; 0.3 |
| PSI-68_Experimental table_Flex2.csv | PSI-68 | Ambient Pressure (atm) | categorical | 8 | 0 | 0.0 | 1 | 0.5; 1.0; 1.5; 2.0; or 3.0 |
| PSI-68_Experimental table_Flex2.csv | PSI-68 | Ambient Temperature (C) | numeric | 8 | 0 | 0.0 | 1 | 25 |
| PSI-68_Experimental table_Flex2.csv | PSI-68 | Flow Velocity (cm/s) | categorical | 8 | 0 | 0.0 | 1 | 0.1 - 5 |
| Saffire-I_PSI-98.csv | PSI-98 | Sample Number | categorical | 4 | 0 | 0.0 | 4 | S1, S2, F1C1/F1C2, F2C1/F2C2 |
| Saffire-I_PSI-98.csv | PSI-98 | Material | categorical | 4 | 0 | 0.0 | 3 | SIBAL Fabric, Pre-test flow visulation data for sample 1, Pre-test flow visulation data for sample 2 |
| Saffire-I_PSI-98.csv | PSI-98 | Sample Thickness (cm) | numeric | 2 | 2 | 50.0 | 1 | 0.37 |
| Saffire-I_PSI-98.csv | PSI-98 | Sample Length (cm) | numeric | 2 | 2 | 50.0 | 1 | 40.6 |
| Saffire-I_PSI-98.csv | PSI-98 | Sample Width (cm) | numeric | 2 | 2 | 50.0 | 1 | 94 |
| Saffire-I_PSI-98.csv | PSI-98 | Air Flow (cm/s) | numeric | 2 | 2 | 50.0 | 1 | 20 |
| Saffire-I_PSI-98.csv | PSI-98 | Percent O2 | categorical | 2 | 2 | 50.0 | 2 | 21.5 - 21.7, ~ 21.5 |
| Saffire-I_PSI-98.csv | PSI-98 | Ignition Power (W) | numeric | 2 | 2 | 50.0 | 1 | 182 |
| Saffire-I_PSI-98.csv | PSI-98 | Ignition Time (s) | numeric | 2 | 2 | 50.0 | 1 | 8 |
| Saffire-I_PSI-98.csv | PSI-98 | Burn Time (s) | numeric | 2 | 2 | 50.0 | 2 | 420, 70 |
| Saffire-I_PSI-98.csv | PSI-98 | Flow Direction | categorical | 2 | 2 | 50.0 | 2 | Concurrent, Opposed |
| Saffire-I_PSI-98.csv | PSI-98 | Camera 1 | categorical | 2 | 2 | 50.0 | 2 | S1C1, S2C1 |
| Saffire-I_PSI-98.csv | PSI-98 | Camera 2 | categorical | 2 | 2 | 50.0 | 2 | S1C2, S2C2 |
| Saffire-II_PSI-99.csv | PSI-99 | Sample Number | categorical | 15 | 0 | 0.0 | 15 | 2-1, 2-2, 2-3, 2-4, 2-5, 2-6, 2-7, 2-8 ... |
| Saffire-II_PSI-99.csv | PSI-99 | Material | categorical | 9 | 6 | 40.0 | 6 | Silicone, Cotton-Fiberglass (SIBAL), PMMA & Nomex, PMMA, Pre-test flow visulation data for sample 2-1, Pre-test flow visulation data for sample 2-2 |
| Saffire-II_PSI-99.csv | PSI-99 | Samle Thickness | categorical | 9 | 6 | 40.0 | 7 | 0.27 mm, 0.61 mm, 1.03 mm, 037 mm, 0.85 and 0.37 mm, See Fig. 5, 1 cm |
| Saffire-II_PSI-99.csv | PSI-99 | Sample Length | categorical | 9 | 6 | 40.0 | 2 | 29 cm, 5 and 24 cm |
| Saffire-II_PSI-99.csv | PSI-99 | Sample Width (cm) | numeric | 9 | 6 | 40.0 | 1 | 5 cm |
| Saffire-II_PSI-99.csv | PSI-99 | Air Flow (cm/s) | numeric | 9 | 6 | 40.0 | 1 | 20 cm/s |
| Saffire-II_PSI-99.csv | PSI-99 | Percent O2 (Note 1) | text | 9 | 6 | 40.0 | 4 | ~ 21.5, ~ 22.1, 22.1 to 22.0, 22.0 to 21.9 |
| Saffire-II_PSI-99.csv | PSI-99 | Ignition Power (W) | numeric | 9 | 6 | 40.0 | 2 | 80 W, 97 W |
| Saffire-II_PSI-99.csv | PSI-99 | Ignition Time (s) | numeric | 9 | 6 | 40.0 | 2 | 9.2 s, 30 s |
| Saffire-II_PSI-99.csv | PSI-99 | Burn Time (s) | categorical | 9 | 6 | 40.0 | 6 | Insignificant, 145 s, 115 s, 140 s, 600 s, 900 s |
| Saffire-II_PSI-99.csv | PSI-99 | Flow Direction | categorical | 9 | 6 | 40.0 | 2 | Concurrent, Opposed |
| Saffire-II_PSI-99.csv | PSI-99 | ?-g Burn Length | categorical | 9 | 6 | 40.0 | 5 | ~ 0, 29 cm, 5 cm & 0 (note 2), ~ 10 cm (note 3), ~ 10 cm (note 4) |
| Saffire-II_PSI-99.csv | PSI-99 | ?-g Spread Length | categorical | 5 | 10 | 66.67 | 4 | 2.1 mm/s, 2.6 mm/s, n/a (Nomex), Note 4 |
| Saffire-II_PSI-99.csv | PSI-99 | 1-g Burn Length | categorical | 9 | 6 | 40.0 | 4 | Complete, 7.6 cm, ~ 0, ~ 0 (Nomex) |
| Saffire-II_PSI-99.csv | PSI-99 | 1-g Spread Rate | categorical | 8 | 7 | 46.67 | 4 | Acceleratory, 1.2 mm/s, 0.6 mm/s, n/a (Nomex) |
| Saffire-II_PSI-99.csv | PSI-99 | Camera 1 | categorical | 7 | 8 | 53.33 | 7 | S1C1, S4C1, S5C1, S6C1, S7C1, S8C1, S9C1 |
| Saffire-II_PSI-99.csv | PSI-99 | Camera 2 | categorical | 6 | 9 | 60.0 | 6 | S1C2, S2C2, S3C2, S4C1, S5C2, S56C2 |
| Saffire-III_PSI-100.csv | PSI-100 | Sample Number | categorical | 2 | 0 | 0.0 | 2 | S1, S2 |
| Saffire-III_PSI-100.csv | PSI-100 | Material | categorical | 2 | 0 | 0.0 | 1 | SIBAL Fabric |
| Saffire-III_PSI-100.csv | PSI-100 | Sample Thickness | numeric | 2 | 0 | 0.0 | 1 | .33 cm |
| Saffire-III_PSI-100.csv | PSI-100 | Sample Length | numeric | 2 | 0 | 0.0 | 1 | 94 cm |
| Saffire-III_PSI-100.csv | PSI-100 | Sample Width | numeric | 2 | 0 | 0.0 | 1 | 40.6 cm |
| Saffire-III_PSI-100.csv | PSI-100 | Air Flow | numeric | 2 | 0 | 0.0 | 1 | 30 cm/s |
| Saffire-III_PSI-100.csv | PSI-100 | Direction | categorical | 2 | 0 | 0.0 | 2 | Concurrent, Opposed |
| Saffire-III_PSI-100.csv | PSI-100 | Camera 1 | categorical | 2 | 0 | 0.0 | 2 | S1C1, S2C1 |
| Saffire-III_PSI-100.csv | PSI-100 | Camera 2 | categorical | 2 | 0 | 0.0 | 2 | S1C2, S2C2 |
| SAME-R_PSI-101.csv | PSI-101 | Sample Type | categorical | 109 | 0 | 0.0 | 5 | Kapton, Silicone, Lampwick, Teflon, Pyrell |
| SAME-R_PSI-101.csv | PSI-101 | SAME Test # | text | 109 | 0 | 0.0 | 108 | 51, 51a, 61, 61a, 62, 62a, 70, 73 ... |
| SAME-R_PSI-101.csv | PSI-101 | Description | text | 109 | 0 | 0.0 | 34 | B.L. new formula, Baseline Aging, aged, High Temp aging, High temp aged STS det, Mid Temp aging (no Ptrak), Mid Temp aging run. Repeat 75, Mid Temp aging reburn 85 ... |
| SAME-R_PSI-101.csv | PSI-101 | Date | categorical | 109 | 0 | 0.0 | 17 | 21-Jul, 22-Jul, 2-Aug, 24-Aug, 26-Aug, 30-Aug, 7-Sep, 8-Sep ... |
| SAME-R_PSI-101.csv | PSI-101 | Inlet velocity (cm/s) | numeric | 109 | 0 | 0.0 | 5 | 8.1, 0, 1, 2, 8 |
| SAME-R_PSI-101.csv | PSI-101 | Rt/R0 | numeric | 109 | 0 | 0.0 | 20 | 1.38, 1.48, 1.43, 1.45, 1.304, 1.35, 1.327, 1.36 ... |
| SAME-R_PSI-101.csv | PSI-101 | Duration (sec) | numeric | 68 | 41 | 37.61 | 2 | 60, 120 |
| SAME-R_PSI-101.csv | PSI-101 | Primary aging time (sec) | numeric | 67 | 42 | 38.53 | 3 | 11, 720, 1 |
| SAME-R_PSI-101.csv | PSI-101 | Primary mixing time (sec) | numeric | 67 | 42 | 38.53 | 1 | 8 |
| SAME-R_PSI-101.csv | PSI-101 | Net aging time (sec) | numeric | 104 | 5 | 4.59 | 66 | 38, 261, 807, 39, 808, 747, 33, 560 ... |
| SAME_PSI-102.csv | PSI-102 | Sample # | numeric | 8 | 0 | 0.0 | 8 | 1, 2, 3, 4, 5, 6, 7, 8 |
| SAME_PSI-102.csv | PSI-102 | Sample Material | categorical | 8 | 0 | 0.0 | 5 | Teflon, Kapton: same conditions as 1-4, Silicone Rubber: same conditions as 1-4, Lampwick: same conditions as 1-4, Dibutyl Phthalate: same conditions as 1-4 |
| SAME_PSI-102.csv | PSI-102 | Air Flow (cm/s) | numeric | 4 | 4 | 50.0 | 2 | 5, 10 |
| SAME_PSI-102.csv | PSI-102 | Weight loss rate (mg/min) | numeric | 4 | 4 | 50.0 | 2 | 2, 1 |
| SAME_PSI-102.csv | PSI-102 | Aging Duration (minutes) | numeric | 4 | 4 | 50.0 | 2 | 1, 20 |
| Slice_PSI-106.csv | PSI-106 | Test Date | categorical | 12 | 0 | 0.0 | 12 | 2012-FEB-09, 2012-FEB-13 SLICE testing with, 2012-FEB-17, 2012-FEB-20, 2012-FEB-27, 2012-MAR-01, 2012-MAR-05 SLICE testing with, 2012-MAR-09 ... |
| Slice_PSI-106.csv | PSI-106 | Fuel Type | categorical | 12 | 0 | 0.0 | 9 | 100% CH4, 40% CH4 (balance N2) including 2 pyrometry calibration tests and 2 fan calibrations, 70% CH4 (balance N2) including 1 pyrometry calibration test, 20% C2H4 (balance N2), 40% CH4 (balance N2), 70% CH4 (balance N2) where the fuel bottle was not emptied (in contrast to most days), 100% C2H6, 70% CH4 (balance N2) including 1 pyrometry calibration test and 2 fan calibrations ... |
| Spice_PSI-107.csv | PSI-107 | GMT date | numeric | 469 | 0 | 0.0 | 11 | 45, 48, 52, 55, 58, 119, 136, 167 ... |
| Spice_PSI-107.csv | PSI-107 | GMT ignition | text | 468 | 1 | 0.21 | 150 | 14:37:08, 14:50:07, 15:35:44, 15:42:22, 15:48:39, 15:50:59, 17:11:46, 17:15:05 ... |
| Spice_PSI-107.csv | PSI-107 | GMT  Flame Off | text | 457 | 12 | 2.56 | 142 | 14:48:03, 14:52:11, 15:37:00, 15:43:03, 15:49:19, 15:51:43, 17:12:37, 17:15:32 ... |
| Spice_PSI-107.csv | PSI-107 | Fuel | categorical | 469 | 0 | 0.0 | 7 | Ethylene, Propane, 75% Propylene, 75 % Propylene, 50 % Propylene, Propylene, Methane |
| Spice_PSI-107.csv | PSI-107 | Nozzle (mm) | numeric | 469 | 0 | 0.0 | 3 | 1.6002, 0.762, 0.4064 |
| Spice_PSI-107.csv | PSI-107 | Fuel Rate (sccm) | numeric | 457 | 12 | 2.56 | 284 | 103.8, 51, 51.6, 138, 137.4, 69, 63.6, 34.8 ... |
| Spice_PSI-107.csv | PSI-107 | Fuel Rate (mg/s) | numeric | 457 | 12 | 2.56 | 275 | 1.971, 0.968, 0.98, 2.62, 2.608, 1.31, 1.207, 0.661 ... |
| Spice_PSI-107.csv | PSI-107 | HC Fuel Rate (mg/s) | numeric | 469 | 0 | 0.0 | 269 | 1.971, 0.968, 0.98, 2.62, 2.608, 1.31, 1.207, 0.661 ... |
| Spice_PSI-107.csv | PSI-107 | Air Rate (cm/s) | numeric | 444 | 25 | 5.33 | 62 | 36.39, 40.15, 57.08, 58.02, 17.59, 16.65, 33.57, 34.51 ... |

## Numeric profiles

| Source path | Investigation reference | Column | Count | Missing | Missing % | Unparseable | Min | Max | Mean | Median | Std dev | Unit | Flags |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ACME_BRE_PSI-20.csv | PSI-20 | Year | 18 | 0 | 0.0 | 0 | 2019.0 | 2021.0 | 2019.611111111111 | 2019.5 | 0.6978023391872252 | not stated | none |
| ACME_BRE_PSI-20.csv | PSI-20 | Date | 18 | 0 | 0.0 | 0 | 1.0 | 28.0 | 13.11111111111111 | 11.0 | 9.21564455560019 | not stated | none |
| ACME_BRE_PSI-20.csv | PSI-20 | Burner Size (mm) | 18 | 0 | 0.0 | 0 | 25.0 | 50.0 | 27.77777777777778 | 25.0 | 8.084520834544431 | mm | none |
| ACME_BRE_PSI-20.csv | PSI-20 | Flames Ignited | 18 | 0 | 0.0 | 0 | 0.0 | 21.0 | 10.777777777777779 | 10.0 | 5.047486917566655 | not stated | none |
| BASS-II_PSI-25.csv | PSI-25 | GMT | 129 | 0 | 0.0 | 0 | 45.0 | 216.0 | 166.93023255813952 | 188.0 | 55.79331081748729 | not stated | none |
| BASS-II_PSI-25.csv | PSI-25 | Flow restrictor | 129 | 0 | 0.0 | 0 | 0.0 | 2.0 | 1.689922480620155 | 2.0 | 0.6349021776571557 | not stated | none |
| BASS-II_PSI-25.csv | PSI-25 | Calibrated  initial O2 % by vol | 129 | 0 | 0.0 | 0 | 13.6 | 22.2 | 18.569767441860463 | 18.2 | 2.294715554648154 | % | none |
| BASS-II_PSI-25.csv | PSI-25 | Calibrated final O2 % by vol | 127 | 2 | 1.55 | 0 | 0.6 | 40.4 | 17.934645669291335 | 17.4 | 4.374209732757648 | % | none |
| BASS-II_PSI-25.csv | PSI-25 | Initial CO2 % by vol | 127 | 2 | 1.55 | 0 | 0.0 | 1.85 | 0.5215748031496062 | 0.41 | 0.3587863696444161 | % | none |
| BASS-II_PSI-25.csv | PSI-25 | Final CO2 % by vol | 123 | 6 | 4.65 | 0 | 0.2 | 3.22 | 0.9205691056910569 | 0.7 | 0.5923547076654797 | % | none |
| BASS_PSI-26.csv | PSI-26 | GMT | 122 | 0 | 0.0 | 0 | 90.0 | 234.0 | 156.14754098360655 | 157.0 | 43.40729118232976 | not stated | none |
| BASS_PSI-26.csv | PSI-26 | As Run Test # | 121 | 1 | 0.82 | 0 | 1.0 | 116.0 | 59.21487603305785 | 60.0 | 33.525414889694815 | not stated | none |
| BASS_PSI-26.csv | PSI-26 | Sample # | 121 | 1 | 0.82 | 0 | 2.0 | 44.0 | 24.983471074380166 | 24.0 | 9.567291040374995 | not stated | none |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | Day | 179 | 0 | 0.0 | 0 | 1.0 | 11.0 | 5.793296089385475 | 6.0 | 2.969273314900487 | not stated | none |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | XO2 before test | 179 | 0 | 0.0 | 0 | 0.179685675 | 0.3997 | 0.3218061493798883 | 0.375900202 | 0.08273114427908304 | not stated | none |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | XO2  after test | 179 | 0 | 0.0 | 0 | 0.17939183 | 0.397258964 | 0.3194376544134078 | 0.366422787 | 0.08131266960226374 | not stated | none |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | approx p (bar) | 179 | 0 | 0.0 | 0 | 0.50665 | 3.0399 | 1.2793846547486032 | 1.0133 | 0.6750965656551761 | bar | none |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | Xf | 179 | 0 | 0.0 | 0 | 0.0 | 1.0 | 0.37120972067039104 | 0.3 | 0.3055645507658783 | not stated | none |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | mHC (mg/s) | 179 | 0 | 0.0 | 0 | 0.0 | 3.215 | 1.1355027932960893 | 1.0 | 0.6770617897407778 | not stated | none |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | burn time (sec) | 175 | 4 | 2.23 | 0 | 0.0 | 304.0 | 44.04571428571428 | 20.0 | 64.08882280506162 | not stated | none |
| CFI_PSI-39.csv | PSI-39 | Flex Number | 87 | 0 | 0.0 | 0 | 1206.0 | 1387.0 | 1299.287356321839 | 1300.0 | 55.172859026538184 | not stated | none |
| CFI_PSI-39.csv | PSI-39 | Pressure | 87 | 0 | 0.0 | 0 | 0.5 | 5.0 | 1.5373563218390804 | 1.0 | 1.0083436334833047 | not stated | none |
| CFI_PSI-39.csv | PSI-39 | Oxygen | 87 | 0 | 0.0 | 0 | 0.17 | 0.21 | 0.19896551724137942 | 0.21 | 0.017981546274316803 | not stated | none |
| CFI_PSI-39.csv | PSI-39 | Nitrogen | 87 | 0 | 0.0 | 0 | 0.2 | 0.83 | 0.7322988505747126 | 0.79 | 0.17096648079902388 | not stated | none |
| CFI_PSI-39.csv | PSI-39 | Helium | 87 | 0 | 0.0 | 0 | 0.0 | 0.59 | 0.06735632183908045 | 0.0 | 0.16589054790429808 | not stated | none |
| Flex2_PSI-68.csv | PSI-68 | Ambient Temperature (C) | 8 | 0 | 0.0 | 0 | 25.0 | 25.0 | 25.0 | 25.0 | 0.0 | deg C | none |
| FLEX_PSI-69.csv | PSI-69 | FLEX Test # | 274 | 0 | 0.0 | 0 | 1.0 | 274.0 | 137.5 | 137.5 | 79.24119299118777 | not stated | none |
| FLEX_PSI-69.csv | PSI-69 | Ambient pressure; mmHg | 274 | 0 | 0.0 | 0 | 0.0 | 2319.9 | 716.7076642335766 | 759.6 | 275.1102246892873 | mmHg | manual review: zero pressure |
| FLEX_PSI-69.csv | PSI-69 | O initial ambient composition; mole fraction | 274 | 0 | 0.0 | 0 | 0.12 | 0.34 | 0.20065693430656933 | 0.2 | 0.04800342447433378 | mole fraction | none |
| FLEX_PSI-69.csv | PSI-69 | N initial ambient composition; mole fraction | 274 | 0 | 0.0 | 0 | 0.09 | 0.88 | 0.63007299270073 | 0.66 | 0.17577039781427217 | mole fraction | none |
| FLEX_PSI-69.csv | PSI-69 | CO initial ambient composition; mole fraction | 274 | 0 | 0.0 | 0 | 0.0 | 0.7 | 0.12025547445255476 | 0.0 | 0.17440513355674547 | mole fraction | none |
| FLEX_PSI-69.csv | PSI-69 | He initial ambient composition; mole fraction | 274 | 0 | 0.0 | 0 | 0.0 | 0.45 | 0.0478102189781022 | 0.0 | 0.11206823750983118 | mole fraction | none |
| FLEX_PSI-69.csv | PSI-69 | Burning rate; mm | 258 | 16 | 5.84 | 0 | 0.05 | 1.06 | 0.5018992248062016 | 0.5 | 0.1375999018731688 | mm | none |
| PSI-68_Experimental table_Flex2.csv | PSI-68 | Ambient Temperature (C) | 8 | 0 | 0.0 | 0 | 25.0 | 25.0 | 25.0 | 25.0 | 0.0 | deg C | none |
| Saffire-I_PSI-98.csv | PSI-98 | Sample Thickness (cm) | 2 | 2 | 50.0 | 0 | 0.37 | 0.37 | 0.37 | 0.37 | 0.0 | not stated | none |
| Saffire-I_PSI-98.csv | PSI-98 | Sample Length (cm) | 2 | 2 | 50.0 | 0 | 40.6 | 40.6 | 40.6 | 40.6 | 0.0 | not stated | none |
| Saffire-I_PSI-98.csv | PSI-98 | Sample Width (cm) | 2 | 2 | 50.0 | 0 | 94.0 | 94.0 | 94.0 | 94.0 | 0.0 | not stated | none |
| Saffire-I_PSI-98.csv | PSI-98 | Air Flow (cm/s) | 2 | 2 | 50.0 | 0 | 20.0 | 20.0 | 20.0 | 20.0 | 0.0 | cm/s | none |
| Saffire-I_PSI-98.csv | PSI-98 | Ignition Power (W) | 2 | 2 | 50.0 | 0 | 182.0 | 182.0 | 182.0 | 182.0 | 0.0 | not stated | none |
| Saffire-I_PSI-98.csv | PSI-98 | Ignition Time (s) | 2 | 2 | 50.0 | 0 | 8.0 | 8.0 | 8.0 | 8.0 | 0.0 | s | none |
| Saffire-I_PSI-98.csv | PSI-98 | Burn Time (s) | 2 | 2 | 50.0 | 0 | 70.0 | 420.0 | 245.0 | 245.0 | 247.48737341529164 | s | none |
| Saffire-II_PSI-99.csv | PSI-99 | Sample Width (cm) | 9 | 6 | 40.0 | 0 | 5.0 | 5.0 | 5.0 | 5.0 | 0.0 | not stated | none |
| Saffire-II_PSI-99.csv | PSI-99 | Air Flow (cm/s) | 9 | 6 | 40.0 | 0 | 20.0 | 20.0 | 20.0 | 20.0 | 0.0 | cm/s | none |
| Saffire-II_PSI-99.csv | PSI-99 | Ignition Power (W) | 9 | 6 | 40.0 | 0 | 80.0 | 97.0 | 83.77777777777777 | 80.0 | 7.4962953813496735 | not stated | none |
| Saffire-II_PSI-99.csv | PSI-99 | Ignition Time (s) | 9 | 6 | 40.0 | 0 | 9.2 | 30.0 | 13.822222222222223 | 9.2 | 9.171937878357248 | s | none |
| Saffire-III_PSI-100.csv | PSI-100 | Sample Thickness | 2 | 0 | 0.0 | 0 | 0.33 | 0.33 | 0.33 | 0.33 | 0.0 | not stated | none |
| Saffire-III_PSI-100.csv | PSI-100 | Sample Length | 2 | 0 | 0.0 | 0 | 94.0 | 94.0 | 94.0 | 94.0 | 0.0 | not stated | none |
| Saffire-III_PSI-100.csv | PSI-100 | Sample Width | 2 | 0 | 0.0 | 0 | 40.6 | 40.6 | 40.6 | 40.6 | 0.0 | not stated | none |
| Saffire-III_PSI-100.csv | PSI-100 | Air Flow | 2 | 0 | 0.0 | 0 | 30.0 | 30.0 | 30.0 | 30.0 | 0.0 | not stated | none |
| SAME-R_PSI-101.csv | PSI-101 | Inlet velocity (cm/s) | 109 | 0 | 0.0 | 0 | 0.0 | 8.1 | 5.792660550458716 | 8.1 | 3.5376992529153 | cm/s | none |
| SAME-R_PSI-101.csv | PSI-101 | Rt/R0 | 109 | 0 | 0.0 | 0 | 1.22 | 1.48 | 1.3472568807339445 | 1.35 | 0.092255723868367 | not stated | none |
| SAME-R_PSI-101.csv | PSI-101 | Duration (sec) | 68 | 41 | 37.61 | 0 | 60.0 | 120.0 | 60.88235294117647 | 60.0 | 7.27606875108999 | not stated | none |
| SAME-R_PSI-101.csv | PSI-101 | Primary aging time (sec) | 67 | 42 | 38.53 | 0 | 1.0 | 720.0 | 63.76119402985075 | 11.0 | 187.76977275959266 | not stated | none |
| SAME-R_PSI-101.csv | PSI-101 | Primary mixing time (sec) | 67 | 42 | 38.53 | 0 | 8.0 | 8.0 | 8.0 | 8.0 | 0.0 | not stated | none |
| SAME-R_PSI-101.csv | PSI-101 | Net aging time (sec) | 104 | 5 | 4.59 | 0 | 21.0 | 1923.0 | 312.7980769230769 | 51.0 | 344.92980515128403 | not stated | none |
| SAME_PSI-102.csv | PSI-102 | Sample # | 8 | 0 | 0.0 | 0 | 1.0 | 8.0 | 4.5 | 4.5 | 2.449489742783178 | not stated | none |
| SAME_PSI-102.csv | PSI-102 | Air Flow (cm/s) | 4 | 4 | 50.0 | 0 | 5.0 | 10.0 | 6.25 | 5.0 | 2.5 | cm/s | none |
| SAME_PSI-102.csv | PSI-102 | Weight loss rate (mg/min) | 4 | 4 | 50.0 | 0 | 1.0 | 2.0 | 1.75 | 2.0 | 0.5 | not stated | none |
| SAME_PSI-102.csv | PSI-102 | Aging Duration (minutes) | 4 | 4 | 50.0 | 0 | 1.0 | 20.0 | 5.75 | 1.0 | 9.5 | min | none |
| Spice_PSI-107.csv | PSI-107 | GMT date | 469 | 0 | 0.0 | 0 | 45.0 | 174.0 | 100.8315565031983 | 58.0 | 56.39144501105969 | not stated | none |
| Spice_PSI-107.csv | PSI-107 | Nozzle (mm) | 469 | 0 | 0.0 | 0 | 0.4064 | 1.6002 | 0.9497108742004264 | 0.762 | 0.5276203411855737 | mm | none |
| Spice_PSI-107.csv | PSI-107 | Fuel Rate (sccm) | 457 | 12 | 2.56 | 0 | 0.0 | 231.6 | 52.72369300610503 | 43.61702128 | 38.56452734429687 | not stated | none |
| Spice_PSI-107.csv | PSI-107 | Fuel Rate (mg/s) | 457 | 12 | 2.56 | 0 | 0.0 | 4.397 | 1.2227024070021884 | 1.02 | 0.821549420739786 | not stated | none |
| Spice_PSI-107.csv | PSI-107 | HC Fuel Rate (mg/s) | 469 | 0 | 0.0 | 0 | 0.0 | 4.397 | 1.0036609808102346 | 0.817 | 0.7851254256268247 | not stated | none |
| Spice_PSI-107.csv | PSI-107 | Air Rate (cm/s) | 444 | 25 | 5.33 | 0 | -5.92 | 85.28 | 30.581666666666667 | 27.93 | 17.03559109063651 | cm/s | manual review: negative airflow |

## Outcome columns by source file

| Source path | Investigation reference | Outcome columns |
| --- | --- | --- |
| ACME_BRE_PSI-20.csv | PSI-20 | Not reported |
| BASS-II_PSI-25.csv | PSI-25 | Final CO (ppm), Final CO2 % by vol, Initial CO (ppm), Initial CO2 % by vol |
| BASS_PSI-26.csv | PSI-26 | Not reported |
| CFI-G_Normal_Flames_PSI-159.csv | PSI-159 | Cool flame?, Flame Type, burn time (sec) |
| CFI_PSI-39.csv | PSI-39 | Not reported |
| Flex2_PSI-68.csv | PSI-68 | Not reported |
| FLEX_PSI-69.csv | PSI-69 | Burn time; s, Burning rate; mm, CO initial ambient composition; mole fraction, Visible flame extinction diameter; mm |
| PSI-68_Experimental table_Flex2.csv | PSI-68 | Not reported |
| Saffire-I_PSI-98.csv | PSI-98 | Burn Time (s) |
| Saffire-II_PSI-99.csv | PSI-99 | 1-g Burn Length, 1-g Spread Rate, ?-g Burn Length, ?-g Spread Length, Burn Time (s) |
| Saffire-III_PSI-100.csv | PSI-100 | Not reported |
| SAME-R_PSI-101.csv | PSI-101 | Not reported |
| SAME_PSI-102.csv | PSI-102 | Not reported |
| Slice_PSI-106.csv | PSI-106 | Not reported |
| Spice_PSI-107.csv | PSI-107 | GMT  Flame Off |

## Optional inputs and processing notes

- Optional chunks.parquet loaded successfully.
- Optional discrepancies log: loaded.
- Investigations with no chunks: bass, bass-ii, saffire-i, saffire-ii, saffire-iii, same, same-r, flex, flex-2, cfi, cfi-g, e-field-flames, flame-design, acme-cld-flame, acme-s-flame, bre, spice, slice, daft, psi-117, psi-62, psi-60, psi-142, psi-115
- Discrepancy references: PSI-159, PSI-39, PSI-68, PSI-69

## Investigation separation

Statistics are calculated per source path and PSI reference. Tables sharing a PSI reference are not pooled; measurements are never compared across files without verified unit and experimental comparability.

## Things to review by hand

- Numeric flags: 3 profile(s) contain requested impossible-value or placeholder flags.
- Conflicts recorded for: PSI-159, PSI-39, PSI-68, PSI-69.
- Investigations with no chunks: bass, bass-ii, saffire-i, saffire-ii, saffire-iii, same, same-r, flex, flex-2, cfi, cfi-g, e-field-flames, flame-design, acme-cld-flame, acme-s-flame, bre, spice, slice, daft, psi-117, psi-62, psi-60, psi-142, psi-115.
