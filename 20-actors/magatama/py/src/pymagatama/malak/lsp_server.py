"""JSON-RPC 2.0 LSP-style server for the Malak cybercrime role layer.

Transport: Unix socket (`--socket PATH`).
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .roles import ROLES, MalakRole, GateVerdict, by_id, gate

LEDGER_PATH = Path(os.environ.get(
    "MALAK_LEDGER_PATH",
    str(Path(__file__).resolve().parents[6] / "_working" / "malak" / "THREAT-LEDGER.md"),
))

def _ledger_init() -> None:
    if LEDGER_PATH.exists():
        return
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_PATH.write_text(
        "# MALAK-THREAT-LEDGER\n\n"
        "Append-only audit trail of cybercrime intelligence actions.\n\n"
        "| seq | date | role | tlp | action | verdict | details |\n"
        "|---|---|---|---|---|---|---|\n"
    )

def _ledger_next_seq() -> int:
    if not LEDGER_PATH.exists():
        return 1
    rows = [ln for ln in LEDGER_PATH.read_text().splitlines() if ln.startswith("| ") and not ln.startswith("| seq")]
    return len(rows) + 1

def ledger_append(*, role: str, tlp: str, action: str, verdict: str, details: str) -> int:
    _ledger_init()
    seq = _ledger_next_seq()
    date = time.strftime("%Y-%m-%d", time.gmtime())
    safe = lambda s: str(s).replace("|", "\\|").replace("\n", " ")
    row = f"| {seq} | {date} | {role} | {tlp} | {safe(action)} | {safe(verdict)} | {safe(details)} |\n"
    with LEDGER_PATH.open("a") as fh:
        fh.write(row)
    return seq

class MalakServer:
    async def handle(self, msg: dict) -> dict | None:
        method = msg.get("method")
        msg_id = msg.get("id")
        params = msg.get("params") or {}

        if method == "initialize":
            return self._reply(msg_id, self._initialize())
        if method == "malak/listRoles":
            return self._reply(msg_id, self._list_roles())
        
        if method and method.startswith("malak/") and method.count("/") == 2:
            _, role_id, verb = method.split("/", 2)
            try:
                role = by_id(role_id)
            except KeyError:
                return self._error(msg_id, -32601, f"unknown role {role_id!r}")
            
            if verb == "execute":
                return self._reply(msg_id, await self._execute(role, params))

        return self._error(msg_id, -32601, f"unknown method {method!r}")

    def _initialize(self) -> dict:
        return {
            "serverInfo": {"name": "malak-lsp", "version": "0.1.0"},
            "serverCapabilities": {
                "roles": [
                    {
                        "id": r.id,
                        "allowed_tlp": list(r.allowed_tlp),
                        "capabilities": list(r.capabilities),
                    }
                    for r in ROLES
                ],
                "auditChannel": str(LEDGER_PATH)
            },
        }

    def _list_roles(self) -> list[dict]:
        return [{"id": r.id, "title": r.title} for r in ROLES]

    async def _execute(self, role: MalakRole, params: dict) -> dict:
        tlp = params.get("tlp", "AMBER")
        action = params.get("action", "ingest-ioc")
        details = params.get("details", "")

        verdict: GateVerdict = gate(role, tlp, action)
        
        result = {
            "role": role.id,
            "action": action,
            "verdict": asdict(verdict),
        }

        if verdict.allowed:
            try:
                from .langgraph import run_langgraph_pipeline
                resp = await run_langgraph_pipeline(role.id, params)
                result["rationale"] = resp["rationale"]
                result["rationaleSource"] = resp["rationale_source"]
                result["deliberationSteps"] = resp["deliberation_steps"]
                result["tickVertexId"] = resp["tick_vertex_id"]
            except Exception as e:
                result["rationale"] = f"(graph error: {type(e).__name__}: {e})"
                result["rationaleSource"] = "graph-error"

            seq = ledger_append(
                role=role.id,
                tlp=tlp,
                action=action,
                verdict="allowed" + (" (sanitized)" if verdict.requires_sanitization else ""),
                details=details
            )
            result["status"] = "executed"
            result["ledgerSeq"] = seq
        else:
            result["status"] = "denied"
            ledger_append(
                role=role.id,
                tlp=tlp,
                action=action,
                verdict="denied",
                details=verdict.reason
            )

        return result

    @staticmethod
    def _reply(msg_id: Any, result: Any) -> dict:
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    @staticmethod
    def _error(msg_id: Any, code: int, message: str) -> dict:
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}

async def _serve_unix(server: MalakServer, path: str) -> None:
    if os.path.exists(path):
        os.unlink(path)

    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        while True:
            try:
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
            except ConnectionResetError:
                writer.close()
                return

    srv = await asyncio.start_unix_server(handle_client, path=path)
    async with srv:
        await srv.serve_forever()

import random
import urllib.request

async def _fetch_live_threat() -> dict:
    """Fetches a real, live cybercrime indicator from OpenPhish."""
    try:
        url = "https://openphish.com/feed.txt"
        req = urllib.request.Request(url, headers={'User-Agent': 'malak-langserver/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = response.read().decode().splitlines()
            if data:
                # Pick a random recent threat URL
                payload_url = random.choice(data[:20])
                
                details = (
                    f"Live Threat Ingested: Malicious phishing payload detected at {payload_url}. "
                    f"Reported by OpenPhish Global Feed."
                )
                return {
                    "role_id": "malak",
                    "params": {
                        "tlp": "AMBER",
                        "action": "correlate_ttp",
                        "details": details
                    }
                }
    except Exception as e:
        sys.stderr.write(f"[Heartbeat] Failed to fetch live threat: {e}\n")
    
    # Fallback if API fails
    return {
        "role_id": "malak",
        "params": {
            "tlp": "AMBER",
            "action": "correlate_ttp",
            "details": "Fallback: Continuous monitoring of network boundaries for anomalous outbound connections."
        }
    }

async def _heartbeat_loop(server: MalakServer) -> None:
    """Autonomous heartbeat loop fetching real-world data."""
    idx = 0
    while True:
        await asyncio.sleep(10)  # Wake up every 10 seconds for testing
        sys.stderr.write("[Heartbeat] Waking up to check for new Live IOCs/Threats...\n")
        sys.stderr.flush()
        try:
            mode = idx % 3
            
            if mode == 0:
                # Live OpenPhish OSINT ingestion
                live_event = await _fetch_live_threat()
                role_id = random.choice(["malak", "honeypot-tracker"])
                params = live_event["params"]
            elif mode == 1:
                role_id = "crypto-tracker"
                params = {
                    "tlp": "AMBER",
                    "action": "trace_wallet",
                    "details": "Suspicious fund transfer detected involving BTC wallet 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa. Potential laundering via Tornado Cash to Binance deposit."
                }
            else:
                role_id = "sns-tracker"
                params = {
                    "tlp": "GREEN",
                    "action": "correlate_sns",
                    "details": "Identified persona @dark_knght correlating with email admin@dark-knght-ops.com. Linked to Telegram channel and initial access broker forum Discord."
                }
                
            role = by_id(role_id)
            result = await server._execute(role, params)
            sys.stderr.write(f"[Heartbeat] Executed: {role_id} - {result.get('status')} - Rationale Source: {result.get('rationaleSource')}\n")
            sys.stderr.flush()
            idx += 1
        except Exception as e:
            sys.stderr.write(f"[Heartbeat] Error: {e}\n")
            sys.stderr.flush()

async def main(argv: list[str]) -> None:
    server = MalakServer()
    asyncio.create_task(_heartbeat_loop(server))
    
    if len(argv) >= 2 and argv[1] == "--socket":
        path = argv[2] if len(argv) >= 3 else "/tmp/malak.sock"
        sys.stderr.write(f"malak-lsp listening on unix:{path}\n")
        await _serve_unix(server, path)
    else:
        sys.stderr.write("malak-lsp requires --socket\n")
        sys.exit(1)
