import json
import threading
import time
import urllib.request

import config

sent = []


def telegram_ready():
    return config.TELEGRAM_TOKEN != "" and config.TELEGRAM_CHAT_ID != ""


def post_to_telegram(text):
    url = "https://api.telegram.org/bot%s/sendMessage" % config.TELEGRAM_TOKEN
    body = json.dumps({"chat_id": config.TELEGRAM_CHAT_ID, "text": text}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print("telegram failed:", e)


def send_alert(text):
    channel = "Telegram" if telegram_ready() else "Dashboard only"
    sent.insert(0, {"time": time.time(), "text": text, "channel": channel})
    del sent[20:]
    if telegram_ready():
        threading.Thread(target=post_to_telegram, args=(text,), daemon=True).start()
    return channel
