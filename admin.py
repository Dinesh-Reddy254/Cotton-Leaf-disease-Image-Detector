"""
admin.py — Admin Blueprint
"""
import logging
from datetime import datetime, timezone, timedelta
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from db_models import db, User, ScanHistory, APIKey
from middleware import admin_required

log      = logging.getLogger(__name__)
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@login_required
@admin_required
def admin_dashboard():
    since_24h = datetime.now(timezone.utc) - timedelta(hours=24)
    since_7d  = datetime.now(timezone.utc) - timedelta(days=7)

    total_users    = User.query.count()
    total_scans    = ScanHistory.query.count()
    total_api_keys = APIKey.query.filter_by(is_active=True).count()
    scans_24h      = ScanHistory.query.filter(ScanHistory.timestamp >= since_24h).count()
    new_users_24h  = User.query.filter(User.created_at >= since_24h).count()
    scans_7d       = ScanHistory.query.filter(ScanHistory.timestamp >= since_7d).count()

    disease_stats = (
        db.session.query(ScanHistory.disease, func.count(ScanHistory.id).label("cnt"))
        .group_by(ScanHistory.disease).all()
    )
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    recent_scans = ScanHistory.query.order_by(ScanHistory.timestamp.desc()).limit(10).all()

    return render_template(
        "admin.html",
        total_users=total_users, total_scans=total_scans,
        total_api_keys=total_api_keys, scans_24h=scans_24h,
        new_users_24h=new_users_24h, scans_7d=scans_7d,
        disease_stats=disease_stats, recent_users=recent_users,
        recent_scans=recent_scans,
    )


@admin_bp.route("/api/users", methods=["GET"])
@login_required
@admin_required
def admin_list_users():
    page     = request.args.get("page", 1, type=int)
    per_page = 25
    pag      = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        "users": [u.to_dict() for u in pag.items],
        "total": pag.total, "page": page, "pages": pag.pages,
    })


@admin_bp.route("/api/users/<int:user_id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    if user.id == current_user.id:
        return jsonify({"error": "Cannot deactivate yourself"}), 400
    user.is_active = not user.is_active
    db.session.commit()
    status = "activated" if user.is_active else "deactivated"
    return jsonify({"message": f"User {status}", "is_active": user.is_active})


@admin_bp.route("/api/users/<int:user_id>/promote", methods=["POST"])
@login_required
@admin_required
def promote_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    user.is_admin = True
    user.role     = "admin"
    db.session.commit()
    return jsonify({"message": f"{user.username} promoted to admin"})


@admin_bp.route("/api/scans", methods=["GET"])
@login_required
@admin_required
def admin_scans():
    page     = request.args.get("page", 1, type=int)
    per_page = 25
    pag      = ScanHistory.query.order_by(ScanHistory.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        "scans": [s.to_dict() for s in pag.items],
        "total": pag.total, "page": page, "pages": pag.pages,
    })


@admin_bp.route("/api/stats/timeline", methods=["GET"])
@login_required
@admin_required
def scan_timeline():
    """Daily scan counts for last 14 days."""
    rows = (
        db.session.query(
            func.date(ScanHistory.timestamp).label("day"),
            func.count(ScanHistory.id).label("cnt"),
        )
        .filter(ScanHistory.timestamp >= datetime.now(timezone.utc) - timedelta(days=14))
        .group_by(func.date(ScanHistory.timestamp))
        .order_by("day")
        .all()
    )
    return jsonify([{"day": str(r.day), "count": r.cnt} for r in rows])
