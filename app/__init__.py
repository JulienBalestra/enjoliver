import os.path
import sys

APP_PATH = os.path.dirname(os.path.abspath(__file__))
PROJECT_PATH = os.path.dirname(APP_PATH)
sys.path.append(APP_PATH)

for p in os.listdir(os.path.join(PROJECT_PATH, "env/lib/")):
    python_lib = os.path.join(PROJECT_PATH, "env/lib/%s/site-packages" % p)
    sys.path.append(python_lib)
