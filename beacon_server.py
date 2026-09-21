"""
beacon_server.py
-----------------
STEPS 3, 4, 5 of the workflow: MONITOR -> ANALYZE -> ALERT

A lightweight Flask server that listens for tracking-beacon hits fired
by any decoy document created with generate_decoy.py. Every hit is:

  1. Logged to logs/alerts.log (JSONL, one event per line) with
     timestamp, source IP, user-agent, and which decoy fired.
  2. Printed to the console as an immediate alert.
  3. Viewable on a simple dashboard at /dashboard.

This is the "security signal" the slides describe: legitimate users
have no reason to load this invisible image, so any hit is treated as
suspicious interaction with a decoy.

Run:
    python beacon_server.py
Then open http://127.0.0.1:5000/dashboard to view captured alerts.
"""

import json
import os
from datetime import datetime, timezone

from flask import Flask, request, Response, render_template

BASE_DIR = os.path.dirname(__file__)
REGISTRY_PATH = os.path.join(BASE_DIR, "logs", "decoy_registry.json")
ALERTS_PATH = os.path.join(BASE_DIR, "logs", "alerts.log")

# 1x1 transparent GIF served in response to every beacon hit, so the
# request looks like an ordinary image load to whatever opened the decoy.
TRANSPARENT_GIF = bytes.fromhex(
    "47494638396101000100800000000000ffffff21f90401000000002c00000000010001000002024401003b"
)

app = Flask(__name__)


def load_registry():
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH, "r") as f:
            return json.load(f)
    return {}


def log_alert(event: dict):
    os.makedirs(os.path.dirname(ALERTS_PATH), exist_ok=True)
    with open(ALERTS_PATH, "a") as f:
        f.write(json.dumps(event) + "\n")


def load_alerts():
    if not os.path.exists(ALERTS_PATH):
        return []
    with open(ALERTS_PATH, "r") as f:
        return [json.loads(line) for line in f if line.strip()]


@app.route("/track/<token>")
def track(token):
    registry = load_registry()
    decoy_info = registry.get(token, {"title": "UNKNOWN DECOY", "filename": "unknown"})

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "token": token,
        "decoy_title": decoy_info.get("title"),
        "decoy_filename": decoy_info.get("filename"),
        "source_ip": request.headers.get("X-Forwarded-For", request.remote_addr),
        "user_agent": request.headers.get("User-Agent", "unknown"),
        "severity": "HIGH" if token in registry else "MEDIUM",  # unknown token = still suspicious
    }
    log_alert(event)

    print("=" * 60)
    print("[ALERT] Honey document triggered!")
    print(f"  Decoy:     {event['decoy_title']} ({event['decoy_filename']})")
    print(f"  Time:      {event['timestamp']}")
    print(f"  Source IP: {event['source_ip']}")
    print(f"  UA:        {event['user_agent']}")
    print("=" * 60)

    return Response(TRANSPARENT_GIF, mimetype="image/gif")


@app.route("/dashboard")
def dashboard():
    alerts = sorted(load_alerts(), key=lambda a: a["timestamp"], reverse=True)
    return render_template("dashboard.html", alerts=alerts, count=len(alerts))


@app.route("/")
def index():
    return (
        "<h3>Honey Document beacon server is running.</h3>"
        "<p>View captured alerts at <a href='/dashboard'>/dashboard</a>.</p>"
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
