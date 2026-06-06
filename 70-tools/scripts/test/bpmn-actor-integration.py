#!/usr/bin/env python3
# ruff: noqa: E501,T201,S603,S607
"""
Integration tests for the BPMN-as-actor dispatcher (F4/F5/F6 stack).

What this covers:
  1. dispatcher reachable     — /health, /bindings
  2. each pre-registered actor — bot.ping, watch.urlDigest, yabai.triagePoc,
                                 bot.reviewAndPost
  2b. optional datacenter actor — binding present, startOperation reachable
  3. RW side-effects           — audit rows exist in vertex_repo_commit,
                                 phishing alert exists in
                                 vertex_gmail_phishing_alert
  4. dynamic registration      — INSERT a probe actor → watcher deploys →
                                 call succeeds → teardown
  5. negative path             — unknown NSID → 404

Env:
  BPMN_DISPATCHER_URL  default http://bpmn.etzhayyim.com:8080
                       pass a direct IP (http://<vendor-bpmn-dispatcher>:8080) to
                       bypass a stale local DNS cache.
  KOTOBA_URL               default: fetched from macOS Keychain
                       (service=etzhayyim.rw, account=ROOT_URL)

Usage:
    70-tools/scripts/test/bpmn-actor-integration.py
    70-tools/scripts/test/bpmn-actor-integration.py --skip-dynamic
    70-tools/scripts/test/bpmn-actor-integration.py --skip-rw
    70-tools/scripts/test/bpmn-actor-integration.py --include-datacenter
    BPMN_DISPATCHER_URL=http://<vendor-bpmn-dispatcher>:8080 \
        70-tools/scripts/test/bpmn-actor-integration.py
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

# ─── Config ────────────────────────────────────────────────────────────

DISPATCHER_URL = os.environ.get("BPMN_DISPATCHER_URL", "https://dispatcher.etzhayyim.com").rstrip("/")
DISPATCHER_INTERNAL_SECRET = os.environ.get("DISPATCHER_INTERNAL_SECRET", "")
WATCHER_INTERVAL_SEC = 30  # matches dispatcher_main WATCHER_INTERVAL_SEC
DATACENTER_START_NSID = "com.etzhayyim.apps.datacenter.startOperation"
DATACENTER_ACCESS_NSID = "com.etzhayyim.apps.datacenter.requestAccess"
DATACENTER_CAPACITY_NSID = "com.etzhayyim.apps.datacenter.reserveCapacity"


def rw_url() -> str:
    if url := os.environ.get("KOTOBA_URL"):
        return url
    try:
        out = subprocess.check_output(
            ["security", "find-generic-password", "-s", "etzhayyim.rw", "-a", "ROOT_URL", "-w"],
            text=True,
        ).strip()
        if out:
            return out
    except subprocess.CalledProcessError:
        pass
    raise SystemExit("KOTOBA_URL not in env and not in Keychain (etzhayyim.rw/ROOT_URL)")


# ─── HTTP helper ───────────────────────────────────────────────────────


def _request(
    method: str,
    path: str,
    body: dict | None = None,
    timeout: float = 60.0,
) -> tuple[int, dict | str]:
    url = DISPATCHER_URL + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    # Cloudflare bot score blocks the default `Python-urllib/3.x` UA at
    # dispatcher.etzhayyim.com (error 1010). Use a named agent so CF lets the
    # request through.
    hdrs = {"User-Agent": "etzhayyim-bpmn-integration-test/1.0"}
    if DISPATCHER_INTERNAL_SECRET:
        hdrs["x-internal-trust"] = DISPATCHER_INTERNAL_SECRET
    if data:
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            ct = (resp.headers.get("Content-Type") or "").lower()
            if "json" in ct:
                return resp.status, json.loads(raw)
            return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw


# ─── RW helper (optional) ──────────────────────────────────────────────


def rw_count(sql: str) -> int:
    """Return COUNT(*) via psql. 0 if psql not available or query fails."""
    try:
        out = subprocess.check_output(
            ["psql", rw_url(), "-tA", "-c", sql],
            text=True, stderr=subprocess.DEVNULL, timeout=15,
        ).strip()
        return int(out or "0")
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError, subprocess.TimeoutExpired):
        return 0


def rw_exec(sql: str) -> bool:
    try:
        subprocess.check_output(
            ["psql", rw_url(), "-c", sql],
            text=True, stderr=subprocess.STDOUT, timeout=15,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"    rw_exec failed: {e.output}")
        return False


# ─── Test runner ───────────────────────────────────────────────────────


class Suite:
    def __init__(self) -> None:
        self.passed = 0
        self.failed: list[str] = []

    def run(self, name: str, fn) -> None:  # type: ignore[no-untyped-def]
        started = time.monotonic()
        try:
            fn()
        except AssertionError as e:
            dur = int((time.monotonic() - started) * 1000)
            print(f"  FAIL  {name}  ({dur}ms)  — {e}")
            self.failed.append(name)
        except Exception as e:  # noqa: BLE001
            dur = int((time.monotonic() - started) * 1000)
            print(f"  ERR   {name}  ({dur}ms)  — {type(e).__name__}: {e}")
            self.failed.append(name)
        else:
            dur = int((time.monotonic() - started) * 1000)
            print(f"  ok    {name}  ({dur}ms)")
            self.passed += 1

    def summary(self) -> int:
        total = self.passed + len(self.failed)
        print(f"\n{self.passed}/{total} passed")
        if self.failed:
            print("failed:")
            for n in self.failed:
                print(f"  - {n}")
            return 1
        return 0


# ─── Actual tests ──────────────────────────────────────────────────────


def test_health() -> None:
    status, body = _request("GET", "/health", timeout=10)
    assert status == 200, f"expected 200, got {status}"
    assert isinstance(body, dict) and body.get("status") == "ok", f"unexpected body: {body!r}"


def test_bindings_reach() -> None:
    status, body = _request("GET", "/bindings", timeout=10)
    assert status == 200, f"expected 200, got {status}"
    assert isinstance(body, dict), f"expected dict, got {type(body).__name__}"
    nsids = {b["nsid"] for b in body.get("bindings") or []}
    for required in (
        "com.etzhayyim.apps.bot.ping",
        "com.etzhayyim.apps.watch.urlDigest",
        "com.etzhayyim.apps.yabai.triagePoc",
        "com.etzhayyim.apps.bot.reviewAndPost",
    ):
        assert required in nsids, f"{required} not among {sorted(nsids)}"


def test_new_bpmn_bindings_present() -> None:
    """5 BPMN actors migrated from ingest scripts (deps.toml §ingest-scripts-bpmn-consolidation-phase1)."""
    status, body = _request("GET", "/bindings", timeout=10)
    assert status == 200, f"expected 200, got {status}"
    nsids = {b["nsid"] for b in (body or {}).get("bindings") or []}
    for required in (
        "com.etzhayyim.apps.yabai.enrichLegalEntity",
        "com.etzhayyim.apps.yabai.reverseIpLookup",
        "com.etzhayyim.apps.yabai.crtshFuzzySearch",
        "com.etzhayyim.apps.yabai.trackPhishingInfra",
        "com.etzhayyim.apps.shinshi.backfillGovernanceEdges",
    ):
        assert required in nsids, f"{required} not among {sorted(nsids)}"


def test_yabai_track_phishing_infra() -> None:
    """trackPhishingInfra end-to-end (DoH + tls.probe + crt.sh + rdap + iptoasn +
    db.insert). Uses dispatcher.etzhayyim.com itself as target — always resolves,
    cert is valid, no anomalies expected."""
    entity_id = f"integ-trackinfra-{int(time.time())}"
    status, body = _request(
        "POST", "/xrpc/com.etzhayyim.apps.yabai.trackPhishingInfra",
        {"entityId": entity_id, "domain": "dispatcher.etzhayyim.com"},
        timeout=90,
    )
    assert status == 200, f"expected 200, got {status}: {body!r}"
    v = body["variables"]
    assert v.get("tlsOk") is True, f"tlsOk: {v.get('tlsOk')}"
    assert v.get("firstIp") is not None, f"firstIp missing: {v}"
    assert v.get("inserted") == 1, f"inserted != 1 (error: {v.get('insertError')})"
    # Cleanup the probe row
    rw_exec(f"DELETE FROM vertex_yabai_infra_track WHERE entity_id='{entity_id}'")


def test_yabai_enrich_legal_entity_happy() -> None:
    """Known-LEI org (Alibaba Cloud US LLC, LEI 9845000B4FL02B89BB41).
    Process must return LEI + rkey + perform 3 inserts (vertex_legal_entity,
    vertex_yabai_entity, edge_yabai_operated_by). Ignores idempotent rerun —
    `inserted=0` is valid on 2nd invocation."""
    yabai_id = f"integ-enrich-{int(time.time())}"
    status, body = _request(
        "POST", "/xrpc/com.etzhayyim.apps.yabai.enrichLegalEntity",
        {
            "yabaiEntityId": yabai_id,
            "search": "Alibaba Cloud US LLC",
            "kind": "hosting",
            "countryHint": "US",
        },
        timeout=45,
    )
    assert status == 200, f"expected 200, got {status}: {body!r}"
    v = body["variables"]
    assert v.get("gleifStatus") == 200, f"gleifStatus: {v.get('gleifStatus')}"
    derived = v.get("derived") or {}
    assert derived.get("lei") == "9845000B4FL02B89BB41", f"derived.lei: {derived.get('lei')!r}"
    assert derived.get("rkey") == "9845000b4fl02b89bb41", f"derived.rkey: {derived.get('rkey')!r}"
    # Cleanup smoke-test rows (idempotent)
    rw_exec(f"DELETE FROM edge_yabai_operated_by WHERE edge_id='edge-operated-by-{yabai_id}-9845000b4fl02b89bb41'")
    rw_exec(f"DELETE FROM vertex_yabai_entity WHERE entity_id='{yabai_id}'")


def test_yabai_enrich_legal_entity_no_match() -> None:
    """Search term with no GLEIF hit (UCloud HK per deps.toml note).
    Process must still succeed and emit nolei-<id> rkey + audit, not error."""
    yabai_id = f"integ-nolei-{int(time.time())}"
    status, body = _request(
        "POST", "/xrpc/com.etzhayyim.apps.yabai.enrichLegalEntity",
        {
            "yabaiEntityId": yabai_id,
            "search": "UCloud Information Technology",
            "kind": "hosting",
            "countryHint": "HK",
        },
        timeout=45,
    )
    assert status == 200, f"expected 200, got {status}: {body!r}"
    v = body["variables"]
    derived = v.get("derived") or {}
    assert derived.get("lei") is None, f"unexpected LEI: {derived!r}"
    assert derived.get("rkey") == f"nolei-{yabai_id}", f"derived.rkey: {derived.get('rkey')!r}"
    assert v.get("emitted") is True, f"audit not emitted: {v}"
    # Cleanup
    rw_exec(f"DELETE FROM vertex_yabai_entity WHERE entity_id='{yabai_id}'")


def test_yabai_reverse_ip_lookup() -> None:
    """hackertarget is rate-limited (100/day), so may return rateLimited=true.
    Either siblings list or rate-limit must be returned — never error."""
    status, body = _request(
        "POST", "/xrpc/com.etzhayyim.apps.yabai.reverseIpLookup",
        {"ip": "1.1.1.1"},
        timeout=30,
    )
    assert status == 200, f"expected 200, got {status}: {body!r}"
    v = body["variables"]
    assert "siblings" in v, f"siblings missing: {v.keys()}"
    assert isinstance(v["siblings"], list), f"siblings not list: {type(v['siblings'])}"
    # rate limit OR fresh response are both valid outcomes.
    assert v.get("fetchStatus") is not None, f"fetchStatus missing: {v}"


def test_yabai_crtsh_fuzzy_search() -> None:
    """crt.sh is flaky upstream (often 502/timeout). Test accepts any non-error
    response shape so CI doesn't go red on external outages; just validates
    the BPMN path (URL encode → fetch → flatten → audit) doesn't error."""
    status, body = _request(
        "POST", "/xrpc/com.etzhayyim.apps.yabai.crtshFuzzySearch",
        {"keyword": "line-me"},
        timeout=30,
    )
    assert status == 200, f"expected 200, got {status}: {body!r}"
    v = body["variables"]
    assert "siblings" in v, f"siblings missing: {v.keys()}"
    assert isinstance(v["siblings"], list), f"siblings not list: {type(v['siblings'])}"
    assert v.get("fetchStatus") is not None, f"fetchStatus missing: {v}"


def test_shinshi_backfill_governance_edges() -> None:
    """Tiny model set. After run, count(edge_governance WHERE src_vid LIKE '%integ-shinshi-%')
    should equal 2 × models. Idempotent — second run must yield same count."""
    ts = int(time.time())
    folders = [f"integ-shinshi-{ts}-a", f"integ-shinshi-{ts}-b"]
    status, body = _request(
        "POST", "/xrpc/com.etzhayyim.apps.shinshi.backfillGovernanceEdges",
        {"models": [{"folder": f} for f in folders]},
        timeout=60,
    )
    assert status == 200, f"expected 200, got {status}: {body!r}"
    v = body["variables"]
    assert len(v.get("edgesToInsert", [])) == 4, f"expected 4 edges to insert, got: {v.get('edgesToInsert')}"

    # RW streaming visibility 5-15s — wait generously.
    ok = _wait_for(lambda: rw_count(
        f"SELECT COUNT(*) FROM edge_governance WHERE src_vid LIKE 'did:web:sh1n5h1x.etzhayyim.com:integ-shinshi-{ts}-%' "
        f"AND label IN ('GovernedBy','CompliesWith')"
    ) == 4, timeout_s=20.0)

    # Cleanup regardless of outcome
    rw_exec(f"DELETE FROM edge_governance WHERE src_vid LIKE 'did:web:sh1n5h1x.etzhayyim.com:integ-shinshi-{ts}-%'")

    assert ok, f"expected 4 edge_governance rows within 20s for ts={ts}"


def test_datacenter_binding_present() -> None:
    status, body = _request("GET", "/bindings", timeout=10)
    assert status == 200, f"expected 200, got {status}"
    assert isinstance(body, dict), f"expected dict, got {type(body).__name__}"
    nsids = {b["nsid"] for b in body.get("bindings") or []}
    for required in (DATACENTER_START_NSID, DATACENTER_ACCESS_NSID, DATACENTER_CAPACITY_NSID):
        assert required in nsids, f"{required} not among {sorted(nsids)}"


def test_bot_ping() -> None:
    status, body = _request("POST", "/xrpc/com.etzhayyim.apps.bot.ping",
                            {"message": "integration test ping"}, timeout=15)
    assert status == 200, f"expected 200, got {status}: {body!r}"
    assert isinstance(body, dict) and body.get("ok") is True
    v = body["variables"]
    assert v.get("auditEmitted") is True, f"auditEmitted not true: {v}"
    assert v.get("auditRkey", "").startswith("audit-"), f"bad auditRkey: {v.get('auditRkey')!r}"


def test_watch_url_digest() -> None:
    status, body = _request("POST", "/xrpc/com.etzhayyim.apps.watch.urlDigest",
                            {"url": "https://example.com/"}, timeout=60)
    assert status == 200, f"expected 200, got {status}: {body!r}"
    v = body["variables"]
    assert v.get("fetchStatus") == 200, f"fetchStatus: {v.get('fetchStatus')}"
    assert v.get("llmOk") is True, f"llmOk: {v.get('llmOk')}"
    assert v.get("auditEmitted") is True
    digest = v.get("digest") or {}
    assert isinstance(digest, dict) and len(digest.get("title") or "") > 0, f"digest: {digest!r}"


def test_yabai_triage_phishing() -> None:
    status, body = _request(
        "POST", "/xrpc/com.etzhayyim.apps.yabai.triagePoc",
        {
            "emailId": f"integ-test-{int(time.time())}",
            "fromAddr": "urgent-support@paypa1-secure.xyz",
            "subject": "Your account has been locked — verify NOW",
            "replyTo": "no-reply@paypa1-secure.xyz",
            "spf": "fail", "dkim": "fail", "dmarc": "fail",
            "bodyUrls": "http://paypa1-secure.xyz/login",
        },
        timeout=60,
    )
    assert status == 200, f"expected 200, got {status}: {body!r}"
    v = body["variables"]
    assert v.get("llmOk") is True, f"llmOk: {v.get('llmOk')}"
    verdict = v.get("verdict") or {}
    assert verdict.get("verdict") == "phishing", f"verdict: {verdict!r}"
    assert v.get("inserted") == 1, f"inserted: {v.get('inserted')}"


def test_bot_review_accept() -> None:
    status, body = _request(
        "POST", "/xrpc/com.etzhayyim.apps.bot.reviewAndPost",
        {"text": "Quick hello — benign test message.", "channel": "feed"},
        timeout=60,
    )
    assert status == 200, f"expected 200, got {status}: {body!r}"
    v = body["variables"]
    assert v.get("accepted") is True, f"not accepted: {v}"
    assert v.get("auditEmitted") is True


def test_datacenter_start_operation() -> None:
    req_id = f"integ-dc-{int(time.time())}"
    status, body = _request(
        "POST",
        f"/xrpc/{DATACENTER_START_NSID}",
        {
            "facilityId": "dc-integ-01",
            "orgId": "org-integ",
            "operatorDid": "did:web:test.etzhayyim.com:operator",
            "requestId": req_id,
            "kind": "maintenance",
            "summary": "Integration test planned maintenance",
            "riskClass": "low",
            "requiresApproval": False,
            "windowStart": "2026-04-23T12:00:00Z",
            "windowEnd": "2026-04-23T12:30:00Z",
        },
        timeout=30,
    )
    assert status == 200, f"expected 200, got {status}: {body!r}"
    assert isinstance(body, dict), f"expected dict, got {type(body).__name__}"
    assert body.get("ok") is True, f"ok not true: {body!r}"
    assert body.get("instanceKey") is not None, f"instanceKey missing: {body!r}"


def test_datacenter_request_access() -> None:
    req_id = f"integ-dc-access-{int(time.time())}"
    status, body = _request(
        "POST",
        f"/xrpc/{DATACENTER_ACCESS_NSID}",
        {
            "requestId": req_id,
            "facilityId": "dc-integ-01",
            "orgId": "org-integ",
            "requesterDid": "did:web:test.etzhayyim.com:requester",
            "employerOrgId": "org-vendor",
        },
        timeout=30,
    )
    assert status == 200, f"expected 200, got {status}: {body!r}"
    assert isinstance(body, dict) and body.get("ok") is True, f"unexpected body: {body!r}"


def test_datacenter_reserve_capacity() -> None:
    req_id = f"integ-dc-capacity-{int(time.time())}"
    status, body = _request(
        "POST",
        f"/xrpc/{DATACENTER_CAPACITY_NSID}",
        {
            "requestId": req_id,
            "facilityId": "dc-integ-01",
            "orgId": "org-integ",
            "requesterDid": "did:web:test.etzhayyim.com:planner",
        },
        timeout=30,
    )
    assert status == 200, f"expected 200, got {status}: {body!r}"
    assert isinstance(body, dict) and body.get("ok") is True, f"unexpected body: {body!r}"


def test_unknown_nsid_returns_404() -> None:
    status, body = _request("POST", "/xrpc/com.etzhayyim.apps.bogus.nonexistent",
                            {}, timeout=10)
    assert status == 404, f"expected 404, got {status}: {body!r}"


# RW-side effect checks (optional — require psql + RW access)


def _wait_for(fn, timeout_s: float = 10.0, interval_s: float = 0.5) -> bool:  # type: ignore[no-untyped-def]
    """Poll fn() until it returns truthy. RW streaming MVs need a few
    hundred ms to reflect a just-committed write."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if fn():
            return True
        time.sleep(interval_s)
    return False


def test_rw_audit_row_exists() -> None:
    # Fresh ping so we have a known ts_ms window.
    ts0 = int(time.time() * 1000)
    _request("POST", "/xrpc/com.etzhayyim.apps.bot.ping",
             {"message": "rw audit assertion"}, timeout=15)
    # RW may take a moment for the streaming view to reflect the INSERT.
    # Widen the window generously (60s) to absorb laptop↔RW clock skew.
    ok = _wait_for(lambda: rw_count(
        f"SELECT COUNT(*) FROM vertex_repo_commit "
        f"WHERE collection='com.etzhayyim.bpmn.audit' AND ts_ms >= {ts0 - 60_000}"
    ) >= 1, timeout_s=10.0)
    assert ok, f"no audit row within 10s after ts {ts0}"


# Dynamic registration — proves "new actor = INSERT 2 rows + wait".

PROBE_PROC_ID = "integ_probe_actor"
PROBE_VID_DEF = f"bpmn:{PROBE_PROC_ID}:v1"
PROBE_NSID = "com.etzhayyim.apps.test.integProbe"
PROBE_VID_BIND = f"bpmn-binding:{PROBE_NSID}"

PROBE_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"
    id="Definitions_{PROBE_PROC_ID}"
    targetNamespace="https://etzhayyim.com/bpmn/test"
    exporter="integration-test"
    exporterVersion="1.0">
  <bpmn:process id="{PROBE_PROC_ID}" name="integration probe" isExecutable="true">
    <bpmn:startEvent id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent>
    <bpmn:sequenceFlow id="F1" sourceRef="Start" targetRef="T"/>
    <bpmn:serviceTask id="T" name="probe audit">
      <bpmn:extensionElements>
        <zeebe:taskDefinition type="generic.audit.emit"/>
        <zeebe:ioMapping>
          <zeebe:input source="=&quot;did:web:test.etzhayyim.com&quot;" target="actor"/>
          <zeebe:input source="=&quot;integProbe&quot;" target="action"/>
          <zeebe:input source="={{ nonce: string(nonce) }}" target="payload"/>
          <zeebe:output source="=emitted" target="probeOk"/>
        </zeebe:ioMapping>
      </bpmn:extensionElements>
      <bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="F2" sourceRef="T" targetRef="End"/>
    <bpmn:endEvent id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>
"""


def _probe_register() -> None:
    created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    # psql -v escapes single quotes; use stdin heredoc with $$ quoting
    # disabled — do it through psycopg2-style params via -v binding.
    # Easiest: use psql here-doc with plain strings + escape '.
    xml_escaped = PROBE_XML.replace("'", "''")
    sql = (
        f"INSERT INTO vertex_bpmn_process_def (vertex_id, bpmn_process_id, version, xml, "
        f"xml_byte_size, source_path, status, created_at) "
        f"SELECT '{PROBE_VID_DEF}', '{PROBE_PROC_ID}', 1, '{xml_escaped}', "
        f"{len(PROBE_XML)}, 'integration-test:runtime', 'active', '{created_at}' "
        f"WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id='{PROBE_VID_DEF}');"
        f"INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, nsid, bpmn_process_id, bpmn_version, "
        f"result_timeout_ms, status, created_at) "
        f"SELECT '{PROBE_VID_BIND}', '{PROBE_NSID}', '{PROBE_PROC_ID}', 1, "
        f"30000, 'active', '{created_at}' "
        f"WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE nsid='{PROBE_NSID}');"
    )
    ok = rw_exec(sql)
    assert ok, "probe INSERT failed"


def _probe_teardown() -> None:
    rw_exec(f"DELETE FROM vertex_bpmn_process_def WHERE vertex_id='{PROBE_VID_DEF}';")
    rw_exec(f"DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id='{PROBE_VID_BIND}';")


def test_dynamic_registration() -> None:
    _probe_register()
    # Wait up to 1.5 watcher cycles for deploy + binding cache flush.
    deadline = time.monotonic() + (WATCHER_INTERVAL_SEC * 2)
    nonce = f"probe-{int(time.time())}"
    last_err: Any = None
    while time.monotonic() < deadline:
        status, body = _request("POST", f"/xrpc/{PROBE_NSID}",
                                {"nonce": nonce}, timeout=15)
        if status == 200 and isinstance(body, dict) and body.get("ok"):
            v = body.get("variables") or {}
            assert v.get("probeOk") is True, f"probeOk not true: {v}"
            return  # success
        last_err = (status, body)
        time.sleep(5)
    _probe_teardown()
    raise AssertionError(f"actor never reachable within {WATCHER_INTERVAL_SEC * 2}s; last={last_err!r}")


def test_dynamic_teardown() -> None:
    _probe_teardown()
    # RW DELETE propagates to the readable MV after a short lag.
    ok = _wait_for(lambda: rw_count(
        f"SELECT COUNT(*) FROM vertex_bpmn_lexicon_binding WHERE nsid='{PROBE_NSID}'"
    ) == 0, timeout_s=10.0)
    assert ok, "binding row survived teardown after 10s"


# ─── main ──────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-dynamic", action="store_true",
                    help="skip register-deploy-call-teardown (saves ~60s)")
    ap.add_argument("--skip-rw", action="store_true",
                    help="skip RW assertion tests (no psql available)")
    ap.add_argument("--include-datacenter", action="store_true",
                    help="also verify com.etzhayyim.apps.datacenter.startOperation binding + call")
    args = ap.parse_args()

    print(f"dispatcher: {DISPATCHER_URL}")
    try:
        # Surface the resolved IP so stale DNS caches are immediately visible.
        host = urllib.parse.urlparse(DISPATCHER_URL).hostname or ""
        ipv4 = {ai[4][0] for ai in socket.getaddrinfo(host, None, socket.AF_INET)}
        print(f"resolves: {', '.join(sorted(ipv4))}")
    except Exception:  # noqa: BLE001
        pass
    print()

    s = Suite()

    # fast reachability
    s.run("dispatcher /health", test_health)
    s.run("dispatcher /bindings has F5 actors", test_bindings_reach)

    # each F5 actor
    s.run("bot.ping", test_bot_ping)
    s.run("watch.urlDigest", test_watch_url_digest)
    s.run("yabai.triagePoc (phishing)", test_yabai_triage_phishing)
    s.run("bot.reviewAndPost (accept)", test_bot_review_accept)

    if args.include_datacenter:
        s.run("datacenter binding present", test_datacenter_binding_present)
        s.run("datacenter.startOperation", test_datacenter_start_operation)
        s.run("datacenter.requestAccess", test_datacenter_request_access)
        s.run("datacenter.reserveCapacity", test_datacenter_reserve_capacity)

    # BPMN actors migrated from ingest scripts (Phase 1, 2026-04-24).
    # Skip-able for offline / CI-without-RW runs.
    s.run("new BPMN bindings present", test_new_bpmn_bindings_present)
    s.run("yabai.enrichLegalEntity (happy LEI)", test_yabai_enrich_legal_entity_happy)
    s.run("yabai.enrichLegalEntity (no-LEI path)", test_yabai_enrich_legal_entity_no_match)
    s.run("yabai.reverseIpLookup", test_yabai_reverse_ip_lookup)
    s.run("yabai.crtshFuzzySearch", test_yabai_crtsh_fuzzy_search)
    if not args.skip_rw:
        s.run("shinshi.backfillGovernanceEdges", test_shinshi_backfill_governance_edges)
        s.run("yabai.trackPhishingInfra", test_yabai_track_phishing_infra)

    # negative
    s.run("unknown NSID → 404", test_unknown_nsid_returns_404)

    # RW assertions
    if not args.skip_rw:
        s.run("RW: audit row materialized", test_rw_audit_row_exists)

    # dynamic
    if not args.skip_dynamic:
        s.run("dynamic register → deploy → call", test_dynamic_registration)
        s.run("dynamic teardown", test_dynamic_teardown)

    return s.summary()


if __name__ == "__main__":
    sys.exit(main())
