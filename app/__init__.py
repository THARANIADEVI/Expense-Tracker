import os
from pathlib import Path
from datetime import datetime
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

load_dotenv()
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()
jwt = JWTManager()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-change-this-secret"),
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY", "dev-only-change-this-secret")),
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(days=7),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///expense_tracker.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("RENDER") == "true" or os.getenv("FLASK_ENV") == "production",
        REMEMBER_COOKIE_HTTPONLY=True,
    )
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    jwt.init_app(app)
    cors_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", r"http://localhost:5173,http://127.0.0.1:5173,https://.*\.vercel\.app").split(",") if origin.strip()]
    CORS(app, resources={r"/api/*": {"origins": cors_origins}}, allow_headers=["Authorization", "Content-Type"], methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    app.context_processor(lambda: {"now": datetime.now})
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please sign in to continue."
    login_manager.login_message_category = "info"

    from app import models  # noqa: F401
    from app.auth import bp as auth_bp
    from app.expenses import bp as expenses_bp
    from app.api import bp as api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(api_bp)
    csrf.exempt(api_bp)

    @app.errorhandler(404)
    def not_found(_error):
        from flask import render_template
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(_error):
        db.session.rollback()
        from flask import render_template
        return render_template("500.html"), 500

    with app.app_context():
        db.create_all()
    return app
