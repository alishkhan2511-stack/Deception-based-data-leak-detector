"""
generate_decoy.py
------------------
STEP 1 of the workflow: CREATE

Generates a realistic-looking "honey document" (a decoy file) and embeds
a unique tracking beacon inside it. When the beacon fires (the decoy is
opened in something that renders HTML/images, e.g. a browser or an
HTML-rendering preview), it silently calls home to beacon_server.py.

Each decoy gets a random, unguessable token so we can tell WHICH decoy
was touched and WHEN, without the token appearing "suspicious" to
whoever opens it.

Usage:
    python generate_decoy.py "Confidential_Salary_Report_2026"
"""

import json
import os
import secrets
import sys
from datetime import datetime, timezone

DECOY_DIR = os.path.join(os.path.dirname(__file__), "decoys")
REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "logs", "decoy_registry.json")
BEACON_HOST = "http://127.0.0.1:5000"  # change to your beacon_server's real address when deployed


def load_registry():
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH, "r") as f:
            return json.load(f)
    return {}


def save_registry(registry):
    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)


def make_decoy(title: str) -> str:
    token = secrets.token_hex(16)  # 32-char unguessable token
    filename = f"{title}.html"
    filepath = os.path.join(DECOY_DIR, filename)

    # The decoy looks like a plausible confidential report. A 1x1
    # invisible tracking image points at the beacon server with this
    # decoy's unique token baked into the URL path.
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title.replace('_', ' ')}</title>
<style>
  body {{ font-family: Georgia, serif; max-width: 700px; margin: 60px auto; color: #222; }}
  h1 {{ border-bottom: 2px solid #333; padding-bottom: 8px; }}
  .stamp {{ color: #b00; font-weight: bold; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
  td, th {{ border: 1px solid #999; padding: 8px; text-align: left; }}
</style>
</head>
<body>
  <p class="stamp">CONFIDENTIAL — INTERNAL USE ONLY</p>
  <h1>{title.replace('_', ' ')}</h1>
  <p>This document contains sensitive information intended solely for
  authorized personnel. Unauthorized access, duplication, or
  distribution is strictly prohibited and may be subject to
  disciplinary or legal action.</p>

  <table>
    <tr><th>Field</th><th>Value</th></tr>
    <tr><td>Document ID</td><td>{token[:8].upper()}</td></tr>
    <tr><td>Classification</td><td>Restricted</td></tr>
    <tr><td>Last Reviewed</td><td>{datetime.now(timezone.utc).strftime('%Y-%m-%d')}</td></tr>
  </table>

  <p>(Body content intentionally omitted in this decoy version.)</p>

  <!-- Tracking beacon: invisible 1x1 image. Any client that renders
       this HTML and loads images will silently notify the beacon
       server, which logs it as a suspicious interaction. -->
  <img src="{BEACON_HOST}/track/{token}" width="1" height="1" style="display:none" alt="">
</body>
</html>
"""

    os.makedirs(DECOY_DIR, exist_ok=True)
    with open(filepath, "w") as f:
        f.write(html)

    registry = load_registry()
    registry[token] = {
        "filename": filename,
        "path": filepath,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "title": title,
    }
    save_registry(registry)

    print(f"[+] Decoy created: {filepath}")
    print(f"[+] Token:         {token}")
    print(f"[+] Registered in: {REGISTRY_PATH}")
    return filepath


if __name__ == "__main__":
    title = sys.argv[1] if len(sys.argv) > 1 else "Confidential_Document"
    make_decoy(title)
