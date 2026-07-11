"""
middleware.py — Security middleware
"""
import time
import hashlib
import logging
from functools import wraps
from flask import request, jsonify, g, current_app
from flask_login import current_user
from datetime import datetime, timezone

log = logging.getLogger(__name__)

def add_security_headers(response):
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: blob:; "
        "connect-src 'self'; "
        "frame-ancestors 'self' https://*.huggingface.co; "
    )
    response.headers["Content-Security-Policy"] = csp
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers.pop("Server", None)
    return response

def before_request_timing():
    g.request_start = time.time()

def after_request_timing(response):
    if hasattr(g, "request_start"):
        elapsed = (time.time() - g.request_start) * 1000
        response.headers["X-Response-Time"] = f"{elapsed:.1f}ms"
    return response

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 401
        if not getattr(current_user, "is_admin", False):
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated

def api_key_or_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.is_authenticated:
            return f(*args, **kwargs)
        api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "")
        if api_key:
            from db_models import APIKey, db
            from datetime import datetime, timezone
            key_obj = APIKey.query.filter_by(key=api_key, is_active=True).first()
            if key_obj and key_obj.user and key_obj.user.is_active:
                key_obj.last_used = datetime.now(timezone.utc)
                key_obj.calls_made = (key_obj.calls_made or 0) + 1
                db.session.commit()
                g.api_user = key_obj.user
                return f(*args, **kwargs)
        return jsonify({"error": "Auth required"}), 401
    return decorated

def get_current_api_user():
    return current_user if current_user.is_authenticated else getattr(g, "api_user", None)

def sanitize_string(value: str, max_length: int = 255) -> str:
    if not isinstance(value, str):
        return ""
    cleaned = "".join(ch for ch in value if ch.isprintable() or ch in "\n\r\t")
    return cleaned[:max_length].strip()

def compute_image_hash(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()
