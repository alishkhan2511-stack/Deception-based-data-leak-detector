# Honey Document — Deception-Based Data Leak Detector

A working prototype of the project described in your exhibition slides
(*Honey Document: Deception-Based Data Leak Detector*, VIT Bhopal).

A realistic decoy file is planted where an attacker or unauthorized
insider might find it. Legitimate users have no reason to open it, so
any interaction — a beacon firing, a copy, a move, a deletion — is
treated as a security signal.

## Core loop

```
Decoy → Interaction → Detection → Alert / Evidence → Investigation
```

## Architecture

| Layer | File | Role |
|---|---|---|
| Decoy layer | `generate_decoy.py` | Creates a realistic-looking honey document with a unique, invisible tracking beacon embedded in it |
| Monitoring (network) | `beacon_server.py` | Listens for the beacon firing, the primary "someone opened this" signal |
| Monitoring (filesystem) | `file_monitor.py` | Secondary layer: watches the decoy on disk for copy/move/rename/delete |
| Detection + Alert | built into `beacon_server.py` / `file_monitor.py` | Every hit is logged and immediately printed as an alert |
| Evidence | `logs/alerts.log` | Append-only JSON-lines record: timestamp, source IP, user-agent, decoy, severity |
| Dashboard | `templates/dashboard.html` | Human-readable view of all captured alerts, served at `/dashboard` |

## How the beacon works

1. `generate_decoy.py` creates an HTML file styled like a confidential
   report (e.g. `Confidential_Salary_Report_2026.html`) and generates a
   random 32-character token for it.
2. The token is baked into a 1×1 invisible tracking image inside the
   decoy: `<img src="http://.../track/<token>">`.
3. The token → decoy mapping is saved to `logs/decoy_registry.json`.
4. When the decoy is opened somewhere that renders images (a browser,
   an HTML preview pane, etc.), that image request hits
   `beacon_server.py`, which logs the event and serves a harmless
   transparent GIF back — nothing looks broken to whoever opened it.

This mirrors the classic "canary token" technique used in real
deception/DLP tooling.

## Setup

```bash
pip install -r requirements.txt
```

## Running the demo

**Terminal 1 — start the beacon server:**
```bash
python beacon_server.py
```

**Terminal 2 — create a decoy:**
```bash
python generate_decoy.py "Confidential_Salary_Report_2026"
```

**Terminal 3 (optional) — start the filesystem watcher:**
```bash
python file_monitor.py
```

**Trigger it:** open `decoys/Confidential_Salary_Report_2026.html` in a
browser (or `curl` the printed beacon URL directly to simulate an
attacker). Watch Terminal 1 print an alert, then visit
`http://127.0.0.1:5000/dashboard` to see it logged.

## Matching this back to the slide deck

- **Problem Statement** → traditional controls (auth, permissions,
  malware/network filters) don't catch someone browsing files they
  already have some access to; this adds a deception-based tripwire.
- **System Workflow** (Create → Deploy → Monitor → Analyze → Alert) →
  `generate_decoy.py` (Create), placing the file somewhere discoverable
  (Deploy), `beacon_server.py` + `file_monitor.py` (Monitor), severity
  scoring in the alert event (Analyze), console output + dashboard +
  `alerts.log` (Alert).
- **Limitations** this prototype shares with the real thing: a decoy
  can be recognized if styled unrealistically; a beacon only fires if
  the viewer renders images/HTML; filesystem events alone can't see a
  file copied to a location outside the watched folder.

## Ideas to extend (matches "Future Scope" slide)

- Swap the HTML decoy for a real `.docx`/`.pdf` with an embedded remote
  image or field code, for a more convincing deployment.
- Add a real notification channel (email/Slack webhook) instead of
  console output.
- Feed `alerts.log` into a SIEM or a simple risk-scoring rule engine.
- Deploy multiple decoy "flavors" (finance, HR, source code) across
  different folders/servers with per-decoy severity weighting.
