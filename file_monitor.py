"""
file_monitor.py
-----------------
STEP 3 of the workflow (secondary layer): MONITOR

Complements the HTML tracking beacon by watching the decoys/ folder
directly on disk. This catches interactions the beacon can't see, e.g.
a decoy being copied, moved, renamed, or deleted outright — actions a
legitimate process should basically never take on this folder.

Note: reliable "file opened for reading" events depend on the OS
(inotify on Linux exposes IN_OPEN/IN_ACCESS; Windows/macOS do not
expose this as cleanly). This script uses `watchdog`, which is
cross-platform for modify/move/delete/create events, and documents
where OS-specific extensions would be needed for full read-access
detection.

Run:
    python file_monitor.py
"""

import json
import os
import time
from datetime import datetime, timezone

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

BASE_DIR = os.path.dirname(__file__)
DECOY_DIR = os.path.join(BASE_DIR, "decoys")
ALERTS_PATH = os.path.join(BASE_DIR, "logs", "alerts.log")


def log_alert(event: dict):
    os.makedirs(os.path.dirname(ALERTS_PATH), exist_ok=True)
    with open(ALERTS_PATH, "a") as f:
        f.write(json.dumps(event) + "\n")


class DecoyWatcher(FileSystemEventHandler):
    def _alert(self, action: str, path: str, severity: str = "HIGH"):
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decoy_title": os.path.basename(path),
            "decoy_filename": os.path.basename(path),
            "source_ip": "local-filesystem",
            "user_agent": f"file_monitor:{action}",
            "severity": severity,
        }
        log_alert(event)
        print("=" * 60)
        print(f"[ALERT] Filesystem event on decoy: {action.upper()}")
        print(f"  Path: {path}")
        print(f"  Time: {event['timestamp']}")
        print("=" * 60)

    def on_modified(self, event):
        if not event.is_directory:
            self._alert("modified", event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._alert(f"moved to {event.dest_path}", event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self._alert("deleted", event.src_path, severity="HIGH")

    def on_created(self, event):
        # Fires if a decoy is copied INTO this folder from elsewhere;
        # copies made TO another folder aren't visible from here.
        if not event.is_directory:
            self._alert("created/copied-in", event.src_path, severity="MEDIUM")


if __name__ == "__main__":
    os.makedirs(DECOY_DIR, exist_ok=True)
    handler = DecoyWatcher()
    observer = Observer()
    observer.schedule(handler, DECOY_DIR, recursive=False)
    observer.start()
    print(f"[*] Watching {DECOY_DIR} for suspicious file activity... (Ctrl+C to stop)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
