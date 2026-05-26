"""UnispscOrganism — wrap a UNSPSC LangGraph code into a tick-able organism.

Per ADR-2605232345. Combines:
  - ``pymagatama.langgraph_graphs.unispsc_agents.c{code}.graph`` (classify)
  - ``pymagatama.organism.cadence.resolve_heartbeat_cadence`` (heartbeat)

The class is substrate-agnostic by design. ``post_sink`` and
``follower_score_provider`` are caller-supplied so the same class runs in
unit tests, the cell-runner LAN cell, and K8s Pods without modification.
"""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from pymagatama.organism.cadence import (
    CadenceState,
    ContentSource,
    HeartbeatCadence,
    resolve_heartbeat_cadence,
)
from pymagatama.organism.inbox import (
    FollowerCurrentScore,
    FollowerReward,
    InboxBuffer,
)
from pymagatama.organism.joucho import JouchoScores

logger = logging.getLogger("pymagatama.organism")

_AGENTS_PKG = "pymagatama.langgraph_graphs.unispsc_agents"

ClassifyInputFactory = Callable[["object"], dict[str, Any]]
# Legacy sink shape (text only). New code should pass a ``PostSink`` from
# pymagatama.organism.post_sink that accepts kwargs (ctx + mood + source).
LegacyPostSink = Callable[[str], None]
PostSink = LegacyPostSink  # backwards-compatible alias
JouchoProvider = Callable[[str], JouchoScores]
FollowerScoreProvider = Callable[[str], list[FollowerCurrentScore]]


@dataclass
class OrganismTickResult:
    """What happened this tick."""

    cadence: HeartbeatCadence
    classifications: list[dict[str, Any]] = field(default_factory=list)
    posts: list[str] = field(default_factory=list)
    rewards: list[FollowerReward] = field(default_factory=list)


def _default_classify_input_factory(commit: object) -> dict[str, Any]:
    """Default: pass the commit's rkey as the classify description."""
    rkey = getattr(commit, "rkey", "")
    return {"description": rkey}


def _format_post(
    code: str,
    title: str,
    cadence: HeartbeatCadence,
    classifications: list[dict[str, Any]],
) -> str | None:
    """Format the Shinka post text from the chosen content source.

    Returns None if cadence says not to post.
    """
    if not cadence.should_post or cadence.content_source.kind == "none":
        return None

    src = cadence.content_source
    if src.kind == "inbound" and classifications:
        last = classifications[-1]
        result = last.get("result") if isinstance(last, dict) else None
        permit = (result or {}).get("permit") if isinstance(result, dict) else None
        return (
            f"[{code}/{title}] inbound classify → "
            f"permit={permit!r} mood={cadence.mood}"
        )
    if src.kind == "reaction":
        return f"[{code}/{title}] reacted to engagement (mood={cadence.mood})"
    if src.kind == "recordAnalysis":
        return f"[{code}/{title}] mood={cadence.mood}; reflecting on recent classify history"
    if src.kind == "followerCelebration" and src.reward is not None:
        r = src.reward
        return (
            f"[{code}/{title}] celebrating follower {r.did} "
            f"({r.reward_type} on {r.metric})"
        )
    if src.kind == "moodShift":
        return f"[{code}/{title}] mood shifted {src.prev_mood} → {src.current_mood}"
    if src.kind == "dataRepair":
        return f"[{code}/{title}] dataRepair tick (missing={src.detail})"
    if src.kind == "milestone":
        return f"[{code}/{title}] milestone {src.detail}"
    return None


class UnispscOrganism:
    """Wrap one UNSPSC code into a tick-able organism.

    Underlying classify engine is the LangGraph at
    ``pymagatama.langgraph_graphs.unispsc_agents.c{code}``. The organism
    layer adds joucho mood + InboxBuffer + Shinka emission on top, without
    modifying the generated agent file.
    """

    def __init__(
        self,
        *,
        code: str,
        graph: Any,
        title: str = "",
        actor_did: str = "",
        classify_input_factory: ClassifyInputFactory | None = None,
        post_sink: PostSink | None = None,
        joucho_provider: JouchoProvider | None = None,
        follower_score_provider: FollowerScoreProvider | None = None,
    ) -> None:
        self.code = code
        self.title = title or f"c{code}"
        self.actor_did = actor_did or f"did:web:etzhayyim.com:actor:c{code}"
        self.graph = graph
        self.classify_input_factory = classify_input_factory or _default_classify_input_factory
        self.post_sink = post_sink
        self.joucho_provider = joucho_provider
        self.follower_score_provider = follower_score_provider
        self.inbox = InboxBuffer()
        self.cadence_state = CadenceState()
        self.tick_count = 0

    @classmethod
    def for_code(
        cls,
        code: str,
        *,
        title: str = "",
        actor_did: str = "",
        classify_input_factory: ClassifyInputFactory | None = None,
        post_sink: PostSink | None = None,
        joucho_provider: JouchoProvider | None = None,
        follower_score_provider: FollowerScoreProvider | None = None,
    ) -> "UnispscOrganism":
        """Lazy-import the underlying ``c{code}`` LangGraph and wrap it."""
        module_name = f"{_AGENTS_PKG}.c{code}"
        mod = importlib.import_module(module_name)
        graph = getattr(mod, "graph", None)
        if graph is None:
            raise ImportError(f"{module_name} has no `graph` attribute")
        resolved_title = title or getattr(mod, "UNISPSC_TITLE", "") or f"c{code}"
        resolved_did = actor_did or getattr(mod, "UNISPSC_DID", "") or f"did:web:etzhayyim.com:actor:c{code}"
        return cls(
            code=code,
            graph=graph,
            title=resolved_title,
            actor_did=resolved_did,
            classify_input_factory=classify_input_factory,
            post_sink=post_sink,
            joucho_provider=joucho_provider,
            follower_score_provider=follower_score_provider,
        )

    def tick(self, *, now_ms: int) -> OrganismTickResult:
        """Run one heartbeat. Returns what was done.

        Synchronous so unit tests can drive ticks deterministically.
        Cell-runner wraps this in ``asyncio.to_thread`` if the heartbeat
        period is short enough to need cooperative scheduling.
        """
        self.tick_count += 1
        cadence = resolve_heartbeat_cadence(
            self.actor_did,
            self.cadence_state,
            self.inbox,
            now_ms=now_ms,
            joucho_provider=self.joucho_provider,
            follower_score_provider=self.follower_score_provider,
        )

        classifications: list[dict[str, Any]] = []
        # If the chosen content source consumed an inbound commit, also
        # invoke the underlying classify graph on it. This is the bridge
        # from "organism" back to "specialist UNSPSC agent".
        src = cadence.content_source
        if cadence.should_post and src.kind == "inbound" and src.commit is not None:
            try:
                input_state = self.classify_input_factory(src.commit)
                terminal = self.graph.invoke(input_state)
                if isinstance(terminal, dict):
                    classifications.append(terminal)
                else:
                    classifications.append({"value": terminal})
            except Exception as exc:  # noqa: BLE001 — organism stays alive on classify failure
                logger.warning("c%s classify failed on tick %d: %s", self.code, self.tick_count, exc)

        posts: list[str] = []
        text = _format_post(self.code, self.title, cadence, classifications)
        if text is not None:
            posts.append(text)
            if self.post_sink is not None:
                try:
                    self._dispatch_post(text, cadence)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("c%s post_sink failed: %s", self.code, exc)
            self.cadence_state.last_post_at = now_ms

        if cadence.should_engage:
            self.cadence_state.last_engage_at = now_ms
        if cadence.should_analyze:
            self.cadence_state.last_analyze_at = now_ms
        if cadence.should_drill:
            self.cadence_state.last_drill_at = now_ms
        if cadence.should_validate:
            self.cadence_state.last_validate_at = now_ms
        if cadence.follower_rewards:
            self.cadence_state.last_reward_at = now_ms

        return OrganismTickResult(
            cadence=cadence,
            classifications=classifications,
            posts=posts,
            rewards=list(cadence.follower_rewards),
        )

    def _dispatch_post(self, text: str, cadence: Any) -> None:
        """Call post_sink with the right signature.

        Supports both the legacy text-only ``Callable[[str], None]`` and
        the ADR-2605240100 context-aware ``PostSink`` from
        ``pymagatama.organism.post_sink``.
        """
        sink = self.post_sink
        if sink is None:
            return
        try:
            sink(  # type: ignore[call-arg]
                text,
                ctx=self,
                mood=cadence.mood,
                content_source_kind=cadence.content_source.kind,
            )
            return
        except TypeError:
            pass
        sink(text)  # legacy text-only signature


__all__ = [
    "ClassifyInputFactory",
    "FollowerScoreProvider",
    "JouchoProvider",
    "OrganismTickResult",
    "PostSink",
    "UnispscOrganism",
]
