from flask import Flask, jsonify, render_template, request

import alerts
import config
import db
from engine import Checker
from monitor import LiveMonitor, SimulatedMonitor
from throttler import Throttler

app = Flask(__name__)
checker = None


def make_checker():
    if config.MODE == "live":
        return Checker(LiveMonitor(), Throttler(live=True))
    return Checker(SimulatedMonitor(), Throttler(live=False))


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/status")
def status():
    devices, times = checker.status()
    events, samples = db.count_rows()
    return jsonify({
        "mode": config.MODE,
        "sim_time": checker.monitor.sim_time(),
        "devices": devices,
        "times": times,
        "total": round(sum(d["usage"] for d in devices), 1),
        "alerts": alerts.sent[:8],
        "commands": checker.throttler.history[-6:],
        "samples": samples,
        "settings": {
            "limit": config.DEFAULT_LIMIT,
            "speed": config.THROTTLE_SPEED,
            "strikes": config.STRIKES_NEEDED,
            "release": config.RELEASE_AFTER,
        },
    })


@app.route("/api/events")
def events():
    return jsonify(db.get_events(40))


@app.route("/api/spike/<mac>", methods=["POST"])
def spike(mac):
    return jsonify({"ok": checker.monitor.add_spike(mac)})


@app.route("/api/throttle/<mac>", methods=["POST"])
def throttle(mac):
    checker.throttle_now(mac)
    return jsonify({"ok": True})


@app.route("/api/release/<mac>", methods=["POST"])
def release(mac):
    checker.release(mac)
    return jsonify({"ok": True})


@app.route("/api/limit/<mac>", methods=["POST"])
def limit(mac):
    data = request.get_json(silent=True) or {}
    try:
        value = int(float(data.get("limit", config.DEFAULT_LIMIT)))
    except ValueError:
        return jsonify({"ok": False}), 400
    checker.set_limit(mac, max(value, 1))
    return jsonify({"ok": True})


@app.route("/api/clear", methods=["POST"])
def clear():
    db.clear_events()
    return jsonify({"ok": True})


if __name__ == "__main__":
    db.setup()
    checker = make_checker()
    checker.start()
    print("Wi-Fi Bandwidth Monitor started in", config.MODE, "mode")
    print("Devices:", len(checker.monitor.devices))
    print("Open http://127.0.0.1:5050 in your browser")
    app.run(host="127.0.0.1", port=5050)
