"""European Power Market Lab — results dashboard (read-only).

Run:  streamlit run report/dashboard/app.py

It only reads the committed step outputs in ``report/data/`` and ``report/results/key_numbers.json``.
No data is fetched and nothing is re-estimated.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

REPORT = Path(__file__).resolve().parents[1]
DATA = REPORT / "data"


@st.cache_data
def load():
    kn = json.loads((REPORT / "results" / "key_numbers.json").read_text(encoding="utf-8"))
    m4 = pd.read_csv(DATA / "epm-capacity-adequacy" / "monthly.csv")
    b5 = pd.read_csv(DATA / "epm-price-forecast-benchmark" / "bias_by_month.csv")
    mae5 = pd.read_csv(DATA / "epm-price-forecast-benchmark" / "metrics.csv")
    v6 = pd.read_csv(DATA / "epm-bess-value-from-scenarios" / "value_by_scenario.csv")
    return kn, m4, b5, mae5, v6


kn, m4, b5, mae5, v6 = load()
st.set_page_config(page_title="European Power Market Lab", layout="wide")
st.title("European Power Market Lab — DE-LU day-ahead, 2025–2026")
st.caption("Read-only view of the committed outputs of steps 1–6. Historical backtests, not trading advice.")

view = st.sidebar.radio("View", ["Headlines", "H2-2026 underpricing", "Forecasts (step 5)", "BESS value (step 6)"])

if view == "Headlines":
    c = st.columns(4)
    c[0].metric("Stack M0 test MAE (step 2)", f"{kn['s2_m0_mae']['value']:.2f} €/MWh")
    c[1].metric("Rolling stack C3 MAE (step 2)", f"{kn['s2_c3_mae']['value']:.2f} €/MWh")
    c[2].metric("Best ex-ante forecast MAE (step 5)", f"{kn['s5_ensnb_mae']['value']:.2f} €/MWh")
    c[3].metric("2 h BESS value kept, best forecast (step 6)", f"{kn['s6_ret_ensnb']['value']:.1f} %")
    st.dataframe(pd.DataFrame([{"key": k, "value": v["value"], "unit": v["unit"], "source": v["source"], "path": v["path"]}
                               for k, v in kn.items()]), hide_index=True, use_container_width=True)
elif view == "H2-2026 underpricing":
    st.subheader("Monthly M0 stack bias vs system context (step 4 monthly table)")
    st.line_chart(m4.set_index("month")[["m0_bias"]])
    st.line_chart(m4.set_index("month")[["rl_mean_mw", "margin_mean_mw", "net_import_mean_mw"]] / 1e3)
    st.caption("GW. Deratings are ASSUMED (see the step-4 repo).")
    models = st.multiselect("Step 5 model bias by month", [c for c in b5.columns if c != "month"],
                            default=["stack_C3_exante", "ens_nb"])
    if models:
        st.line_chart(b5.set_index("month")[models])
elif view == "Forecasts (step 5)":
    period = st.selectbox("Period", sorted(mae5.period.unique()))
    t = mae5[mae5.period == period].sort_values("mae")[["model", "track", "mae", "rmse", "bias", "smape_pct"]]
    st.dataframe(t, hide_index=True, use_container_width=True)
else:
    dur = st.selectbox("Battery duration (h)", sorted(v6.duration_h.unique()), index=1)
    per = st.selectbox("Period", ["full", "H1", "H2"])
    t = v6[(v6.duration_h == dur) & (v6.period == per)].sort_values("retained_pct", ascending=False)
    st.dataframe(t[["signal", "realised_eur_per_mw", "pf_eur_per_mw", "retained_pct", "implied_over_pf", "mae"]],
                 hide_index=True, use_container_width=True)
    st.bar_chart(t.set_index("signal")["retained_pct"])
