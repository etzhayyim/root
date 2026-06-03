---
id: 260427-lexicon-did-pattern-method-agnostic
title: Lexicon DID Pattern Method-Agnostic Migration
status: active
doc_type: how-to
topic: lexicon-validation
authoritative: true
last_verified: 2026-04-27
related:
  - adr-0074-ethereum-identity-bridge-cacao-webauthn
  - adr-0049-legal-corpus-global-ingest
---

# Lexicon DID Pattern Method-Agnostic Migration

## Goal

ADR-0074 が新規 platform primary identity を `did:erc725:etzhayyim:260425:{contract}` と定義した結果、
従来の lexicon で広く使われていた strict pattern `^did:etzhayyim:[0-9a-f]{24}(:[0-9a-f]{24}){0,5}$`
は did:erc725 / did:web / did:plc / did:pkh を拒絶してしまう。

ADR-0049 D5 で legal-corpus + 4 logical actors の lexicon を method-agnostic
(`format: "did"` のみ、pattern なし) で書き、これを repo-wide 規約として採用する。

## Decision

全 lexicon の DID 入力フィールドから strict regex pattern を削除し、`format: "did"` のみで
受理する。受理対象 DID method:

| method | 例 | 用途 |
|---|---|---|
| `did:erc725` | `did:erc725:etzhayyim:260425:0xAbC...` | platform primary identity (ADR-0074) |
| `did:web` | `did:web:lawfirm.etzhayyim.com`, `did:web:judge.etzhayyim.com:JPN:tanaka-001` | AT Protocol facade / external entity catalogue |
| `did:plc` | `did:plc:abcd1234...` | legacy AT primary (Bluesky compatibility) |
| `did:pkh` | `did:pkh:eip155:1:0xAbC...` | wallet alias (CAIP-10) |
| `did:etzhayyim` | `did:etzhayyim:lf1rm8k0:abc:def` | legacy / migration 期間中のみ受理 |

## Why pattern-free, not union-pattern?

Union pattern (例: `^(did:erc725:etzhayyim:[0-9]+:0x[0-9a-fA-F]+|did:web:...|did:plc:...|did:pkh:...|did:etzhayyim:...)$`) は:

1. 各 method の正規 syntax を tracking しなければならず、外部仕様 (CAIP-10, ERC-725) の
   drift で false-reject が発生する
2. 1 lexicon ファイル = 1 大型 regex の重複コードを 100+ ファイルに展開すると、
   仕様変更時の grep/edit コストが線形増加
3. 真の不変条件 (depth ≤ 6 for did:etzhayyim / contract-address checksum for ERC-725 等) は
   handler 内の business logic で検証すべき。lexicon は I/O contract layer

`format: "did"` だけ宣言し、syntactic 妥当性は handler の `parseDid()` ヘルパに委ねる。

## Scope

`grep -rl '"pattern": "\^did:' 00-contracts/lexicons/` で 15 ファイル抽出 (2026-04-27):

- `00-contracts/lexicons/com/etzhayyim/auth/mintChildDid.json`
- `00-contracts/lexicons/com/etzhayyim/apps/lawfirm/{14 files}`

各ファイルの JSON snippet `, "pattern": "^did:..."` を `sed`/`python` で削除。
JSON 構造、format 宣言、description は変更なし。

将来追加される lexicon は ADR-0049 D5 + 本ドキュメントに従い strict pattern を書かない。

## Verification

```bash
# 残留 strict pattern なし
grep -rl '"pattern": "\^did:' 00-contracts/lexicons/ | wc -l   # 0

# 全 JSON 妥当
find 00-contracts/lexicons -name "*.json" -exec python3 -c "import json,sys; json.load(open(sys.argv[1]))" {} \;
```

## Migration runbook

1. このドキュメントの commit 後、新規 lexicon は `format: "did"` のみ
2. 旧 strict pattern を含む既存 lexicon は本 PR で全削除済み
3. handler 側の DID validation は `parseDid()` / `isLegacyDidetzhayyim()` / `extractDidMethod()` に統合
4. `lawfirm.createMatter` 等の depth=2 invariant は handler 内 `firmDid.split(":").length === 4` で gate

## References

- ADR-0074 — ERC725 Root Identity + Coinbase Smart Wallet
- ADR-0049 — Global Legal Corpus (D5 で初めて method-agnostic 規約を確立)
- ADR-0029 — did:etzhayyim method spec (legacy)
