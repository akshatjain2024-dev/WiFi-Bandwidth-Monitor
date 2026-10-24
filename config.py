import os

MODE = os.environ.get("WIFI_MODE", "simulation")
INTERFACE = os.environ.get("WIFI_INTERFACE", "wlan0")
SUBNET = os.environ.get("WIFI_SUBNET", "192.168.1.0/24")

POLL_INTERVAL = 1
DEFAULT_LIMIT = 25
THROTTLE_SPEED = 5
STRIKES_NEEDED = 3
RELEASE_AFTER = 60
START_MINUTE = 18 * 60

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.environ.get("DB_FILE", os.path.join(BASE_DIR, "bandwidth.db"))
DATASET_FILE = os.path.join(BASE_DIR, "data", "traffic_dataset.csv")
