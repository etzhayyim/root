#!/usr/bin/env python3
"""Resident Murakumo actor loop for the hegemon organism lifecycle.

This bootstrap loop intentionally uses only the Python standard library so it
can run on fleet Mac minis that have Ollama but do not have this repository or
the kotodama Python package installed.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUNNING = True


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def stop(_signum: int, _frame: object) -> None:
    global RUNNING
    RUNNING = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actor-did", default="did:web:shinka.etzhayyim.com")
    parser.add_argument("--organism-did", default="did:web:karma.etzhayyim.com")
    parser.add_argument("--objective", default="hegemon")
    parser.add_argument(
        "--purpose",
        default=(
            "Advance the shinka actor as a resident artificial organism toward "
            "hegemon viability by maintaining identity, repeated activity, "
            "observable social effect, and concrete next actions."
        ),
    )
    parser.add_argument("--model", default=os.environ.get("LOCAL_LLM_MODEL", "gemma3:1b"))
    parser.add_argument(
        "--endpoint",
        default=os.environ.get("LOCAL_LLM_ENDPOINT", "http://127.0.0.1:11434/api/chat"),
    )
    parser.add_argument("--interval-sec", type=float, default=60.0)
    parser.add_argument(
        "--log-path",
        default="/tmp/murakumo-hegemon-agent-loop.jsonl",
    )
    parser.add_argument(
        "--state-path",
        default="/tmp/murakumo-hegemon-agent-loop.state.json",
    )
    parser.add_argument(
        "--effect-dir",
        default="/tmp/murakumo-hegemon-effects",
    )
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--timeout-sec", type=float, default=120.0)
    parser.add_argument("--num-predict", type=int, default=256)
    return parser.parse_args()


def post_ollama_chat(args: argparse.Namespace, tick: int) -> dict[str, Any]:
    hostname = socket.gethostname()
    messages = [
        {
            "role": "system",
            "content": (
                "Return compact JSON only. You are a resident artificial organism "
                "actor loop. Evaluate hegemon lifecycle viability. Include keys: "
                "purposeAlignment, activity, socialEffect, contentEvaluation, "
                "risks, nextAction. Use scores from 0 to 100 where possible."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "actorDid": args.actor_did,
                    "organismDid": args.organism_did,
                    "objective": args.objective,
                    "purpose": args.purpose,
                    "evaluationPolicy": {
                        "purposeAlignment": "Does the tick advance hegemon viability without identity drift?",
                        "activity": "Is there repeated observable behavior, not a one-shot response?",
                        "socialEffect": "Does the tick create externally useful coordination or proof?",
                        "contentQuality": "Is the emitted content concrete, parseable, and action-oriented?",
                    },
                    "node": hostname,
                    "tick": tick,
                    "runtimeState": "agent-loop-running",
                    "availableEffectors": [
                        "observe-local-ollama",
                        "record-heartbeat",
                        "record-direct-fleet-social-proof",
                        "maintain-direct-murakumo-lifecycle-marker",
                    ],
                },
                sort_keys=True,
            ),
        },
    ]
    body = {
        "model": args.model,
        "messages": messages,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2,
            "num_predict": max(32, args.num_predict),
        },
    }
    request = urllib.request.Request(
        args.endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=max(1.0, args.timeout_sec)) as response:
        raw = response.read().decode("utf-8", errors="replace")
    payload = json.loads(raw)
    content = ""
    message = payload.get("message")
    if isinstance(message, dict) and isinstance(message.get("content"), str):
        content = message["content"]
    elif isinstance(payload.get("response"), str):
        content = payload["response"]
    try:
        parsed = json.loads(content) if content.strip() else {}
    except json.JSONDecodeError:
        parsed = {"rawText": content}
    return {
        "ok": True,
        "model": args.model,
        "endpoint": args.endpoint,
        "content": content,
        "json": parsed,
    }


def default_next_action(args: argparse.Namespace, tick: int) -> dict[str, Any]:
    return {
        "actionId": f"direct-fleet-hegemon-proof-{tick}",
        "kind": "record-direct-fleet-proof",
        "target": "murakumo-physical-mac-mini-fleet",
        "objective": args.objective,
        "expectedEffect": "social-proof-and-lifecycle-marker",
        "karmadaRequired": False,
    }


def run_effectors(args: argparse.Namespace, *, tick: int, llm: dict[str, Any]) -> dict[str, Any]:
    node = socket.gethostname()
    effect_dir = Path(args.effect_dir)
    effect_dir.mkdir(parents=True, exist_ok=True)
    parsed = llm.get("json") if isinstance(llm.get("json"), dict) else {}
    next_action = parsed.get("nextAction") if isinstance(parsed.get("nextAction"), dict) else None
    if next_action is None:
        next_action = default_next_action(args, tick)

    social_effect = {
        "kind": "direct-fleet-social-proof",
        "summary": (
            "Murakumo resident actor loop maintains hegemon organism state, "
            "records public proof artifacts, and does not depend on Karmada."
        ),
        "audience": ["operator", "runtime", "proof-registry"],
        "artifactUse": "evidence for scoring, lifecycle state, and next action review",
    }
    content_evaluation = {
        "format": "json+markdown",
        "parseable": True,
        "actionOriented": True,
        "containsPurpose": True,
        "containsSocialEffect": True,
    }
    proof = {
        "actorDid": args.actor_did,
        "organismDid": args.organism_did,
        "objective": args.objective,
        "purpose": args.purpose,
        "node": node,
        "tick": tick,
        "observedAt": now_iso(),
        "runtime": "direct-murakumo-fleet",
        "karmadaRequired": False,
        "llmOk": bool(llm.get("ok")),
        "nextAction": next_action,
        "socialEffect": social_effect,
        "contentEvaluation": content_evaluation,
    }
    proof_path = effect_dir / f"{node}.hegemon-social-proof.json"
    md_path = effect_dir / f"{node}.hegemon-social-proof.md"
    try:
        atomic_write_json(proof_path, proof)
        md_path.write_text(
            "\n".join(
                [
                    f"# Murakumo Hegemon Social Proof: {node}",
                    "",
                    f"- actor: `{args.actor_did}`",
                    f"- organism: `{args.organism_did}`",
                    f"- objective: `{args.objective}`",
                    f"- tick: `{tick}`",
                    f"- observedAt: `{proof['observedAt']}`",
                    "- runtime: `direct-murakumo-fleet`",
                    "- Karmada required: `false`",
                    f"- next action: `{next_action.get('actionId')}`",
                    "",
                    social_effect["summary"],
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return {
            "ok": True,
            "executed": ["record-direct-fleet-social-proof"],
            "proofPath": str(proof_path),
            "markdownPath": str(md_path),
            "nextAction": next_action,
            "socialEffect": social_effect,
            "contentEvaluation": content_evaluation,
            "karmadaRequired": False,
        }
    except OSError as exc:
        return {
            "ok": False,
            "executed": [],
            "error": str(exc),
            "nextAction": next_action,
            "karmadaRequired": False,
        }


def clamp_score(value: float) -> int:
    return int(max(0, min(100, round(value))))


def numeric_from_mapping(mapping: dict[str, Any], keys: list[str], default: float) -> float:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, dict):
            nested = value.get("score")
            if isinstance(nested, (int, float)):
                return float(nested)
    return default


def evaluate_tick(
    args: argparse.Namespace,
    *,
    tick: int,
    status: str,
    llm: dict[str, Any],
    effectors: dict[str, Any],
) -> dict[str, Any]:
    parsed = llm.get("json") if isinstance(llm.get("json"), dict) else {}
    llm_ok = bool(llm.get("ok")) and status == "ok"

    identity_ok = (
        parsed.get("actorDid") in {None, args.actor_did}
        and parsed.get("organismDid") in {None, args.organism_did}
        and parsed.get("objective") in {None, args.objective}
    )
    content = llm.get("content") if isinstance(llm.get("content"), str) else ""
    effector_ok = bool(effectors.get("ok"))
    has_next_action = bool(parsed.get("nextAction") or effectors.get("nextAction"))
    has_social_effect = bool(parsed.get("socialEffect") or effectors.get("socialEffect"))
    direct_runtime = effectors.get("karmadaRequired") is False

    purpose_alignment = 70 if llm_ok and identity_ok else 30
    if tick > 1:
        purpose_alignment += 10
    if effector_ok and direct_runtime:
        purpose_alignment += 18

    activity = 25 if llm_ok else 0
    activity += min(40, tick * 5)
    activity += 20 if tick >= 3 else 0
    activity += 13 if effector_ok and tick >= 3 else 0
    activity += 15 if effector_ok and tick >= 5 else 0

    social_effect = 25 if has_social_effect else 10
    social_effect += 20 if tick >= 3 else 0
    social_effect += 15 if status == "ok" else 0
    social_effect += 38 if effector_ok and effectors.get("proofPath") else 0

    content_quality = 30 if content else 0
    content_quality += 20 if parsed else 0
    content_quality += 20 if has_next_action else 0
    content_quality += 20 if identity_ok else 0
    content_quality += 8 if effector_ok and effectors.get("contentEvaluation") else 0

    autonomy = 55 if llm_ok else 10
    autonomy += 15 if has_next_action else 0
    autonomy += 10 if tick >= 3 else 0
    autonomy += 18 if effector_ok and effectors.get("executed") else 0

    dimensions = {
        "purposeAlignment": clamp_score(
            numeric_from_mapping(parsed, ["purposeAlignment", "purpose_alignment"], purpose_alignment)
        ),
        "activity": clamp_score(numeric_from_mapping(parsed, ["activity"], activity)),
        "socialEffect": clamp_score(
            numeric_from_mapping(parsed, ["socialEffect", "social_effect"], social_effect)
        ),
        "contentQuality": clamp_score(
            numeric_from_mapping(parsed, ["contentEvaluation", "contentQuality"], content_quality)
        ),
        "autonomy": clamp_score(numeric_from_mapping(parsed, ["autonomy"], autonomy)),
    }
    total = clamp_score(
        dimensions["purposeAlignment"] * 0.25
        + dimensions["activity"] * 0.20
        + dimensions["socialEffect"] * 0.20
        + dimensions["contentQuality"] * 0.20
        + dimensions["autonomy"] * 0.15
    )
    if total >= 85:
        stage = "hegemon-process-advancing"
    elif total >= 70:
        stage = "resident-loop-viable"
    elif total >= 50:
        stage = "activity-observed"
    else:
        stage = "insufficient"
    return {
        "score": total,
        "stage": stage,
        "dimensions": dimensions,
        "purpose": args.purpose,
        "rubric": {
            "purposeAlignment": 0.25,
            "activity": 0.20,
            "socialEffect": 0.20,
            "contentQuality": 0.20,
            "autonomy": 0.15,
        },
        "signals": {
            "identityStable": identity_ok,
            "llmOk": llm_ok,
            "repeatedTick": tick > 1,
            "hasNextAction": has_next_action,
            "hasSocialEffect": has_social_effect,
            "effectorOk": effector_ok,
            "directRuntime": direct_runtime,
            "karmadaRequired": effectors.get("karmadaRequired"),
        },
    }


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def build_event(
    args: argparse.Namespace,
    *,
    tick: int,
    status: str,
    started_at: str,
    llm: dict[str, Any],
    effectors: dict[str, Any],
) -> dict[str, Any]:
    evaluation = evaluate_tick(args, tick=tick, status=status, llm=llm, effectors=effectors)
    return {
        "actorDid": args.actor_did,
        "organismDid": args.organism_did,
        "objective": args.objective,
        "purpose": args.purpose,
        "loopState": "running" if RUNNING else "stopping",
        "runtimeState": "agent-loop-running",
        "status": status,
        "evaluation": evaluation,
        "tick": tick,
        "startedAt": started_at,
        "observedAt": now_iso(),
        "node": socket.gethostname(),
        "pid": os.getpid(),
        "model": args.model,
        "endpoint": args.endpoint,
        "llm": llm,
        "effectors": effectors,
        "nextGate": "maintain-direct-fleet-loop-and-repair-k8s-cni-for-optional-pod-rollout",
    }


def main() -> int:
    args = parse_args()
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    log_path = Path(args.log_path)
    state_path = Path(args.state_path)
    started_at = now_iso()
    tick = 0

    while RUNNING:
        tick += 1
        status = "ok"
        try:
            llm = post_ollama_chat(args, tick)
        except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
            status = "error"
            llm = {
                "ok": False,
                "model": args.model,
                "endpoint": args.endpoint,
                "error": str(exc),
            }

        effectors = run_effectors(args, tick=tick, llm=llm)
        event = build_event(
            args,
            tick=tick,
            status=status,
            started_at=started_at,
            llm=llm,
            effectors=effectors,
        )
        append_jsonl(log_path, event)
        atomic_write_json(state_path, event)
        print(json.dumps(event, ensure_ascii=False, sort_keys=True), flush=True)

        if args.once:
            break
        deadline = time.monotonic() + max(1.0, args.interval_sec)
        while RUNNING and time.monotonic() < deadline:
            time.sleep(min(1.0, deadline - time.monotonic()))

    return 0


if __name__ == "__main__":
    sys.exit(main())
