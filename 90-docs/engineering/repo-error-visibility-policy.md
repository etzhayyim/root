---
id: repo-error-visibility-policy
title: "ADR-0007: API / Worker のエラーは必ず 4xx/5xx で可視化する。Fallback / fail-open 禁止"
status: active
doc_type: adr
topic: error-visibility-policy
authoritative: true
last_verified: 2026-04-29
authoritative_for:
  - public API error handling policy
  - fallback / fail-open prohibition
related:
  - adr-0006-no-synthetic-data-in-production
supersedes: []
superseded_by: []
---

# Repo Error Visibility Policy

## Rule (CRITICAL — repo-wide, inviolable)

- API/Worker/CLI/SDK 実装で、上流障害を隠す `fallback` / `fail-open` / `silent degrade` / `retry-until-empty` を全面禁止する。
- エラー時は `4xx/5xx` を返し、`error` (machine-readable code) と `message` (human-readable detail, 原因・対象 id・upstream error 含む) を必ず含める。
- 空配列・ダミーデータ・`{}`・成功レスポンスへの置換で障害を隠蔽してはならない。
- **Uncaught exception を握り潰して Cloudflare Worker / runtime 側の opaque error (CF 1101, 1042 等) にしてはならない。** すべての Worker entry handler / XRPC method は自前の try/catch で上流例外 (Hyperdrive, Kotoba/Datomic, D1, service binding, fetch) を受け、ADR-0007 形式の JSON に正規化する。
- Browser/CLI は受け取ったエラーを UI/stderr に原文で表示する。"データの読み込みに失敗しました" のような無内容メッセージへの塗り潰しも禁止。
- LLM/RAG/agent workflow で、LLM backend failure / empty content を retrieval
  chunks から作った extractive answer に置換してはならない。これは品質劣化を
  成功に見せる lossy fallback であり、repo-wide に損失として評価する。正しくは
  `ok=false`、`error`、`errorKind`、可能なら upstream latency/correlation id を返す。
- LLM/RAG task timeout は公開 API/SSE の result window 内に収める。
  `answerWithKnowledge` は backend hang を SSE timeout ではなく明示的な
  `LlmError` として返すため、per-attempt LLM timeout を短く保つ。

## Applies To

- `50-infra/cloudflare/workers/**` (PDS, auth, vault, routing-gateway 等すべて)
- `60-apps/**/appview/**` + `60-apps/**/worker/**`
- `10-protocol/wproto/**` / `10-protocol/xrpc/**` / `20-actors/magatama/sdk/**`
- `70-tools/etzhayyim/**` (CLI: エラーは stderr に JSON で原文表示し exit code 非 0)
- 公開 XRPC エンドポイント全般
- Browser frontend (`*/svelte/src/**`): fetch 応答の error/message を UI に表示する

## Allowed Exception

- 例外は「read-only 補助機能のベストエフォート enrich」(例: avatar fetch の失敗をアイコン描画で握り潰す) に限定。
- この場合もメインレスポンスの成否を偽装してはならず、`warnings[]` として呼び出し元に伝える。

## Banned Patterns

| ❌ 禁止 | ✅ 正しい |
|---|---|
| `catch { return { records: [] }; }` | `catch (e) { return json({error:"UpstreamQueryFailed", message: e.message}, 502); }` |
| `catch { return []; }` (list API) | 明示的 4xx/5xx JSON |
| `await query.execute()` (no try/catch in Worker entry) | try/catch で包む (uncaught → CF 1101) |
| `if (err) { /* swallow */ }` | 再 throw または明示エラー response |
| Browser: `try { await fetch() } catch { showEmptyState(); }` | error/message を UI に表示 |
| "データの読み込みに失敗しました" (原因隠蔽) | 原文 error/message + correlation id |
| LLM失敗時にRAG本文を箇条書きで返す | `ok=false` + `errorKind=LlmError` / `EmptyLlmContent` |

## Enforcement Checklist

- `catch` で `[]` / `{}` / `null` / 空 object を返していないか
- `5xx` を `200` に書き換えていないか
- `x-pds-query-degraded` 等の診断がある場合、必要エンドポイントで明示エラー化しているか
- Worker entry が try/catch なしで上流 DB/service binding を呼んでいないか (→ uncaught = CF 1101 違反)
- Browser は error/message をそのまま表示しているか (汎用 "failed to load" への置換禁止)
- CLI は error/message を stderr に JSON で出し non-zero exit しているか

## Automated Enforcement (build-time)

`pnpm lint:adr-0007` runs 8 static checks. CI workflow:
`.github/workflows/adr-0007-error-visibility.yml` (PR + push to main).

| # | Rule | Script | Baseline |
|---|---|---|---|
| 1 | `no-pg-pool-in-worker` | `70-tools/scripts/lint/no-pg-pool-in-worker.mjs` | hard-fail (0 allowed) |
| 2 | `worker-entry-top-level-try` | `worker-entry-top-level-try.mjs` | hard-fail |
| 3 | `waituntil-requires-catch` | `waituntil-requires-catch.mjs` | `90-docs/rules/waituntil-requires-catch-baseline.txt` |
| 4 | `event-emitter-error-listener` | `event-emitter-error-listener.mjs` | hard-fail |
| 5 | `no-silent-catch` | `no-silent-catch.mjs` | `90-docs/rules/silent-catch-baseline.txt` |
| 6 | `hyperdrive-driver-unified` | `hyperdrive-driver-unified.mjs` | hard-fail |
| 7 | `lexicon-const-name-collision` | `lexicon-const-name-collision-check.mjs` | hard-fail (generator + post-check) |
| 8 | `repo-record-view-cid-integrity` | `repo-record-view-cid-integrity.mjs` | hard-fail |

**Pre-deploy hook**: run `pnpm lint:adr-0007` before `wrangler deploy` / `etzhayyim deploy`.
Baselines are "seal & shrink": run `pnpm lint:adr-0007:<rule>:update` only after fixing
underlying violations — never to silence new ones.

## Historical Incidents

- 2026-04-14: yoro.etzhayyim.com のデータ読み込み失敗。`com.atproto.repo.listRecords` の Hyperdrive query が try/catch なしで uncaught exception → CF Worker 1101 を間欠発生。修正: `handlers/pds/repo.ts` listRecords/getRecord に明示 try/catch → 502 `UpstreamQueryFailed` JSON 化 + `helpers.ts buildRecordView` の `cid=rkey` 取り違え bug 修正。併せて本 policy を priority 10.0 (inviolable) に昇格。
