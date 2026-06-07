---
id: adr-2604251220-record-log-not-mst
title: "ADR: etzhayyim PDS uses append-only record log, not AT Protocol MST CAR commit"
status: active
doc_type: adr
topic: pds-record-log
authoritative: true
last_verified: 2026-04-25
authoritative_for:
  - etzhayyim PDS commit storage shape
  - prohibited use of @atproto/repo MST path
  - ON CONFLICT / transaction restrictions on Kotoba/Datomic writes
related:
  - adr-0014-self-hosted-did-plc
  - adr-0041-pds-commit-content-addressed-pk
  - adr-2604241121-repo-commit-stays-on-pds
  - adr-0085-non-federable-nsid-firehose-gate
supersedes: []
superseded_by: []
---

# Context

AT Protocol PDS reference implementation は MST (Merkle Search Tree) を用い、
commit 単位で CAR file を生成し firehose で federation する。etzhayyim PDS は
Kotoba/Datomic を primary storage に採用しており (ADR-0048)、Kotoba/Datomic は OLTP
契約を提供しない (`ON CONFLICT` / write transaction / read-your-writes /
UNIQUE 列制約 / `START TRANSACTION` write すべて非対応または degraded)。
加えて plc.etzhayyim.com は self-hosted (ADR-0014) で Bluesky Relay は etzhayyim の
DID を discover しないため、外部 federation 需要が事実上 0。

本 ADR は CLAUDE.md Root-Only Rule "Record-log semantics, not MST" を ADR
化し、storage shape と禁止 API を確定する。

# Decision

## D1. Storage shape

etzhayyim PDS は以下 2 表のみで commit を表現する:
- `vertex_repo_commit` — append-only commit log (PK = content-addressed,
  ADR-0041 §D)
- `vertex_repo_record` — append-only record log

**MST 表現は持たない**。`vertex_repo_block` への書き込みは禁止。

## D2. Prohibited APIs

- `vertex_repo_block` への INSERT / UPDATE
- SqlRepoStorage の再導入
- `@atproto/repo` の MST path (`MerkleSearchTree` / `commitData` / `formatCommit`)
  呼び出し
- `com.atproto.sync.getRepo` で完全な CAR を生成しようとする実装

## D3. Allowed degraded responses

`com.atproto.sync.*` handler は内部 caller (graph-worker / audit) のために
以下 degraded response を返し続ける:
- `getRepo` → 空 CAR (header only)
- `getCheckout` → `chainValid: false`
- `listRepos` / `getLatestCommit` → record log 由来の latest seq

## D4. Kotoba/Datomic write contract for LLM-generated code

LLM が Kotoba/Datomic 向け Kysely / 生 SQL を書く際の規約:

- **`.onConflict()` / `ON CONFLICT` 禁止** — RW 仕様で同 PK 再 insert は
  implicit overwrite (PK upsert) になる
- conflict resolution が必要な場合は `core.ts:2998` 方式 (delete-then-insert)
- `db.transaction()` は no-op — RW は write TX 非対応 (`START TRANSACTION` は
  READ ONLY のみ受理)
- bulk INSERT は `SET dml_rate_limit = N` で throttle (ADR-0048 §B2 incident)

## D5. Federation re-enable path

将来 Bluesky Relay と federation が必要になった場合:
1. 別 storage (PostgreSQL / SQLite) に MST projection を build する dedicated
   worker を追加
2. `com.atproto.sync.*` を MST projection に切り替え
3. 既存 `vertex_repo_record` は read path として保持

本 ADR の禁止 API は federation 経路の dedicated worker 内のみで解禁する。
PDS Worker / app handler では引き続き禁止。

# Consequences

- etzhayyim 内部の commit / record 書き込みは 1-RTT INSERT で完結 (MST hash chain
  計算なし)。
- 外部 Relay に etzhayyim DID は federate されない (ADR-0085 firehose gate と整合)。
- LLM 生成コードで `.onConflict()` を見たら必ず削除 review 対象。

# Alternatives Considered

- **MST CAR 維持 + Kotoba/Datomic OLTP shim**: shim 層 (Postgres frontnet) を
  挟む案だが、2 系統 storage の同期で eventual consistency 問題が顕在化。
  federation 需要 0 の現状ではコスト過多。
- **Kotoba/Datomic を捨てて Postgres に戻す**: graph MV / streaming pipeline
  (ADR-0036 / 0044) の前提が崩壊。RW を primary に維持する方が η 高い。

# References

- `90-docs/260424-bsky-compat-kotoba-split.md`
- ADR-0014 (self-hosted did:plc — federation 0 の根拠)
- ADR-0041 (commit content-addressed PK)
- ADR-2604241121 (repo commit stays on PDS)
- ADR-0048 (Kotoba/Datomic Vultr+B2 primary)
- ADR-0085 (non-federable NSID firehose gate)
