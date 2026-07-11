"""
utils.py — CBAM Attention, Grad-CAM, plotting helpers.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import seaborn as sns
import tensorflow as tf
from tensorflow.keras import layers, Model
from sklearn.metrics import classification_report, confusion_matrix, roc_curve, auc
from sklearn.preprocessing import label_binarize
import cv2
from config import CLASS_NAMES, PLOTS_DIR, NUM_CLASSES

os.makedirs(PLOTS_DIR, exist_ok=True)

# ──────────────────────────────────────────────────────────────────────────────
# CBAM ATTENTION MODULE
# ──────────────────────────────────────────────────────────────────────────────

class ChannelAttention(layers.Layer):
    """Squeeze-and-Excitation style channel attention."""
    def __init__(self, ratio=8, **kwargs):
        super().__init__(**kwargs)
        self.ratio = ratio

    def build(self, input_shape):
        filters = input_shape[-1]
        self.gap = layers.GlobalAveragePooling2D()
        self.gmp = layers.GlobalMaxPooling2D()
        self.reshape = layers.Reshape((1, 1, filters))
        self.dense1 = layers.Dense(max(filters // self.ratio, 1), activation='relu', use_bias=False)
        self.dense2 = layers.Dense(filters, activation='sigmoid', use_bias=False)

    def call(self, x):
        avg = self.reshape(self.gap(x))
        mx  = self.reshape(self.gmp(x))
        avg = self.dense2(self.dense1(avg))
        mx  = self.dense2(self.dense1(mx))
        scale = avg + mx
        return x * scale


class SpatialAttention(layers.Layer):
    """Spatial attention using conv on avg+max pooled features."""
    def __init__(self, kernel_size=7, **kwargs):
        super().__init__(**kwargs)
        self.conv = layers.Conv2D(1, kernel_size, padding='same',
                                  activation='sigmoid', use_bias=False)

    def call(self, x):
        avg = tf.reduce_mean(x, axis=-1, keepdims=True)
        mx  = tf.reduce_max(x,  axis=-1, keepdims=True)
        concat = tf.concat([avg, mx], axis=-1)
        scale  = self.conv(concat)
        return x * scale


class CBAM(layers.Layer):
    """Convolutional Block Attention Module (CBAM)."""
    def __init__(self, ratio=8, kernel_size=7, **kwargs):
        super().__init__(**kwargs)
        self.channel  = ChannelAttention(ratio=ratio)
        self.spatial   = SpatialAttention(kernel_size=kernel_size)

    def call(self, x):
        x = self.channel(x)
        x = self.spatial(x)
        return x


# ──────────────────────────────────────────────────────────────────────────────
# GRAD-CAM
# ──────────────────────────────────────────────────────────────────────────────

def make_gradcam_heatmap(img_array, model, last_conv_layer_name):
    grad_model = tf.keras.models.Model(
        [model.inputs],
        [model.get_layer(last_conv_layer_name).output, model.output]
    )

    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(img_array)
        pred_index = tf.argmax(predictions[0])
        class_channel = predictions[:, pred_index]

    grads = tape.gradient(class_channel, conv_outputs)

    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    conv_outputs = conv_outputs[0]

    heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)

    # Normalize heatmap
    heatmap = tf.maximum(heatmap, 0) / tf.reduce_max(heatmap + 1e-8)
    return heatmap.numpy()


def save_gradcam(image_array, model, last_conv_layer_name, save_path):
    """
    image_array: numpy image (H, W, 3) in range [0,255]
    """

    # Preprocess SAME as training
    img = image_array.astype(np.float32) 
    img_tensor = np.expand_dims(img, axis=0)

    heatmap = make_gradcam_heatmap(img_tensor, model, last_conv_layer_name)

    # Resize heatmap
    heatmap = cv2.resize(heatmap, (image_array.shape[1], image_array.shape[0]))

    # Normalize heatmap safely
    heatmap = np.maximum(heatmap, 0)
    heatmap = heatmap / (np.max(heatmap) + 1e-8)

    # Convert to 0–255
    heatmap = np.uint8(255 * heatmap)

    # Apply colormap
    heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
    

    # Superimpose
    superimposed = cv2.addWeighted(image_array, 0.7, heatmap, 0.3, 0)

    cv2.imwrite(save_path, superimposed)

# ──────────────────────────────────────────────────────────────────────────────
# PLOTTING HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def plot_training_history(history, save_path=None):
    """Plot accuracy and loss curves for both training phases."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Training History", fontsize=16, fontweight='bold')

    axes[0].plot(history.history['accuracy'],     label='Train Acc',  color='#2196F3')
    axes[0].plot(history.history['val_accuracy'], label='Val Acc',    color='#4CAF50', linestyle='--')
    axes[0].set_title('Accuracy'); axes[0].set_xlabel('Epoch'); axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(history.history['loss'],     label='Train Loss', color='#F44336')
    axes[1].plot(history.history['val_loss'], label='Val Loss',   color='#FF9800', linestyle='--')
    axes[1].set_title('Loss'); axes[1].set_xlabel('Epoch'); axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    path = save_path or os.path.join(PLOTS_DIR, "training_history.png")
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[Plot] Training history saved → {path}")


def plot_confusion_matrix(y_true, y_pred, save_path=None):
    """Plot and save confusion matrix heatmap."""
    cm_arr = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(12, 10))
    sns.heatmap(cm_arr, annot=True, fmt='d', cmap='Blues',
                xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES,
                linewidths=0.5)
    plt.title('Confusion Matrix', fontsize=16, fontweight='bold')
    plt.ylabel('True Label'); plt.xlabel('Predicted Label')
    plt.xticks(rotation=45, ha='right'); plt.yticks(rotation=0)
    plt.tight_layout()
    path = save_path or os.path.join(PLOTS_DIR, "confusion_matrix.png")
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[Plot] Confusion matrix saved → {path}")


def plot_roc_curves(y_true, y_pred_proba, save_path=None):
    """Plot per-class ROC-AUC curves."""
    y_true_bin = label_binarize(y_true, classes=list(range(NUM_CLASSES)))
    plt.figure(figsize=(12, 8))
    colors = plt.cm.tab10(np.linspace(0, 1, NUM_CLASSES))

    for i, (cls, color) in enumerate(zip(CLASS_NAMES, colors)):
        fpr, tpr, _ = roc_curve(y_true_bin[:, i], y_pred_proba[:, i])
        roc_auc = auc(fpr, tpr)
        plt.plot(fpr, tpr, color=color, lw=2, label=f'{cls} (AUC = {roc_auc:.3f})')

    plt.plot([0, 1], [0, 1], 'k--', lw=1)
    plt.xlim([0.0, 1.0]); plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate'); plt.ylabel('True Positive Rate')
    plt.title('ROC-AUC Curves per Class', fontsize=16, fontweight='bold')
    plt.legend(loc='lower right', fontsize=9)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    path = save_path or os.path.join(PLOTS_DIR, "roc_curves.png")
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[Plot] ROC curves saved → {path}")


def print_classification_report(y_true, y_pred):
    """Print detailed per-class classification report."""
    report = classification_report(y_true, y_pred, target_names=CLASS_NAMES, digits=4)
    print("\n" + "="*60)
    print("  CLASSIFICATION REPORT")
    print("="*60)
    print(report)
    return report
