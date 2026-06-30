---
id: adr-2606302038-manimani-cli-kotobase-secure-storage-and-local-tier
title: "ADR-2606302038: manimani CLI (bb/clj) + secure storage tiers — local hot tier, E2E Vault, kotobase.net ciphertext pin"
status: proposed
doc_type: adr
topic: manimani-cli-secure-storage
authoritative: true
last_verified: 2026-06-30
priority: 6.5
axis: architecture
weight: 0.5
priority_note: "manimani personal knowledge router の実行口を CLI として確定する。runtime/inference/persistence は ADR-2605291100 の kotoba-native 決定を踏襲し、新たに (a) bb/clj CLI コマンド面 `e7m manimani *`、(b) storage tier モデル（local hot tier ⇄ ingest source / kotoba QuadStore E2E Vault / kotobase.net 暗号文 pin / B2 archival）、(c) public-repo での PII 隔離（local gitignored Phase-0 journal）を定める。"
authoritative_for:
  - manimani CLI のコマンド面（bb task `e7m manimani *` + clj namespace etzhayyim.manimani.*）
  - manimani storage tier モデル（local folder hot tier / E2E Vault / kotobase.net 暗号文 pin / B2 cold）
  - manimani が local folder を ingest source かつ hot 永続層として用いる設計の明文化
  - manimani PII の public-repo 隔離（80-data/manimani/ は gitignored, README pointer のみ tracked）
depends_on:
  - adr-2605291100-manimani-kotoba-native-reconciliation-gmail-pc-ingest
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2606041130-kotoba-b2-blockstore-cold-pin
  - adr-2605241500-etzhayyim-dataset-cid-substrate
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
related:
  - adr-2605080801-manimani-langgraph-user-intake-routing
  - "ADR-2606091500 (kotobase.net canonical remote pin)"
  - "repo-root CLAUDE.md § Operational code = clj/bb over the kotoba Datom log"
supersedes: []
superseded_by: []
---

# ADR-2606302038: manimani CLI + secure storage tiers

**Status**: proposed
**Date**: 2026-06-30
**Deciders**: Jun Kawasaki

# Context

ADR-2605291100 reconciled the manimani personal knowledge router onto kotoba-native
primitives (EAVT datoms, kotoba `StateGraph`, Murakumo inference, E2E Vault PII) but
left it **Phase-0 contract only**: a CF Worker edge facade with no execution backend
and **no local entrypoint**. The owner's actual day-to-day surface for "throw a
fragment at manimani and let projects emerge" is a **terminal**, not an HTTP edge.

Three questions are now on the table, each answered by this ADR:

1. **What is the manimani CLI?** There is none today (`grep manimani bb.edn` → ∅).
   The repo-wide rule (root `CLAUDE.md` § "Operational code = clj/bb over the kotoba
   Datom log") says new operational tooling MUST be `bb`/clj folding over the Datom
   log — so the CLI is a `bb` task group `e7m manimani *`, not a `.py`/`.sh`.
2. **Can kotobase.net store it securely?** Yes — by construction (see D2). kotobase.net
   is a Kubo-compatible IPFS *pin* tier that only ever holds **AEAD ciphertext blocks
   addressed by their own hash**; it cannot read plaintext.
3. **Does manimani use local folders as storage?** Yes — in **two** roles (see D3):
   local roots are both an **ingest source** (ADR-2605291100 §D4b) and the **local hot
   block tier** that fans pins out to kotobase.net.

# Decision

## D1 — manimani CLI = `bb e7m manimani *` over the kotoba Datom log

The CLI is a `bb` task group backed by a clj/cljc namespace tree
`70-tools/src/etzhayyim/manimani/` (mirrors `etzhayyim.organism` / `etzhayyim.vitals`).
It writes the **same intake/project/artifact/run datoms** as the XRPC backend (it is a
second mouth on one stomach), so CLI and edge converge on identical EAVT state. No
Python pool, no `.sh`. Inference goes through the Murakumo LiteLLM gateway
(`:4000`, ADR-2605215000); model ids resolve via `MURAKUMO_DEFAULT_MODEL`, never hardcoded.

Command surface (mirrors the 8 XRPC methods + ingest sources + storage ops):

| command | role | writes / reads |
|---|---|---|
| `e7m manimani ingest <text\|url\|file>` | submit one intake → StateGraph → artifact | intake + artifact datoms |
| `e7m manimani ingest-gmail [--since\|--backfill]` | read-only OAuth2 (`gmail.readonly`) poll/backfill | intake datoms (`source-kind :email`) |
| `e7m manimani ingest-fs <root>...` | walk allowlisted local roots (secret-skip) | intake datoms (`source-kind :fs-file`) |
| `e7m manimani classify <intake> <project>` | re-route an intake | `belongs-to` datom |
| `e7m manimani process <intake> [--kind]` | re-run a processor (facts/todos/summary) | artifact datom |
| `e7m manimani projects` / `project <slug>` | list / show projects + artifacts | kqe read |
| `e7m manimani coverage [--days N]` | counters + unrouted | kqe read |
| `e7m manimani pin [--all\|<cid>]` | push local ciphertext blocks → kotobase.net | IPFS pin fan-out |
| `e7m manimani get <cid>` / `drop <cid>` | fetch / evict an E2E blob by CID | Vault read / local evict |
| `e7m manimani vault [init\|rotate]` | read-cap key mgmt (macOS Keychain) | key only, never datoms |

`classify` uses one Murakumo structured-output call with the `confidence < 0.5 →
unsorted` fallback (carried from ADR-2605291100 §D3). Classifier output is serde/spec
-validated before any datom write.

## D2 — kotobase.net is secure by construction (ciphertext-only pin tier)

**Yes, manimani can persist to kotobase.net securely**, because confidentiality lives in
the encryption layer, not in trusting the pin host (暗号化≠忘却, ADR-2605181100):

- PII-bearing bodies are sealed as **`SecureVault` blobs** — XChaCha20-Poly1305 AEAD
  via `SovereignCrypto` — **before** the CID is computed. The **CID is taken over the
  ciphertext** (ADR-2605181100 hard rule). So the block's address reveals nothing.
- The **read-cap** (symmetric key + nonce) is held in the owner's macOS Keychain /
  1Password and **never leaves the device**; it is never a datom and never pinned.
- kotobase.net (canonical remote pin, ADR-2606091500, Kubo-compatible) and the colder
  B2/DataLad tier (ADR-2606041130) therefore store **only opaque ciphertext blocks +
  their hashes**. A full compromise of the pin host yields ciphertext, not content.
- Plaintext datoms pinned are **non-sensitive metadata only** (source-kind, CID refs,
  kind, timestamps, sensitivity-ord); identifying text rides as a Vault CID, not a quad
  object.

Net: kotobase.net is a *dumb, sovereign, content-addressed replication tier*. It is the
**canonical remote** store for manimani's encrypted blocks — not Google/Apple cloud.

## D3 — local folder is storage, in two distinct roles

manimani's storage is **tiered**, and the local folder appears twice:

```
(ingest source)  allowlisted roots ~/Documents … repo  ──read-only──┐
                                                                     ▼
(hot tier)   LOCAL: kotoba QuadStore datoms + local Kubo block repo (flatfs)
                    · plaintext metadata datoms + ciphertext Vault blocks
                    · Phase-0 interim: 80-data/manimani/*.journal.edn (gitignored)
                                                                     │ pin fan-out
                                                                     ▼
(cold pin)   kotobase.net  — canonical remote IPFS pin, CIPHERTEXT BLOCKS ONLY
                                                                     │
                                                                     ▼
(archival)   Backblaze B2 / DataLad git-annex (ADR-2606041130)
```

- **As ingest source**: `ingest-fs` walks an **explicit allowlist** of local roots
  (never `/` or `~`), read-only, with the hard **secret-skip** policy (Keychain, 1Password,
  `.ssh`, `.env*`, `*.pem/key`, `*_history`, anything matching repo `.gitignore` secret
  patterns) — ADR-2605291100 §D5.
- **As hot storage tier**: the local Kubo block repo is the primary, fastest copy of every
  block (ADR-2606041130 found the durable unit is the block store itself); kotobase.net is
  the off-host replica. So **local folders are first-class storage**, not a cache — kotobase.net
  replicates them, and bytes restored from any tier resolve by their original CID.

## D4 — public-repo PII isolation (Phase-0 interim store)

Until the kotoba `QuadStore` backend ships, the CLI writes intake datoms to a **local,
gitignored** journal `80-data/manimani/intake.journal.edn`. Because `etzhayyim/root` is
**public**, this Phase-0 plaintext hot tier MUST stay off git:

- `.gitignore`: `/80-data/manimani/*` + `!/80-data/manimani/README.md` (only the PII-free
  pointer is tracked).
- The journal holds real correspondence (subjects, counterparties, legal/tax detail) at
  `sensitivity-ord 2`; it is the local hot tier the kotoba QuadStore + E2E Vault replaces.
- First real intake set committed to this local journal: the 2026-06-30 Gmail session
  (LingLing litigation 第5準備書面 report + JK源泉所得税 納付案内 → projects
  `lingling-litigation` / `jk-tax`, one reply-draft artifact, two todos).

# Consequences

**Positive**
- A real terminal entrypoint for manimani that obeys the clj/bb-over-Datom-log rule.
- Honest answer to "secure on kotobase.net?" — yes, via CID-over-ciphertext; the pin host
  is untrusted by design.
- local folder is explicitly both ingest source and hot storage tier; no Google/Apple cloud
  in the persistence path (Gmail is read-only ingest only).
- PII never enters the public repo (gitignored Phase-0 journal + README pointer).

**Negative / risks**
- CLI and (future) XRPC backend must converge on one datom schema or state forks; the CLI
  is authored against the ADR-2605291100 §D1 predicate set to prevent drift.
- The Phase-0 local journal is plaintext-at-rest on the owner's disk (no Vault yet); it is
  gitignored but relies on full-disk encryption until D2's Vault path is wired.
- `ingest-fs` is an exfiltration-risk surface; it ships **only** with allowlist + secret-skip
  + read-only + (at Vault stage) E2E-at-rest + the Charter Rider content scanner, or not at all.

# Implementation status (2026-06-30, landed this session)

Phase-0 scaffold is **landed** (commit `4ea83ba`), design-first per the ADR-2605291100
precedent — real where it can be, honest stubs where external integration is pending:

- **`70-tools/src/etzhayyim/manimani.cljc`** — the CLI ns (clj/bb over the kotoba Datom
  log), registered as `"manimani" → etzhayyim.manimani` in the `e7m` dispatch map
  (`70-tools/src/etzhayyim/cli.cljc`). Invoked `bb e7m manimani <cmd>`.
- **Working over the local journal**: `ingest` (heuristic classify → intake/project/
  belongs-to datoms, `confidence<0.5 → unsorted` honest fallback), `classify`, `projects`,
  `coverage`. Verified: `bb e7m manimani projects` → the 2 seeded projects
  (`lingling-litigation`, `jk-tax`); `coverage` → `projects:2 intakes:2 unrouted:0`.
- **Honest stubs (no fake behavior)** for the external-integration seams: `ingest-gmail`
  (read-only OAuth2, Phase-3), `ingest-fs` (allowlist + secret-skip, Phase-4), `pin`
  (kotobase.net ciphertext, Phase-5), `vault` (Keychain read-cap, Phase-2),
  `murakumo-classify` (LiteLLM `:4000` seam, Phase-2). Each prints its plan and exits.
- **Not yet wired** (next phases): Murakumo structured-output classify, Gmail OAuth backfill,
  fs-walker, E2E `SecureVault` blobs, kotobase.net pin fan-out. The Phase-0 classifier is a
  deterministic keyword heuristic; the `intake-id` is a sha-256 stand-in for the blake3 CID.

Adjacent repair (same session): the committed **`adr-index.edn`** was the stale, un-parseable
hand-edited index (prose written as map literals — broken before this session). It was
regenerated from ADR `.md` front matter via the canonical SSoT generator
(`etzhayyim.tools.adr-mdedn` `index`, per ADR-2606162200): **923 entries, one-per-line,
clojure.edn-parseable**. Recommend wiring `index-check` into lefthook to prevent re-drift.

# Alternatives Considered

1. **iCloud / Google Drive as the manimani store.** Rejected: centralized off-chain stores
   are prohibited (ADR-2605172000); they would see plaintext, create lock-in, and break the
   sovereign content-addressed model. Gmail/Drive touch only as a *read-only ingest source*.
2. **Python/Granian CLI calling the LangGraph pool.** Rejected: violates the clj/bb-over-Datom
   -log rule and re-adds the inference/pool surface ADR-2605291100 §D3 removed.
3. **Commit the intake journal to the public repo (descriptive slugs).** Rejected: leaks
   litigation/tax PII. Chosen path is gitignored local journal (owner decision, 2026-06-30).
4. **Trust kotobase.net with plaintext, rely on host ACLs.** Rejected: confidentiality must be
   by encryption, not host trust (ADR-2605181100); CID-over-ciphertext makes the host untrusted.

# References

- ADR-2605291100 (manimani kotoba-native reconciliation — substrate/runtime/inference + Gmail/PC ingest)
- ADR-2605262130 (kotoba storage substrate unification) · ADR-2605312345 (Datom log = canonical state)
- ADR-2606041130 (kotoba IPFS block-store cold pin to B2; kotobase.net amendment) · ADR-2606091500 (kotobase.net canonical pin)
- ADR-2605241500 (dataset CID substrate — local `ipfs add` → kotobase.net fan-out)
- ADR-2605181100 (MST encrypted records — XChaCha20-Poly1305 AEAD, CID-over-ciphertext, Signal keywrap)
- ADR-2605215000 (Murakumo-only inference) · ADR-2605080801 (manimani product contract)
- repo-root CLAUDE.md § "Operational code = clj/bb over the kotoba Datom log"
- 60-apps/etzhayyim-project-manimani/CLAUDE.md (edge facade surface) · 80-data/manimani/README.md (local tier pointer)
