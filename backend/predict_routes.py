from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User

from ml.predict import predict_for_ticker
from ml.investment import calculate_investment, decide

predict_bp = Blueprint("predict", __name__, url_prefix="/api")


@predict_bp.route("/predict", methods=["POST"])
@jwt_required()
def predict():
    data = request.get_json() or {}

    ticker = (data.get("ticker") or "").strip()
    amount = data.get("amount")
    horizon = data.get("horizon_days")

    supported = current_app.config["SUPPORTED_TICKERS"]
    if ticker not in supported:
        return jsonify({"error": f"ticker must be one of: {list(supported.keys())}"}), 400

    try:
        amount = float(amount)
        horizon = int(horizon)
    except (TypeError, ValueError):
        return jsonify({"error": "amount must be a number, horizon_days must be an integer"}), 400

    if amount <= 0:
        return jsonify({"error": "amount must be > 0"}), 400
    if horizon <= 0 or horizon > 365:
        return jsonify({"error": "horizon_days must be between 1 and 365"}), 400

    # Round to nearest supported horizon bucket for model lookup
    allowed_horizons = [7, 30, 90, 180]
    bucket = min(allowed_horizons, key=lambda h: abs(h - horizon))

    try:
        prediction = predict_for_ticker(ticker, bucket)
    except Exception as e:
        return jsonify({"error": f"prediction failed: {str(e)}"}), 500

    investment = calculate_investment(
        current_price=prediction["current_price"],
        predicted_price=prediction["predicted_price"],
        amount=amount,
    )
    decision = decide(investment["return_pct"])

    return jsonify({
        "ticker": ticker,
        "ticker_name": supported[ticker],
        "requested_horizon_days": horizon,
        "used_model_horizon_days": bucket,
        "prediction": {
            "as_of_date": prediction["as_of_date"],
            "current_price": prediction["current_price"],
            "predicted_price": prediction["predicted_price"],
        },
        "investment": investment,
        "decision": decision,
        "model_info": prediction["model_info"],
        "history": prediction["history"],
    }), 200