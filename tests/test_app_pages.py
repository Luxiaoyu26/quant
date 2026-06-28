from pathlib import Path

import numpy as np
import pandas as pd
import pytest


def test_app_exposes_single_stock_and_main_wave_pages():
    source = Path("app.py").read_text(encoding="utf-8")

    assert "def render_main_wave_page" in source
    assert "run_main_wave_candidate_selection" in source
    assert "actual_feature_date" in source
    assert "requested_select_date" in source


@pytest.mark.filterwarnings("ignore:Type google.protobuf.*:DeprecationWarning")
def test_main_wave_page_generates_default_pool_result(monkeypatch):
    import core.data_loader as loader
    import selection.main_wave_selector as selector
    from streamlit.testing.v1 import AppTest

    index = pd.date_range("2025-01-01", periods=120, freq="D", name="Date")
    close = pd.Series(np.linspace(10, 20, len(index)), index=index)
    sample = pd.DataFrame(
        {
            "Open": close * 0.995,
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Volume": 10_000.0,
        },
        index=index,
    )

    fake_load = lambda *args, **kwargs: sample.copy()
    monkeypatch.setattr(loader, "load_price_data", fake_load)
    monkeypatch.setattr(selector, "load_price_data", fake_load)

    app = AppTest.from_file("app.py").run(timeout=20)
    assert not app.exception
    app.sidebar.radio[0].set_value(app.sidebar.radio[0].options[1])
    app.run(timeout=20)
    assert not app.exception
    app.sidebar.button[0].click()
    app.run(timeout=30)

    assert not app.exception
    assert len(app.dataframe) == 1
    result = app.dataframe[0].value
    assert len(result) == 10
    assert {
        "symbol",
        "sector",
        "final_score",
        "requested_select_date",
        "actual_feature_date",
        "ret_20",
        "ret_60",
        "sector_strength_score",
        "main_wave_score",
        "near_high_score",
        "trend_structure_score",
        "volume_breakout_score",
        "risk_score",
    }.issubset(result.columns)
    assert len(app.get("download_button")) == 1
