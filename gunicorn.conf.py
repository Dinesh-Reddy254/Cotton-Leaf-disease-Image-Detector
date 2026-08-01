# gunicorn.conf.py
# Single-worker, 2-threaded configuration to keep TensorFlow memory usage
# under Render's 512MB RAM limit while binding dynamically to Render's PORT.
import os

port = os.environ.get("PORT", "5000")
bind = f"0.0.0.0:{port}"
timeout = 120
workers = 1
threads = 2
keepalive = 5
