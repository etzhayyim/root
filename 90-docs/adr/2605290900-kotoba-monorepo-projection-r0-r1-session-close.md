---
id: adr-2605290900-kotoba-monorepo-projection-r0-r1-session-close
title: "ADR-2605290900: kotoba monorepo projection R0+R1 session close — substrate live, Rider deferred, Kubo repaired"
status: accepted
doc_type: adr
topic: kotoba-monorepo-projection
authoritative: true
last_verified: 2026-05-29
priority: 4.5
axis: closure
weight: 0.30
priority_note: "Closure ADR for the 2026-05-28→29 session. Records: subrepo pull a673a8ce6 + LiteLLM patch + ADR-2605281700 R0 schema + ADR-2605281800 R1 ingest tool + ADR-2605281900 Rider reconciliation + first live 473-ADR ingest + 473/473 Kubo pinned + Kubo datastore corruption diagnosed and repaired. Punch-list for next operator."
authoritative_for:
  - 2026-05-28→29 kotoba session execution record
depends_on:
  - adr-2605281700-kotoba-content-addressed-monorepo-projection
  - adr-2605281800-kotoba-monorepo-projection-r1-adr-corpus-ingest
  - adr-2605281900-kotoba-subrepo-charter-rider-reconciliation
related:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
supersedes: []
superseded_by: []
---

# ADR-2605290900: kotoba monorepo projection R0+R1 session close

**Status**: accepted
**Date**: 2026-05-29
**Deciders**: Jun Kawasaki

# Context

Two-day session (2026-05-28 → 2026-05-29 JST) drove the kotoba subrepo from the prior `4cbb27747` pull state to a live, content-addressed projection of the etzhayyim monorepo's ADR corpus. This ADR closes the wave, documents what landed, and writes the punch-list.

# Decision

This is an **accepted closure record**, not a design change. State at close:

## 5.1 Landed commits (chronological)

| Commit | Subject |
|---|---|
| `5e05ac98f` | `git subrepo pull (merge) 40-engine/kotoba` — upstream `a673a8ce6` (+19176 / −14142, 262 files; new `kotoba-cli` crate, IPFS-primary `kotoba-store` redesign, `KuboBlockStore` replaces `IrohBlockStore`, all per-crate NOTICE + CHARTER-RIDER.md removed by upstream) |
| `3beff8bdf` | `charter-rider: reapply NOTICE + Rider symlinks to 40-engine/kotoba (21 dirs)` (later reverted) |
| `a4bb5cf89` | Revert of `3beff8bdf` per user "remote 優先" directive |
| `c847ef5d9` | **ADR-2605281700**: R0 schema for kotoba content-addressed monorepo projection (D1-D4 invariants, predicate vocabulary, IRI scheme, 7-phase rollout) |
| `559ded032` | **ADR-2605281800** R1 ingest tool spec + Python implementation + **ADR-2605281900** Rider reconciliation + LiteLLM `KOTOBA_INFERENCE_API_KEY` patch (`40-engine/kotoba/crates/kotoba-llm/src/http_infer.rs`) |
| `074508838` | R1 first live run: 473 ADRs ingested with real Kubo CIDs (1.2 s wall) |
| `12501b579` | `git subrepo push 40-engine/kotoba` — LiteLLM patch shipped to upstream `etzhayyim/kotoba@17e30d9db5` |

All pushed to `origin/main`.

## 5.2 Live substrate state at close

- **kotoba server**: PID/task `bh13vox55`, listening on `0.0.0.0:4080`, `TieredBlockStore<BudgetedMemory, KuboIpfs>` active, `KSE Journal + Vault + SecureVault` block-store persistent, libp2p QUIC + GossipSub + Kademlia
- **Local Kubo** (v0.41.0, `/Volumes/260317/etzhayyim/ipfs-data`): healthy after datastore repair (see §5.4), 751 recursive pins total, of which 473 are ADR content CIDs
- **NDJSON**: `90-docs/_registry/kotoba-quads.ndjson` carries 6,564 quads over 473 ADRs at commit `074508838`. Subject IRI scheme `adr:<10-digit-id>`, graph `kotoba:graph:etzhayyim-root`
- **Upstream kotoba** (`github.com/etzhayyim/kotoba@main`): at `17e30d9db5...`, includes `KOTOBA_INFERENCE_API_KEY` auth support (sent as `Authorization: Bearer ...`); unblocks LiteLLM master-key auth on the etzhayyim Murakumo gateway

## 5.3 ADR-2605281700 D1-D4 invariants confirmed in production

- **D1 (file SoT)**: git remains the canonical edit surface; kotoba never wrote back
- **D2 (kotoba read-only projection)**: ingest tool is the only write path, file → kotoba one-direction
- **D3 (same CID across IPFS / DataLad / kotoba)**: verified — `bafybeih7jcrtuytptjly2as...` returns block via Kubo `block/stat` (Size: 30772) and same CID is reachable via kotoba `KuboBlockStore` cold tier
- **D4 (deterministic re-ingest)**: `--dry-run` placeholders vs `--live` run produced identical subject/predicate sets, only `hasCid` objects differed (placeholder → real CID), `ingestRun` provenance differs by `gitSha` + `utc_iso`

## 5.4 Operational incident — Kubo datastore I/O corruption (resolved)

During first `pin/add` smoke after live ingest, Kubo returned:

```
pin: write /Volumes/260317/etzhayyim/ipfs-data/datastore/000013.log: input/output error
```

`df` showed the volume mount healthy (926 Gi total / 868 Gi free) — corruption was internal to Kubo's flatfs/badger datastore, not disk hardware. User re-seated the disk (no effect on the corrupted log file).

Recovery sequence:
1. `IPFS_PATH=/Volumes/260317/etzhayyim/ipfs-data ipfs shutdown` — graceful API shutdown
2. PID exited after ~2 s
3. `ipfs repo verify` — completed clean, no non-progress output
4. `nohup ipfs daemon` restart, `Daemon is ready` log line
5. Single `pin/add` smoke: `{"Pins":[...]}` returned (was returning I/O error before)
6. Bulk `pin/add` over all 473 hasCid CIDs: **473 / 473 succeeded, 0 failed**, recursive pin count 278 → 751

**Root cause**: CLI's default `~/.ipfs` IPFS_PATH did not match the actual daemon path `/Volumes/260317/etzhayyim/ipfs-data`, masking the issue (earlier `ipfs shutdown` reported "daemon not running" while a daemon was actually live on port 5001). `repo verify` with the correct path cleared the corruption window without data loss.

# Consequences

## 6.1 What this session unlocked

- **ADR cross-reference queries** become a Datalog read: `(?adr, dependsOn, adr:<X>)` over `kotoba:graph:etzhayyim-root`. The static `e7m verify` grep-based lints (currently iter-30..70 audit substrate, ADR-2605270735) can migrate to kotoba queries at R5
- **Content-addressed ADR distribution** via IPFS pin: any IPFS node anywhere can `ipfs cat bafybeih7jcrtuytptjly2as...` and get the ADR-2604231328 text byte-for-byte
- **Provenance audit trail**: each ingest run emits a `(ingestRun, gitSha, …)` triple, so the canonical CID of any ADR can be tied back to the git revision that produced it
- **LiteLLM master-key path** is open upstream — any kotoba node operator can set `KOTOBA_INFERENCE_API_KEY=sk-...` and route inference through a LiteLLM gateway with auth (ADR-2605215000 Murakumo-only context)

## 6.2 Punch-list for next operator

1. **R1.5 ADR + CACAO signing implementation** (NDJSON → kotoba server via `quad.create` XRPC). Server requires `cacao_b64` field, no dev bypass. Needs DID key management + CACAO chain construction client-side. Separate ADR + multi-hour scope
2. **ADR-2605281900 Council Lv6+ ratification path** (Path A §3.4 carve-out amendment recommended). Earliest after Bootstrap Council Seat 2-5 RFP close 2026-06-19
3. **ADR ID 4-way collision on `2605263800`** — `baien-ameno-r1b` / `biomethane-d-gate` / `corporate-disclosure` / `shidemori` all share the same minute-precision ID. Cleanup requires renaming 3 of the 4 + updating internal `id:` front-matter + README table + deps.toml + grep-and-patch cross-references in other ADRs. Separate cleanup task (substantial scope creep)
4. **30 ADRs skipped by ingest** due to YAML parse errors in front matter (backticks, unescaped colons). Manual fix per file or stricter front-matter validator at PR time
5. **launchctl `com.etzhayyim.kubo` unit repair** — `launchctl list | grep kubo` shows status `-	78	com.etzhayyim.kubo` (last exit code 78). Kubo now runs via `nohup ipfs daemon &` (foreground/disowned), not under launchctl. After Mac reboot, the daemon will not auto-start until the unit is repaired. Operator action only
6. **Branded ADR ID convention enforcement** — add a lefthook hook that verifies `90-docs/adr/<id>-<slug>.md` filename id uniqueness against the existing corpus, preventing future collisions like §6.2.3 above

## 6.3 Risk

| Risk | Severity | Mitigation |
|---|---|---|
| Kubo datastore corruption recurs | Medium | Operator should consider migrating datastore to a local SSD (`IPFS_PATH=~/.ipfs ipfs init` + `ipfs repo migrate`) — out of session scope |
| Upstream kotoba diverges further from monorepo's Charter Rider expectation | Medium | ADR-2605281900 Path A ratification (Council Lv6+ ≥3) before 2026-08-01 |
| 473 ADR pins disappear (Kubo GC + restart) | Low | Pins are explicit (`pin add`); only `repo gc` removes them, and `repo gc` is operator-initiated, not automatic |
| concurrent agent commits during session-close window | Low | Stash discipline applied; 2 stashes preserved (deps.toml/2605261800 WIP, 2605281950+CLAUDE.md WIP) |

# Alternatives Considered

This is a closure ADR. No alternatives — the work landed as it landed. The 4-ADR family (R0/R1/Rider/Closure) is the canonical record for this wave.

# References

- ADR-2605281700 (R0 schema)
- ADR-2605281800 (R1 ingest tool)
- ADR-2605281900 (Charter Rider reconciliation)
- ADR-2605262130 (kotoba storage substrate unification — parent substrate ADR)
- ADR-2605215000 (Murakumo-only inference — bounds LiteLLM patch context)
- ADR-2605192200 (Charter Rider v2.0 — invariant under reconciliation)
- ADR-2605262200 (procedural precedent for "Founder Lv7+ emergency auth explicitly NOT taken")
- Commits: `5e05ac98f` / `3beff8bdf` / `a4bb5cf89` / `c847ef5d9` / `559ded032` / `074508838` / `12501b579`
- Upstream kotoba commit: `17e30d9db5...` (`github.com/etzhayyim/kotoba@main`)
- Local Kubo: v0.41.0 (Homebrew), repo `/Volumes/260317/etzhayyim/ipfs-data`, 751 recursive pins at close
- NDJSON: `90-docs/_registry/kotoba-quads.ndjson` (6,564 quads / 473 ADRs at HEAD `074508838`)
