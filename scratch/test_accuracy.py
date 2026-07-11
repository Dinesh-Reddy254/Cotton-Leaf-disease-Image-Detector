import os
import sys
import numpy as np
from PIL import Image
import tensorflow as tf

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config import get_config
import ml_engine

def main():
    # Initialize Flask app to set config and engine
    app = create_app()
    app.app_context().push()
    
    model = ml_engine.get_model()
    if model is None:
        print("Error: Could not load model!")
        return

    print("Model loaded successfully!")
    print("Output shape:", model.output_shape)
    
    classes = app.config.get("CLASS_NAMES", [])
    print("Configured Class Names:", classes)

    # Test directories
    test_dirs = {
        "Diseased Cotton Leaf": r"model_training/data/raw/Cotton Disease/test/diseased cotton leaf",
        "Fresh Cotton Leaf": r"model_training/data/raw/Cotton Disease/test/fresh cotton leaf"
    }

    for category, path in test_dirs.items():
        print(f"\nEvaluating Category: {category} (Path: {path})")
        if not os.path.exists(path):
            print(f"Directory {path} does not exist!")
            continue
        
        files = [f for f in os.listdir(path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not files:
            print("No images found in directory.")
            continue
            
        print(f"Found {len(files)} images. Running predictions:")
        for filename in files:
            file_path = os.path.join(path, filename)
            try:
                img = Image.open(file_path)
                result = ml_engine.predict_image(img)
                print(f" - {filename}: Predicted = '{result['disease']}' (Confidence: {result['confidence']:.2f}%)")
                # Also show top 3
                top3_str = ", ".join([f"{name}: {conf:.1f}%" for name, conf in result['top3']])
                print(f"   Top 3: {top3_str}")
            except Exception as e:
                print(f" - {filename}: Failed to predict. Error: {e}")

if __name__ == "__main__":
    main()
