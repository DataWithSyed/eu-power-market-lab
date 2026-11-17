"""Checks that the final report quotes the step outputs correctly and its artefacts exist."""
import hashlib
import importlib.util
import json
import re
from pathlib import Path

import pytest

REPORT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_report", REPORT / "scripts" / "build_report.py")
br = importlib.util.module_from_spec(spec)
spec.loader.exec_module(br)


def test_key_numbers_match_step_outputs():
    stored = json.loads((REPORT / "results" / "key_numbers.json").read_text(encoding="utf-8"))
    fresh = br.extract()
    assert stored.keys() == fresh.keys()
    for k in fresh:
        assert stored[k]["value"] == pytest.approx(fresh[k]["value"]), k


def test_every_key_number_is_quoted_in_the_report():
    text = (REPORT / "README.md").read_text(encoding="utf-8")
    kn = br.extract()
    missing = [k for k, v in kn.items() if br.fmt(v) not in text]
    assert not missing, missing


def test_snapshot_hashes_match_sources_manifest():
    man = (REPORT / "data" / "SOURCES.md").read_text(encoding="utf-8")
    rows = re.findall(r"\| `([^`]+)` \| `([0-9a-f]{64})` \|", man)
    assert len(rows) >= 20
    for rel, sha in rows:
        assert hashlib.sha256((REPORT / "data" / rel).read_bytes()).hexdigest() == sha, rel


def test_figures_referenced_in_report_exist():
    text = (REPORT / "README.md").read_text(encoding="utf-8")
    figs = re.findall(r"\]\((figures/[^)]+\.png)\)", text)
    assert len(figs) >= 8
    for f in figs:
        assert (REPORT / f).stat().st_size > 10_000, f


def test_no_institution_terms_in_report():
    text = (REPORT / "README.md").read_text(encoding="utf-8").lower()
    for w in ("university", "professor", "thesis", "fluxiss"):
        assert w not in text


def test_dashboard_runs():
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(REPORT / "dashboard" / "app.py"), default_timeout=60).run()
    assert not at.exception
    assert len(at.metric) == 4
    for view in ("H2-2026 underpricing", "Forecasts (step 5)", "BESS value (step 6)"):
        at.sidebar.radio[0].set_value(view).run()
        assert not at.exception, view
