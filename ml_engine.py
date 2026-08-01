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


def patch_keras_module_paths():
    """
    Patch sys.modules to handle Keras internal module name migrations
    (e.g., 'keras.src.models.functional' -> 'keras.src.models.functional_model' or 'keras.Model')
    """
    import sys
    import types
    try:
        import keras
        # 1. Alias 'keras.src.models.functional'
        if "keras.src.models.functional" not in sys.modules:
            try:
                from keras.src.models import functional_model
                sys.modules["keras.src.models.functional"] = functional_model
            except (ImportError, ModuleNotFoundError):
                mod = types.ModuleType("keras.src.models.functional")
                mod.Functional = getattr(keras, "Model", None) or getattr(keras.src.models, "Model", None)
                sys.modules["keras.src.models.functional"] = mod

        # 2. Alias 'keras.src.models.functional_model' if missing
        if "keras.src.models.functional_model" not in sys.modules:
            try:
                from keras.src.models import functional
                sys.modules["keras.src.models.functional_model"] = functional
            except (ImportError, ModuleNotFoundError):
                mod = types.ModuleType("keras.src.models.functional_model")
                mod.Functional = getattr(keras, "Model", None)
                sys.modules["keras.src.models.functional_model"] = mod

        # 3. Ensure 'keras.src.engine.functional' legacy compatibility
        if "keras.src.engine.functional" not in sys.modules:
            mod = types.ModuleType("keras.src.engine.functional")
            mod.Functional = getattr(keras, "Model", None)
            sys.modules["keras.src.engine.functional"] = mod

        log.info("⚡ Keras module paths patched successfully for deserialization compatibility")
    except Exception as e:
        log.warning("Keras module path patch warning: %s", e)


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
                    # Attempt download with configured filename, or fallback to basename
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
            import tensorflow as tf
            import keras
            log.info("Loading Keras model using TF %s / Keras %s...", tf.__version__, keras.__version__)

            patch_keras_module_paths()

            from tensorflow.keras.layers import InputLayer, Dense
            class SafeInputLayer(InputLayer):
                def __init__(self, *args, **kwargs):
                    kwargs.pop("optional", None)
                    kwargs.pop("batch_shape", None)
                    super().__init__(*args, **kwargs)

            class SafeDense(Dense):
                def __init__(self, *args, **kwargs):
                    kwargs.pop("quantization_config", None)
                    super().__init__(*args, **kwargs)

            custom_objects = {
                "InputLayer": SafeInputLayer,
                "Dense": SafeDense,
                "Functional": keras.Model,
            }

            # Try loading via tf.keras / keras with custom object scope
            with keras.saving.custom_object_scope(custom_objects):
                try:
                    _model = keras.models.load_model(model_path, compile=False)
                except Exception as e1:
                    log.warning("Keras load_model failed (%s), attempting tf.keras.models.load_model...", e1)
                    _model = tf.keras.models.load_model(model_path, compile=False)

            log.info("✅ Model successfully loaded from %s", model_path)

            # Pre-warm TensorFlow execution graph to eliminate cold-start latency on first request
            try:
                from tensorflow.keras.applications.efficientnet import preprocess_input
                dummy = preprocess_input(np.zeros((1, 224, 224, 3), dtype=np.float32))
                _model.predict(dummy, verbose=0)
                log.info("⚡ TensorFlow execution graph pre-warmed successfully")
            except Exception as w_err:
                log.warning("Model graph warm-up warning: %s", w_err)

        except Exception as exc:
            log.error("❌ Model load failed completely: %s", exc, exc_info=True)
            _model = None

        return _model


def get_model():
    return _model if _model is not None else load_model()


def _check_ood(img: Image.Image) -> dict:
    """
    Memory-efficient OOD check using Hugging Face Inference API (Free Tier).
    Uses 0 local memory instead of loading another heavy Keras model.
    """
    try:
        import requests
        import io
        
        # Convert image to JPEG bytes
        buf = io.BytesIO()
        img.copy().convert('RGB').resize((224, 224)).save(buf, format='JPEG')
        data = buf.getvalue()
        
        # Use ViT ImageNet model on HF free inference API
        API_URL = "https://api-inference.huggingface.co/models/google/vit-base-patch16-224"
        
        # 2 second timeout to ensure max diagnosis time stays < 5 seconds
        response = requests.post(API_URL, data=data, timeout=2)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                top_label = result[0].get('label', '')
                top_score = result[0].get('score', 0.0)
                
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
                
                label_lower = top_label.lower()
                # If the image is not a plant, flag it as OOD
                if not any(kw in label_lower for kw in PLANT_KEYWORDS):
                    # Clean up label (e.g. 'sports car, sport car' -> 'Sports Car')
                    human_label = top_label.split(',')[0].title()
                    return {
                        'is_ood': True, 
                        'ood_label': human_label, 
                        'ood_confidence': round(top_score * 100, 2)
                    }
        else:
            log.warning(f"HF API returned {response.status_code}: {response.text[:100]}")
            
        # If API fails, rate-limited, or it's a plant, let the main model handle it
        return {'is_ood': False}
    except Exception as e:
        log.warning("HF API OOD check failed or timed out: %s", e)
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
