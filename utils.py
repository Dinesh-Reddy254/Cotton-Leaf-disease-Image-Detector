"""
utils.py — Utilities
"""
import io
import hashlib
from datetime import datetime, timezone
from PIL import Image

DISEASE_INFO = {
    "Bacterial Blight": {"severity": "High", "description": "Angular water-soaked lesions.", "treatment": "Copper-based bactericides.", "prevention": "Disease-free seeds."},
    "Curl Virus": {"severity": "Very High", "description": "Leaf curling and stunting via whiteflies.", "treatment": "Imidacloprid for vectors.", "prevention": "Resistant cultivars."},
    "Healthy Leaf": {"severity": "None", "description": "No disease detected.", "treatment": "N/A", "prevention": "Balanced fertilisation."},
    "Herbicide Growth Damage": {"severity": "Medium", "description": "Abnormal growth from herbicide.", "treatment": "Flush soil.", "prevention": "Calibrate sprayers."},
    "Leaf Hopper Jassids": {"severity": "Medium", "description": "Damage by Amrasca.", "treatment": "Imidacloprid 17.8 SL.", "prevention": "Natural predators."},
    "Leaf Redding": {"severity": "Low", "description": "Potassium deficiency.", "treatment": "Potassium sulphate.", "prevention": "Soil testing."},
    "Leaf Variegation": {"severity": "Medium", "description": "Mosaic-like patterns.", "treatment": "Control aphid vectors.", "prevention": "Virus-free seed."}
}

def generate_thumbnail(file_bytes: bytes, size: int = 150) -> str:
    import base64
    img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    w, h = img.size
    crop_size = min(w, h)
    left, top = (w - crop_size) // 2, (h - crop_size) // 2
    img = img.crop((left, top, left + crop_size, top + crop_size)).resize((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=60)
    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"

def generate_pdf_report(prediction: dict, username: str = "Anonymous") -> bytes:
    disease = prediction.get("disease", "Unknown")
    conf = prediction.get("confidence", 0)
    info = prediction.get("info", {})
    lines = [
        "COTTONGREEN AI — DIAGNOSIS REPORT",
        f"User: {username} | Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        f"Disease: {disease} ({conf:.1f}%)",
        f"Severity: {info.get('severity', 'N/A')}",
        "\nDESCRIPTION\n" + info.get('description', 'N/A'),
        "\nTREATMENT\n" + info.get('treatment', 'N/A')
    ]
    return "\n".join(lines).encode("utf-8")

def compute_user_stats(user_id: int) -> dict:
    from db_models import ScanHistory
    from sqlalchemy import func
    total = ScanHistory.query.filter_by(user_id=user_id).count()
    healthy = ScanHistory.query.filter_by(user_id=user_id, disease="Healthy Leaf").count()
    freq_rows = ScanHistory.query.with_entities(ScanHistory.disease, func.count(ScanHistory.id).label("cnt")).filter_by(user_id=user_id).group_by(ScanHistory.disease).all()
    avg_conf = ScanHistory.query.with_entities(func.avg(ScanHistory.confidence)).filter_by(user_id=user_id).scalar() or 0
    return {
        "total_scans": total,
        "healthy_scans": healthy,
        "diseased_scans": total - healthy,
        "health_rate": round((healthy/total*100) if total>0 else 0, 1),
        "avg_confidence": round(float(avg_conf), 1),
        "disease_frequency": [{"disease": r.disease, "count": r.cnt} for r in freq_rows]
    }
