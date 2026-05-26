from flask import Flask, jsonify
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

    CORS(app, resources={r"/api/*": {"origins": app.config["FRONTEND_ORIGIN"]}})
    init_mongo(app)

    app.register_blueprint(dashboard_bp, url_prefix="/api")
    app.register_blueprint(suppliers_bp, url_prefix="/api/suppliers")
    app.register_blueprint(transactions_bp, url_prefix="/api")
    app.register_blueprint(voice_bp, url_prefix="/api")
    app.register_blueprint(pdf_bp, url_prefix="/api/suppliers")

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
