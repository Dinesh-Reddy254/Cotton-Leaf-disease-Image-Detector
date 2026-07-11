"""
evaluate.py — Full evaluation: classification report, confusion matrix, ROC-AUC, Grad-CAM.
Run AFTER training: python evaluate.py
"""

import os
import sys
import numpy as np
import tensorflow as tf
from tqdm import tqdm

from config import (
    BEST_MODEL_PATH, FINAL_MODEL_H5, PLOTS_DIR,
    CLASS_NAMES, NUM_CLASSES, IMG_SIZE, SEED
)
from dataset import prepare_datasets
from utils import (
    plot_confusion_matrix, plot_roc_curves,
    print_classification_report, save_gradcam
)

os.makedirs(PLOTS_DIR, exist_ok=True)
tf.random.set_seed(SEED)


def load_best_model():
    """Load the best saved model."""
    if os.path.exists(BEST_MODEL_PATH):
        path = BEST_MODEL_PATH
    elif os.path.exists(FINAL_MODEL_H5):
        path = FINAL_MODEL_H5
    else:
        print("[Evaluate] ❌ No saved model found. Run train.py first.")
        sys.exit(1)
    print(f"[Evaluate] Loading model from: {path}")
    model = tf.keras.models.load_model(path)
    return model


def get_true_and_pred(model, dataset):
    """Run inference on entire dataset, return true labels and predictions."""
    y_true, y_pred_proba = [], []
    print("[Evaluate] Running inference on test set...")
    for images, labels in tqdm(dataset):
        preds = model.predict(images, verbose=0)
        y_pred_proba.append(preds)
        y_true.append(labels.numpy())
    y_true       = np.concatenate(y_true)
    y_pred_proba = np.concatenate(y_pred_proba)
    y_pred       = np.argmax(y_pred_proba, axis=1)
    return y_true, y_pred, y_pred_proba


def find_last_conv_layer(model):
    """Find the last Conv2D layer name for Grad-CAM."""
    for layer in reversed(model.layers):
        if isinstance(layer, tf.keras.layers.Conv2D):
            return layer.name
    return None


def run_gradcam_samples(model, dataset, last_conv, n_samples=8):
    """Generate Grad-CAM for a few sample images from each class."""
    gradcam_dir = os.path.join(PLOTS_DIR, "gradcam")
    os.makedirs(gradcam_dir, exist_ok=True)

    if last_conv is None:
        print("[GradCAM] No Conv2D layer found — skipping.")
        return

    print(f"[GradCAM] Generating heatmaps using layer: {last_conv}")
    count = 0
    for images, labels in dataset:
        for i in range(len(images)):
            if count >= n_samples:
                break
            img_tensor = tf.expand_dims(images[i], 0)
            true_label = CLASS_NAMES[int(labels[i])]
            pred_proba = model.predict(img_tensor, verbose=0)
            pred_label = CLASS_NAMES[int(np.argmax(pred_proba))]
            confidence = float(np.max(pred_proba)) * 100

            # Save Grad-CAM overlay
            import cv2

            img_np = (images[i].numpy() * 255).astype(np.uint8)

            save_path = os.path.join(
            gradcam_dir,
            f"{count:02d}_true-{true_label}_pred-{pred_label}_{confidence:.1f}pct.png"
            )

            save_gradcam(img_np, model, last_conv, save_path)
            #os.unlink(tmp.name)
            count += 1
        if count >= n_samples:
            break
    print(f"[GradCAM] ✅ Saved {count} heatmaps to {gradcam_dir}")


def main():
    print("\n" + "="*60)
    print("  COTTON LEAF DISEASE DETECTION — EVALUATION")
    print("="*60 + "\n")

    # Load model and data
    model = load_best_model()
    _, _, test_ds, _ = prepare_datasets()

    # Get predictions
    y_true, y_pred, y_pred_proba = get_true_and_pred(model, test_ds)

    # Classification report
    report = print_classification_report(y_true, y_pred)
    report_path = os.path.join(PLOTS_DIR, "classification_report.txt")
    with open(report_path, "w") as f:
        f.write(report)
    print(f"[Evaluate] Report saved → {report_path}")

    # Confusion matrix
    plot_confusion_matrix(y_true, y_pred)

    # ROC-AUC curves
    plot_roc_curves(y_true, y_pred_proba)

    # Grad-CAM heatmaps
    last_conv = "top_conv"
    run_gradcam_samples(model, test_ds, last_conv, n_samples=10)

    # Summary
    acc = np.mean(y_true == y_pred) * 100
    print(f"\n✅ Overall Test Accuracy: {acc:.4f}%")
    print(f"📁 All plots saved to: {PLOTS_DIR}\n")


if __name__ == "__main__":
    main()
