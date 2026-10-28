import os
import pandas as pd
from datetime import datetime, timedelta
from curl_cffi import requests as curl_requests
import yfinance as yf

from config import Config


def _csv_path(ticker: str) -> str:
    return os.path.join(Config.DATA_DIR, f"{ticker}.csv")


def download_history(ticker: str, years: int = 5, force: bool = False) -> pd.DataFrame:
    """
    Use yfinance + curl_cffi to impersonate a browser and fetch NSE data.
    """
    path = _csv_path(ticker)

    # Cache valid for 1 day
    if not force and os.path.exists(path):
        age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
        if age < timedelta(days=1):
            return pd.read_csv(path, parse_dates=["Date"])

    end = datetime.now()
    start = end - timedelta(days=365 * years)

    # Key: establish a session impersonating Chrome
    session = curl_requests.Session(impersonate="chrome")

    try:
        df = yf.download(
            ticker,
            start=start,
            end=end,
            progress=False,
            auto_adjust=False,
            session=session,
        )
    except Exception as e:
        raise RuntimeError(f"yfinance download failed for {ticker}: {e}")

    if df is None or df.empty:
        raise RuntimeError(f"No data returned for {ticker} (session may be blocked)")

    # Flatten MultiIndex columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()
    df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]
    df = df.dropna().sort_values("Date").reset_index(drop=True)

    # Data sanity
    df = df[df["Close"] > 0].reset_index(drop=True)
    df = df[df["Volume"] >= 0].reset_index(drop=True)

    df.to_csv(path, index=False)
    return df


def load_history(ticker: str) -> pd.DataFrame:
    return download_history(ticker, force=False)