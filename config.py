"""
config.py — Centralized Configuration for CottonGreen AI
Supports: development, production, testing
"""
import os
import secrets
from datetime import timedelta

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR  = os.path.join(BASE_DIR, "model")

def _resolve_model_path():
    """Try model/final_model.keras first, fall back to best_model.keras at root."""
    candidates = [
        os.path.join(MODEL_DIR,  "final_model.keras"),
        os.path.join(BASE_DIR,   "best_model.keras"),
        os.path.join(MODEL_DIR,  "best_model.keras"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0]   # default (will warn at runtime)


class BaseConfig:
    APP_NAME    = "CottonGreen AI"
    APP_VERSION = "2.0.0"
    SECRET_KEY  = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES      = False

    SESSION_COOKIE_HTTPONLY  = True
    SESSION_COOKIE_SAMESITE  = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024   # 16 MB
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "bmp"}

    MODEL_PATH  = os.environ.get("MODEL_PATH") or _resolve_model_path()
    IMG_SIZE    = (224, 224)
    CLASS_NAMES = [
        "Bacterial Blight", "Curl Virus", "Healthy Leaf",
        "Herbicide Growth Damage", "Leaf Hopper Jassids",
        "Leaf Redding", "Leaf Variegation",
    ]
    HF_REPO_ID        = "DineshReddy254/Cotton-Green-AI"
    HF_MODEL_FILENAME = "model/final_model.keras"

    RATELIMIT_STORAGE_URI    = os.environ.get("REDIS_URL", "memory://")
    RATELIMIT_DEFAULT        = "200/hour"
    RATELIMIT_HEADERS_ENABLED = True
    # Caching configuration
    CACHE_TYPE   = os.environ.get("CACHE_TYPE", "SimpleCache")
    CACHE_REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    # CORS configuration – list of allowed origins (comma‑separated)
    CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "*")  # use "*" for dev, restrict in prod

    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION   = timedelta(minutes=15)
    PASSWORD_MIN_LENGTH = 8

    WTF_CSRF_ENABLED   = True
    WTF_CSRF_TIME_LIMIT = 3600

    HISTORY_PER_PAGE      = 20
    ADMIN_USERS_PER_PAGE  = 25


class DevelopmentConfig(BaseConfig):
    DEBUG   = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'cotton_green.db')}"
    )
    SESSION_COOKIE_SECURE  = False
    REMEMBER_COOKIE_SECURE = False
    RATELIMIT_DEFAULT      = "1000/hour"


class ProductionConfig(BaseConfig):
    DEBUG   = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'cotton_green.db')}"
    )
    SESSION_COOKIE_SECURE  = True
    REMEMBER_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME   = "https"

    @property
    def SQLALCHEMY_ENGINE_OPTIONS(self):
        db_url = self.SQLALCHEMY_DATABASE_URI or ""
        if "postgresql" in db_url:
            return {
                "pool_pre_ping": True,
                "pool_recycle":  280,
                "pool_size":     5,
                "max_overflow":  3,
                "connect_args":  {"connect_timeout": 10},
            }
        return {}


class TestingConfig(BaseConfig):
    DEBUG   = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED        = False
    SESSION_COOKIE_SECURE   = False
    RATELIMIT_ENABLED       = False
    CACHE_TYPE              = "NullCache"


config_map = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
}


def get_config():
    env       = os.environ.get("FLASK_ENV", "development").lower()
    cfg_class = config_map.get(env, DevelopmentConfig)
    cfg       = cfg_class()
    # Normalise postgres:// → postgresql://
    db_url = cfg.SQLALCHEMY_DATABASE_URI or ""
    if db_url.startswith("postgres://"):
        cfg.SQLALCHEMY_DATABASE_URI = db_url.replace("postgres://", "postgresql://", 1)
    return cfg
