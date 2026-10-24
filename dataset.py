import csv
import math
import os
import random

import config

DEVICES = [
    ("A4:83:E7:12:9C:01", "192.168.1.11", "Akshat-Laptop", "laptop"),
    ("3C:22:FB:45:10:02", "192.168.1.12", "Vidit-Phone", "phone"),
    ("F0:18:98:7A:22:03", "192.168.1.13", "Living-Room-TV", "tv"),
    ("B8:27:EB:33:6D:04", "192.168.1.14", "Gaming-PC", "desktop"),
    ("DC:A6:32:5E:81:05", "192.168.1.15", "Smart-Speaker", "iot"),
    ("00:1A:11:F4:B7:06", "192.168.1.16", "Guest-Tablet", "tablet"),
    ("8C:85:90:1D:44:07", "192.168.1.17", "Mom-Phone", "phone"),
    ("70:3A:CB:66:2E:08", "192.168.1.18", "Dad-Laptop", "laptop"),
    ("E4:5F:01:A9:13:09", "192.168.1.19", "Bedroom-TV", "tv"),
    ("50:C7:BF:0B:72:10", "192.168.1.20", "Office-Printer", "printer"),
    ("2C:F0:5D:88:39:11", "192.168.1.21", "Door-Camera", "camera"),
    ("44:65:0D:C2:5A:12", "192.168.1.22", "PS5", "console"),
    ("98:DA:C4:17:6B:13", "192.168.1.23", "Sister-Phone", "phone"),
    ("CC:50:E3:4F:90:14", "192.168.1.24", "Smart-Bulb-Hall", "iot"),
    ("D8:3A:DD:21:08:15", "192.168.1.25", "Study-Desktop", "desktop"),
    ("60:AB:67:E0:5C:16", "192.168.1.26", "Kindle", "tablet"),
    ("1C:91:80:73:B4:17", "192.168.1.27", "Guest-Phone", "phone"),
    ("A0:B7:65:3C:D1:18", "192.168.1.28", "Garage-Camera", "camera"),
]


def hour_curve(minute, peak_hour, width):
    hour = minute / 60
    diff = min(abs(hour - peak_hour), 24 - abs(hour - peak_hour))
    return math.exp(-(diff ** 2) / (2 * width ** 2))


def normal_usage(kind, minute):
    if kind == "laptop":
        return 1 + 7 * hour_curve(minute, 14, 3) + 5 * hour_curve(minute, 21, 2)
    if kind == "phone":
        return 0.5 + 3 * hour_curve(minute, 13, 4) + 4 * hour_curve(minute, 22, 2)
    if kind == "tv":
        return 0.3 + 16 * hour_curve(minute, 21, 1.5)
    if kind == "desktop":
        return 0.8 + 6 * hour_curve(minute, 20, 2.5)
    if kind == "console":
        return 0.2 + 9 * hour_curve(minute, 22, 1.5)
    if kind == "tablet":
        return 0.3 + 4 * hour_curve(minute, 17, 3)
    if kind == "camera":
        return 2.2
    if kind == "printer":
        return 0.05
    return 0.3


def make_sessions(rng, kind):
    if kind in ("iot", "printer", "camera"):
        return []
    count = {"desktop": 3, "console": 3, "tv": 2, "laptop": 2}.get(kind, 1)
    sessions = []
    for _ in range(rng.randint(0, count)):
        start = rng.randint(0, 1439)
        length = rng.randint(8, 40)
        level = rng.uniform(30, 70)
        sessions.append((start, start + length, level))
    return sessions


def generate(path=None, seed=42):
    path = path or config.DATASET_FILE
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rng = random.Random(seed)
    rows = 0
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["minute", "time", "mac", "ip", "name", "type", "mbps", "heavy"])
        for mac, ip, name, kind in DEVICES:
            sessions = make_sessions(rng, kind)
            for minute in range(1440):
                value = normal_usage(kind, minute) * rng.uniform(0.75, 1.25)
                heavy = 0
                for start, end, level in sessions:
                    if start <= minute < end:
                        value = level * rng.uniform(0.85, 1.15)
                        heavy = 1
                time_text = "%02d:%02d" % (minute // 60, minute % 60)
                writer.writerow([minute, time_text, mac, ip, name, kind, round(value, 2), heavy])
                rows += 1
    return rows


if __name__ == "__main__":
    total = generate()
    print("wrote", total, "rows to", config.DATASET_FILE)
