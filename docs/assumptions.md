# Assumptions register

Every modelling choice that is not a direct observation is tagged **ASSUMED** and given a source or rationale. Update this file when a downstream repo adds parameters.

| ID | Assumption | Value / rule | Source / rationale | Used in |
|---|---|---|---|---|
| A-D1 | Bidding zone | DE-LU only | CC BY 4.0 day-ahead prices via Energy-Charts / SMARD | step 1+ |
| A-D2 | Gas price proxy | World Bank “Natural gas, Europe” (USD/MMBtu) | Pink Sheet; standard TTF proxy | step 1, 2, 3 |
| A-D3 | Coal price proxy | World Bank “Coal, South Africa” (USD/t) | Pink Sheet seaborne thermal coal | step 1, 2, 3 |
| A-D4 | EUA proxy | DEHSt German primary-auction VWAP (annual; 2026 = H1) | Official DEHSt/EEX public figures; **not** futures | step 1, 2, 3 |
| A-D5 | FX | ECB USD/EUR monthly reference | ECB Data Portal | step 1+ |
| A-D6 | MMBtu per MWh | 3.412141156 | ASSUMED engineering conversion | step 1 |
| A-D7 | Coal MWh_th per t | 6000 kcal/kg × 4.1868 / 3600 ≈ 6.978 | ASSUMED NAR 6000 convention | step 1 |
| A-D8 | Hourly aggregation | Mean of 15-min Energy-Charts intervals | ASSUMED; documents smoothing | step 1+ |
| A-D9 | No ENTSO-E token | Energy-Charts public net generation instead of Transparency Platform | Key-free design | step 1 |
| A-D10 | Raw redistribution | Raw API JSON git-ignored; licence gate on non-CC BY zones | CC BY / SMARD terms | step 1 |

Downstream steps will append plant efficiencies, VOM, FOR, BESS parameters, etc., each with an ID.
