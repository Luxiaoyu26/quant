from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = [
    "ret_20",
    "ret_60",
    "volatility_20",
    "Volume",
    "volume_ratio_5_20",
    "Close",
    "ma20",
]


def apply_candidate_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Mark candidate eligibility while retaining every input row."""
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Candidate filters missing required columns: {missing}")

    result = df.copy()
    reasons: list[list[str]] = [[] for _ in range(len(result))]

    rules = [
        (result["ret_20"].isna(), "ret_20缺失"),
        (result["ret_60"].isna(), "ret_60缺失"),
        (result["volatility_20"].isna(), "volatility_20缺失"),
        (result["Volume"] <= 0, "成交量非正"),
        (result["volatility_20"] > 0.08, "波动率过高"),
        (result["ret_20"] < -0.15, "20日收益过低"),
        (result["volume_ratio_5_20"] < 0.6, "短期量能不足"),
        (result["Close"] < result["ma20"], "收盘价低于MA20"),
    ]
    for mask, reason in rules:
        for position in range(len(result)):
            if bool(mask.iloc[position]) if not pd.isna(mask.iloc[position]) else False:
                reasons[position].append(reason)

    result["filter_pass"] = [not row_reasons for row_reasons in reasons]
    result["filter_reason"] = ["；".join(row_reasons) for row_reasons in reasons]
    return result
