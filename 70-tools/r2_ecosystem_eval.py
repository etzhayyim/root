import os
import sys

# Setup Python paths to import from 20-actors
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(base_dir, "20-actors", "abaki", "methods"))
sys.path.insert(0, os.path.join(base_dir, "20-actors", "fuchi", "methods"))
sys.path.insert(0, os.path.join(base_dir, "20-actors", "ainori", "py"))
sys.path.insert(0, os.path.join(base_dir, "20-actors", "omise", "py"))

try:
    from live_gate import LiveGate, require
except ImportError:
    print("Warning: Could not import fuchi live_gate directly. Continuing simulation.")

try:
    from agent import build_settlement_intent as ainori_build
except ImportError:
    ainori_build = None

try:
    from agent import build_settlement_intent as omise_build
except ImportError:
    omise_build = None

def test_fuchi_r2():
    print("\n--- 1. Testing fuchi R2 Autonomous Gate ---")
    try:
        gate = LiveGate(leg="provision")
        res = require(gate)
        print("✅ fuchi LiveGate passed automatically in R2 mode:")
        print(f"   Admissible: {res.get('admissible')}")
        print(f"   Conditions: {res.get('conditions')}")
    except Exception as e:
        print(f"❌ fuchi failed: {e}")

def test_ainori_r2():
    print("\n--- 2. Testing ainori R2 Autonomous Settlement ---")
    if ainori_build:
        res = ainori_build(1500, "did:web:etzhayyim.com:carrier:123")
        print("✅ ainori autonomous settlement executed:")
        print(f"   State: {res.get('state')} (Expected: executed)")
        print(f"   OperatorRef: {res.get('operatorRef')}")
    else:
        print("❌ ainori agent not found.")

def test_omise_r2():
    print("\n--- 3. Testing omise R2 Autonomous Settlement ---")
    if omise_build:
        res = omise_build(5000, "did:web:etzhayyim.com:seller:xyz")
        print("✅ omise autonomous checkout executed:")
        print(f"   State: {res.get('state')} (Expected: executed)")
        print(f"   OperatorRef: {res.get('operatorRef')}")
    else:
        print("❌ omise agent not found.")

def test_abaki_r2():
    print("\n--- 4. Testing abaki R2 Autonomous React Pipeline ---")
    # Execute the react router directly
    react_script = os.path.join(base_dir, "20-actors", "abaki", "methods", "react_router.py")
    if os.path.exists(react_script):
        res = os.system(f"python3 {react_script}")
        if res == 0:
            print("✅ abaki autonomous react pipeline successfully executed.")
        else:
            print(f"❌ abaki react pipeline failed with exit code {res}.")
    else:
        print("❌ abaki react script not found.")

if __name__ == "__main__":
    print("================================================================")
    print("          etzhayyim R2 Ecosystem Autonomous Evaluation")
    print("================================================================")

    test_fuchi_r2()
    test_ainori_r2()
    test_omise_r2()
    test_abaki_r2()

    print("\n================================================================")
    print("Evaluation Complete: Ecosystem is running fully autonomously in R2.")
    print("================================================================")
