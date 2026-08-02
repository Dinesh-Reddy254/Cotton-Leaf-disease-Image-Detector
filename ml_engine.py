"""
ml_engine.py — Singleton ML Model Engine
Fixes circular import: api.py no longer imports from app.py
"""
import os
import logging
import numpy as np
from PIL import Image

import threading

log = logging.getLogger(__name__)

_model = None
_ood_model = None
_config: dict = {}
_model_lock = threading.Lock()


def init_engine(app_config: dict):
    """Called once from app factory with app.config snapshot."""
    global _config
    _config = {
        "MODEL_PATH": app_config.get("MODEL_PATH"),
        "IMG_SIZE":   app_config.get("IMG_SIZE", (224, 224)),
        "CLASS_NAMES": app_config.get("CLASS_NAMES", []),
        "HF_REPO_ID": app_config.get("HF_REPO_ID"),
        "HF_MODEL_FILENAME": app_config.get("HF_MODEL_FILENAME"),
        "HF_TOKEN": app_config.get("HF_TOKEN") or os.environ.get("HF_TOKEN"),
    }


def is_model_loaded() -> bool:
    """Return True if the Keras model is loaded in memory."""
    return _model is not None


def is_model_available() -> bool:
    """Return True if model is loaded or model file / HF repo is available."""
    if _model is not None:
        return True
    model_path = _config.get("MODEL_PATH")
    if model_path and os.path.exists(model_path):
        return True
    return bool(_config.get("HF_REPO_ID"))


def load_model():
    global _model
    if _model is not None:
        return _model

    with _model_lock:
        # Re-check if another thread initialized model while waiting for lock
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
                    hf_token = _config.get("HF_TOKEN")
                    try:
                        model_path = hf_hub_download(repo_id=hf_repo_id, filename=hf_filename, token=hf_token)
                    except Exception:
                        basename = os.path.basename(hf_filename)
                        model_path = hf_hub_download(repo_id=hf_repo_id, filename=basename, token=hf_token)
                    log.info("Successfully downloaded model to %s", model_path)
                except Exception as e:
                    log.error("Failed to download model from Hugging Face: %s", e)
                    return None
            else:
                log.error("No Hugging Face config provided, cannot download model.")
                return None

        try:
            import keras
            log.info("Loading model with Keras %s ...", keras.__version__)

            # 1. Monkey-patch Dense.__init__ to gracefully ignore quantization_config
            original_dense_init = keras.layers.Dense.__init__
            def safe_dense_init(self, *args, **kwargs):
                kwargs.pop("quantization_config", None)
                original_dense_init(self, *args, **kwargs)
            keras.layers.Dense.__init__ = safe_dense_init

            # 2. Monkey-patch InputLayer.__init__ to gracefully ignore Keras 3 specifics
            original_input_init = keras.layers.InputLayer.__init__
            def safe_input_init(self, *args, **kwargs):
                kwargs.pop("optional", None)
                batch_shape = kwargs.pop("batch_shape", None)
                
                if batch_shape is not None:
                    try:
                        # Try newer Keras style
                        original_input_init(self, *args, batch_shape=batch_shape, **kwargs)
                    except TypeError as e:
                        # Fallback to Keras 2 style if batch_shape is unrecognized
                        if "batch_shape" in str(e) or "unexpected keyword argument" in str(e).lower():
                            original_input_init(self, *args, batch_input_shape=batch_shape, **kwargs)
                        else:
                            raise
                else:
                    original_input_init(self, *args, **kwargs)
            keras.layers.InputLayer.__init__ = safe_input_init

            custom_objects = {
                "Functional": keras.Model,
            }

            with keras.saving.custom_object_scope(custom_objects):
                _model = keras.models.load_model(model_path, compile=False)
                
            log.info("✅ Model loaded from %s", model_path)

            # Pre-warm execution graph to eliminate cold-start latency
            try:
                dummy = np.zeros((1, 224, 224, 3), dtype=np.float32)
                _model.predict(dummy, verbose=0)
                log.info("⚡ Execution graph pre-warmed successfully")
            except Exception as w_err:
                log.warning("Warm-up warning (non-fatal): %s", w_err)

        except Exception as exc:
            log.error("❌ Model load failed: %s", exc, exc_info=True)
            _model = None

        return _model


def get_model():
    return _model if _model is not None else load_model()


def _check_ood(img: Image.Image) -> dict:
    """
    Memory-efficient OOD check using Hugging Face Inference API (Free Tier).
    If the API fails (e.g. DNS error or timeout), falls back to a lightweight
    local MobileNetV2 model to prevent non-leaf images (like cars) from being diagnosed.
    """
    PLANT_KEYWORDS = {
        'leaf', 'plant', 'flower', 'tree', 'herb', 'shrub', 'vine', 'moss',
        'fungus', 'mushroom', 'seed', 'petal', 'stem', 'grass', 'weed',
        'cotton', 'daisy', 'rose', 'sunflower', 'tulip', 'orchid', 'lily',
        'corn', 'wheat', 'hay', 'straw', 'garden', 'pot', 'planter',
        'greenhouse', 'acorn', 'hip', 'fig', 'lemon', 'orange', 'banana',
        'pineapple', 'strawberry', 'pomegranate', 'jackfruit', 'custard_apple',
        'cardoon', 'artichoke', 'cabbage', 'broccoli', 'cauliflower',
        'zucchini', 'cucumber', 'bell_pepper', 'agaric', 'ear', 'rapeseed',
        'buckeye', 'coral_fungus', 'granny_smith',
    }

    # 1. Try Hugging Face API (0 RAM overhead)
    try:
        import requests
        import io
        buf = io.BytesIO()
        img.copy().convert('RGB').resize((224, 224)).save(buf, format='JPEG')
        data = buf.getvalue()
        
        API_URL = "https://api-inference.huggingface.co/models/google/vit-base-patch16-224"
        response = requests.post(API_URL, data=data, timeout=2)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                top_label = result[0].get('label', '')
                top_score = result[0].get('score', 0.0)
                
                label_lower = top_label.lower()
                if not any(kw in label_lower for kw in PLANT_KEYWORDS):
                    human_label = top_label.split(',')[0].title()
                    return {
                        'is_ood': True, 
                        'ood_label': human_label, 
                        'ood_confidence': round(top_score * 100, 2)
                    }
                return {'is_ood': False}
    except Exception as e:
        log.warning("HF API OOD check failed (%s). Falling back to local MobileNetV2...", type(e).__name__)

    # 2. Local Fallback (Lightweight MobileNetV2)
    try:
        global _ood_model
        import tensorflow as tf
        from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
        
        if _ood_model is None:
            log.info("Loading local MobileNetV2 OOD fallback (14MB)...")
            _ood_model = MobileNetV2(weights='imagenet')
            
        img_resized = img.copy().convert('RGB').resize((224, 224))
        arr = preprocess_input(np.array(img_resized, dtype=np.float32))
        tensor = np.expand_dims(arr, 0)
        
        probs = _ood_model.predict(tensor, verbose=0)
        decoded = decode_predictions(probs, top=3)[0]
        
        is_plant = False
        top_label = decoded[0][1].replace('_', ' ')
        top_score = decoded[0][2]
        
        for _, label, prob in decoded:
            label_lower = label.lower().replace('_', ' ')
            if any(kw in label_lower for kw in PLANT_KEYWORDS):
                is_plant = True
                break
                
        if not is_plant:
            return {
                'is_ood': True, 
                'ood_label': top_label.title(), 
                'ood_confidence': round(float(top_score) * 100, 2)
            }
            
        return {'is_ood': False}
        
    except Exception as e:
        log.error("Local OOD fallback failed: %s", e)
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