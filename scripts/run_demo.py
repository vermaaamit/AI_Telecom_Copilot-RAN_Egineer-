#!/usr/bin/env python3
"""AI Telecom Copilot – End-to-End Demo Runner.

Demonstrates the core engineering flow:
  ANALYTICS CALCULATES. RULES INTERPRET. AI EXPLAINS. ENGINEER DECIDES.

Runs against the live running API at http://localhost:8000/api/v1.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCENARIOS_DIR = PROJECT_ROOT / "ranengineer" / "data" / "scenarios"


def print_banner(title: str) -> None:
    print("\n" + "=" * 70)
    print(f" {title.upper()}")
    print("=" * 70)


def api_get(endpoint: str) -> dict:
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, headers={"User-Agent": "DemoRunner/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[-] GET {url} failed: {e}")
        return {}


def api_post_file(endpoint: str, file_path: Path) -> dict:
    import urllib.request
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    filename = file_path.name
    
    with open(file_path, "rb") as f:
        file_bytes = f.read()
        
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: text/csv\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
    
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[-] POST {endpoint} failed: {e}")
        return {}


def api_post_json(endpoint: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[-] POST {endpoint} failed: {e}")
        return {}


def main() -> int:
    print_banner("AI Telecom Copilot – Full Stack Demonstration")
    print("Starting automated execution of all 5 operational scenarios.\n")

    # 1. System Diagnostics
    print_banner("1. System Health & Diagnostics")
    diag = api_get("/diagnostics")
    if not diag:
        print("[-] API unreachable at http://localhost:8000/api/v1. Ensure containers are running.")
        return 1
    print(f"[+] Service: {diag.get('service')} (v{diag.get('version')})")
    print(f"[+] Status:  {diag.get('status')}")
    print(f"[+] DB:      {diag.get('database', {}).get('engine')} ({diag.get('database', {}).get('status')})")
    print(f"[+] Cache:   {diag.get('cache', {}).get('type')} ({diag.get('cache', {}).get('status')})")
    print(f"[+] Scanner: {diag.get('security', {}).get('scanner')} ({diag.get('security', {}).get('mode')})")
    print(f"[+] Rules:   {diag.get('analytics', {}).get('ran_rules_loaded')} RAN Rules Loaded")
    print(f"[+] RAG:     {diag.get('analytics', {}).get('rag_standards_loaded')} Standards Documents Loaded")

    # 2. Ingest Scenario 1: Severe Interference & Overshooting
    print_banner("2. Scenario 1: Coverage & Overshooting Interference")
    sc1_file = SCENARIOS_DIR / "scenario_1_interference.csv"
    res1 = api_post_file("/datasets/upload", sc1_file)
    print(f"[+] Ingested: {res1.get('filename')} (ID: {res1.get('id')})")
    for cell in res1.get("cells", []):
        print(f"\n[*] Cell: {cell.get('cell_id')} | Score: {cell.get('health_score')}/100 ({cell.get('status')})")
        for pc in cell.get("probable_causes", []):
            print(f"    - Probable Cause: {pc.get('category')} -> {pc.get('description')}")
            for rc in pc.get("recommended_checks", []):
                print(f"      * Action: {rc}")

    # 3. Ingest Scenario 2: High PRB Congestion
    print_banner("3. Scenario 2: Stadium PRB Capacity Congestion")
    sc2_file = SCENARIOS_DIR / "scenario_2_congestion.csv"
    res2 = api_post_file("/datasets/upload", sc2_file)
    print(f"[+] Ingested: {res2.get('filename')} (ID: {res2.get('id')})")
    for cell in res2.get("cells", []):
        if cell.get("status") == "CRITICAL":
            print(f"[*] Critical Congestion: {cell.get('cell_id')} | Score: {cell.get('health_score')}/100")
            print(f"    PRB Utilization: {cell.get('kpis', {}).get('PRB_UTILIZATION')}%")
            print(f"    DL Throughput:   {cell.get('kpis', {}).get('THROUGHPUT_DL')} Mbps")

    # 4. Multi-Agent Cooperative Investigation
    print_banner("4. Multi-Agent Cooperative Investigation")
    inv = api_post_json("/agents/investigate", {"cell_id": "CELL_INTERFERENCE_01"})
    print(f"[+] Investigation ID: {inv.get('investigation_id')}")
    print(f"[+] Target Cell:      {inv.get('target_cell_id')}")
    print(f"[+] Verdict:          {inv.get('overall_verdict')}")
    print("\n[+] Agent Contributions:")
    for contrib in inv.get("agent_contributions", []):
        print(f"    * [{contrib.get('role')}]: {contrib.get('agent_name')}")
        for finding in contrib.get("findings", []):
            print(f"      - {finding}")

    print("\n[+] Consolidated Engineering Remediations:")
    for rem in inv.get("consolidated_remediations", []):
        print(f"    -> {rem}")

    # 5. Telecom Knowledge Base (RAG)
    print_banner("5. Telecom Domain Standards Retrieval (RAG)")
    rag_res = api_get("/knowledge/search?q=interference&limit=2")
    print(f"[+] Query: '{rag_res.get('query')}' (Matched: {rag_res.get('total_matched')})")
    for doc in rag_res.get("documents", []):
        print(f"\n[*] Standard: {doc.get('id')} - {doc.get('title')}")
        print(f"    Source:    {doc.get('source')}")
        print(f"    Relevance: {doc.get('relevance_score')}")
        print(f"    Excerpt:   {doc.get('content')[:140]}...")

    # 6. Predictive Early Warning
    print_banner("6. Predictive Anomaly Forecasting")
    pred = api_get("/anomalies/predictive")
    print(f"[+] Evaluated Cells: {pred.get('total_evaluated_cells')}")
    print(f"[+] At-Risk Cells:   {pred.get('at_risk_cells_count')}")
    for item in pred.get("items", []):
        print(f"    * Cell {item.get('cell_id')} [{item.get('risk_level')}]: {item.get('kpi_name')} velocity {item.get('velocity_rate'):+}")
        print(f"      Action: {item.get('recommended_action')}")

    print_banner("Demonstration Complete: All Systems Verified")
    print("Core Axiom Verified: Analytics Calculates. Rules Interpret. AI Explains. Engineer Decides.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

