"""shinka_engine — the Shinka self-evolution engine (ADR-2606142200).

Loop A (capability evolution): ShinkaEvolutionCell — the co-scientist
generate→debate→evolve→synthesize super-step graph.
Loop B (weight evolution): maxwell_rsi — Robin's hypothesis→experiment→analyse→
update over the Maxwell RSi pipeline (DeployGate, flywheel_ingest).
Supervisor: ShinkaOrchestrator — the ibuki-style beat cycle that drives both
loops and the flywheel between them.
"""

from .cell import (
    ShinkaEvolutionCell,
    EvolutionState,
    Proposal,
    elo_update,
)
from .maxwell_rsi import (
    DeployGate,
    RSiState,
    run_rsi,
    flywheel_ingest,
    FlywheelResult,
    CORPUS_TRAIN_FLOOR,
    CORPUS_M1_TARGET,
)
from .orchestrator import ShinkaOrchestrator, BeatRecord
from .kotoba_sink import InMemorySink, KotobaBridgeSink
from .fleet_sampler import (
    FleetSampler,
    FLEET_WORKER_NODES,
    pass_at_k,
    BestOfNResult,
)
from .bench_harness import BenchHarness, BenchTask, BenchReport, KPoint
from .reward import (
    RewardComponents,
    ScoredCandidate,
    PreferencePair,
    aggregate_reward,
    build_preference_pair,
)

__all__ = [
    # Loop A
    "ShinkaEvolutionCell",
    "EvolutionState",
    "Proposal",
    "elo_update",
    # Loop B
    "DeployGate",
    "RSiState",
    "run_rsi",
    "flywheel_ingest",
    "FlywheelResult",
    "CORPUS_TRAIN_FLOOR",
    "CORPUS_M1_TARGET",
    # Supervisor
    "ShinkaOrchestrator",
    "BeatRecord",
    # append-only sink (I1 commit-DAG)
    "InMemorySink",
    "KotobaBridgeSink",
    # Research Track A — fleet test-time compute
    "FleetSampler",
    "FLEET_WORKER_NODES",
    "pass_at_k",
    "BestOfNResult",
    # Research Track A — standing eval harness
    "BenchHarness",
    "BenchTask",
    "BenchReport",
    "KPoint",
    # Research Track E — verifier-grounded reward / preference
    "RewardComponents",
    "ScoredCandidate",
    "PreferencePair",
    "aggregate_reward",
    "build_preference_pair",
]
