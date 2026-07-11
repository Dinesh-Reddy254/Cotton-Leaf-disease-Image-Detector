# Cotton Leaf Disease Image Detector

A Flask-based web app that detects cotton leaf diseases using deep learning (EfficientNetB3) on uploaded leaf images or real-time camera captures.

## What It Does

- Upload a cotton leaf photo or capture one directly using your device camera.
- Analyze the image with a deep learning classification pipeline (EfficientNetB3).
- Detect 7 different cotton leaf conditions (including Bacterial Blight, Curl Virus, and Healthy Leaf).
- Show side-by-side diagnosis results, confidence levels, treatment & prevention recommendations, and class probabilities.

## Key Features

- Web UI for quick image upload, preview, and camera capture.
- Multilingual support (English, Telugu, and Hindi).
- User Dashboard for tracking scan history, health rates, and metrics.
- Admin Panel for user management and system stats.
- Secure API endpoints with CSRF protection, rate limiting, and API key management.

## Sample Output Images

The screenshots below show the app in action from upload to diagnosis results.

<table>
  <tr>
    <td align="center">
      <strong>App Preview</strong><br>
      <img src="image%20(1).png" alt="App preview screenshot" width="220">
    </td>
    <td align="center">
      <strong>Detection Summary</strong><br>
      <img src="image%20(2).png" alt="Detection summary screenshot" width="220">
    </td>
  </tr>
  <tr>
    <td align="center">
      <strong>Detection Comparison</strong><br>
      <img src="image%20(3).png" alt="Detection comparison screenshot" width="220">
    </td>
    <td align="center">
      <strong>Class Lists + Metrics</strong><br>
      <img src="image%20(4).png" alt="Class lists and metrics screenshot" width="220">
    </td>
  </tr>
</table>

## Quick Start (Windows)

### 1) Open terminal in the project folder

```powershell
cd "C:\Users\Admin\OneDrive\Desktop\Projects\cotton-disease-detection"
```

### 2) Create and activate a virtual environment

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

CMD:

```bat
python -m venv .venv
.\.venv\Scripts\activate
```

### 3) Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4) Run the app

Using start script:

```powershell
.\start.bat
```

Or manually:

```powershell
python app.py
```

Open the app in your browser at http://127.0.0.1:5000.

## Usage

1. Register a new user account (or sign in).
2. Upload a cotton leaf image or start the camera to capture one.
3. Click `Analyze Leaf` to see the diagnosis, class probability charts, and treatment recommendations.
4. Download the report or check your past scans in the `Dashboard`.

## Project Structure

- `app.py` - Flask backend application factory and routing.
- `ml_engine.py` - TensorFlow/Keras prediction engine loader and image preprocessor.
- `api.py` - REST API endpoints for predictions, history, and key management.
- `auth.py` - User authentication blueprint (login, registration, lockout).
- `config.py` - App environment configurations (dev, prod, testing).
- `db_models.py` - SQLAlchemy models (User, ScanHistory, APIKey).
- `templates/` - HTML front-end templates (Index, Dashboard, Admin, Errors).
- `static/` - Stylesheets (`style.css`, `dashboard.css`, `auth.css`) and JavaScript logic (`app.js`, `translations.js`).
- `model/` - Deep learning model weights (`final_model.keras`).

## More Setup Details

See `model_training/README.md` for detailed model training and evaluation guides.
