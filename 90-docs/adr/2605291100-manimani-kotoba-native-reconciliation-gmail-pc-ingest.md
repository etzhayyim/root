---
id: adr-2605291100-manimani-kotoba-native-reconciliation-gmail-pc-ingest
title: "ADR-2605291100: manimani — kotoba-native personal knowledge router (Gmail + PC ingest), reconciling RisingWave/Anthropic-direct/RunPod"
status: proposed
doc_type: adr
topic: manimani-kotoba-native-reconciliation
authoritative: true
last_verified: 2026-05-29
priority: 7.0
axis: architecture
weight: 0.6
priority_note: "manimani personal knowledge router を religious-corp 憲章 (kotoba substrate + Murakumo-only inference + Signal E2E PII) に整合させ、Gmail 全アーカイブ + 広範囲 PC ファイルの ingest 経路を確定する統合 ADR。旧 ADR-2605080800 の persistence/inference/runtime 層を supersede し、product contract (XRPC surface / 4 kind / LLM 主導分類 / non-federable) は保存する。"
authoritative_for:
  - manimani.etzhayyim.com の substrate 配置 (kotoba EAVT datoms; RisingWave 廃止)
  - manimani inference 経路 (Murakumo LiteLLM gateway のみ; Anthropic-direct / RunPod 廃止)
  - manimani runtime (kotoba StateGraph; pymagatama LangGraph Server + Granian pool 廃止)
  - Gmail 全アーカイブ ingest 経路 (kotoba-ingest gmail.rs OAuth2 → RFC2822 → E2E encrypt → QuadStore)
  - 広範囲 PC ファイル ingest 経路 (kotoba-kse Vault chunking → BlobManifest CID → intake datom)
  - manimani datom schema (vertex_manimani_* RisingWave テーブルの EAVT predicate 置換)
depends_on:
  - adr-2605080800-manimani-langgraph-user-intake-routing
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605181100-confidentiality-encrypted-records
  - adr-2604251830-shannon-optimal-layered-architecture
related:
  - adr-2605120000-ses-anken-jokyo-ingest-langgraph
  - kotoba-internal ADR-2605250002 (kotoba StateGraph / LangGraph-compatible API)
  - kotoba-internal ADR-2605252400 (kotoba-ingest Gmail OAuth2 → QuadStore)
  - kotoba-internal ADR-2605250004 / 2605250005 (kotoba WebGPU train / infer)
supersedes: []
superseded_by: []
---

# ADR-2605291100: manimani — kotoba-native personal knowledge router (Gmail + PC ingest)

**Status**: proposed
**Date**: 2026-05-29
**Deciders**: Jun Kawasaki

# Context

## What manimani is, and why it stalled

`manimani.etzhayyim.com` is the **personal knowledge router** defined in ADR-2605080800
(2026-05-08): the user throws a fragment (text / url / file_ref / email) at one `ingest`
XRPC, an LLM auto-routes it into an emergent *project*, and a per-kind processor turns it
into an artifact (facts / todos / summary / deferred). The name 「まにまに / 随に」 means
"to let things take their natural course" — projects emerge from accumulated intake rather
than from a pre-declared taxonomy.

**Current state (2026-05-29): Phase 0 contract only.** The CF Worker edge facade exists and
is non-trivial (`60-apps/etzhayyim-project-manimani/src/{app,dispatcher,embed}.ts` — Hono +
auth middleware + 6 NSID XRPC routing + embed UI). But the execution backend
(`20-actors/magatama/py/src/pymagatama/manimani/`) **was never implemented** — the directory
does not exist. manimani has a mouth and no stomach.

## Why the old design is now unshippable as-written

ADR-2605080800 predates the religious-corp constitutional wave (2026-05-19) and the kotoba
substrate pivot (2026-05-26). It specifies three things that the repo's own substrate
boundary (root `CLAUDE.md` § "Substrate boundary") now **prohibits**:

| ADR-2605080800 says | Now prohibited by | Constitutional reason |
|---|---|---|
| Persist to **RisingWave** via Hyperdrive (4 vertex + 1 edge + 2 MV) | ADR-2605262130 (kotoba) | RisingWave / Postgres / Kysely are banned; canonical substrate is **kotoba** |
| Inference via **Anthropic API direct** or **vLLM Gemma4 on RunPod** | ADR-2605215000 | religious-corp inference is **Murakumo-fleet-only**; no RunPod / commercial API direct |
| LangGraph state → (deferred) RisingWave `BaseCheckpointSaver` | ADR-2605262130 | no RisingWave anywhere in the state path |

So "manimani をまとめる" does **not** mean resurrecting the 2026-05-08 design. It means
**reconciling the manimani product onto the substrate the repo actually has today**, and on
that reconciled foundation, defining the user's actual ask: ingest the **full Gmail archive**
and **broad PC files**, organize them into a "datomic"-style store + "langgraph".

## What "datomic" and "langgraph" resolve to in this repo

The user said *datomic* and *langgraph*. In this monorepo both already exist as **kotoba**
primitives — there is no need to introduce proprietary Datomic (Clojure) or a Python LangGraph
pool, both of which would re-introduce constitutional conflicts:

- **datomic → `kotoba-kqe`.** kotoba is literally *"Datomic-style immutable datoms, EAVT"*
  (40-engine/kotoba/README.md). Its 4-index Arrangement **is** Datomic's EAVT / AEVT / AVET /
  VAET (40-engine/kotoba/CLAUDE.md § "4-Index Arrangement (Datomic EAVT/AEVT/AVET/VAET)").
  This is the "production datomic-compatible API" the deliverable assumes.
- **langgraph → kotoba `StateGraph`** (kotoba-internal ADR-2605250002): a LangGraph-compatible
  Rust API — `add_node` / `add_edge` / `add_conditional_edges` / `compile` / `run`, with
  `Reducer::Append` matching LangGraph's `add_messages`, and Thread checkpointing into a KQE
  Arrangement (time-travel via Delta). It runs inside `kotoba-server`, on the Murakumo fleet,
  with **no** Python pool and **no** RisingWave.
- **Gmail ingest → `kotoba-ingest`** (kotoba-internal ADR-2605252400): already implements
  `gmail.rs` (OAuth2 poll) + RFC 2822 parse + `EmailIngestor` (now `Arc<dyn AgentCrypto>` +
  `Arc<Vault>`, raw key removed 2026-05-26) → E2E-encrypted body blob + QuadStore datoms.
- **PC files → `kotoba-kse` Vault**: file-type chunking (Single / FixedLen 512KB / CDC
  gear-hash / CodecAware CBOR) → `BlobManifest` CID; `SovereignCrypto` / `SecureVault` for
  E2E-at-rest. The walker over PC roots is the one genuinely new component.

## Deliverable shape (decided with user, 2026-05-29)

1. **Deliverable**: consolidation ADR + design **first** (this document). No live ingestion
   of real Gmail / filesystem in this session; no destructive code changes.
2. **Ingest scope**: full Gmail archive + broad PC files (with the privacy guardrails in
   § "Privacy & PII boundary").
3. **Target store**: kotoba (assuming kotoba exposes a production Datomic-compatible API —
   which `kotoba-kqe` does today via the 4-index Arrangement + `QuadStore::assert`).

# Decision

## D0 — Split: preserve the product contract, replace the substrate

manimani's **product contract** is sound and is **preserved unchanged** from ADR-2605080800:

- The XRPC surface (`ingest` / `classify` / `process` / `resumeRun` / `getProject` /
  `listProjects` / `listPendingRuns` / `coverage`) and the CF Worker edge-facade role
  (state-less Hono forwarder, no LLM call, no DB write at the edge).
- The 4 project kinds (`knowledge` / `task` / `memo` / `unsorted`) and their processors.
- **LLM-led classification** with the `confidence < 0.5 → unsorted` fallback (silent
  misclassification is worse than an honest "unsorted" the user can re-route).
- **Non-federable by default**: no AT Repo emit; social derive only via explicit user
  opt-in `pds.dispatch({type:'app.bsky.feed.post'})`.

Everything **below** the contract — persistence, runtime, inference, checkpoint, PII at-rest
— is replaced with kotoba-native primitives. This ADR **supersedes the substrate/runtime/
inference layers of ADR-2605080800**; ADR-2605080800 remains authoritative only for the
product contract (and gets a banner pointing here).

## D1 — Persistence: RisingWave `vertex_manimani_*` → kotoba EAVT datoms

The four RisingWave vertices + one edge + two MVs become **content-addressed EAVT datoms**
written via `QuadStore::assert` / `assert_batch`. Subject CIDs keep the old content-addressed
PK formulas. PII-bearing text never lands as a plaintext quad object — it is stored as a
`SecureVault` blob and referenced by CID.

**intake** — subject `Cid = blake3(actor_did + ts_ms + raw_text_hash)`:

| predicate | object | notes |
|---|---|---|
| `manimani/intake/source_kind` | Text ∈ {text,url,file_ref,email,fs_file} | `email` + `fs_file` are new |
| `manimani/intake/raw_ref` | Cid → SecureVault blob | **E2E-encrypted** body (replaces plaintext `raw_text`) |
| `manimani/intake/parsed_text_ref` | Cid → Vault blob | parse output (classify/search input) |
| `manimani/intake/source_uri` | Text | url / file_ref / gmail msg-id / fs path |
| `manimani/intake/lang` | Text (BCP-47) | |
| `manimani/intake/sensitivity_ord` | Integer (0/1/2, default 2) | |
| `manimani/intake/byte_size` | Integer | |
| `manimani/intake/actor_did` `…/created_at` | Text / Integer | ADR-0095 scope columns → datoms |

**project** — subject `Cid = blake3(actor_did + slug)`:
`manimani/project/{slug,title,kind,status,intake_count,last_intake_at,actor_did,created_at}`.
`project_did = did:web:manimani.etzhayyim.com:project:{slug}` retained as a `…/did` datom.

**artifact** — subject `Cid = blake3(intake_id + processor + content_hash)`:
`manimani/artifact/{kind,content_ref(→Vault Cid),model_id,tokens_in,tokens_out,error_text}`
plus **ref** datoms `manimani/artifact/intake → Cid(intake)`, `…/project → Cid(project)`,
`…/run → Cid(run)` (ref-typed → indexed in **VAET** for reverse lookup).

**belongs_to edge** — ref-typed quad `Cid(intake) — manimani/belongs_to → Cid(project)`.
`confidence` / `is_primary` / `classification_method` live on a reified statement entity
`Cid = blake3(intake_id + project_id)` so the edge stays a clean VAET ref.

**run** — subject `= run_id = thread_id = sha256(actor_did + ts_ms + intake_hash)`:
`manimani/run/{status,current_node,started_at,finished_at,cost_mkoto}`. The checkpoint is **not**
a column — it is the kotoba `StateGraph` Thread state in the KQE Arrangement (D3), giving
time-travel for free (replaces the deferred RisingWave `BaseCheckpointSaver`).

**The two RisingWave MVs** (`mv_manimani_project_active`, `mv_manimani_intake_unrouted`)
become **kotoba-kqe Datalog rules / MV** over AEVT (`manimani/project/status`) and AVET
(`manimani/artifact/kind ∈ {raw_passthrough,error}`), evaluated on the hot Arrangement — no
separate projection layer (per ADR-2605262130 the read path is `kotoba-kqe` arrangements
directly; no RisingWave / Lance / DuckDB).

## D2 — Inference: Murakumo LiteLLM gateway only

Every LLM call (classifier + `extract_facts` / `expand_todo` / `summarize`) goes through the
**Murakumo LiteLLM gateway `http://192.168.1.70:4000`** (OpenAI-compatible, the sole
abstraction layer per ADR-2605215000), with per-node `gemma3:4b` at `127.0.0.1:11434` as
fallback. **No** Anthropic-direct, **no** RunPod vLLM, **no** commercial GPU rental.
Model names are never hardcoded — resolved via `resolveModelId()` / `MURAKUMO_DEFAULT_MODEL`.
The classifier's structured output is still Pydantic/serde-validated before any datom write.

## D3 — Runtime: kotoba StateGraph (the "langgraph"), not a Python pool

The 7-node topology from ADR-2605080800 is preserved, now expressed as a kotoba `StateGraph`
(kotoba-internal ADR-2605250002) compiled inside `kotoba-server`:

```
START(ingest) → parse_input → classify_project → route_processor
  → { extract_facts | expand_todo | summarize | defer_for_user_review }
  → persist_artifact → emit_audit → END
```

- `classify_project` = one Murakumo structured-output call returning
  `(existing_project_id | new_project_proposal, confidence, rationale)`; `confidence<0.5`
  forces `unsorted`. Context = top-20 active projects (kqe MV) + last-5 intake history.
- `route_processor` = `add_conditional_edges` on `project.kind`.
- `persist_artifact` = `QuadStore::assert_batch` (the datoms in D1) — **not** Hyperdrive.
- Thread state (channels: `messages: Append`, `intake/project/run: Override`) checkpoints to
  the KQE Arrangement; `resumeRun` (HITL, old Phase 4) is now a `StateGraph` thread resume.

The `mitama-manimani-pool` Helm release (Granian + Python LangGraph Server) from ADR-2605080800
is **not built**. If a Python authoring/eval harness is ever wanted, it may only write through
`kotoba-server` XRPC/MCP (`agent.run` / `kotoba_datalog_run`) — never Hyperdrive, never its own
inference key.

## D4 — Ingest: Gmail full archive + broad PC files

### D4a — Gmail full archive (`kotoba-ingest`)

Backfill the **entire mailbox**, oldest→newest, via `kotoba-ingest` `gmail.rs`:

1. OAuth2 with **read-only** scope (`gmail.readonly`); token in macOS Keychain, never committed.
2. Page the full history in batches; per message → `EmailIngestor` → RFC 2822 parse →
   body **E2E-encrypted** into a `SecureVault` blob (`Arc<dyn AgentCrypto>` + `Arc<Vault>`).
3. Emit `intake` datoms (D1) with `source_kind=email`, `source_uri=<gmail msg-id>`,
   `raw_ref=<vault Cid>`. **Idempotency / dedup** is free: the intake subject is content-
   addressed, so re-running the backfill re-asserts identical datoms (no duplicates).
4. Each new intake then flows the manimani `StateGraph` (D3) for classification → artifact.

Volume note: a full archive is large; the backfill is a **paged, resumable** job (kotoba
`SyncWindow` + `Journal` seq-index already support resume). The first run is metadata + body
ingest; StateGraph classification can run as a second pass to bound Murakumo load.

### D4b — Broad PC files (new `manimani-fs-ingest` walker)

A new walker enumerates an **explicit allowlist of roots** (e.g. `~/Documents`, `~/Desktop`,
and this repo), and per file:

1. Type-detect → Vault chunk: `Single` (small) / `CDC gear-hash` (large) / `CodecAware`
   (CBOR/JSON) → `BlobManifest` CID, E2E-encrypted at rest.
2. Emit `intake` datoms with `source_kind=fs_file`, `source_uri=<abs path>`,
   `raw_ref=<manifest Cid>`, plus `mtime` / `byte_size`.
3. Re-walks are content-addressed → unchanged files are no-ops; changed files append a new
   content-addressed intake (full history retained via Delta).

This walker is the **only net-new code** the design requires; everything else is wiring
existing kotoba crates.

## D5 — Privacy & PII boundary

manimani intake is **PII tier-3** (ADR-0018) and **confidential** (ADR-2605181100). The
old RisingWave-RLS model is replaced by **content-addressing + E2E encryption + DID-scoped
datoms**:

- Bodies are `SecureVault` blobs (XChaCha20/AEAD via `SovereignCrypto`); only references
  (CIDs) and non-sensitive metadata are plaintext datoms.
- **Non-federable**: no AT Repo emit by default (carried from ADR-2605080800).
- Gmail OAuth is **read-only**; the fs-walker is **read-only**.
- **Secret-skip policy (hard)**: never ingest the macOS Keychain, 1Password, `.ssh`,
  `.env*`, `*.pem/key`, `*_history`, browser credential stores, or anything matching the
  repo's `.gitignore` secret patterns. Roots are an explicit allowlist, never `/` or `~`.
- The Charter Rider §2(a)-(h) content scanner
  (`etzhayyim_organism.sensors.charter_rider.scan()`) runs on every generated artifact.

# Consequences

**Positive**
- Constitutional compliance: one substrate (kotoba), one inference path (Murakumo), E2E PII.
- No Python LangGraph pool, no RisingWave, no Hyperdrive — fewer moving parts, no cluster DB.
- Content-addressed intake → free dedup + resumable backfill + full-history time-travel.
- "datomic" and "langgraph" are satisfied by primitives the repo already ships and benches.

**Negative / risks**
- kotoba `StateGraph` is younger than Python LangGraph for rich HITL; `resumeRun` semantics
  must be validated against the old Phase-4 contract before it is advertised.
- Full Gmail backfill is large and Murakumo classification throughput (gemma-class) is the
  bottleneck, not API quota — hence the two-pass (ingest then classify) design.
- The fs-walker is a real exfiltration-risk surface; mitigated by allowlist + secret-skip +
  read-only + E2E-at-rest + Charter scanner, but it must ship with those guards or not at all.

# Alternatives Considered

1. **Resurrect ADR-2605080800 as-written (RisingWave + Anthropic-direct + RunPod + Python
   LangGraph pool).** Rejected: three constitutional violations (D-table in Context).
2. **Introduce real Datomic (Clojure/JVM).** Rejected: proprietary, JVM dependency, no
   content-addressing, no E2E, and it would be a parallel substrate engine — banned by
   ADR-2605262130 without an ADR carve-out. `kotoba-kqe` already gives the EAVT/AEVT/AVET/VAET
   surface the word "datomic" was reaching for.
3. **Stage to intermediate JSONL, defer kotoba writes.** Rejected as the *primary* path per
   the user's choice to target the kotoba datomic-compatible API directly. JSONL is retained
   only as an optional Phase-1 debug dump (facts/todos/summary) for eyeballing before commit.
4. **Keep Python LangGraph but point its writes at kotoba via XRPC.** Held as a fallback for a
   Python authoring/eval harness only (D3); not the canonical runtime, because it re-adds a
   pool + a second inference integration surface for no product gain.

# Migration plan

| Phase | scope | trigger to next |
|---|---|---|
| **0 — this ADR** | contract reconciliation, doc only | user 承認 |
| 1 — schema + graph | manimani EAVT predicate module + `StateGraph` def in kotoba; synthetic text intake → artifact datom (in-memory `QuadStore`) | one StateGraph run asserts a valid artifact datom set |
| 2 — Murakumo wiring | classifier + processors via LiteLLM `:4000`; re-point CF Worker edge from bpmn-dispatcher→LangGraph to `kotoba-server` XRPC | text intake → project auto-emerges + artifact lands, all via Murakumo |
| 3 — Gmail full archive | `kotoba-ingest` paged backfill + dedup + 2nd-pass StateGraph classification | full archive ingested idempotently; re-run is a no-op |
| 4 — PC broad files | `manimani-fs-ingest` walker (allowlist + secret-skip + Vault chunk) | configured roots ingested; secret-skip verified on a planted decoy |
| 5 — query + UI | `getProject`/`listProjects`/`coverage` as kqe Datalog; embed UI read path | coverage snapshot returns live counts from arrangements |

Phases 1–5 are separate sessions. This PR authors Phase 0 only.

# References

- ADR-2605080800 (manimani LangGraph User Intake & Project Routing — product contract preserved; substrate/runtime/inference layers superseded here)
- ADR-2605262130 (kotoba storage substrate unification — no RisingWave; read path = kqe arrangements)
- ADR-2605215000 (etzhayyim inference Murakumo-only — no RunPod / no commercial GPU)
- ADR-2605192100 (mission charter — non-profit, Wellbecoming, PII posture)
- ADR-2605192200 (Charter Rider v2.0 — §2(a)-(h) content scanner)
- ADR-2605181100 (confidentiality — `com.etzhayyim.encrypted.*`, Signal-wrapped envelopes)
- ADR-2605120000 (SES anken/jokyo ingest — sibling LangGraph ingest pattern)
- kotoba-internal ADR-2605250002 (kotoba StateGraph / LangGraph-compatible API)
- kotoba-internal ADR-2605252400 (kotoba-ingest Gmail OAuth2 → QuadStore)
- 40-engine/kotoba/CLAUDE.md § "4-Index Arrangement (Datomic EAVT/AEVT/AVET/VAET)" + § "StateGraph 設計"
- 60-apps/etzhayyim-project-manimani/CLAUDE.md (edge facade surface)
