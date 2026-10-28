from datetime import datetime
import pandas as pd

from ml.data_loader import load_history
from ml.features import make_prediction_row, FEATURE_COLS
from ml.train import load_trained, train_for_ticker
from ml.investment import calculate_investment, decide


def predict_for_ticker(ticker: str, horizon_days: int) -> dict:
    """
    Load the trained model for (ticker, horizon) and predict using latest features.
    If no trained model exists, trains one on the fly (first-time fallback).
    """
    bundle = load_trained(ticker, horizon_days)
    if bundle is None:
        train_for_ticker(ticker, horizon_days, save=True)
        bundle = load_trained(ticker, horizon_days)
        if bundle is None:
            raise RuntimeError(f"Could not train/load model for {ticker} ({horizon_days}d)")

    model = bundle["model"]
    meta = bundle["meta"]

    df = load_history(ticker)
    latest_features, last_close, last_date = make_prediction_row(df)

    predicted_price = float(model.predict(latest_features)[0])

    # For chart: 6 months of history + the predicted point
    hist = df.tail(180)[["Date", "Close"]].copy()
    hist["Date"] = pd.to_datetime(hist["Date"]).dt.strftime("%Y-%m-%d")

    return {
        "ticker": ticker,
        "horizon_days": horizon_days,
        "as_of_date": pd.to_datetime(last_date).strftime("%Y-%m-%d"),
        "current_price": round(last_close, 2),
        "predicted_price": round(predicted_price, 2),
        "model_info": {
            "name": meta["best_model_name"],
            "metrics": meta["best_metrics"],
            "all_models": meta["all_metrics"],
            "trained_at": meta["trained_at"],
        },
        "history": hist.to_dict(orient="records"),
    }