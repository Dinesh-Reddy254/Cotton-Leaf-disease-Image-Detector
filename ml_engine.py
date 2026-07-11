"""
ml_engine.py — Singleton ML Model Engine
Fixes circular import: api.py no longer imports from app.py
"""
import os
import logging
import numpy as np
from PIL import Image

log = logging.getLogger(__name__)

_model = None
_config: dict = {}


def init_engine(app_config: dict):
    """Called once from app factory with app.config snapshot."""
    global _config
    _config = {
        "MODEL_PATH": app_config.get("MODEL_PATH"),
        "IMG_SIZE":   app_config.get("IMG_SIZE", (224, 224)),
        "CLASS_NAMES": app_config.get("CLASS_NAMES", []),
    }


def load_model():
    global _model
    if _model is not None:
        return _model

    model_path = _config.get("MODEL_PATH")
    if not model_path or not os.path.exists(model_path):
        log.error("MODEL_PATH not found: %s", model_path)
        return None

    try:
        import tensorflow as tf
        import keras
        from tensorflow.keras.layers import InputLayer

        class SafeInputLayer(InputLayer):
            def __init__(self, *args, **kwargs):
                kwargs.pop("optional", None)
                kwargs.pop("batch_shape", None)
                super().__init__(*args, **kwargs)

        with keras.saving.custom_object_scope({"InputLayer": SafeInputLayer}):
            try:
                _model = tf.keras.models.load_model(model_path, compile=False)
            except Exception:
                _model = keras.models.load_model(model_path)

        log.info("✅ Model loaded from %s", model_path)
    except Exception as exc:
        log.error("❌ Model load failed: %s", exc)
        _model = None

    return _model


def get_model():
    return _model if _model is not None else load_model()


def predict_image(img: Image.Image) -> dict:
    """Run inference. Returns dict with disease, confidence, top3, all_probs, info."""
    from tensorflow.keras.applications.efficientnet import preprocess_input
    from utils import DISEASE_INFO

    model = get_model()
    if model is None:
        raise RuntimeError("Model unavailable")

    class_names = _config["CLASS_NAMES"]
    img_size    = _config["IMG_SIZE"]

    img_rgb  = img.convert("RGB").resize(img_size)
    arr      = preprocess_input(np.array(img_rgb, dtype=np.float32))
    tensor   = np.expand_dims(arr, 0)
    probs    = model.predict(tensor, verbose=0)[0]

    top_idx  = int(np.argmax(probs))
    all_probs = {class_names[i]: round(float(probs[i]) * 100, 2)
                 for i in range(len(class_names))}
    top3 = sorted(all_probs.items(), key=lambda x: -x[1])[:3]

    return {
        "disease":    class_names[top_idx],
        "confidence": round(float(probs[top_idx]) * 100, 2),
        "all_probs":  all_probs,
        "top3":       top3,
        "info":       DISEASE_INFO.get(class_names[top_idx], {}),
    }
