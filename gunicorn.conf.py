# gunicorn.conf.py
# Single-worker, multi-threaded configuration to keep TensorFlow memory usage
# under Render's 512MB RAM limit while providing non-blocking request handling.

timeout = 120
workers = 1
threads = 4
keepalive = 5
