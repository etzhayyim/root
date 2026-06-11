import json
import os
from pathlib import Path

def simulate_murakumo_compute_routing(routing_policy):
    print("\n[Murakumo Compute Router] Intercepting request...")
    requested_vendor = "entity:compute:megacorp_a"

    blocked = [e['id'] for e in routing_policy['blocked_entities']]
    safe = [e['id'] for e in routing_policy['safe_entities'] if e['domain'] == 'compute']

    if requested_vendor in blocked:
        print(f"🚨 ALERT: Request to '{requested_vendor}' is BLOCKED by abaki policy.")
        print(f"   Reason: High Chokepoint Index (Monopolistic behavior).")
        if safe:
            fallback = safe[0]
            print(f"🔄 ROUTE AROUND: Redirecting workload to safe provider: {fallback}")
        else:
            print(f"❌ FATAL: No safe compute providers available. Failing securely.")
    else:
        print("✅ Request permitted.")

def simulate_ossekai_survival_tree(routing_policy):
    print("\n[Ossekai Survival Simulator] Generating survival tree...")
    blocked_domains = set([e['domain'] for e in routing_policy['blocked_entities']])

    print("Survival Branches Activated:")
    if 'biology' in blocked_domains:
        print("🌱 Biology/Agri branch: Dependency on F1 seeds blocked. Activating 'suki' (Local Heirloom Seed Bank) fallback.")
    if 'logistics' in blocked_domains:
        print("🚚 Logistics branch: Centralized logistics blocked. Activating 'wadachi' (Autonomous mesh delivery) fallback.")
    if 'compute' in blocked_domains:
        print("💻 Compute branch: Proprietary API blocked. Activating 'ameno' (WebGPU local inference) fallback.")

    print("Ossekai simulation updated to reflect the new Charter-aligned constraints.")

def main():
    base_dir = Path(__file__).parent.paren
    policy_file = base_dir / "out" / "routing-policy.json"

    if not policy_file.exists():
        print(f"Error: Policy file not found at {policy_file}")
        return

    with open(policy_file, 'r', encoding='utf-8') as f:
        policy = json.load(f)

    print("=== etzhayyim React & Route-Around Execution ===")
    simulate_murakumo_compute_routing(policy)
    simulate_ossekai_survival_tree(policy)
    print("\n================================================")

if __name__ == "__main__":
    main()
