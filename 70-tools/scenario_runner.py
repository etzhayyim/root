#!/usr/bin/env python3
"""
Inter-Actor Scenario Runner

Simulates a cross-domain business workflow traversing the Root Router:
1. Payment processed via Stripe API.
2. Heavy Machinery activated via John Deere API.
3. Wholesale funds settled via SWIFT MT network.
"""

import urllib.request
import json
import time

ROUTER_URL = "http://127.0.0.1:8000/api/v1"

def call_router(actor, path, payload):
    url = f"{ROUTER_URL}/{actor}/{path}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        return {"error": str(e)}

def run_scenario():
    print("Waiting for Root Router to initialize...")
    time.sleep(2) # Give uvicorn a moment to bind to the port

    print("\n" + "="*50)
    print("INITIATING CROSS-ACTOR WORKFLOW")
    print("="*50)

    # 1. Fintech: Stripe
    print("\n[Step 1] Triggering Fintech Payment (Stripe)...")
    stripe_res = call_router(
        "stripe-compat",
        "v1/charges",
        {"amount": 500000, "currency": "usd", "description": "Tractor Fleet Lease"}
    )
    print(f"Router Response: {json.dumps(stripe_res, indent=2)}")

    # 2. AgriTech: John Deere
    print("\n[Step 2] Activating Physical Substrate (John Deere)...")
    jd_res = call_router(
        "johndeere_api-compat",
        "substrate/ingest",
        {"signalType": "ACTIVATE_FLEET", "target": "field_7A_iowa"}
    )
    print(f"Router Response: {json.dumps(jd_res, indent=2)}")

    # 3. Deep Financial: SWIFT
    print("\n[Step 3] Settling Wholesale Funds (SWIFT MT)...")
    swift_res = call_router(
        "swift_mt-compat",
        "legacy/transaction",
        {"protocol": "SWIFT_MT103", "amount": 500000, "beneficiary": "DEERE_CORP"}
    )
    print(f"Router Response: {json.dumps(swift_res, indent=2)}")

    print("\n" + "="*50)
    print("WORKFLOW COMPLETE: 3 Distinct Ecosystems Unified.")
    print("="*50)

if __name__ == "__main__":
    run_scenario()
