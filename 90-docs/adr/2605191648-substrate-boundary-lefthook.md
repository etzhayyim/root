---
id: 2605191648-substrate-boundary-lefthook
title: Substrate boundary enforcement via lefthook pre-commit
status: proposed
doc_type: adr
topic: substrate-governance
authoritative: true
last_verified: 2026-05-19
depends_on:
  - adr-2605172000-etzhayyim-kotoba-substrate
  - adr-2605172100-etzhayyim-payments-on-chain-only
related:
  - adr-2605173100-gitguardian-incident-response
V05191346-etzhayyim-vultr-free-murakumo-control-plane
---

# ADR 2605191648: Substrate boundary enforcement via lefthook pre-commit

## Context

ADR-2605172000(kotoba state substrate)+ ADR-2605172100(payments
on-chain only)が **etzhayyim/* 全体の architectural invariant** を
定義したが、 enforcement は人間レビューに依存していた。 過去には
GitGuardian インシデント(ADR-2605173100)で Kotoba/Datomic credential が
HEAD に紛れ込むなど、 ガード無しで HEAD が落ちる事故も発生。

contributing pattern が増えるにつれて(parallel branches: `cf-worker-murakumo`、`sdk-write-read-impl`、`ameno-daemon-wave`、`e7m-cli` 等)、commit gate での 機械的 enforcement が必要。

`lefthook.yml` には既に `secret-scan` / `trailing-whitespace` / `end-of-file` の 3 hook がある(scaffolding stub と銘打って TODO 残し)。本 ADR で **substrate-boundary hook を追加** し、 ADR-2605172000 / 172100 を構造的に守る。

## Decision

**`pre-commit` で `node 70-tools/scripts/lint/substrate-boundary.mjs {staged_files}` を走らせる。**

### スクリプト責務

staged な `.ts` / `.tsx` / `.js` / `.jsx` / `.mjs` / `.cjs` / `.py` / `.svelte` ファイルを scan、 以下 import が **SDK seam の外** で見つかれば commit を block:

| カテゴリ | 禁止 import | 推奨置換 |
|---|---|---|
| 中央集権 storage(ADR-2605172000) | `kysely` / `pg` / `postgres` / `mysql` / `mongodb` / `kotoba` / `@kotobalabs/*` / `psycopg` / `psycopg2` / `pg8000` | `@etzhayyim/sdk/{pds,checkpointer}` |
| Fiat 決済(ADR-2605172100) | `stripe` / `@stripe/*` / `paypal-rest-sdk` / `@paypal/*` / `square` / `razorpay` / `braintree` / `@braintree/*` / `@adyen/*` | `@etzhayyim/sdk/pay`(USDC + ERC-4337) |
| Substrate client seam(ADR-2605172000 §seam) | `@atproto/api` / `viem` / `@noble/ciphers` / `@signalapp/libsignal-client` / `ipfs-http-client` / `helia` | `@etzhayyim/sdk` |

### Allowlist(SDK seam + substrate components)

`70-tools/scripts/lint/substrate-boundary.mjs` の `allowedPrefixes`:

```js
"20-actors/etzhayyim-sdk/",
"50-infra/etzhayyim-sdk-checkpointer/",
"50-infra/mst-projector/",
"50-infra/anchor-cron/",
"50-infra/etzhayyim-{paymaster,membership-contract,chain-contracts,did-web,pds-did-web}/",
"50-infra/cloudflare/",
"50-infra/vultr/",           // etzhayyim.com legacy (ADR-2605191346 §2)
"50-infra/l2-anchor-contract/",
"_archive/",
"60-apps/etzhayyim-project-ameno/appview/.../_svelte/",  // vite build output
```

加えて test / spec / example / node_modules / dist パスは pattern マッチで除外。

### Error message UX

block 時:

```
✘ substrate-boundary lint failed — direct imports detected outside the SDK seam.
  These are prohibited by ADR-2605172000 / ADR-2605172100.

  60-apps/etzhayyim-project-foo/src/app.ts:12  storage substrate (ADR-2605172000)
    pattern: from "kysely"
    fix:     route through @etzhayyim/sdk (Kysely (use @etzhayyim/sdk read/write))

If this file genuinely IS a substrate component, add its
path prefix to `allowedPrefixes` in this script with a code
comment justifying the exception.
```

### 検証

ADR commit 自身でも substrate-boundary を通る:本 PR の changeset は
script + lefthook config + ADR の 3 ファイルのみ、 substrate import なし。

### 既存コードベースは scan しない

hook は **staged files のみ**に対して走る。 既存の repo 全体には未適用
(legacy etzhayyim 系コードに既存違反が残るのは別 sweep PR で対応)。
新規 commit から先は守られる。

### bypass

緊急時の `git commit --no-verify` は許可するが、 reviewer が PR で
理由を明文化する義務 - `bypass-substrate-boundary` ラベルなどの GitHub
側ルール化は別 ADR で。

## Consequences

- ADR-2605172000 / 172100 が **構造的に維持される**:人間レビューの
  see-and-block ではなく、 commit 時点でハードブロック
- 例外を作る場合は allowlist に明示追記 → コメントで justify、自動的に
  audit trail 化(git blame で誰が allowlist を緩めたか追跡可)
- pre-commit が ~50ms 程度の追加コスト(ファイル数依存)。気にならない
- 既存ファイルを edit すると hook が走る → legacy 違反 file を触ると
  block されることがある(`--no-verify` で個別判断)
- ADR-2605191346(Vultr-free)とも整合:vultr/ パスは etzhayyim legacy として
  allowlist 内、 etzhayyim 開発者は `50-infra/vultr/` に手を入れない
  運用と相性が良い

## Alternatives Considered

1. **CI のみで enforce(commit は通す)** — feedback ループが長い、
   既に PR を開いてからの修正コスト高
2. **TypeScript compiler API による semantic 解析** — overkill、 string
   match で十分(import 文は宣言的)
3. **eslint plugin** — JS のみ。 Python 含めると独自 script 不可避
4. **GitHub branch protection rule で main を保護** — 並走戦略には弱い、
   pre-commit + CI の組合せが堅い

## References

- ADR-2605172000(kotoba substrate、 本 hook の根拠)
- ADR-2605172100(payments on-chain only、 同上)
- ADR-2605173100(GitGuardian incident、 過去の boundary 違反例)
- ADR-2605191346(Vultr 非依存、 vultr/ パスを etzhayyim legacy として明示)
- `70-tools/scripts/lint/substrate-boundary.mjs`
- `lefthook.yml` § pre-commit.substrate-boundary
