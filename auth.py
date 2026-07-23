"""
auth.py — Authentication Blueprint with brute-force lockout
"""
import re, logging
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from db_models import db, User
from authlib.integrations.flask_client import OAuth
import secrets

log     = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
oauth   = OAuth()

oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)
EMAIL_RE    = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")
        min_len  = current_app.config.get("PASSWORD_MIN_LENGTH", 8)

        if not USERNAME_RE.match(username):
            flash("Username: 3–30 chars, letters/numbers/underscore only.", "error")
            return render_template("register.html", username=username, email=email)
        if not EMAIL_RE.match(email):
            flash("Please enter a valid email address.", "error")
            return render_template("register.html", username=username, email=email)
        if len(password) < min_len:
            flash(f"Password must be at least {min_len} characters.", "error")
            return render_template("register.html", username=username, email=email)
        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("register.html", username=username, email=email)
        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "error")
            return render_template("register.html", username=username, email=email)
        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
            return render_template("register.html", username=username, email=email)

        user = User(username=username, email=email)
        user.set_password(password)
        if User.query.count() == 0:
            user.is_admin = True
            user.role = "admin"
        db.session.add(user)
        db.session.commit()
        user.record_successful_login(ip=request.remote_addr)
        login_user(user, remember=True)
        flash(f"Welcome to CottonGreen AI, {username}! 🌿", "success")
        return redirect(url_for("index"))
    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password   = request.form.get("password", "")
        remember   = request.form.get("remember") == "on"
        user = (User.query.filter_by(username=identifier).first()
                or User.query.filter_by(email=identifier.lower()).first())
        if not user:
            flash("Invalid credentials.", "error")
            return render_template("login.html", identifier=identifier)
        if user.is_locked():
            flash("Account locked due to too many failed attempts. Try again later.", "error")
            return render_template("login.html", identifier=identifier)
        if not user.is_active:
            flash("Account deactivated. Contact support.", "error")
            return render_template("login.html", identifier=identifier)
        if not user.check_password(password):
            max_att  = current_app.config.get("MAX_LOGIN_ATTEMPTS", 5)
            lock_min = int(current_app.config.get("LOCKOUT_DURATION").total_seconds() // 60)
            locked   = user.record_failed_login(max_attempts=max_att, lockout_minutes=lock_min)
            if locked:
                flash(f"Account locked for {lock_min} minutes.", "error")
            else:
                flash(f"Invalid credentials. {max_att - user.failed_login_count} attempt(s) left.", "error")
            return render_template("login.html", identifier=identifier)
        user.record_successful_login(ip=request.remote_addr)
        login_user(user, remember=remember)
        flash(f"Welcome back, {user.username}! 🌿", "success")
        nxt = request.args.get("next", "")
        return redirect(nxt if nxt.startswith("/") else url_for("index"))
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/google/login")
def google_login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    redirect_uri = url_for("auth.google_authorize", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/google/authorize")
def google_authorize():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    try:
        token = oauth.google.authorize_access_token()
    except Exception as e:
        log.error(f"Google auth error: {e}")
        flash("Google authentication failed or was cancelled.", "error")
        return redirect(url_for("auth.login"))
    
    user_info = token.get("userinfo")
    if not user_info:
        flash("Could not fetch user information from Google.", "error")
        return redirect(url_for("auth.login"))
        
    email = user_info.get("email", "").lower()
    if not email:
        flash("Google account must have an email address.", "error")
        return redirect(url_for("auth.login"))

    # Check if user already exists
    user = User.query.filter_by(email=email).first()
    if user:
        if not user.is_active:
            flash("Account deactivated. Contact support.", "error")
            return redirect(url_for("auth.login"))
        
        # Link Google account if not linked
        if user.oauth_provider != "google":
            user.oauth_provider = "google"
            user.oauth_provider_id = user_info.get("sub")
            db.session.commit()
    else:
        # Create a new user for Google login
        username = email.split("@")[0][:30]
        # Handle potential username collisions
        base_username = username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username[:25]}_{counter}"
            counter += 1

        user = User(
            username=username, 
            email=email,
            oauth_provider="google",
            oauth_provider_id=user_info.get("sub")
        )
        if User.query.count() == 0:
            user.is_admin = True
            user.role = "admin"
        db.session.add(user)
        db.session.commit()

    user.record_successful_login(ip=request.remote_addr)
    login_user(user, remember=True)
    flash(f"Welcome back, {user.username}! 🌿", "success")
    return redirect(url_for("index"))

