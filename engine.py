import threading
import time

import config
import db
from alerts import send_alert


class Checker:
    def __init__(self, monitor, throttler):
        self.monitor = monitor
        self.throttler = throttler
        self.limits = {}
        self.strikes = {}
        self.throttled_at = {}
        self.latest = {}
        self.history = {}
        self.times = []
        self.lock = threading.Lock()

    def device(self, mac):
        for d in self.monitor.devices:
            if d["mac"] == mac:
                return d
        return None

    def get_limit(self, mac):
        return self.limits.get(mac, config.DEFAULT_LIMIT)

    def step(self):
        sim_time = self.monitor.sim_time()
        readings = self.monitor.read(self.throttler.caps)
        with self.lock:
            self.latest = readings
            self.times.append(sim_time)
            self.times = self.times[-60:]
            for mac, value in readings.items():
                self.history.setdefault(mac, []).append(value)
                self.history[mac] = self.history[mac][-60:]
        db.add_usage(sim_time, readings)
        for mac, value in readings.items():
            self.check(mac, value)
        return readings

    def check(self, mac, value):
        d = self.device(mac)
        limit = self.get_limit(mac)
        if mac in self.throttled_at:
            if time.time() - self.throttled_at[mac] >= config.RELEASE_AFTER:
                self.release(mac, auto=True)
            return
        if value > limit:
            self.strikes[mac] = self.strikes.get(mac, 0) + 1
        else:
            self.strikes[mac] = 0
        if self.strikes[mac] >= config.STRIKES_NEEDED:
            self.throttle(d, value, limit)

    def throttle(self, d, value, limit, manual=False):
        mac = d["mac"]
        self.throttler.limit(mac, d["ip"], config.THROTTLE_SPEED)
        self.throttled_at[mac] = time.time()
        self.strikes[mac] = 0
        if manual:
            db.add_event(mac, d["name"], value, limit, "MANUAL_THROTTLE", "limited from dashboard")
            return
        msg = "Alert: %s (%s) is using %.1f Mbps, limit is %d Mbps. Speed cut to %d Mbps." % (
            d["name"], mac, value, limit, config.THROTTLE_SPEED)
        channel = send_alert(msg)
        db.add_event(mac, d["name"], value, limit, "BREACH", "over limit for %d checks" % config.STRIKES_NEEDED)
        db.add_event(mac, d["name"], value, limit, "ALERT", "sent to " + channel)
        db.add_event(mac, d["name"], value, limit, "THROTTLE", "speed set to %d Mbps" % config.THROTTLE_SPEED)

    def throttle_now(self, mac):
        d = self.device(mac)
        if d and mac not in self.throttled_at:
            self.throttle(d, self.latest.get(mac, 0), self.get_limit(mac), manual=True)

    def release(self, mac, auto=False):
        d = self.device(mac)
        if not d:
            return
        self.throttler.release(mac, d["ip"])
        self.throttled_at.pop(mac, None)
        self.strikes[mac] = 0
        if auto:
            db.add_event(mac, d["name"], self.latest.get(mac, 0), self.get_limit(mac), "AUTO_RELEASE", "released after %d s" % config.RELEASE_AFTER)
        else:
            db.add_event(mac, d["name"], self.latest.get(mac, 0), self.get_limit(mac), "RELEASE", "released from dashboard")

    def set_limit(self, mac, value):
        d = self.device(mac)
        if d:
            self.limits[mac] = value
            db.add_event(mac, d["name"], self.latest.get(mac, 0), value, "LIMIT_CHANGED", "new limit %d Mbps" % value)

    def status(self):
        now = time.time()
        rows = []
        with self.lock:
            for d in self.monitor.devices:
                mac = d["mac"]
                left = 0
                if mac in self.throttled_at:
                    left = int(config.RELEASE_AFTER - (now - self.throttled_at[mac]))
                rows.append({
                    "mac": mac, "ip": d["ip"], "name": d["name"], "type": d["type"],
                    "usage": self.latest.get(mac, 0),
                    "limit": self.get_limit(mac),
                    "throttled": mac in self.throttled_at,
                    "release_in": max(left, 0),
                    "strikes": self.strikes.get(mac, 0),
                    "history": list(self.history.get(mac, [])),
                })
            times = list(self.times)
        return rows, times

    def loop(self):
        while True:
            try:
                self.step()
            except Exception as e:
                print("error:", e)
            time.sleep(config.POLL_INTERVAL)

    def start(self):
        threading.Thread(target=self.loop, daemon=True).start()
