"""
api.py — REST API v1 Blueprint
Circular import FIXED: uses ml_engine instead of importing from app.py
"""
import io
import time
import logging
from flask import Blueprint, request, jsonify, current_app
from PIL import Image

from db_models import db, ScanHistory, APIKey
from middleware import api_key_or_login_required, get_current_api_user
from utils import generate_thumbnail, compute_user_stats
import ml_engine

log = logging.getLogger(__name__)
api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


# ── Predict ───────────────────────────────────────────────────────
@api_bp.route("/predict", methods=["POST"])
@api_key_or_login_required
def api_predict():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    # Validate request using schema
    from schemas import PredictRequestSchema
    schema = PredictRequestSchema()
    errors = schema.validate(request.files)
    if errors:
        return jsonify({"error": "Invalid request payload"}), 400
    # Existing file handling remains
    file = request.files["file"]
    raw  = file.read()

    # Size guard
    max_size = current_app.config.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)
    if len(raw) > max_size:
        return jsonify({"error": "File too large (max 16 MB)"}), 413

    # Validate image
    try:
        img = Image.open(io.BytesIO(raw))
        img.verify()
        img = Image.open(io.BytesIO(raw))   # re-open after verify()
    except Exception:
        return jsonify({"error": "Invalid or corrupted image file"}), 400

    if ml_engine.get_model() is None:
        return jsonify({"error": "Model not ready — please try again shortly"}), 503

    user = get_current_api_user()
    t0   = time.time()

    try:
        result     = ml_engine.predict_image(img)
        elapsed_ms = int((time.time() - t0) * 1000)
        result["processing_ms"] = elapsed_ms

        # Persist scan
        if request.form.get("save", "true").lower() != "false" and user:
            thumb = generate_thumbnail(raw) if len(raw) < 4 * 1024 * 1024 else None
            scan  = ScanHistory(
                user_id      = user.id,
                disease      = result["disease"],
                severity     = result.get("info", {}).get("severity", "Unknown"),
                confidence   = result["confidence"],
                processing_ms= elapsed_ms,
                thumbnail    = thumb,
                client_ip    = request.remote_addr,
                model_version= current_app.config.get("APP_VERSION", "2.0.0"),
            )
            db.session.add(scan)
            db.session.commit()
            result["scan_id"] = scan.id

        return jsonify(result)

    except Exception as exc:
        log.error("Prediction error: %s", exc, exc_info=True)
        return jsonify({"error": "Prediction failed — internal error"}), 500


# ── History ───────────────────────────────────────────────────────
@api_bp.route("/history", methods=["GET"])
@api_key_or_login_required
def api_get_history():
    user     = get_current_api_user()
    page     = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    pag      = (
        ScanHistory.query
        .filter_by(user_id=user.id)
        .order_by(ScanHistory.timestamp.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return jsonify({
        "scans":  [s.to_dict() for s in pag.items],
        "total":  pag.total,
        "page":   page,
        "pages":  pag.pages,
    })


@api_bp.route("/history", methods=["DELETE"])
@api_key_or_login_required
def api_clear_history():
    user = get_current_api_user()
    ScanHistory.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    return jsonify({"message": "Scan history cleared successfully"})



# ── Stats ─────────────────────────────────────────────────────────
@api_bp.route("/stats", methods=["GET"])
@api_key_or_login_required
def api_stats():
    return jsonify(compute_user_stats(get_current_api_user().id))


# ── API Key Management ────────────────────────────────────────────
@api_bp.route("/keys", methods=["GET"])
@api_key_or_login_required
def list_api_keys():
    user = get_current_api_user()
    keys = APIKey.query.filter_by(user_id=user.id).all()
    return jsonify({"keys": [k.to_dict() for k in keys]})


@api_bp.route("/keys", methods=["POST"])
@api_key_or_login_required
def create_api_key():
    user = get_current_api_user()
    if APIKey.query.filter_by(user_id=user.id, is_active=True).count() >= 5:
        return jsonify({"error": "Maximum of 5 active API keys allowed"}), 400
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "My Key"))[:100].strip() or "My Key"
    key  = APIKey(user_id=user.id, key=APIKey.generate_key(), name=name)
    db.session.add(key)
    db.session.commit()
    return jsonify({"id": key.id, "key": key.key, "name": key.name}), 201


@api_bp.route("/keys/<int:key_id>", methods=["DELETE"])
@api_key_or_login_required
def revoke_api_key(key_id):
    user = get_current_api_user()
    key  = APIKey.query.filter_by(id=key_id, user_id=user.id).first_or_404()
    key.is_active = False
    db.session.commit()
    return jsonify({"message": "API key revoked"})
