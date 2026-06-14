"""shinka_engine — the Shinka capability-evolution cell (Loop A).

See ADR-2606142200. Exposes ShinkaEvolutionCell (the Supervisor-driven
generate→debate→evolve→synthesize graph) and its pure node functions.
"""

from .cell import (
    ShinkaEvolutionCell,
    EvolutionState,
    Proposal,
    elo_update,
)

__all__ = [
    "ShinkaEvolutionCell",
    "EvolutionState",
    "Proposal",
    "elo_update",
]
