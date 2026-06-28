import numpy as np
import pandas as pd
from core.indicators import add_moving_averages, add_rsi, add_bollinger_bands


def ma_cross_strategy(df: pd.DataFrame, fast: int = 5, slow: int = 20) -> pd.DataFrame:
    """Position = 1 when fast MA is above slow MA, else 0."""
    if fast >= slow:
        raise ValueError("fast window must be smaller than slow window")

    out = add_moving_averages(df, windows=(fast, slow))
    out["Signal"] = 0
    out.loc[out[f"MA{fast}"] > out[f"MA{slow}"], "Signal"] = 1
    out["Position"] = out["Signal"].shift(1).fillna(0)
    return out


def rsi_mean_reversion_strategy(
    df: pd.DataFrame,
    window: int = 14,
    buy_threshold: float = 30,
    sell_threshold: float = 70,
) -> pd.DataFrame:
    """Buy oversold, sell overbought."""
    out = add_rsi(df, window=window)
    out["Signal"] = np.nan
    out.loc[out["RSI"] < buy_threshold, "Signal"] = 1
    out.loc[out["RSI"] > sell_threshold, "Signal"] = 0
    out["Signal"] = out["Signal"].ffill().fillna(0)
    out["Position"] = out["Signal"].shift(1).fillna(0)
    return out


def bollinger_strategy(df: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """Buy when close is below lower band, sell when close is above upper band."""
    out = add_bollinger_bands(df, window=window, num_std=num_std)
    out["Signal"] = np.nan
    out.loc[out["Close"] < out["BB_LOWER"], "Signal"] = 1
    out.loc[out["Close"] > out["BB_UPPER"], "Signal"] = 0
    out["Signal"] = out["Signal"].ffill().fillna(0)
    out["Position"] = out["Signal"].shift(1).fillna(0)
    return out
