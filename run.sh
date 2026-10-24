#!/bin/bash
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt
if [ ! -f data/traffic_dataset.csv ]; then
  python dataset.py
fi
if [ "$1" == "live" ]; then
  pip install -q scapy
  sudo -E env PATH="$PATH" WIFI_MODE=live python app.py
else
  WIFI_MODE=simulation python app.py
fi
