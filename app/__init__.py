import os
import sys

APP_PATH = os.path.dirname(os.path.abspath(__file__))
PROJECT_PATH = os.path.dirname(APP_PATH)
SITE_PACKAGES_PATH = os.path.join(PROJECT_PATH, "env/lib/python3.5/site-packages/")

sys.path.append(SITE_PACKAGES_PATH)
sys.path.append(APP_PATH)
