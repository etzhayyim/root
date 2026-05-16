"""JSON-RPC 2.0 LSP-style server for the keiei C-suite role layer.

Wire shape mirrors LSP: `initialize` handshake, `shutdown`/`exit`,
`$/cancelRequest`, plus `cxo/{role}/{method}` request/response and
`$/escalate` / `$/decisionMade` / `$/sla` server-pushed notifications.

Transport: stdio (default) or Unix socket (`--socket PATH`). WebSocket
deferred to k8s deploy phase — the same dispatcher serves any framing.

Per ADR 2605101200. Does **not** execute Class A; routes to escalate.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .leader import get_leader
from .roles import ROLES, CxoRole, DecisionClass, GateVerdict, by_id, gate


class NotLeaderError(RuntimeError):
    """Raised when a replica that does not hold the writer lease attempts
    to append to the ledger. The caller (HTTP transport / stdio) should
    surface this as a 503-equivalent with the leader's identity so the
    client can retry against the correct replica.
    """

    def __init__(self, *, identity: str) -> None:
        super().__init__(f"not leader (local identity={identity!r})")
        self.identity = identity

LEDGER_PATH = Path(os.environ.get(
    "KEIEI_LEDGER_PATH",
    str(Path(__file__).resolve().parents[6] / "_working" / "keiei" / "CXO-LEDGER.md"),
))

# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------

def _ledger_init() -> None:
    if LEDGER_PATH.exists():
        return
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_PATH.write_text(
        "# CXO-LEDGER\n\n"
        "Append-only audit trail of every keiei C-suite decision.\n"
        "Per ADR 2605101200. Never edit prior rows.\n\n"
        "| seq | date | role | class | summary | decided_by | escalated_to | artefact |\n"
        "|---|---|---|---|---|---|---|---|\n"
    )


def _ledger_next_seq() -> int:
    if not LEDGER_PATH.exists():
        return 1
    rows = [ln for ln in LEDGER_PATH.read_text().splitlines() if ln.startswith("| ") and not ln.startswith("| seq")]
    return len(rows) + 1


def ledger_append(*, role: str, decision_class: str, summary: str,
                  decided_by: str, escalated_to: str = "—",
                  artefact: str = "—") -> int:
    """Append a row to CXO-LEDGER.md (leader-gated).

    Phase 4 (ADR 2605101200 §7): when running under k8s with
    ``KEIEI_LEADER_ENABLED=1``, only the replica holding the
    ``coordination.k8s.io/v1`` Lease may write. Followers raise
    ``NotLeaderError`` so the transport can return a structured
    not-leader response with the holder's identity for client retry.
    Local dev (launchd / stdio) uses ``LocalLeader`` which is always
    leader, preserving existing behaviour.
    """

    leader = get_leader()
    if not leader.is_leader():
        raise NotLeaderError(identity=leader.identity())

    _ledger_init()
    seq = _ledger_next_seq()
    date = time.strftime("%Y-%m-%d", time.gmtime())
    safe = lambda s: str(s).replace("|", "\\|").replace("\n", " ")
    row = f"| {seq} | {date} | {role} | {decision_class} | {safe(summary)} | {safe(decided_by)} | {safe(escalated_to)} | {safe(artefact)} |\n"
    with LEDGER_PATH.open("a") as fh:
        fh.write(row)
    return seq


# ---------------------------------------------------------------------------
# JSON-RPC dispatcher
# ---------------------------------------------------------------------------

@dataclass
class Session:
    initialized: bool = False
    client_name: str = ""
    acting_as: str = ""           # email of the human operator behind the client
    principal_did: str = ""


class KeieiServer:
    def __init__(self) -> None:
        self.session = Session()
        self._pending: dict[Any, asyncio.Task] = {}

    # ---- public dispatch ----------------------------------------------------

    async def handle(self, msg: dict) -> dict | None:
        method = msg.get("method")
        msg_id = msg.get("id")
        params = msg.get("params") or {}

        if method == "initialize":
            return self._reply(msg_id, self._initialize(params))
        if method == "initialized":
            self.session.initialized = True
            return None
        if method == "shutdown":
            return self._reply(msg_id, None)
        if method == "exit":
            raise SystemExit(0)
        if method == "cxo/listRoles":
            return self._reply(msg_id, self._list_roles())
        if method == "$/cancelRequest":
            t = self._pending.pop(params.get("id"), None)
            if t:
                t.cancel()
            return None

        # cxo/{role}/{verb}
        if method and method.startswith("cxo/") and method.count("/") == 2:
            _, role_id, verb = method.split("/", 2)
            try:
                role = by_id(role_id)
            except KeyError:
                return self._error(msg_id, -32601, f"unknown role {role_id!r}")
            if verb == "decide":
                return self._reply(msg_id, await self._decide(role, params))
            if verb == "review":
                return self._reply(msg_id, await self._review(role, params))
            if verb == "state":
                return self._reply(msg_id, self._state(role))
            if verb == "escalate":
                return self._reply(msg_id, self._escalate(role, params))
            return self._error(msg_id, -32601, f"unknown verb {verb!r} for role {role_id!r}")

        return self._error(msg_id, -32601, f"unknown method {method!r}")

    # ---- handlers -----------------------------------------------------------

    def _initialize(self, params: dict) -> dict:
        self.session.client_name = (params.get("clientInfo") or {}).get("name", "?")
        self.session.acting_as = params.get("actingAs", "")
        self.session.principal_did = params.get("principal", "did:web:etz-hayim")
        return {
            "serverInfo": {"name": "keiei-lsp", "version": "0.1.0"},
            "serverCapabilities": {
                "roles": [
                    {
                        "id": r.id,
                        "title": r.title,
                        "mode": r.mode,
                        "humanSeat": r.human_seat,
                        "financialActionGated": r.financial_action_gated,
                        "payrollGated": r.payroll_gated,
                        "methods": list(r.methods),
                    }
                    for r in ROLES
                ],
                "decisionClasses": ["A", "B", "C", "D"],
                "auditChannel": str(LEDGER_PATH),
                "operatingEntity": "amanomibashira",
                "vendor": "Gftd Japan株式会社",
            },
        }

    def _list_roles(self) -> list[dict]:
        return [
            {"id": r.id, "title": r.title, "mode": r.mode, "humanSeat": r.human_seat}
            for r in ROLES
        ]

    async def _decide(self, role: CxoRole, params: dict) -> dict:
        decision_class: DecisionClass = params.get("class", "C")
        action_kind: str = params.get("actionKind", "")
        summary: str = params.get("summary", "")
        artefact: str = params.get("artefact", "—")

        verdict: GateVerdict = gate(role, decision_class, action_kind=action_kind)

        result: dict[str, Any] = {
            "role": role.id,
            "class": decision_class,
            "verdict": asdict(verdict),
        }

        # Phase 1 (iter126): if the gate allows execution, run the role's
        # graph to produce a real rationale. Roles without a registered
        # graph (Phase 2/3) get a "no-graph" placeholder.
        rationale = None
        rationale_source = None
        if verdict.allowed:
            try:
                from . import graph as _g  # lazy import — keeps gate path fast
                resp = await _g.dispatch_decide(role.id, params)
                rationale = resp.rationale
                rationale_source = resp.rationale_source
                result["rationale"] = rationale
                result["rationaleSource"] = rationale_source
                result["deliberationSteps"] = resp.deliberation_steps
            except KeyError:
                result["rationale"] = "(no graph registered for this role yet — Phase 2/3 pending)"
                result["rationaleSource"] = "no-graph"
            except Exception as e:                                       # noqa: BLE001
                result["rationale"] = f"(graph error: {type(e).__name__}: {e})"
                result["rationaleSource"] = "graph-error"

        try:
            if verdict.must_escalate:
                result["status"] = "escalated"
                result["escalatedTo"] = list(role.escalate_to)
                ledger_append(
                    role=role.id, decision_class=decision_class,
                    summary=summary or "(no summary)",
                    decided_by="(escalated, not executed)",
                    escalated_to=",".join(role.escalate_to),
                    artefact=artefact,
                )
            elif verdict.requires_human_confirm:
                result["status"] = "pending-confirm"
                result["confirmFrom"] = role.human_seat or role.escalate_to[0]
            elif verdict.allowed:
                result["status"] = "executed"
                artefact_with_src = artefact
                if rationale_source and rationale_source != "llm":
                    # Mark the ledger row when rationale fell back from LLM —
                    # auditors must be able to distinguish real from stub.
                    artefact_with_src = f"{artefact} [rationale={rationale_source}]"
                seq = ledger_append(
                    role=role.id, decision_class=decision_class, summary=summary,
                    decided_by=f"AI-{role.id.upper()} (acting via {self.session.acting_as or 'unknown client'})",
                    escalated_to="—" if role.mode == "primary" and decision_class == "B" else "—",
                    artefact=artefact_with_src,
                )
                result["ledgerSeq"] = seq
            else:
                result["status"] = "denied"
        except NotLeaderError as e:
            # Phase 4: multi-replica safety. This pod doesn't hold the
            # writer lease — surface so caller retries against the leader.
            result["status"] = "not-leader"
            result["leaderIdentity"] = e.identity
            result["retryHint"] = "retry against the replica named in leaderIdentity"

        return result

    async def _review(self, role: CxoRole, params: dict) -> dict:
        # Advisory-only: review never writes ledger; reviewer just emits notes.
        return {
            "role": role.id,
            "advisory": params.get("placeholder", "review handler stub — wire LangGraph in Phase 1"),
            "decisionClassesAccepted": list(role.autonomous_classes + role.confirm_classes),
        }

    def _state(self, role: CxoRole) -> dict:
        return {
            "role": role.id,
            "mode": role.mode,
            "humanSeat": role.human_seat,
            "ledgerPath": str(LEDGER_PATH),
            "ledgerEntries": _ledger_next_seq() - 1 if LEDGER_PATH.exists() else 0,
        }

    def _escalate(self, role: CxoRole, params: dict) -> dict:
        summary = params.get("summary", "(no summary)")
        try:
            seq = ledger_append(
                role=role.id, decision_class=params.get("class", "A"),
                summary=summary, decided_by="(force-escalated)",
                escalated_to=",".join(role.escalate_to),
                artefact=params.get("artefact", "—"),
            )
        except NotLeaderError as e:
            return {
                "status": "not-leader",
                "leaderIdentity": e.identity,
                "to": list(role.escalate_to),
                "retryHint": "retry against the replica named in leaderIdentity",
            }
        return {"status": "escalated", "ledgerSeq": seq, "to": list(role.escalate_to)}

    # ---- framing helpers ----------------------------------------------------

    @staticmethod
    def _reply(msg_id: Any, result: Any) -> dict:
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    @staticmethod
    def _error(msg_id: Any, code: int, message: str) -> dict:
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


# ---------------------------------------------------------------------------
# Transport — stdio (line-delimited JSON) and Unix socket
# ---------------------------------------------------------------------------

async def _serve_stdio(server: KeieiServer) -> None:
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader(loop=loop)
    await loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), sys.stdin)
    while True:
        line = await reader.readline()
        if not line:
            return
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = await server.handle(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


async def _serve_unix(server: KeieiServer, path: str) -> None:
    if os.path.exists(path):
        os.unlink(path)

    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        while True:
            line = await reader.readline()
            if not line:
                writer.close()
                return
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            resp = await server.handle(msg)
            if resp is not None:
                writer.write((json.dumps(resp) + "\n").encode())
                await writer.drain()

    srv = await asyncio.start_unix_server(handle_client, path=path)
    async with srv:
        await srv.serve_forever()


async def main(argv: list[str]) -> None:
    server = KeieiServer()
    if len(argv) >= 2 and argv[1] == "--socket":
        path = argv[2] if len(argv) >= 3 else os.path.join(
            os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "keiei.sock",
        )
        sys.stderr.write(f"keiei-lsp listening on unix:{path}\n")
        await _serve_unix(server, path)
    else:
        sys.stderr.write("keiei-lsp listening on stdio\n")
        await _serve_stdio(server)
