# gunicorn.conf.py
# This configuration increases the worker timeout so that heavy ML models 
# (like TensorFlow's EfficientNet) don't get killed during their first prediction.

timeout = 120
workers = 1
threads = 2
