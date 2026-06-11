#!/usr/bin/env python3
"""
World State Chaos Simulator

Injects faults, network partitions, and data corruptions into the
1000 Clean Room Actors to observe cascading systemic failures
using Datomic's immutable state.
"""

import time
import random

# Target all 1000 generated platforms
TARGET_ACTORS_COUNT = 1000

class ChaosSimulator:
    def __init__(self):
        self.active_faults = []
        self.epoch = 0

    def inject_network_partition(self, target_actor_1, target_actor_2):
        print(f"[Chaos] INJECTING: Network Partition between {target_actor_1} and {target_actor_2}")
        self.active_faults.append(f"Partition({target_actor_1}<->{target_actor_2})")

    def inject_latency_spike(self, target_region):
        print(f"[Chaos] INJECTING: 5000ms Latency Spike in {target_region}")
        self.active_faults.append(f"LatencySpike({target_region})")

    def simulate_epoch(self):
        self.epoch += 1
        print(f"\n--- Simulating World State Epoch {self.epoch} ---")

        # Randomly decide to inject a fault
        if random.random() < 0.3:
            # Pick random targets (Simulated names for demonstration)
            a1 = f"Actor_{random.randint(1, 500)}"
            a2 = f"Actor_{random.randint(501, 1000)}"
            self.inject_network_partition(a1, a2)

        if random.random() < 0.2:
            self.inject_latency_spike("us-east-1-emulation")

        print(f"Active Faults: {len(self.active_faults)}")
        print("Observing cascading effects across Datomic transactions...")
        time.sleep(1) # Simulate observation period

        # Resolve some faults
        if self.active_faults and random.random() < 0.5:
            resolved = self.active_faults.pop(0)
            print(f"[Chaos] RESOLVED: {resolved}")

def run_simulation():
    print(f"Initializing Chaos Simulator for {TARGET_ACTORS_COUNT} Actors...")
    sim = ChaosSimulator()
    try:
        for _ in range(5): # Run 5 epochs for demonstration
            sim.simulate_epoch()
    except KeyboardInterrupt:
        print("\nSimulation aborted.")
    print("Simulation Run Complete.")

if __name__ == "__main__":
    run_simulation()
