import numpy as np
import pandas as pd


def add_returns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Return"] = out["Close"].pct_change()
    return out


def add_moving_averages(df: pd.DataFrame, windows=(5, 10, 20, 60)) -> pd.DataFrame:
    out = df.copy()
    for w in windows:
        out[f"MA{w}"] = out["Close"].rolling(w).mean()
    return out


def add_rsi(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    out = df.copy()
    delta = out["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out["RSI"] = 100 - (100 / (1 + rs))
    return out


def add_bollinger_bands(df: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    out = df.copy()
    mid = out["Close"].rolling(window).mean()
    std = out["Close"].rolling(window).std()
    out["BB_MID"] = mid
    out["BB_UPPER"] = mid + num_std * std
    out["BB_LOWER"] = mid - num_std * std
    return out


def add_macd(df: pd.DataFrame, fast=12, slow=26, signal=9) -> pd.DataFrame:
    out = df.copy()
    ema_fast = out["Close"].ewm(span=fast, adjust=False).mean()
    ema_slow = out["Close"].ewm(span=slow, adjust=False).mean()
    out["MACD"] = ema_fast - ema_slow
    out["MACD_SIGNAL"] = out["MACD"].ewm(span=signal, adjust=False).mean()
    out["MACD_HIST"] = out["MACD"] - out["MACD_SIGNAL"]
    return out
