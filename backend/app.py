import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config
from models import db
from auth import auth_bp
from predict_routes import predict_bp

jwt = JWTManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure folders exist
    os.makedirs(os.path.join(os.path.dirname(__file__), "instance"), exist_ok=True)
    os.makedirs(app.config["DATA_DIR"], exist_ok=True)
    os.makedirs(app.config["MODEL_DIR"], exist_ok=True)

    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    db.init_app(app)
    jwt.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(predict_bp)

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "stocksight-api"})

    @app.route("/api/tickers")
    def tickers():
        return jsonify({
            "tickers": [
                {"symbol": sym, "name": name}
                for sym, name in app.config["SUPPORTED_TICKERS"].items()
            ]
        })

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)