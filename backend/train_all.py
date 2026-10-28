# backend/train_all.py
from app import create_app
from config import Config
from ml.train import train_for_ticker

HORIZONS = [7, 30, 90, 180]

def main():
    app = create_app()
    with app.app_context():
        for ticker in Config.SUPPORTED_TICKERS:
            for h in HORIZONS:
                try:
                    res = train_for_ticker(ticker, h, save=True)
                    bm = res["best_model_name"]
                    m = res["best_metrics"]
                    print(f"[OK] {ticker:14s} h={h:3d}d  best={bm:16s} RMSE={m['RMSE']:.2f}  R2={m['R2']:.3f}")
                except Exception as e:
                    print(f"[ERR] {ticker} h={h}: {e}")

if __name__ == "__main__":
    main()