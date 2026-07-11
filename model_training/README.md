# Cotton Leaf Disease Detection — Model Training Pipeline

## 📂 Project Structure

```
model_training/
├── config.py        ← ⚙️ ALL settings (edit DATASET_DIR here!)
├── dataset.py       ← Data loading + augmentation
├── model.py         ← EfficientNetV2L + CBAM architecture
├── train.py         ← Two-phase training loop
├── evaluate.py      ← Metrics, plots, Grad-CAM
├── predict.py       ← Single/batch inference
├── utils.py         ← CBAM, GradCAM, plotting helpers
├── requirements.txt ← Dependencies
└── data/
    └── raw/
        ├── SAR-CLD-2024/          ← Extract SAR-CLD-2024.zip here
        ├── severity-levels/       ← Extract Severity Levels.zip here
        ├── cotton-plant-disease/  ← Extract archive(1).zip here
        └── archive-dataset/       ← Extract archive.zip here
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Extract Datasets
Right-click each ZIP → Extract All → choose folder under `data/raw/`.

Each folder must contain **subfolders per class**, e.g.:
```
SAR-CLD-2024/
├── Bacterial_Blight/   ← disease images here
├── Curl_Virus/
├── Fusarium_Wilt/
├── Healthy/
...
```

### 3. Configure Dataset Path
Open `config.py` and set `DATASET_DIR` to your primary dataset:
```python
DATASET_DIR = os.path.join(BASE_DIR, "data", "raw", "SAR-CLD-2024")
```

### 4. Train the Model
```bash
python train.py
```
This runs two phases:
- **Phase 1** (15 epochs): Trains only the classification head
- **Phase 2** (50 epochs): Fine-tunes top 30% of EfficientNetV2L backbone

### 5. Evaluate
```bash
python evaluate.py
```
Generates:
- Confusion matrix → `outputs/plots/confusion_matrix.png`
- ROC-AUC curves  → `outputs/plots/roc_curves.png`
- Grad-CAM maps   → `outputs/plots/gradcam/`
- Classification report → `outputs/plots/classification_report.txt`

### 6. Predict on New Images
```bash
# Single image
python predict.py path/to/leaf.jpg

# Entire folder
python predict.py path/to/folder/
```

---

## 🧠 Model Architecture

| Component         | Detail                              |
|-------------------|-------------------------------------|
| Backbone          | EfficientNetV2L (ImageNet weights)  |
| Attention         | CBAM (Channel + Spatial)            |
| Head              | GAP → Dense(512) → Dense(256) → Softmax |
| Optimizer         | Adam with CosineAnnealing           |
| Loss              | CategoricalCrossEntropy + Label Smoothing (0.1) |
| Target Accuracy   | **>99.9%**                          |

---

## 📊 Dataset Classes (SAR-CLD-2024)

| Class                  | Disease Type       |
|------------------------|--------------------|
| Bacterial_Blight       | Bacterial          |
| Curl_Virus             | Viral              |
| Fusarium_Wilt          | Fungal             |
| Healthy                | —                  |
| Herbicide_Growth_Damage| Environmental      |
| Leaf_Hopper_Jassids    | Pest               |
| Leaf_Reddening         | Nutrient/Stress    |
| Leaf_Variegation       | Viral/Genetic      |

---

## ⚙️ Copy Model to Web App
After training, copy the best model to the web app:
```bash
copy outputs\models\best_model.h5 ..\web_app\model\best_model.h5
```
