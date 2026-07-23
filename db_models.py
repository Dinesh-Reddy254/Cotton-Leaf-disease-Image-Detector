"""
db_models.py — SQLAlchemy models for CottonGreen AI
"""
from datetime import datetime, timezone, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=True)
    oauth_provider = db.Column(db.String(50), nullable=True)
    oauth_provider_id = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default="user")
    failed_login_count = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    last_login_at = db.Column(db.DateTime, nullable=True)
    last_login_ip = db.Column(db.String(45), nullable=True)

    scans = db.relationship("ScanHistory", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")
    api_keys = db.relationship("APIKey", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def is_locked(self) -> bool:
        if self.locked_until is None:
            return False
        if datetime.now(timezone.utc) > self.locked_until.replace(tzinfo=timezone.utc):
            self.failed_login_count = 0
            self.locked_until = None
            db.session.commit()
            return False
        return True

    def record_failed_login(self, max_attempts: int = 5, lockout_minutes: int = 15) -> bool:
        self.failed_login_count = (self.failed_login_count or 0) + 1
        if self.failed_login_count >= max_attempts:
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=lockout_minutes)
            db.session.commit()
            return True
        db.session.commit()
        return False

    def record_successful_login(self, ip: str = None):
        self.failed_login_count = 0
        self.locked_until = None
        self.last_login_at = datetime.now(timezone.utc)
        if ip:
            self.last_login_ip = ip
        db.session.commit()

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_admin": self.is_admin,
            "is_active": self.is_active,
            "scan_count": self.scans.count(),
        }

class ScanHistory(db.Model):
    __tablename__ = "scan_history"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    disease = db.Column(db.String(100), nullable=False)
    severity = db.Column(db.String(50), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    thumbnail = db.Column(db.Text, nullable=True)
    image_hash = db.Column(db.String(64), nullable=True)
    processing_ms = db.Column(db.Integer, nullable=True)
    model_version = db.Column(db.String(20), default="2.0.0")
    client_ip = db.Column(db.String(45), nullable=True)
    user = db.relationship("User", back_populates="scans")

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.timestamp.isoformat() + "Z",
            "disease": self.disease,
            "severity": self.severity,
            "confidence": self.confidence,
            "thumb": self.thumbnail or "",
            "processing_ms": self.processing_ms
        }

class APIKey(db.Model):
    __tablename__ = "api_keys"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, default="Default Key")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_used = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    calls_made = db.Column(db.Integer, default=0)
    user = db.relationship("User", back_populates="api_keys")

    @staticmethod
    def generate_key():
        return f"cgai_{secrets.token_hex(24)}"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "key_prefix": self.key[:12] + "…",
            "is_active": self.is_active,
            "calls_made": self.calls_made,
        }
