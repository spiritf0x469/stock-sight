import numpy as np
import pandas as pd


FEATURE_COLS = [
    "Open", "High", "Low", "Close", "Volume",
    "Return_1d", "Return_5d",
    "MA_5", "MA_10", "MA_20",
    "Volatility_10", "Volume_Change", "RSI_14",
]


def _rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add technical features. Returns a new DataFrame with Date + features + Close (target base).
    Hardened against inf/-inf and zero-volume/zero-close anomalies.
    """
    df = df.copy().sort_values("Date").reset_index(drop=True)

    # Drop any rows with non-positive close to avoid division-by-zero downstream
    df = df[df["Close"] > 0].reset_index(drop=True)

    df["Return_1d"]  = df["Close"].pct_change(fill_method=None)
    df["Return_5d"]  = df["Close"].pct_change(5, fill_method=None)
    df["MA_5"] = df["Close"].rolling(5).mean()
    df["MA_10"] = df["Close"].rolling(10).mean()
    df["MA_20"] = df["Close"].rolling(20).mean()
    df["Volatility_10"] = df["Return_1d"].rolling(10).std()

    # Guard against zero-volume days creating inf in pct_change
    vol = df["Volume"].replace(0, np.nan)
    df["Volume_Change"] = vol.pct_change(fill_method=None)

    df["RSI_14"] = _rsi(df["Close"], 14)

    # Replace any remaining inf/-inf with NaN and drop
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna().reset_index(drop=True)
    return df


def build_supervised(df: pd.DataFrame, horizon_days: int):
    """
    Build X, y for a given forecast horizon.
    Target y = Close at t+horizon.
    Returns X (DataFrame), y (Series), feature_cols
    """
    df = engineer_features(df)
    df = df.copy()
    df["Target"] = df["Close"].shift(-horizon_days)
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna().reset_index(drop=True)

    X = df[FEATURE_COLS]
    y = df["Target"]
    return X, y, FEATURE_COLS


def make_prediction_row(df: pd.DataFrame):
    """Return the latest feature row (as 2D array) + last close price, for future prediction."""
    df = engineer_features(df)
    last_close = float(df["Close"].iloc[-1])
    last_date = df["Date"].iloc[-1]
    last_row = df[FEATURE_COLS].iloc[[-1]].values
    return last_row, last_close, last_date