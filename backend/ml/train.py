import os
import joblib
import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

from config import Config
from ml.data_loader import load_history
from ml.features import build_supervised, FEATURE_COLS


def _model_path(ticker: str, horizon: int) -> str:
    return os.path.join(Config.MODEL_DIR, f"{ticker}_{horizon}d.pkl")


def _metrics(y_true, y_pred) -> dict:
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = float(np.sqrt(mse))
    r2 = r2_score(y_true, y_pred)
    return {"MAE": round(mae, 4), "MSE": round(mse, 4),
            "RMSE": round(rmse, 4), "R2": round(r2, 4)}


def _candidates():
    return {
        "LinearRegression": Pipeline([
            ("scaler", StandardScaler()),
            ("model", LinearRegression()),
        ]),
        "RandomForest": RandomForestRegressor(
            n_estimators=200, max_depth=10, random_state=42, n_jobs=-1
        ),
        "SVR": Pipeline([
            ("scaler", StandardScaler()),
            ("model", SVR(kernel="rbf", C=10.0, epsilon=0.1)),
        ]),
        "XGBoost": XGBRegressor(
            n_estimators=300, max_depth=5, learning_rate=0.05,
            subsample=0.9, colsample_bytree=0.9,
            random_state=42, n_jobs=-1,
        ),
    }


def train_for_ticker(ticker: str, horizon_days: int = 30, save: bool = True) -> dict:
    """
    Train all candidate models on chronological 80/20 split.
    Pick best by RMSE. Save the best model + metrics to disk.
    """
    df = load_history(ticker)
    X, y, feature_cols = build_supervised(df, horizon_days)

    # Final guard: drop any inf and align y
    X = X.replace([np.inf, -np.inf], np.nan).dropna()
    y = y.loc[X.index]

    if len(X) < 100:
        raise RuntimeError(f"Not enough data for {ticker} (got {len(X)} rows)")

    split = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    results = {}
    best_name, best_rmse, best_model = None, float("inf"), None

    for name, model in _candidates().items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        m = _metrics(y_test, preds)
        results[name] = m
        if m["RMSE"] < best_rmse:
            best_rmse = m["RMSE"]
            best_name = name
            best_model = model

    payload = {
        "ticker": ticker,
        "horizon_days": horizon_days,
        "feature_cols": feature_cols,
        "best_model_name": best_name,
        "best_metrics": results[best_name],
        "all_metrics": results,
        "trained_at": pd.Timestamp.utcnow().isoformat(),
        "n_train": len(X_train),
        "n_test": len(X_test),
    }

    if save:
        joblib.dump({"model": best_model, "meta": payload}, _model_path(ticker, horizon_days))

    return payload


def load_trained(ticker: str, horizon_days: int):
    path = _model_path(ticker, horizon_days)
    if not os.path.exists(path):
        return None
    return joblib.load(path)