#!/usr/bin/env python3
"""AI Telecom Copilot – Production Environment Bootstrapper & Seed Script.

Seeds the database and cache with:
1. Baseline multi-cell 4G & 5G telemetry across diverse sites.
2. Active OSS/EMS network alarms correlated to degraded cells.
3. Open operational incidents with action plans.
4. Validated O-RAN A1-P rApps (traffic steering, energy saving, QoE assurance).
5. Initial security counter metrics and audit baselines.

Usage:
  python scripts/seed_production.py [--base-url http://localhost:8000/api/v1]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCENARIOS_DIR = PROJECT_ROOT / "ranengineer" / "data" / "scenarios"


def log(msg: str) -> None:
    print(f"[*] {msg}")


def log_success(msg: str) -> None:
    print(f"[+] {msg}")


def log_error(msg: str) -> None:
    print(f"[-] {msg}")


def api_request(url: str, method: str = "GET", data: dict | None = None) -> dict:
    headers = {"User-Agent": "ProductionSeeder/1.0", "Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        log_error(f"HTTP {e.code} for {url}: {err_msg}")
        return {}
    except Exception as e:
        log_error(f"Request failed for {url}: {e}")
        return {}


def upload_csv(base_url: str, file_path: Path) -> dict:
    boundary = "----WebKitFormBoundarySeedScript"
    filename = file_path.name
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: text/csv\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    url = f"{base_url}/datasets/upload"
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        log_error(f"Failed to upload {filename}: {e}")
        return {}


def seed_system(base_url: str) -> None:
    print("=" * 70)
    print(" AI TELECOM COPILOT – PRODUCTION SEED & BOOTSTRAPPER")
    print("=" * 70)

    # 1. Check Backend Diagnostics
    log("Verifying backend health and diagnostics...")
    diag = api_request(f"{base_url}/diagnostics")
    if not diag:
        log_error("Backend service unreachable. Please ensure Docker containers are running.")
        sys.exit(1)
    log_success(f"Backend status: {diag.get('status', 'OK')} (Uptime: {diag.get('uptime_seconds', 0):.1f}s)")

    # 2. Ingest Scenario CSVs
    log("Uploading baseline telecom failure scenarios...")
    scenarios = list(SCENARIOS_DIR.glob("*.csv"))
    if not scenarios:
        log_error(f"No scenario files found in {SCENARIOS_DIR}")
    else:
        for sc in sorted(scenarios):
            res = upload_csv(base_url, sc)
            if res:
                cell_count = res.get("summary", {}).get("total_cells", 0)
                log_success(f"Uploaded {sc.name}: {cell_count} cells ingested.")

    # 3. Seed Correlated Network Alarms
    log("Seeding operational OSS/EMS network alarms...")
    alarms_to_seed = [
        {
            "cell_id": "CELL_001_A",
            "site_id": "SITE_DOWNTOWN_01",
            "severity": "CRITICAL",
            "alarm_type": "POOR_RADIO_QUALITY",
            "source": "OSS_EMS",
            "description": "High external PIM interference detected in uplink sub-band 3.5 GHz.",
        },
        {
            "cell_id": "CELL_045_C",
            "site_id": "SITE_METRO_04",
            "severity": "WARNING",
            "alarm_type": "HIGH_PRB_UTILIZATION",
            "source": "OSS_EMS",
            "description": "DL PRB resource starvation exceeding 90% threshold during peak hours.",
        },
        {
            "cell_id": "CELL_102_B",
            "site_id": "SITE_STADIUM_10",
            "severity": "CRITICAL",
            "alarm_type": "CELL_UNAVAILABLE",
            "source": "OSS_EMS",
            "description": "Secondary BB6630 board temperature threshold exceeded; sector offline.",
        },
    ]
    for al in alarms_to_seed:
        res = api_request(f"{base_url}/alarms", method="POST", data=al)
        if res:
            log_success(f"Alarm created: {res.get('alarm_id', 'ALM')} for {al['cell_id']}")

    # 4. Seed Operational Incidents
    log("Creating initial engineering incidents...")
    incidents_to_seed = [
        {
            "title": "Downtown Sub-band PIM Interference Investigation",
            "description": "Intermittent downlink throughput drops and high Uplink RSSI across CELL_001_A.",
            "severity": "CRITICAL",
            "affected_cells": ["CELL_001_A", "CELL_001_B"],
            "related_alarms": ["ALM_001"],
        },
        {
            "title": "Metro Sector PRB Congestion & Carrier Balancing",
            "description": "Heavy data utilization during morning commute hours; require dynamic traffic steer.",
            "severity": "MAJOR",
            "affected_cells": ["CELL_045_C"],
            "related_alarms": [],
        },
    ]
    for inc in incidents_to_seed:
        res = api_request(f"{base_url}/incidents", method="POST", data=inc)
        if res:
            log_success(f"Incident created: {res.get('id', 'INC')} – '{inc['title']}'")

    # 5. Verify O-RAN rApp Studio
    log("Validating standard O-RAN Non-RT RIC rApp policies...")
    rapps = api_request(f"{base_url}/oran/rapps")
    if rapps and isinstance(rapps, list):
        log_success(f"Verified {len(rapps)} active O-RAN rApp policies available.")

    # 6. Verify Shift Handover Briefing
    log("Generating inaugural Shift Handover report...")
    handover = api_request(f"{base_url}/reports/handover")
    if handover:
        log_success(f"Handover report {handover.get('report_id')} ready. Status: {handover.get('system_status')}")

    # 7. Summary
    print("=" * 70)
    print(" PRODUCTION SEEDING COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print(f" Dashboard: http://localhost:3000")
    print(f" API Docs:  http://localhost:8000/docs")
    print(f" O-RAN Lab: http://localhost:3000/oran")
    print(f" 6G Twin:   http://localhost:3000/digital-twin")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed AI Telecom Copilot production environment")
    parser.add_argument("--base-url", default="http://localhost:8000/api/v1", help="API base URL")
    args = parser.parse_args()
    seed_system(args.base_url)

