// security_headers.py — Initialize Flask-Talisman with strict CSP
import os
from flask_talisman import Talisman

def init_security_headers(app):
    # Content Security Policy allowing fonts and scripts from trusted CDNs only
    csp = {
        'default-src': "'self'",
        'script-src': ["'self'", "https://cdnjs.cloudflare.com", "https://cdn.jsdelivr.net"],
        'style-src': ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
        'font-src': ["'self'", "https://fonts.gstatic.com"],
        'img-src': ["'self'", "data:", "blob:"],
        'connect-src': "'self'",
        'frame-ancestors': "'self'",
    }
    # Force HTTPS, set HSTS, and apply CSP
    Talisman(app,
            content_security_policy=csp,
            force_https=app.config.get("FORCE_HTTPS", False),
            strict_transport_security=True,
            session_cookie_secure=app.config.get("SESSION_COOKIE_SECURE", True),
            frame_options='SAMEORIGIN',
            referrer_policy='strict-origin-when-cross-origin')
    # Additional headers are already set by middleware.add_security_headers
    return app
