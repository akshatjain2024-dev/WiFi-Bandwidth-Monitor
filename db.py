import sqlite3
import threading
import time

import config

lock = threading.Lock()


def connect():
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def setup():
    with lock:
        conn = connect()
        conn.execute("""CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time REAL,
            mac TEXT,
            name TEXT,
            usage REAL,
            usage_limit REAL,
            action TEXT,
            detail TEXT)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS usage_log (
            time REAL,
            sim_time TEXT,
            mac TEXT,
            usage REAL)""")
        conn.commit()
        conn.close()


def add_event(mac, name, usage, usage_limit, action, detail=""):
    with lock:
        conn = connect()
        conn.execute("INSERT INTO events (time, mac, name, usage, usage_limit, action, detail) VALUES (?, ?, ?, ?, ?, ?, ?)",
                     (time.time(), mac, name, round(usage, 2), usage_limit, action, detail))
        conn.commit()
        conn.close()


def add_usage(sim_time, readings):
    now = time.time()
    with lock:
        conn = connect()
        conn.executemany("INSERT INTO usage_log VALUES (?, ?, ?, ?)",
                         [(now, sim_time, mac, value) for mac, value in readings.items()])
        conn.commit()
        conn.close()


def get_events(limit=50):
    with lock:
        conn = connect()
        rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        conn.close()
    return [dict(r) for r in rows]


def count_rows():
    with lock:
        conn = connect()
        events = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        samples = conn.execute("SELECT COUNT(*) FROM usage_log").fetchone()[0]
        conn.close()
    return events, samples


def clear_events():
    with lock:
        conn = connect()
        conn.execute("DELETE FROM events")
        conn.commit()
        conn.close()
