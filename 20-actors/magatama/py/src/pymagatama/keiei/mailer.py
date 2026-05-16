"""keiei 24h auto-disclose mailer.

Per ADR 2605101200 §4 hard rule: "Every Class B decision executed by a
primary-mode AI-CXO is appended to `_working/keiei/CXO-LEDGER.md` and
emailed to CEO within 24h via `microsoft.gftd.ai sendMail` (internal direct)."

This module is the disclosure half of that rule. Scan ledger → find
unsent primary-mode Class B rows → format batched email → send via XRPC
`ai.gftd.apps.microsoft.sendMail` → persist seq watermark.

Run periodically (hourly via launchd / cron / manual). Idempotent:
re-running without new rows is a cheap no-op.

Entry point: `python -m pymagatama.keiei.mailer [--dry-run]`.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .leader import get_leader
from .roles import ROLES, CEO_EMAIL


# ---------------------------------------------------------------------------
# Defaults — overridable via env or CLI.
# ---------------------------------------------------------------------------

DEFAULT_LEDGER_PATH = Path(os.environ.get(
    "KEIEI_LEDGER_PATH",
    str(Path(__file__).resolve().parents[6] / "_working" / "keiei" / "CXO-LEDGER.md"),
))
DEFAULT_STATE_PATH = Path(os.environ.get(
    "KEIEI_MAILER_STATE_PATH",
    str(Path(__file__).resolve().parents[6] / "_working" / "keiei" / "CXO-MAILER-STATE.json"),
))
DEFAULT_XRPC_URL = os.environ.get(
    "KEIEI_MAILER_XRPC_URL",
    "https://microsoft.gftd.ai/xrpc/ai.gftd.apps.microsoft.sendMail",
)
DEFAULT_RECIPIENT = os.environ.get("KEIEI_MAILER_RECIPIENT", CEO_EMAIL)
DEFAULT_FROM_UPN = os.environ.get("KEIEI_MAILER_FROM_UPN", "")  # empty → server default
DEFAULT_TOKEN_ENV = "KEIEI_MAILER_TOKEN"  # bearer token from `gftd agent-token`
HTTP_TIMEOUT_SEC = float(os.environ.get("KEIEI_MAILER_TIMEOUT_SEC", "30"))
STATE_VERSION = 1


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LedgerRow:
    seq: int
    date: str
    role: str
    decision_class: str
    summary: str
    decided_by: str
    escalated_to: str
    artefact: str


@dataclass
class MailerState:
    last_emailed_seq: int = 0
    last_emailed_at: str = ""           # ISO-8601 UTC
    version: int = STATE_VERSION
    history: list[dict] = field(default_factory=list)

    def to_json(self) -> dict:
        return {
            "version": self.version,
            "last_emailed_seq": self.last_emailed_seq,
            "last_emailed_at": self.last_emailed_at,
            "history": self.history[-20:],   # keep last 20 batches
        }

    @classmethod
    def from_json(cls, raw: dict) -> "MailerState":
        return cls(
            last_emailed_seq=int(raw.get("last_emailed_seq", 0)),
            last_emailed_at=str(raw.get("last_emailed_at", "")),
            version=int(raw.get("version", STATE_VERSION)),
            history=list(raw.get("history") or []),
        )


# ---------------------------------------------------------------------------
# Ledger parsing — markdown pipe-table written by lsp_server.ledger_append.
# ---------------------------------------------------------------------------

_ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|")


_ESC_SENTINEL = "\x00PIPE\x00"


def _split_pipe_row(line: str) -> list[str]:
    """Split a markdown pipe-row, respecting `\\|` escapes inserted by
    `lsp_server.ledger_append`. Returns trimmed cell values."""
    encoded = line.replace("\\|", _ESC_SENTINEL)
    inner = encoded.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|"):
        inner = inner[:-1]
    return [c.strip().replace(_ESC_SENTINEL, "|") for c in inner.split("|")]


def parse_ledger(path: Path) -> list[LedgerRow]:
    if not path.exists():
        return []
    rows: list[LedgerRow] = []
    for line in path.read_text().splitlines():
        if not _ROW_RE.match(line):
            continue
        parts = _split_pipe_row(line)
        if len(parts) < 8:
            continue
        try:
            seq = int(parts[0])
        except ValueError:
            continue
        rows.append(LedgerRow(
            seq=seq,
            date=parts[1],
            role=parts[2],
            decision_class=parts[3],
            summary=parts[4],
            decided_by=parts[5],
            escalated_to=parts[6],
            artefact=parts[7],
        ))
    return rows


# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------

def load_state(path: Path) -> MailerState:
    if not path.exists():
        return MailerState()
    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError:
        return MailerState()
    return MailerState.from_json(raw)


def save_state(path: Path, state: MailerState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_json(), indent=2, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Pending disclosure detection
# ---------------------------------------------------------------------------

def primary_role_ids() -> frozenset[str]:
    """Roles that operate in primary mode — only those auto-disclose.

    Shadow-mode Class B rows go through human-confirm at gate time; they
    do not need a 24h disclosure mail (the human is already in the loop).
    """
    return frozenset(r.id for r in ROLES if r.mode == "primary")


def find_pending(
    rows: Iterable[LedgerRow],
    state: MailerState,
    *,
    primary_ids: frozenset[str] | None = None,
) -> list[LedgerRow]:
    """Class B rows from primary-mode roles with seq > last_emailed_seq."""
    pids = primary_ids if primary_ids is not None else primary_role_ids()
    return [
        r for r in rows
        if r.seq > state.last_emailed_seq
        and r.decision_class == "B"
        and r.role in pids
    ]


# ---------------------------------------------------------------------------
# Email formatting
# ---------------------------------------------------------------------------

def _truncate(s: str, n: int = 240) -> str:
    s = s.strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def format_email(pending: list[LedgerRow], *, now_iso: str) -> tuple[str, str, str]:
    """Return (subject, body_text, body_html).

    Subject is concise; body is plain text + a minimal HTML mirror so Graph
    sendMail can deliver either depending on `bodyHtml`/`bodyText` choice.
    """
    n = len(pending)
    today = now_iso[:10]
    subject = f"[keiei] {n} Class B disclosure{'s' if n != 1 else ''} — {today}"

    header = (
        "amanomibashira AI-CXO Class B auto-disclosure (24h窓, ADR 2605101200).\n"
        f"Reporting period: up to {now_iso} (UTC).\n"
        f"New autonomous Class B decisions since last disclosure: {n}\n"
        "Per ADR 2605101200 §4: primary-mode Class B = autonomous + 24h disclose. "
        "Silence within 24h = ratification.\n"
    )

    table_text = (
        "\n| seq | date | role | summary | artefact |\n"
        "|---|---|---|---|---|\n"
    )
    for r in pending:
        table_text += (
            f"| {r.seq} | {r.date} | {r.role} | "
            f"{_truncate(r.summary)} | {_truncate(r.artefact, 160)} |\n"
        )

    footer = (
        "\nFull ledger: _working/keiei/CXO-LEDGER.md\n"
        "Object / escalate: reply to this thread or message AI-CEO.\n"
        "— keiei-mailer (auto-generated; do not edit ledger rows)\n"
    )

    body_text = header + table_text + footer

    # Minimal HTML — Outlook renders both; HTML helps in the inbox preview.
    rows_html = "".join(
        "<tr>"
        f"<td>{r.seq}</td><td>{r.date}</td><td>{r.role}</td>"
        f"<td>{_truncate(r.summary)}</td><td>{_truncate(r.artefact, 160)}</td>"
        "</tr>"
        for r in pending
    )
    body_html = (
        f"<p>amanomibashira AI-CXO Class B auto-disclosure "
        f"(24h窓, <a href=\"#\">ADR 2605101200</a>).</p>"
        f"<p>Reporting period up to <code>{now_iso}</code> (UTC). "
        f"<b>{n}</b> new decisions.</p>"
        f"<table border=\"1\" cellpadding=\"4\" cellspacing=\"0\">"
        f"<thead><tr><th>seq</th><th>date</th><th>role</th>"
        f"<th>summary</th><th>artefact</th></tr></thead>"
        f"<tbody>{rows_html}</tbody></table>"
        f"<p>Full ledger: <code>_working/keiei/CXO-LEDGER.md</code>. "
        f"Silence within 24h = ratification.</p>"
        f"<p style=\"color:#888;font-size:0.9em\">— keiei-mailer (auto)</p>"
    )

    return subject, body_text, body_html


# ---------------------------------------------------------------------------
# XRPC client
# ---------------------------------------------------------------------------

class MailerError(RuntimeError):
    """Raised when the XRPC sendMail call fails non-recoverably."""


def send_via_xrpc(
    *,
    xrpc_url: str,
    token: str,
    recipient: str,
    subject: str,
    body_text: str,
    body_html: str,
    from_upn: str = "",
    timeout: float = HTTP_TIMEOUT_SEC,
) -> dict:
    if not token:
        raise MailerError(
            "no bearer token. Set KEIEI_MAILER_TOKEN or pass --token. "
            "Mint via: gftd agent-token --lxm ai.gftd.apps.microsoft.sendMail "
            "--aud did:web:microsoft.gftd.ai --ttl 600"
        )

    payload: dict[str, object] = {
        "to": [recipient],
        "subject": subject,
        "bodyText": body_text,
        "bodyHtml": body_html,
        "importance": "normal",
    }
    if from_upn:
        payload["fromUpn"] = from_upn

    req = urllib.request.Request(
        xrpc_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8")
        except Exception:                                       # noqa: BLE001
            pass
        raise MailerError(f"XRPC {e.code}: {detail[:400]}") from e
    except urllib.error.URLError as e:
        raise MailerError(f"XRPC transport error: {e.reason}") from e
    except (TimeoutError, json.JSONDecodeError) as e:
        raise MailerError(f"XRPC client error: {type(e).__name__}: {e}") from e


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def _now_utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass
class RunResult:
    pending_count: int
    sent: bool
    dry_run: bool
    status: str = "no-op"          # "no-op" / "sent" / "drafted" / "dry-run" / "error"
    detail: str = ""
    new_watermark: int = 0


def run_once(
    *,
    ledger_path: Path = DEFAULT_LEDGER_PATH,
    state_path: Path = DEFAULT_STATE_PATH,
    xrpc_url: str = DEFAULT_XRPC_URL,
    recipient: str = DEFAULT_RECIPIENT,
    from_upn: str = DEFAULT_FROM_UPN,
    token: str = "",
    dry_run: bool = False,
    now_iso: str | None = None,
) -> RunResult:
    # Phase 4 leader gate: in a multi-replica k8s Deployment, only the
    # replica holding the writer lease may send disclosures and advance
    # the state watermark — otherwise we'd send N duplicate mails per
    # tick. Local dev (launchd / cron) always passes since LocalLeader
    # is always-leader.
    leader = get_leader()
    if not leader.is_leader():
        return RunResult(
            pending_count=0, sent=False, dry_run=dry_run,
            status="follower",
            detail=f"follower replica (identity={leader.identity()!r}); leader handles disclosure this tick",
            new_watermark=0,
        )

    rows = parse_ledger(ledger_path)
    state = load_state(state_path)
    pending = find_pending(rows, state)
    now = now_iso or _now_utc_iso()

    if not pending:
        return RunResult(
            pending_count=0, sent=False, dry_run=dry_run,
            status="no-op",
            detail=f"ledger={ledger_path} state.last_emailed_seq={state.last_emailed_seq}",
            new_watermark=state.last_emailed_seq,
        )

    subject, body_text, body_html = format_email(pending, now_iso=now)

    if dry_run:
        return RunResult(
            pending_count=len(pending), sent=False, dry_run=True,
            status="dry-run",
            detail=(
                f"would send to={recipient} subject={subject!r} "
                f"seqs={[r.seq for r in pending]}\n--- body_text ---\n{body_text}"
            ),
            new_watermark=max(r.seq for r in pending),
        )

    tok = token or os.environ.get(DEFAULT_TOKEN_ENV, "")
    try:
        resp = send_via_xrpc(
            xrpc_url=xrpc_url, token=tok, recipient=recipient,
            subject=subject, body_text=body_text, body_html=body_html,
            from_upn=from_upn,
        )
    except MailerError as e:
        return RunResult(
            pending_count=len(pending), sent=False, dry_run=False,
            status="error", detail=str(e),
            new_watermark=state.last_emailed_seq,
        )

    api_status = str(resp.get("status", ""))
    seqs = [r.seq for r in pending]
    new_watermark = max(seqs)

    # Only advance watermark on confirmed `sent` (or `drafted` for external —
    # but recipient is internal here, so we expect `sent`).
    if api_status == "sent":
        state.last_emailed_seq = new_watermark
        state.last_emailed_at = now
        state.history.append({
            "emailed_at": now, "seqs": seqs, "recipient": recipient,
            "status": api_status, "subject": subject,
        })
        save_state(state_path, state)
        return RunResult(
            pending_count=len(pending), sent=True, dry_run=False,
            status="sent",
            detail=f"seqs={seqs} resp={resp}",
            new_watermark=new_watermark,
        )

    # `drafted` for external recipient — record but do NOT advance watermark
    # (caller needs to approve + sendDraft, then we'll retry next tick).
    return RunResult(
        pending_count=len(pending), sent=False, dry_run=False,
        status=api_status or "unknown",
        detail=f"unexpected status, watermark not advanced. resp={resp}",
        new_watermark=state.last_emailed_seq,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="keiei-mailer",
        description="24h auto-disclose for primary-mode AI-CXO Class B decisions "
                    "(ADR 2605101200 §4).",
    )
    p.add_argument("--ledger", default=str(DEFAULT_LEDGER_PATH),
                   help="Path to CXO-LEDGER.md")
    p.add_argument("--state", default=str(DEFAULT_STATE_PATH),
                   help="Path to mailer state JSON")
    p.add_argument("--xrpc", default=DEFAULT_XRPC_URL,
                   help="XRPC sendMail endpoint")
    p.add_argument("--to", default=DEFAULT_RECIPIENT,
                   help=f"Recipient email (default: {DEFAULT_RECIPIENT})")
    p.add_argument("--from-upn", default=DEFAULT_FROM_UPN,
                   help="Sender UPN; empty → server DEFAULT_SENDER_UPN")
    p.add_argument("--token", default="",
                   help=f"Bearer token; falls back to ${DEFAULT_TOKEN_ENV}")
    p.add_argument("--dry-run", action="store_true",
                   help="Print what would be sent and exit without HTTP call")
    args = p.parse_args(argv)

    result = run_once(
        ledger_path=Path(args.ledger),
        state_path=Path(args.state),
        xrpc_url=args.xrpc,
        recipient=args.to,
        from_upn=args.from_upn,
        token=args.token,
        dry_run=args.dry_run,
    )

    print(
        f"[keiei-mailer] status={result.status} "
        f"pending={result.pending_count} sent={result.sent} "
        f"dry_run={result.dry_run} watermark={result.new_watermark}",
        file=sys.stderr,
    )
    if result.detail:
        print(result.detail, file=sys.stderr)

    if result.status == "error":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
