from __future__ import annotations

import pandas as pd

from core.data_loader import load_price_data, normalize_a_share_symbol
from factors.main_wave_scores import calculate_main_wave_scores
from factors.momentum_factors import calculate_momentum_features
from factors.risk_filters import apply_candidate_filters
from factors.sector_factors import calculate_sector_strength
from factors.volume_price_factors import calculate_volume_price_features
from stock_pools.sector_map import get_stock_sector


RESULT_COLUMNS = [
    "rank",
    "symbol",
    "sector",
    "feature_date",
    "requested_select_date",
    "actual_feature_date",
    "final_score",
    "main_wave_score",
    "raw_score",
    "near_high_score",
    "trend_structure_score",
    "volume_breakout_score",
    "risk_score",
    "risk_penalty_score",
    "ret_5",
    "ret_20",
    "ret_60",
    "near_high_20",
    "near_high_60",
    "breakout_20",
    "breakout_60",
    "volume_ratio_5_20",
    "volume_ratio_20_60",
    "volatility_20",
    "sector_strength_score",
    "sector_ret_5_mean",
    "sector_ret_20_mean",
    "sector_volume_strength",
    "sector_breakout_ratio",
    "filter_pass",
    "filter_reason",
]


def _empty_result(errors: list[str]) -> pd.DataFrame:
    result = pd.DataFrame(columns=RESULT_COLUMNS)
    result.attrs["errors"] = errors
    return result


def _resolve_actual_feature_date(
    index: pd.Index, target_date: pd.Timestamp | None
) -> pd.Timestamp | None:
    date_index = pd.DatetimeIndex(index)
    if date_index.empty:
        return None
    if target_date is None:
        return date_index.max()
    available = date_index[date_index <= target_date]
    if available.empty:
        return None
    return available.max()


def run_main_wave_candidate_selection(
    symbols: list[str],
    start: str,
    end: str,
    select_date: str | None = None,
    top_n: int = 20,
    adjust: str = "qfq",
    source: str = "自动",
    use_cache: bool = True,
    disable_proxy: bool = True,
) -> pd.DataFrame:
    """Build and rank a rule-based A-share main-wave candidate cross-section."""
    requested_cutoff = pd.to_datetime(select_date or end)
    requested_select_date = pd.to_datetime(select_date) if select_date else None
    errors: list[str] = []
    rows: list[dict] = []
    seen: set[str] = set()
    prepared_rows: list[dict] = []

    for raw_symbol in symbols:
        try:
            symbol = normalize_a_share_symbol(raw_symbol)
            if symbol in seen:
                continue
            seen.add(symbol)
            prices = load_price_data(
                symbol,
                start,
                end,
                market="A股",
                adjust=adjust,
                source=source,
                use_cache=use_cache,
                disable_proxy=disable_proxy,
            )
            features = calculate_momentum_features(prices)
            features = calculate_volume_price_features(features)
            prepared_rows.append(
                {
                    "symbol": symbol,
                    "sector": get_stock_sector(symbol),
                    "features": features,
                }
            )
        except Exception as exc:
            errors.append(f"{raw_symbol}: {exc}")

    if not prepared_rows or top_n <= 0:
        return _empty_result(errors)

    common_target_date = None
    if requested_select_date is None:
        common_dates = [
            _resolve_actual_feature_date(item["features"].index, requested_cutoff)
            for item in prepared_rows
        ]
        common_dates = [date for date in common_dates if date is not None]
        if common_dates:
            common_target_date = min(common_dates)

    for item in prepared_rows:
        try:
            target_date = requested_select_date or common_target_date or requested_cutoff
            feature_date = _resolve_actual_feature_date(item["features"].index, target_date)
            if feature_date is None:
                raise ValueError(f"选择日期 {target_date.date()} 之前没有行情数据")
            row = item["features"].loc[feature_date].to_dict()
            row.update(
                {
                    "symbol": item["symbol"],
                    "sector": item["sector"],
                    "feature_date": feature_date,
                    "requested_select_date": (
                        requested_select_date.strftime("%Y-%m-%d")
                        if requested_select_date is not None
                        else None
                    ),
                    "actual_feature_date": feature_date.strftime("%Y-%m-%d"),
                }
            )
            rows.append(row)
        except Exception as exc:
            errors.append(f"{item['symbol']}: {exc}")

    if not rows:
        return _empty_result(errors)

    cross_section = pd.DataFrame(rows)
    cross_section = calculate_sector_strength(cross_section)
    cross_section = apply_candidate_filters(cross_section)
    candidates = cross_section[cross_section["filter_pass"]].copy()
    if candidates.empty:
        return _empty_result(errors)

    candidates = calculate_main_wave_scores(candidates)
    candidates = candidates.sort_values("final_score", ascending=False).head(int(top_n))
    candidates.insert(0, "rank", range(1, len(candidates) + 1))
    result = candidates[RESULT_COLUMNS].reset_index(drop=True)
    result.attrs["errors"] = errors
    return result
