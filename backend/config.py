import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "stocksight-dev-secret-change-me")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "stocksight-jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 24  # 24 hours

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'app.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DATA_DIR = os.path.join(BASE_DIR, "data")
    MODEL_DIR = os.path.join(BASE_DIR, "saved_models")

    # NSE tickers (Indian market only, per project scope)
    SUPPORTED_TICKERS = {
        "RELIANCE.NS":   "Reliance Industries",
        "TCS.NS":        "Tata Consultancy Services",
        "INFY.NS":       "Infosys",
        "HDFCBANK.NS":   "HDFC Bank",
        "ICICIBANK.NS":  "ICICI Bank",
        "SBIN.NS":       "State Bank of India",
        "ITC.NS":        "ITC",
        "BHARTIARTL.NS": "Bharti Airtel",
        "LT.NS":         "Larsen & Toubro",
        "WIPRO.NS":      "Wipro",
    }