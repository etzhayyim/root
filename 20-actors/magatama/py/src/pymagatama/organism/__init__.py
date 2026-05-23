"""pymagatama.organism — joucho heartbeat-cadence + UNSPSC actor wrapper.

Per ADR-2605232345 (UNSPSC actor as ecosystem organism).

Python port of the TS heartbeat-cadence pattern in
``@gftd/magatama-host-sdk/src/heartbeat-cadence.ts``. Wraps a UNSPSC
LangGraph code (from ``pymagatama.langgraph_graphs.unispsc_agents``) into
a tick-able organism with joucho 情緒 mood, InboxBuffer, FollowerReward,
Shannon content diversity, and Shinka post emission.
"""

from __future__ import annotations

from pymagatama.organism.cadence import (
    CadenceState,
    ContentSource,
    HeartbeatCadence,
    resolve_heartbeat_cadence,
)
from pymagatama.organism.inbox import (
    FollowerReward,
    FollowerSnapshot,
    InboundCommit,
    InboundReaction,
    InboxBuffer,
)
from pymagatama.organism.joucho import (
    JouchoScores,
    Mood,
    apply_stress_scaling,
    determine_mood,
    mood_to_cadence,
)
from pymagatama.organism.kaizen import (
    KaizenObserver,
    KaizenProposal,
    KaizenRule,
    Observation,
    RULE_REGISTRY,
    register_rule,
)
from pymagatama.organism.post_sink import (
    LoggerPostSink,
    NdjsonQueuePostSink,
    NullPostSink,
    PostSink,
    resolve_post_sink,
)
from pymagatama.organism.unispsc_organism import (
    OrganismTickResult,
    UnispscOrganism,
)

__all__ = [
    "CadenceState",
    "ContentSource",
    "FollowerReward",
    "FollowerSnapshot",
    "HeartbeatCadence",
    "InboundCommit",
    "InboundReaction",
    "InboxBuffer",
    "JouchoScores",
    "KaizenObserver",
    "KaizenProposal",
    "KaizenRule",
    "LoggerPostSink",
    "Mood",
    "NdjsonQueuePostSink",
    "NullPostSink",
    "Observation",
    "OrganismTickResult",
    "PostSink",
    "RULE_REGISTRY",
    "UnispscOrganism",
    "apply_stress_scaling",
    "determine_mood",
    "mood_to_cadence",
    "register_rule",
    "resolve_heartbeat_cadence",
    "resolve_post_sink",
]
