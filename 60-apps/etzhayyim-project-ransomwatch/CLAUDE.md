# etzhayyim-project-ransomwatch — Public TLP:WHITE Ransomware Group Leak-Site Monitor

> Sanitized public-only feed. Tracks active ransomware groups + new
> victim posts via content-hash diff. **TLP:WHITE only — no victim PII.**

`ransomwatch.etzhayyim.com` (nanoid: `r4ns0w4t01`) — Public passive OSINT
on ransomware group leak sites. Sister project to `public-malak` (which
publishes a sanitized ad-transparency feed).

## Tranche F migration status

Per vendor `etzhayyim/etzhayyim-root` deps.toml
`tranche-f-post-freeze-7-actors-audit-2026-05-21`: 3-axis OR-test all
clean (TLP:WHITE public OSINT, no victim PII, no commerce) → confirmed
etzhayyim MOVE TARGET. The vendor `kotodama.jsonld` already declared
`profile.operator = "etzhayyim"`, so the move just formalizes the
existing intent.

Phase 1 (this commit): scaffold mirror + 4 lexicons. Worker + LangGraph
pod rewrite is Phase 2 follow-up (deferred per user direction 2026-05-21
— kotoba quality / runtime fixes are post-migration).

## Identity

| Property | Value |
|---|---|
| Domain | `ransomwatch.etzhayyim.com` |
| Primary DID | `did:web:ransomwatch.etzhayyim.com` |
| nanoid | `r4ns0w4t01` |
| performerType | service |
| NSID prefix | `com.etzhayyim.apps.ransomwatch.*` |
| Tier | T3 (edge dispatcher) |
| TLP | WHITE only (AMBER/RED dropped before exposure) |

## Lexicons (4)

`00-contracts/lexicons/com/etzhayyim/apps/ransomwatch/`:

- `seedGroup` (procedure) — register a ransomware group as a monitoring target
- `listGroups` (query) — list active monitored groups
- `listPosts` (query) — list sanitized post observations (TLP:WHITE)
- `getStats` (query) — coverage + observation counters

## Substrate (etzhayyim — kotoba per ADR-2605172000)

| Concern | Vendor (etzhayyim.com) | etzhayyim (this repo) |
|---|---|---|
| Write path | `createKyselyDb` → RisingWave `vertex_ransomwatch_*` | PDS XRPC `com.atproto.repo.createRecord` against `ai.etzhayyim.apps.ransomwatch.*` (Phase 2 rewrite) |
| Read path | Hyperdrive + Kysely | `mst-projector` indexed views (Phase 2) |
| Orchestrator | LangServer pod (vendor in-cluster `ransomwatch-langgraph.mitama-udf.svc.cluster.local:8000`) | LangServer pod (etzhayyim Murakumo, Phase 2 rewrite) |
| Content sanitization | TLP filter, victim PII drop | Same — TLP filter is structural, no change |

## Governance

- TLP WHITE only. AMBER/RED indicators are not exposed at this surface.
- No victim PII — only sector / country / impact descriptors.
- All sources are public leak-site URLs; ingest is passive OSINT.
- Per ADR-2605172400 catalog: this actor is in the same A-group as
  `public-malak` (sanitized public security feed).

## Cross-actor (planned)

- `malak` (vendor parent) — TLP-filtered indicators flow downstream
  here. ransomwatch shows only the WHITE projection above the
  TLP-filter boundary; vendor `malak` retains AMBER/RED case work.
- `public-malak` — sibling sanitized public feed (ad transparency).
- `tia` — account protection feed.
- `news` — security news consumption.

## Substrate-boundary notes

Per `etzhayyim/root/CLAUDE.md` §"Substrate boundary":
- This project is kotoba. No `createKyselyDb` / `env.HYPERDRIVE` in
  any deploy from this directory.
- All paid-tier / commercial-threat-intel features stay vendor.
- TLP:WHITE-only is a structural invariant — never widen.

## References

- vendor parent: `etzhayyim/etzhayyim-root`
  `60-apps/etzhayyim-project-ransomwatch/wasm/etzhayyim-wasm-ransomwatch-r4ns0w4t01/`
- vendor classification: `tranche-f-post-freeze-7-actors-audit-2026-05-21`
- sibling public feed: `60-apps/etzhayyim-project-public-malak/` (etz PR #226)
- ADR-2605172000 — etzhayyim kotoba substrate
- ADR-2605172400 — vendor 3-axis split rule
- ADR-2605211000 — worker XRPC deploy runbook (when Phase 2 lands)
