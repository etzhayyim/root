---
id: adr-2606161645-sukashi-fleet-continuous-operation-kotoba-native
title: "ADR-2606161645: sukashi fleet continuous operation (kotoba-native) — LaunchDaemon (A) + /loop driver (B)"
status: accepted
doc_type: adr
topic: sukashi-fleet-continuous
authoritative: true
last_verified: 2026-06-16
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 20-actors/sukashi/tools/fleet_drive.py
  - 20-actors/sukashi/tools/fleet_stage.py
  - 20-actors/sukashi/deploy
depends_on:
  - 2606071600
  - 2606071601
  - 2605192415
  - 2605312345
  - 2605215000
  - 2606121225
related:
  - 2606131800
supersedes: []
superseded_by: []
---

# ADR-2606161645: sukashi fleet continuous operation (kotoba-native)

**Status**: accepted (2026-06-16 — A = deploy artifacts committed (operator sudo step); B = live driver landed + proven against issachar)
**Date**: 2026-06-16
**Deciders**: Jun Kawasaki

# Context

The sukashi observatory was registered as a launchd cell (`SukashiObservatoryHeartbeatCell`,
ADR-2606071601 follow-up) and proven to RUN on a real fleet Mac mini (issachar) on demand
(`python3 ~/sukashi-run/cell.py` → verified kotoba commit-DAG). The remaining question was
**continuous** operation on the Murakumo Mac mini fleet.

Reconnaissance over Tailscale SSH (2026-06-16) surfaced the blocking fact: **the fleet Macs sit at
the login window with no Aqua GUI session** (`who` empty, `console-user=root`, `launchctl print
gui/501` → "Domain does not support specified action"). Consequences, verified on issachar /
benjamin / levi:

- a per-user **LaunchAgent cannot load** without an Aqua session — which is exactly why the
  canonical `kotodama-cell-runner` LaunchAgent is **not actually running on any node** (and why `uv`
  + the repo are absent: the execution layer was never provisioned);
- **`crontab` is TCC-blocked** from an SSH session (`Operation not permitted`);
- the k3s control plane (`jacob`) is offline.

So the canonical "LaunchAgent + uv cell-runner" path cannot be brought up from a bare SSH session.

# Decision

Provide **two kotoba-native paths** to continuous operation, and converge both on the kotoba Datom
log as the canonical record (ADR-2605312345).

**A — fleet LaunchDaemon (the headless fix; operator + sudo).**
`20-actors/sukashi/deploy/com.etzhayyim.sukashi-heartbeat.daemon.plist` is a **system-domain
LaunchDaemon** (not an Agent) — it runs headlessly, no GUI session required, solving the wall above.
It runs the pure-stdlib `cell.py` (no `uv`/venv) on `StartCalendarInterval` :42 as the tribe
`UserName`. Install is the operator's `sudo launchctl bootstrap system …` step (per `deploy/README.md`);
staging the actor to a node is `bb sukashi:fleet-stage` (git-archive + tar over Tailscale SSH).
(Alternative: enable **auto-login** at the console so an Aqua session exists, then the canonical
LaunchAgent cell-runner also works.)

**B — local driver + `/loop` (interim pseudo-daemon; works today, no console access).**
`20-actors/sukashi/tools/fleet_drive.py` (`bb sukashi:fleet-drive`) runs FROM an interactive machine
(the founder's mac, which HAS a GUI session). Each tick it resolves node IPs from `tailscale status`,
SSHes each sukashi-assigned node, runs the heartbeat, and **records each run as a `:fleet.run/*`
datom** (node · cell · cycle · head-cid · chain-ok · status · as-of) on a LOCAL kotoba ops Datom log
(`data/fleet-ops.kotoba.edn`, gitignored, append-only, tamper-evident via `verify_chain`). Pair with
`/loop 1h bb sukashi:fleet-drive` for continuity. The network leg + `tailscale status` are INJECTED,
so the loop is a pure function (offline tests, no wall clock → deterministic ops tx).

Constitutional posture holds: the SSH leg is observational/own-fleet (the member runs their OWN
actor on their OWN Macs); the heartbeat does **no live crawl** (G7 keeps acquisition gated); the
acquisition/driver legs are `.py` (the ingest.py I/O boundary, ADR-2606131800) while the analyzer is
`.cljc`; kotoba is canonical state throughout.

# Consequences

- **Proven**: `bb sukashi:fleet-drive` ran live against issachar (cycle 3 → `be2f80c63015c9c6`,
  status `:ok`, chain ok) and recorded the `:fleet.run/*` ops datom — B is operational today.
- A is committed but its `sudo` install is an operator step (I cannot reach the consoles / sudo).
- The honest fleet truth is now documented: the cell execution layer (launchd cell-runner AND k3s)
  is unprovisioned fleet-wide because the Macs have no GUI session; A (LaunchDaemon) or auto-login is
  the fix.
- Tests: `bb test:sukashi` green — python (invariant 31 / autorun 41 / crawl 9 / fleet-drive 7) +
  cljc analyzer (23 tests / 412 assert).

# Alternatives Considered

- **Per-user LaunchAgent over SSH** — rejected: requires an Aqua session the headless Macs lack.
- **crontab over SSH** — rejected: TCC-blocked (`Operation not permitted`).
- **Revive k3s (jacob) + deploy** — deferred: control plane offline; heavier than a LaunchDaemon for
  a single stdlib heartbeat.
- **Full canonical cell-runner bootstrap (uv + monorepo clone + uv sync + install.sh)** — deferred:
  large, needs the GUI-session/auto-login fix first anyway.

# References

- ADR-2606071600 / 2606071601 (sukashi observatory + worldwide crawler)
- ADR-2605192415 (Religious-Corp Daemon Architecture — Tier-1 launchd / cell-runner)
- ADR-2605312345 (kotoba Datom log = canonical state) · ADR-2605215000 (Murakumo-only)
- ADR-2606131800 (.py for I/O-coupled legs; .cljc for the analyzer)
- ADR-2606121225 (founder admin-merge governance)
