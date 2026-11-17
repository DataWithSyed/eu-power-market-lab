"""Build the EPM final-report artefacts from the step repos' committed outputs.

Inputs: ``report/data/<repo>/`` — byte-for-byte copies of files committed in the step repos
(commits listed in ``report/data/SOURCES.md``). Nothing is re-estimated here.

Outputs:
* ``report/results/key_numbers.json`` — every headline number quoted in ``report/README.md``,
  each with its source file and JSON path / CSV selector, so a test can check the report text
  against the step outputs.
* ``report/figures/R1_h2_underpricing_chain.png`` — the H2-2026 stack underpricing as seen by
  steps 2–5 (monthly bias of the stack variants vs the best ex-ante forecast) with the
  step-4 residual load / margin context.
* ``report/figures/R2_accuracy_vs_storage_value.png`` — step-5 forecast MAE vs step-6
  retained share of perfect-foresight value (2 h), per model.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

REPORT = Path(__file__).resolve().parents[1]
DATA = REPORT / "data"

# (key, repo, file, path-in-json or csv selector, decimals, unit)
SPEC = [
    # step 1
    ("s1_hours", "epm-data-pipeline", "summary.json", "measured_facts.n_hourly_rows", 0, "h"),
    ("s1_da_mean", "epm-data-pipeline", "summary.json", "measured_facts.da_price_mean_eur_mwh", 2, "€/MWh"),
    ("s1_neg_share_pct", "epm-data-pipeline", "summary.json", "measured_facts.negative_price_hour_share_pct", 2, "%"),
    ("s1_gas_sep_eur_mwh_th", "epm-data-pipeline", "summary.json", "measured_facts.last_gas_eur_mwh_th", 2, "€/MWh_th"),
    ("s1_eua_proxy", "epm-data-pipeline", "summary.json", "measured_facts.last_eua_eur_t", 2, "€/t"),
    # step 2
    ("s2_m0_mae", "epm-merit-order-model", "summary.json", "metrics.M0_stack.test.mae", 2, "€/MWh"),
    ("s2_m0_bias", "epm-merit-order-model", "summary.json", "metrics.M0_stack.test.bias", 2, "€/MWh"),
    ("s2_m0_corr", "epm-merit-order-model", "summary.json", "metrics.M0_stack.test.corr", 2, ""),
    ("s2_c3_mae", "epm-merit-order-model", "summary.json", "metrics.C3_rolling90_linear.test.mae", 2, "€/MWh"),
    ("s2_c3_bias", "epm-merit-order-model", "summary.json", "metrics.C3_rolling90_linear.test.bias", 2, "€/MWh"),
    ("s2_c2_mae", "epm-merit-order-model", "summary.json", "metrics.C2_structural_2025.test.mae", 2, "€/MWh"),
    ("s2_b2_mae", "epm-merit-order-model", "summary.json", "metrics.B2_ols_resload_srmc.test.mae", 2, "€/MWh"),
    ("s2_neg_model", "epm-merit-order-model", "summary.json", "metrics.M0_stack.test_negative_hours.model_count", 0, "h"),
    ("s2_neg_real", "epm-merit-order-model", "summary.json", "metrics.M0_stack.test_negative_hours.realised_count", 0, "h"),
    # step 3
    ("s3_h2_m0_bias", "epm-co2-gas-price-drivers", "summary.json", "h2_2026_underpricing.m0_bias", 2, "€/MWh"),
    ("s3_h2_m0_adj_bias", "epm-co2-gas-price-drivers", "summary.json", "h2_2026_underpricing.m0_adj_bias", 2, "€/MWh"),
    ("s3_bias_closed", "epm-co2-gas-price-drivers", "summary.json", "h2_2026_underpricing.bias_closed_eur", 2, "€/MWh"),
    ("s3_bias_closed_pct", "epm-co2-gas-price-drivers", "summary.json", "h2_2026_underpricing.bias_closed_share", 1, "%", 100),
    ("s3_h1_da_mean", "epm-co2-gas-price-drivers", "summary.json", "h2_2026_underpricing.h1_2026.da_mean", 1, "€/MWh"),
    ("s3_h2_da_mean", "epm-co2-gas-price-drivers", "summary.json", "h2_2026_underpricing.da_mean", 1, "€/MWh"),
    ("s3_h1_rl_gw", "epm-co2-gas-price-drivers", "summary.json", "h2_2026_underpricing.h1_2026.residual_load_mean", 1, "GW", 1e-3),
    ("s3_h2_rl_gw", "epm-co2-gas-price-drivers", "summary.json", "h2_2026_underpricing.residual_load_mean", 1, "GW", 1e-3),
    ("s3_h2_surplus_share_pct", "epm-co2-gas-price-drivers", "summary.json", "h2_2026_underpricing.marginal_tech_shares.h2_2026.surplus", 1, "%", 100),
    ("s3_2025_surplus_share_pct", "epm-co2-gas-price-drivers", "summary.json", "h2_2026_underpricing.marginal_tech_shares.train_2025.surplus", 1, "%", 100),
    ("s3_rl_slope_h1", "epm-co2-gas-price-drivers", "summary.json", "h2_2026_underpricing.residual_load_slope_eur_per_gw.h1_2026_insample", 2, "€/MWh per GW"),
    ("s3_rl_slope_h2", "epm-co2-gas-price-drivers", "summary.json", "h2_2026_underpricing.residual_load_slope_eur_per_gw.h2_2026_insample", 2, "€/MWh per GW"),
    # step 4
    ("s4_h2_gap_no_margin", "epm-capacity-adequacy", "summary.json", "h2_link.h2_gap_no_margin", 1, "€/MWh"),
    ("s4_h2_gap_with_margin", "epm-capacity-adequacy", "summary.json", "h2_link.h2_gap_with_margin", 1, "€/MWh"),
    ("s4_h2_margin_mean_gw", "epm-capacity-adequacy", "summary.json", "periods.2026-H2.margin_mean_mw", 1, "GW", 1e-3),
    ("s4_2025_margin_mean_gw", "epm-capacity-adequacy", "summary.json", "periods.2025.margin_mean_mw", 1, "GW", 1e-3),
    ("s4_h2_top_rl_price", "epm-capacity-adequacy", "summary.json", "periods.2026-H2.price_top_rl_hours", 1, "€/MWh"),
    ("s4_2025_top_rl_price", "epm-capacity-adequacy", "summary.json", "periods.2025.price_top_rl_hours", 1, "€/MWh"),
    ("s4_junoct25_bias", "epm-capacity-adequacy", "summary.json", "h2_link.jun_oct_matched.2025.m0_bias", 1, "€/MWh"),
    ("s4_junoct25_import_gw", "epm-capacity-adequacy", "summary.json", "h2_link.jun_oct_matched.2025.net_import_mean_mw", 1, "GW", 1e-3),
    ("s4_junoct26_import_gw", "epm-capacity-adequacy", "summary.json", "h2_link.jun_oct_matched.2026.net_import_mean_mw", 2, "GW", 1e-3),
    # step 5
    ("s5_ensnb_mae", "epm-price-forecast-benchmark", "summary.json", "metrics.test_2026_01_10.ens_nb.mae", 2, "€/MWh"),
    ("s5_ensnb_mae_h1", "epm-price-forecast-benchmark", "summary.json", "metrics.H1_2026_01_05.ens_nb.mae", 2, "€/MWh"),
    ("s5_ensnb_mae_h2", "epm-price-forecast-benchmark", "summary.json", "metrics.H2_2026_06_10.ens_nb.mae", 2, "€/MWh"),
    ("s5_c3_mae", "epm-price-forecast-benchmark", "summary.json", "metrics.test_2026_01_10.stack_C3_exante.mae", 2, "€/MWh"),
    ("s5_m0_mae", "epm-price-forecast-benchmark", "summary.json", "metrics.test_2026_01_10.stack_M0_exante.mae", 2, "€/MWh"),
    ("s5_m0_bias_h2", "epm-price-forecast-benchmark", "summary.json", "metrics.H2_2026_06_10.stack_M0_exante.bias", 1, "€/MWh"),
    ("s5_naive_mae", "epm-price-forecast-benchmark", "summary.json", "metrics.test_2026_01_10.naive_d1.mae", 2, "€/MWh"),
    ("s5_ols_static_mae_h2", "epm-price-forecast-benchmark", "summary.json", "metrics.H2_2026_06_10.ols_drivers_exante.mae", 1, "€/MWh"),
    ("s5_ols_rolling_mae", "epm-price-forecast-benchmark", "summary.json", "metrics.test_2026_01_10.ols_drivers_rolling.mae", 2, "€/MWh"),
    # step 6
    ("s6_pf_2h", "epm-bess-value-from-scenarios", "value_by_scenario.csv", "duration_h=2,signal=actual,period=full:pf_eur_per_mw", 0, "€/MW"),
    ("s6_pf_2h_day_h1", "epm-bess-value-from-scenarios", "summary.json", "pf_value_concentration_2h.H1.mean_eur_day", 0, "€/MW/day"),
    ("s6_pf_2h_day_h2", "epm-bess-value-from-scenarios", "summary.json", "pf_value_concentration_2h.H2.mean_eur_day", 0, "€/MW/day"),
    ("s6_ret_ensnb", "epm-bess-value-from-scenarios", "value_by_scenario.csv", "duration_h=2,signal=ens_nb,period=full:retained_pct", 1, "%"),
    ("s6_ret_naive", "epm-bess-value-from-scenarios", "value_by_scenario.csv", "duration_h=2,signal=naive_d1,period=full:retained_pct", 1, "%"),
    ("s6_ret_c3", "epm-bess-value-from-scenarios", "value_by_scenario.csv", "duration_h=2,signal=stack_C3_exante,period=full:retained_pct", 1, "%"),
    ("s6_ret_m0", "epm-bess-value-from-scenarios", "value_by_scenario.csv", "duration_h=2,signal=stack_M0_exante,period=full:retained_pct", 1, "%"),
    ("s6_ret_ols_rolling", "epm-bess-value-from-scenarios", "value_by_scenario.csv", "duration_h=2,signal=ols_drivers_rolling,period=full:retained_pct", 1, "%"),
    ("s6_c3_minus_naive", "epm-bess-value-from-scenarios", "bootstrap_differences_2h.csv", "a=stack_C3_exante,b=naive_d1,period=full:mean_eur_day", 1, "€/MW/day"),
    ("s6_c3_minus_naive_lo", "epm-bess-value-from-scenarios", "bootstrap_differences_2h.csv", "a=stack_C3_exante,b=naive_d1,period=full:lo90", 1, "€/MW/day"),
    ("s6_c3_minus_naive_hi", "epm-bess-value-from-scenarios", "bootstrap_differences_2h.csv", "a=stack_C3_exante,b=naive_d1,period=full:hi90", 1, "€/MW/day"),
    ("s6_ensnb_minus_c3", "epm-bess-value-from-scenarios", "bootstrap_differences_2h.csv", "a=ens_nb,b=stack_C3_exante,period=full:mean_eur_day", 1, "€/MW/day"),
    ("s6_spearman_mae", "epm-bess-value-from-scenarios", "summary.json", "retained_vs_accuracy_spearman.2h.spearman_retained_vs_mae", 2, ""),
    ("s6_spearman_rank", "epm-bess-value-from-scenarios", "summary.json", "retained_vs_accuracy_spearman.2h.spearman_retained_vs_rankcorr", 2, ""),
]


def _get_json(obj, path):
    for part in path.split("."):
        obj = obj[part]
    return obj


def _get_csv(df: pd.DataFrame, selector: str):
    cond, col = selector.split(":")
    m = pd.Series(True, index=df.index)
    for kv in cond.split(","):
        k, v = kv.split("=")
        if pd.api.types.is_numeric_dtype(df[k]):
            m &= df[k] == float(v)
        else:
            m &= df[k].astype(str) == v
    sel = df.loc[m, col]
    if len(sel) != 1:
        raise KeyError(f"{selector}: {len(sel)} rows")
    return float(sel.iloc[0])


def extract(data_dir: Path = DATA) -> dict:
    out, cache = {}, {}
    for row in SPEC:
        key, repo, fname, path, dec, unit = row[:6]
        scale = row[6] if len(row) > 6 else 1.0
        f = data_dir / repo / fname
        if f not in cache:
            cache[f] = json.loads(f.read_text()) if fname.endswith(".json") else pd.read_csv(f)
        raw = _get_json(cache[f], path) if fname.endswith(".json") else _get_csv(cache[f], path)
        val = float(raw) * scale
        out[key] = {"value": round(val, dec), "decimals": dec, "unit": unit, "source": f"{repo}/{fname}", "path": path}
    return out


def fmt(entry: dict) -> str:
    """Report formatting: thousands separator for |x| >= 1,000, Unicode minus."""
    v, d = entry["value"], entry["decimals"]
    s = f"{abs(v):,.{d}f}" if abs(v) >= 1_000 else f"{abs(v):.{d}f}"
    return ("−" if v < 0 else "") + s


def figures(data_dir: Path = DATA, out_dir: Path = REPORT / "figures") -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir.mkdir(parents=True, exist_ok=True)
    m4 = pd.read_csv(data_dir / "epm-capacity-adequacy" / "monthly.csv")
    m3 = pd.read_csv(data_dir / "epm-co2-gas-price-drivers" / "by_month.csv")
    c3 = pd.read_csv(data_dir / "epm-merit-order-model" / "by_month_C3_rolling90_linear.csv").rename(columns={"Unnamed: 0": "month"})
    b5 = pd.read_csv(data_dir / "epm-price-forecast-benchmark" / "bias_by_month.csv")
    fig, ax = plt.subplots(2, 1, figsize=(11, 7), sharex=True, gridspec_kw={"height_ratios": [1.5, 1]})
    x = m4.month
    ax[0].plot(x, m4.m0_bias, "o-", color="tab:red", label="step 2 M0 stack (as built, in-sample 2025 / OOS 2026)")
    ax[0].plot(m3.month, m3.m0_adj_bias, "s--", color="tab:orange", ms=4, label="step 3 M0 + quarterly EUA adjustment")
    ax[0].plot(c3.month, c3.bias, "^-", color="tab:purple", ms=4, label="step 2 C3 rolling-90d recalibration")
    ax[0].plot(b5.month, b5.stack_C3_exante, "v:", color="tab:brown", ms=4, label="step 5 stack C3 ex-ante (D-1 inputs)")
    ax[0].plot(b5.month, b5.ens_nb, "D-", color="tab:green", ms=4, label="step 5 best ex-ante forecast (ens_nb)")
    ax[0].axhline(0, color="k", lw=0.8)
    ax[0].axvspan("2026-06", "2026-10", color="grey", alpha=0.12)
    ax[0].set_ylabel("monthly mean bias, €/MWh (model − realised)")
    ax[0].set_title("H2-2026 stack underpricing across the lab (shaded: Jun–Oct 2026)", fontsize=10)
    ax[0].legend(fontsize=7.5, loc="lower left"); ax[0].grid(alpha=0.3)
    ax[1].plot(x, m4.rl_mean_mw / 1e3, "o-", color="tab:blue", label="residual load mean, GW")
    ax[1].plot(x, m4.margin_mean_mw / 1e3, "s-", color="tab:cyan", label="derated margin mean, GW (ASSUMED deratings)")
    ax[1].plot(x, m4.net_import_mean_mw / 1e3, "^-", color="tab:grey", label="net imports mean, GW")
    t = ax[1].twinx(); t.plot(x, m4.da_mean, "k-", lw=1.2, label="DA mean, €/MWh"); t.set_ylabel("DA mean, €/MWh")
    ax[1].axvspan("2026-06", "2026-10", color="grey", alpha=0.12)
    ax[1].set_ylabel("GW"); ax[1].grid(alpha=0.3)
    h1, l1 = ax[1].get_legend_handles_labels(); h2, l2 = t.get_legend_handles_labels()
    ax[1].legend(h1 + h2, l1 + l2, fontsize=7.5, loc="upper left", ncol=2)
    ax[1].set_title("Step 4 context: the system was looser, not tighter, while prices rose", fontsize=10)
    for lab in ax[1].get_xticklabels():
        lab.set_rotation(60); lab.set_fontsize(7)
    fig.tight_layout()
    p1 = out_dir / "R1_h2_underpricing_chain.png"
    fig.savefig(p1, dpi=130); plt.close(fig)

    met = pd.read_csv(data_dir / "epm-price-forecast-benchmark" / "metrics.csv")
    met = met[met.period == "test_2026_01_10"].set_index("model")
    v6 = pd.read_csv(data_dir / "epm-bess-value-from-scenarios" / "value_by_scenario.csv")
    v6 = v6[(v6.duration_h == 2.0) & (v6.period == "full") & (v6.signal.isin(met.index))].set_index("signal")
    v6 = v6[met.loc[v6.index, "track"] == "ex-ante"]
    fig, ax = plt.subplots(figsize=(7.5, 5))
    for s, r in v6.iterrows():
        c = "tab:red" if s.startswith("stack") else ("tab:grey" if s.startswith("naive") else "tab:blue")
        ax.scatter(met.loc[s, "mae"], r.retained_pct, color=c, s=40)
        ax.annotate(s, (met.loc[s, "mae"], r.retained_pct), fontsize=7.5, xytext=(4, -11) if s == "gbm_nb" else (4, 3),
                    textcoords="offset points")
    ax.set_xlabel("step 5 test MAE 2026-01..10, €/MWh (ex-ante)")
    ax.set_ylabel("step 6 realised value, % of perfect foresight (2 h)")
    ax.set_title("Forecast accuracy vs storage value (red = stack, grey = naive)", fontsize=10)
    ax.grid(alpha=0.3); fig.tight_layout()
    p2 = out_dir / "R2_accuracy_vs_storage_value.png"
    fig.savefig(p2, dpi=130); plt.close(fig)
    return [p1, p2]


def main() -> int:
    kn = extract()
    (REPORT / "results").mkdir(exist_ok=True)
    (REPORT / "results" / "key_numbers.json").write_text(json.dumps(kn, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for k, v in kn.items():
        print(f"{k:28s} {fmt(v):>12s} {v['unit']}")
    figures()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
