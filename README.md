# Auto-Throttling Wi-Fi Bandwidth Alert System

Computer Networks project, VIT Vellore

Akshat Jain (24BCE0380), Vidit Basant Kumar (24BCE0388)

Reads the bandwidth of every device on a Wi-Fi network once a second. If a device stays above its limit for 3 readings in a row, it sends a Telegram alert and limits that device to 5 Mbps with a Linux tc (HTB) rule for 60 seconds. Every event is saved in SQLite and shown on a Flask dashboard.

## How to run

Windows: double click `run.bat`, then open http://127.0.0.1:5050

Linux: `./run.sh` for simulation or `./run.sh live` for real traffic (needs root, uses Scapy and tc)

## Files

| File | What it does |
|---|---|
| config.py | All settings |
| dataset.py | Makes the 24-hour traffic dataset |
| monitor.py | Reads usage per device (dataset or real packets) |
| engine.py | 3-strike check, breach, release |
| throttler.py | tc HTB commands |
| alerts.py | Telegram alerts |
| db.py | SQLite events and usage log |
| app.py | Flask server and API |
| templates/, static/ | Dashboard page |
| tests/ | 11 unit tests |

## Dataset

`dataset.py` makes `data/traffic_dataset.csv`, which has one day of traffic (1440 minutes) for 18 devices, 25,920 rows in total.
In simulation mode 1 second = 1 minute of network time, starting at 18:00.

Every reading is also saved to the `usage_log` table in `bandwidth.db`.

## Rules

- Limit per device: 25 Mbps (can be changed on the page)
- 3 checks in a row over the limit = breach
- On breach: alert is sent and speed is cut to 5 Mbps using tc
- Released after 60 seconds or by pressing Release

## Telegram

Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID before running to get alerts on Telegram.

## Tests

`python -m unittest discover tests`
