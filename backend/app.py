from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from config import Config
from routes.dashboard import dashboard_bp
from routes.pdf import pdf_bp
from routes.suppliers import suppliers_bp
from routes.transactions import transactions_bp
from routes.voice import voice_bp
from services.db import close_mongo, init_mongo


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": app.config["FRONTEND_ORIGIN"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
            }
        },
    )
    init_mongo(app)

    @app.after_request
    def add_cors_headers(response):
        if request.path.startswith("/api/"):
            origin = request.headers.get("Origin")
            response.headers["Access-Control-Allow-Origin"] = origin or app.config["FRONTEND_ORIGIN"]
            response.headers["Vary"] = "Origin"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = request.headers.get(
                "Access-Control-Request-Headers",
                "Content-Type, Authorization",
            )
        return response

    app.register_blueprint(dashboard_bp, url_prefix="/api")
    app.register_blueprint(suppliers_bp, url_prefix="/api/suppliers")
    app.register_blueprint(transactions_bp, url_prefix="/api")
    app.register_blueprint(voice_bp, url_prefix="/api")
    app.register_blueprint(pdf_bp, url_prefix="/api/suppliers")

    @app.get("/")
    def root():
        return jsonify({"status": "ok", "message": "Shop ledger API is running"})

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "message": "Shop ledger API is running"})

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "Route not found"}), 404

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return jsonify({"error": error.description}), error.code

    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.exception(error)
        return jsonify({"error": "Something went wrong", "details": str(error)}), 500

    app.teardown_appcontext(close_mongo)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=app.config["PORT"], debug=app.config["DEBUG"])
