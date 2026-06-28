from __future__ import annotations

import pandas as pd
import pytest

from core.metrics import (
    calculate_annual_return,
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    calculate_total_return,
)


def test_metric_functions_calculate_expected_values():
    assert calculate_total_return([100, 110]) == pytest.approx(0.10)
    assert calculate_max_drawdown([100, 120, 90, 110]) == pytest.approx(-0.25)
    assert calculate_annual_return([100, 110], periods_per_year=1) == pytest.approx(0.10)
    assert calculate_sharpe_ratio([0.01, 0.02, 0.03], periods_per_year=1) == pytest.approx(2.0)


@pytest.mark.parametrize("values", [[], pd.Series(dtype=float), None])
def test_metric_functions_handle_empty_data(values):
    assert calculate_total_return(values) == 0.0
    assert calculate_max_drawdown(values) == 0.0
    assert calculate_annual_return(values) == 0.0
    assert calculate_sharpe_ratio(values) == 0.0


def test_metric_functions_avoid_zero_division():
    assert calculate_total_return([0, 10]) == 0.0
    assert calculate_annual_return([0, 10]) == 0.0
    assert calculate_sharpe_ratio([0.01, 0.01, 0.01]) == 0.0
