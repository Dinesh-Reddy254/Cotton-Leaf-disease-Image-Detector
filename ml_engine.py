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
_ood_model = None
_config: dict = {}


def init_engine(app_config: dict):
    """Called once from app factory with app.config snapshot."""
    global _config
    _config = {
        "MODEL_PATH": app_config.get("MODEL_PATH"),
        "IMG_SIZE":   app_config.get("IMG_SIZE", (224, 224)),
        "CLASS_NAMES": app_config.get("CLASS_NAMES", []),
        "HF_REPO_ID": app_config.get("HF_REPO_ID"),
        "HF_MODEL_FILENAME": app_config.get("HF_MODEL_FILENAME"),
    }


def load_model():
    global _model
    if _model is not None:
        return _model

    model_path = _config.get("MODEL_PATH")
    if not model_path or not os.path.exists(model_path):
        log.warning("MODEL_PATH not found locally: %s", model_path)
        hf_repo_id = _config.get("HF_REPO_ID")
        hf_filename = _config.get("HF_MODEL_FILENAME")
        
        if hf_repo_id and hf_filename:
            log.info("Attempting to download model from Hugging Face: %s/%s", hf_repo_id, hf_filename)
            try:
                from huggingface_hub import hf_hub_download
                model_path = hf_hub_download(repo_id=hf_repo_id, filename=hf_filename)
                log.info("Successfully downloaded model to %s", model_path)
            except Exception as e:
                log.error("Failed to download model from Hugging Face: %s", e)
                return None
        else:
            log.error("No Hugging Face config provided, cannot download model.")
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

        log.info("\u2705 Model loaded from %s", model_path)
    except Exception as exc:
        log.error("\u274c Model load failed: %s", exc)
        _model = None

    return _model


def get_model():
    return _model if _model is not None else load_model()


def _check_ood(img: Image.Image) -> dict:
    global _ood_model
    try:
        import tensorflow.keras.applications.mobilenet_v2 as mobilenet_v2
        if _ood_model is None:
            _ood_model = mobilenet_v2.MobileNetV2(weights='imagenet')

        img_rgb = img.convert('RGB').resize((224, 224))
        arr = mobilenet_v2.preprocess_input(np.array(img_rgb, dtype=np.float32))
        tensor = np.expand_dims(arr, 0)
        
        probs = _ood_model.predict(tensor, verbose=0)
        top3 = mobilenet_v2.decode_predictions(probs, top=3)[0]
        
        PLANT_KEYWORDS = {
            'leaf', 'plant', 'flower', 'tree', 'herb', 'shrub', 'vine', 'moss',
            'fungus', 'mushroom', 'seed', 'petal', 'stem', 'grass', 'weed',
            'cotton', 'daisy', 'rose', 'sunflower', 'tulip', 'orchid', 'lily',
            'corn', 'wheat', 'hay', 'straw', 'garden', 'pot', 'planter',
            'greenhouse', 'acorn', 'hip', 'fig', 'lemon', 'orange', 'banana',
            'pineapple', 'strawberry', 'pomegranate', 'jackfruit', 'custard_apple',
            'cardoon', 'artichoke', 'cabbage', 'broccoli', 'cauliflower',
            'zucchini', 'cucumber', 'bell_pepper', 'mushroom', 'agaric',
            'ear', 'rapeseed', 'buckeye', 'coral_fungus',
        }
        
        top_label_human_readable = top3[0][1]
        top_confidence_pct = round(float(top3[0][2]) * 100, 2)
        
        for _, label, _ in top3:
            label_lower = label.lower()
            if any(kw in label_lower for kw in PLANT_KEYWORDS):
                return {'is_ood': False}
                
        return {'is_ood': True, 'ood_label': top_label_human_readable, 'ood_confidence': top_confidence_pct}
    except Exception as e:
        log.error("OOD check failed: %s", e)
        return {'is_ood': False}


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

    ood_result = _check_ood(img)
    if ood_result.get('is_ood'):
        return {
            'is_ood': True,
            'ood_label': ood_result['ood_label'],
            'ood_confidence': ood_result['ood_confidence'],
            'disease': 'Not a Cotton Leaf',
            'confidence': 0.0,
            'all_probs': {},
            'top3': [],
            'info': {},
        }

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
        "is_ood":     False,
    }
