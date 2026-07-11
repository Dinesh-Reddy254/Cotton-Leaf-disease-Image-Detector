"""
app.py — CottonGreen AI Application Factory
"""
import os
import logging
from dotenv import load_dotenv
load_dotenv()

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

from flask import Flask, render_template, redirect, url_for, jsonify
from flask_login import LoginManager, login_required, current_user
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_limiter import Limiter
from flask_compress import Compress
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

from config import get_config
from db_models import db, User, ScanHistory
from auth import auth_bp
from api import api_bp
from admin import admin_bp
from middleware import add_security_headers, before_request_timing, after_request_timing
from utils import compute_user_stats
from flask_caching import Cache
import ml_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


def create_app(config_obj=None):
    app = Flask(__name__)
    # Initialize CSRF protection
    csrf = CSRFProtect(app)
    csrf.exempt(auth_bp)
    csrf.exempt(api_bp)

    cfg = config_obj or get_config()
    app.config.from_object(cfg)

    # Initialize ML Engine
    ml_engine.init_engine(app.config)

    # ── Middleware ────────────────────────────────────────────────
    Compress(app)
    if os.environ.get("USE_PROXYFIX", "false").lower() == "true":
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # ── Database ──────────────────────────────────────────────────
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # ── Rate limiter ──────────────────────────────────────────────
    Limiter(
        get_remote_address,
        app=app,
        default_limits=[app.config.get("RATELIMIT_DEFAULT", "200/hour")],
        storage_uri=app.config.get("RATELIMIT_STORAGE_URI", "memory://"),
    )

    # ── Login manager ─────────────────────────────────────────────
    login_manager = LoginManager(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please sign in to continue."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # ── Blueprints ────────────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)

    # ── Request hooks ─────────────────────────────────────────────
    app.before_request(before_request_timing)
    app.after_request(after_request_timing)
    app.after_request(add_security_headers)

    # Initialize Flask-Caching
    cache = Cache(app)
    # Initialize Flask-CORS with allowed origins from config
    from flask_cors import CORS
    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ALLOWED_ORIGINS", "*")}})

    # ── Routes ────────────────────────────────────────────────────
    @app.route("/")
    @login_required
    def index():
        class_names = app.config.get("CLASS_NAMES", [])
        return render_template("index.html", class_names=class_names)

    @app.route("/dashboard")
    @login_required
    def dashboard():
        stats = compute_user_stats(current_user.id)
        recent_scans = (
            ScanHistory.query
            .filter_by(user_id=current_user.id)
            .order_by(ScanHistory.timestamp.desc())
            .limit(6).all()
        )
        return render_template("dashboard.html", **stats, recent_scans=recent_scans)

    @app.route("/health")
    def health():
        model_ok = ml_engine.get_model() is not None
        return jsonify({
            "status": "ok" if model_ok else "degraded",
            "model": "loaded" if model_ok else "unavailable",
            "version": app.config.get("APP_VERSION"),
        }), 200 if model_ok else 503

    # ── Error handlers ────────────────────────────────────────────
    @app.errorhandler(400)
    def bad_request(e):
        return render_template("errors/400.html"), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify({"error": "Rate limit exceeded. Please slow down."}), 429

    @app.errorhandler(500)
    def server_error(e):
        log.error("500 error: %s", e)
        return render_template("errors/500.html"), 500

    # ── Context processors ────────────────────────────────────────
    @app.context_processor
    def inject_globals():
        return {
            "app_version": app.config.get("APP_VERSION"),
            "app_name":    app.config.get("APP_NAME"),
            "csrf_token": lambda: generate_csrf(),
        }

    return app


# ── Entry point ───────────────────────────────────────────────────
app = create_app()

if __name__ == "__main__":
    if os.environ.get("FLASK_ENV") == "production":
        from waitress import serve
        log.info("Starting production server (waitress)…")
        serve(app, host="0.0.0.0", port=5000, threads=8)
    else:
        app.run(debug=True, host="0.0.0.0", port=5000)
