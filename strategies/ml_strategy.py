import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from core.indicators import add_returns, add_moving_averages, add_rsi, add_bollinger_bands, add_macd


def ml_direction_strategy(
    df: pd.DataFrame,
    train_ratio: float = 0.7,
    probability_threshold: float = 0.55,
    n_estimators: int = 200,
    random_state: int = 42,
):
    """Train a simple RandomForest to predict next-day direction.

    Label: 1 if next day's close-to-close return is positive, else 0.
    Position: 1 only when predicted probability exceeds threshold.
    """
    out = add_returns(df)
    out = add_moving_averages(out, windows=(5, 10, 20, 60))
    out = add_rsi(out, window=14)
    out = add_bollinger_bands(out, window=20, num_std=2.0)
    out = add_macd(out)

    out["Volatility_5"] = out["Return"].rolling(5).std()
    out["Volatility_20"] = out["Return"].rolling(20).std()
    out["Volume_Change"] = out["Volume"].pct_change()
    out["Target"] = (out["Close"].pct_change().shift(-1) > 0).astype(int)

    features = [
        "Return", "MA5", "MA10", "MA20", "MA60", "RSI",
        "BB_MID", "BB_UPPER", "BB_LOWER", "MACD", "MACD_SIGNAL", "MACD_HIST",
        "Volatility_5", "Volatility_20", "Volume_Change"
    ]

    data = out.dropna().copy()
    if len(data) < 150:
        raise ValueError("Not enough data for ML strategy. Please choose a longer date range.")

    split = int(len(data) * train_ratio)
    train = data.iloc[:split]
    test_index = data.index[split:]

    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=5,
        min_samples_leaf=10,
        random_state=random_state,
        class_weight="balanced_subsample",
    )
    model.fit(train[features], train["Target"])

    probs = model.predict_proba(data[features])[:, 1]
    preds = (probs > probability_threshold).astype(int)
    data["Pred_Prob_Up"] = probs
    data["Signal"] = preds
    data.loc[data.index < test_index[0], "Signal"] = 0  # avoid using train period for trading result
    data["Position"] = data["Signal"].shift(1).fillna(0)

    test = data.loc[test_index]
    test_accuracy = accuracy_score(test["Target"], (test["Pred_Prob_Up"] > 0.5).astype(int))

    # Align back to original output shape.
    out = out.join(data[["Pred_Prob_Up", "Signal", "Position"]], how="left")
    out[["Signal", "Position"]] = out[["Signal", "Position"]].fillna(0)

    info = {
        "test_accuracy": float(test_accuracy),
        "train_size": int(len(train)),
        "test_size": int(len(test)),
        "features": features,
    }
    return out, info
