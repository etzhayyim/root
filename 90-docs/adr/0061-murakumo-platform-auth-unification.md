---
id: adr-0061-murakumo-platform-auth-unification
title: Murakumo Inference — Platform Auth Unification (sk_live_*)
status: active
doc_type: adr
topic: auth-topology
authoritative: true
authoritative_for:
  - murakumo-gateway-auth-model
  - platform-api-key-surface-scope
  - credits-metering-integration-plan
last_verified: 2026-04-14
related:
  - adr-0022-auth-topology-consolidation
  - adr-0010-authoritative-rotation-key
---

# ADR 0023 — Murakumo Inference Platform Auth Unification

## Goal

`murakumo.etzhayyim.com` を platform の単一 API key (`sk_live_*`) トポロジーに統合し、
独立した `murk_*` shared secret / hardcoded fallback / CLI 側の
`~/.config/etzhayyim/murakumo_api_key` path を廃止する。将来の credits 課金統合
(CheckSpendAllowed / SpendCredits / inferenceUsage metering) の土台を置く。

## Scope

- `50-infra/cloudflare/workers/murakumo/src/index-ray.ts` (Gateway)
- `70-tools/etzhayyim/etzhayyim/murakumo.go` (CLI key resolution chain)
- `60-apps/etzhayyim-project-common-crawl/appview/.../src/app.ts`
  (および将来の CC-worker 派生、browser クライアント)

## Decision

### 1. Canonical auth

```
Caller
  │  Authorization: Bearer sk_live_*        ← ADR 0022 で統一した platform key
  ▼
murakumo.etzhayyim.com (CF Worker)
  │  verifyApiKey(sk_live_*)                 ← vertex_api_key lookup (HYPERDRIVE)
  │  → { ownerDid, scopes }
  │  scope check: "murakumo:inference" OR "*"
  │  → proceed else 401 / 403
  ▼
Fleet (proxy unchanged)
```

`sk_live_*` は platform 1-token (ADR 0022 §1). Murakumo gateway は別系統 token を
持たず、同じ `vertex_api_key` graph を source of trust とする。

### 2. Legacy compat (narrow window, Sunset header)

- `x-kotodama-verified: true` (Worker service binding 内部呼出) → `internal` として許可。
  これは platform 他と同じ 3 段階の 1 つに合わせる。
- `env.MURAKUMO_API_KEY` (emergency break-glass) → 残す。値は `sk_live_*` 形式であり、
  verifyApiKey と同じ流れを通る。未設定時のハードコード fallback は **廃止**。

### 3. 廃止する path

| Path | 現在の用途 | 廃止理由 |
|---|---|---|
| `HARDCODED_MURAKUMO_API_KEY = "murk_NQhD..."` (Worker src に埋込) | Cloudflare Secret 未設定時の fallback | git に key が出る / revoke 不能 / 監査不可 |
| CLI `~/.config/etzhayyim/murakumo_api_key` file | `etzhayyim murakumo ingest --extract-raw` の key 解決順 #3 | 別 token store、rotate 不整合、誰でも読める 0600 前提弱い |
| `murk_*` prefix 独自 token 発行 | gateway 認可 | `sk_live_*` で代替可 |
| `env.MURAKUMO_API_KEY` を hardcoded fallback の隠れ蓑に使う実装 | 上記 | 明示 env 時のみ許可、未設定時は fail closed |

### 4. credits 統合 (staged — 本 ADR は path を空ける only)

murakumo worker は現状 usage metering を持たない。ADR では以下の hook 点を明示:

```
pre-inference:  CheckSpendAllowed(ownerDid, "murakumo.inference.token", est_tokens)
                 via PDS service binding
                 → 残高不足なら 402 Payment Required
post-inference: SpendCredits(ownerDid, actual_tokens * rate)
                inferenceUsage record emit
```

実装は **別 PR** で段階導入 (credits ledger が production ready のタイミング)。本 ADR
では `ctx.ownerDid` を request context に持ち込み、後段 metering に渡せる状態まで作る。

### 5. CC Worker (cc26m4x1) への影響

CC Worker は既に `Authorization: Bearer ${env.MURAKUMO_API_KEY}` を
`murakumo.etzhayyim.com` に送る実装になっている (CC-Worker src/app.ts)。

- **変更**: `env.MURAKUMO_API_KEY` の **値** を `sk_live_*` に差し替えるだけ。
  Worker コード変更不要 (Authorization header 形式は同じ)
- 登録: `secrets_store_secrets` の `murakumo_api_key` を `sk_live_*` に rotate
  (atproto app と secret store を共有)

## Rationale

1. **Shannon 削減**: murk_* と sk_live_* の二重 secret 発行を 1 本化。
   `HARDCODED_MURAKUMO_API_KEY` の git leak risk を 0 に。
2. **監査可能性**: 各 inference call が `ownerDid` 付きで記録可能になり、
   ADR 0022 の "2-token model" + ADR 0023 の metering hook で per-user 使用量把握。
3. **rotate**: `etzhayyim authz create-api-key` / `revoke-api-key` で `murakumo.etzhayyim.com` の
   認可も自動的に切替わる。専用 rotate 手順消失。
4. **credits 開発の前提** を作っておく (blocker 除去)。

## Trade-offs

- 旧 clients (`murk_*` 決め打ち CLI, 既存 Mac 端末の config) は **1 回の
  `etzhayyim authz create-api-key` + env 差替** が必要。CLAUDE.md にマイグレーション手順。
- fail-closed 化で Cloudflare Secret 未設定時に gateway が 401 を返す → Worker の
  initial deploy で `MURAKUMO_API_KEY` secret 必須になる。

## Alternatives (rejected)

### A. murk_* を platform api_key system に取り込む

murk prefix の tokens を `vertex_api_key` に移すと、2 prefix の混在が残る。
Shannon 冗長増。却下。

### B. murakumo gateway を廃止して fleet 直叩き

fleet 側の認証が現状 Cloudflare Tunnel 任せ。Per-user 監査できず。却下。

### C. credits 課金も同 ADR で実装

scope 大、credits ledger 本番稼働の状態確認に依存。hook 点のみ置いて別 PR で
実装する方が安全。

## Exceptions

- `x-kotodama-verified` 経路 (Worker service binding) は引き続き許可。
  これは CF 内部 binding を通った service 間呼出 marker で、ADR 0022 の
  `internal` level と整合する。

## References

- `50-infra/cloudflare/workers/murakumo/src/index-ray.ts` — Worker gateway
- `50-infra/cloudflare/workers/atproto/src/auth/verify.ts:106` — verifyApiKey impl
- `70-tools/etzhayyim/etzhayyim/murakumo.go` — CLI key resolution chain
- `60-apps/etzhayyim-project-credits/CLAUDE.md` — credits ledger commands
