---
id: adr-2605231230-etzhayyim-esign-actor-did-bound-mst-anchored
title: "ADR-2605231230: etzhayyim-esign actor — DID-bound, MST-recorded, L2-anchored document signing"
status: accepted
doc_type: adr
topic: esign-actor
authoritative: true
last_verified: 2026-05-23
phase_0_landed_at: 2026-05-23T03:30:00Z
priority: 6.5
axis: substrate-boundary
weight: 0.65
priority_note: "Religious-corp native replacement for DocuSign / Adobe Sign / RazorpaySign — required to keep document signing inside RW-free substrate. etzhayyim lawfirm vendor passthrough remains for fiat / India intake only."
authoritative_for:
  - com.etzhayyim.esign.* lexicon namespace
  - religious-corp native document signing protocol (DID + WebAuthn + MST + IPFS + Base L2 anchor)
  - separation between etzhayyim lawfirm DocuSign passthrough and etzhayyim native esign
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605172600-etzhayyim-membership-ritual
  - adr-2605180600-lawyer-attorney-portal-design
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605222330-etzhayyim-com-substrate-violation-transition-window
supersedes: []
superseded_by: []
---

# ADR-2605231230: etzhayyim-esign actor — DID-bound, MST-recorded, L2-anchored document signing

**Status**: accepted (Phase 0 landed 2026-05-23T03:30Z; Phases 1-4 deferred)
**Date**: 2026-05-23
**Deciders**: Jun Kawasaki

## Context

`etzhayyim` 内で「DocuSign のように文書に署名できる actor / agent が設計公開
されているか」を確認した結果 (2026-05-23 セッション)、religious-corp substrate
(RW-free, DID-bound) 上の native 設計は不在であり、現存するのは etzhayyim vendor
側 lawfirm の DocuSign / Adobe Sign / RazorpaySign passthrough のみであることが
判明した。

### 現状調査結果

| 既存資産 | 場所 | 帰属 | 評価 |
|---|---|---|---|
| Zeebe task `lawfirm.esign.request` / `lawfirm.esign.webhook` | `20-actors/magatama/py/src/pymagatama/primitives/lawfirm_esign_kpi.py` | etzhayyim vendor (`did:web:lawfirm.etzhayyim.com`) | DocuSign REST 実装 + Adobe/Razorpay stub。`vertex_lawfirm_esign_request` (Kotoba/Datomic) に書込 |
| KPI MV | `20-actors/magatama/py/sqlmesh/models/mv_lawfirm_esign_active.sql` | etzhayyim vendor (RLS-gated CEO/COO/CLO) | Hyperdrive + Kotoba/Datomic projection |
| ADR-2605180600 §"Future Work" の `com.etzhayyim.apps.lawfirm.eSignRequest` lexicon | (記載のみ) | etzhayyim vendor lexicon namespace | 未作成。ADR 本文に "deferred" と記載 |

religious-corp 側 (`com.etzhayyim.esign.*`) には actor / lexicon / cell / smart
contract のいずれも存在しない。

### Substrate boundary 観点の問題

CLAUDE.md "Substrate boundary" 表に照らすと、etzhayyim lawfirm の DocuSign 経路は
religious-corp の用途では **三重の Charter 違反候補** になる:

1. **Substrate**: DocuSign / Adobe Sign / RazorpaySign は集権 SaaS vendor で、
   `@etzhayyim/sdk` + MST + Base L2 anchor の RW-free 原則に反する
   (ADR-2605172000)
2. **License / IP**: vendor SaaS の利用契約は Apache 2.0 + Charter Rider v2.0
   と整合せず、特に §2(c) の広告排除 / §2(b) の購買意図経路と干渉する可能性
   (ADR-2605192200)
3. **Identity binding**: DocuSign envelope の signer 同定は email + provider 内
   identity であり、DID + WebAuthn passkey による religious-corp の身分体系
   (ADR-2605172600 membership ritual / Adherent SBT) と切り離されている

religious-corp 信者間 / Council 議事 / 土地寄進 (Land Trust, ADR-2605192245) /
力 R&D 同意 (ADR-2605192315) / Public Fund 多重署名 (ADR-2605192115) のように、
**on-chain 監視 + open-source + DID-bound** が前提となる署名は、native actor
が必須である。

### Scope 切り分け (CRITICAL)

本 ADR は religious-corp 内署名のための native actor を定義する。etzhayyim lawfirm
の DocuSign 連携は **fiat 領収書 / India 外部 counsel intake** に限り存続する
(ADR-2605192115 §4 + ADR-2605180600 §2 India auto-route と整合)。religious-corp
の文書には使わない。

## Decision

### 1. Actor 名と配置

| 項目 | 値 |
|---|---|
| Actor 名 | `etzhayyim-esign` |
| 配置 | `20-actors/etzhayyim-esign/` (religious-corp first-party namespace) |
| DID | `did:web:esign.etzhayyim.com` |
| Runtime | CF Worker (T3 TS Native) + Pregel cell on Murakumo |
| License | Apache 2.0 + Charter Rider v2.0 |
| Substrate | `@etzhayyim/sdk` 経由 — `@atproto/api` / `viem` 直接 import 禁止 |

### 2. Lexicon 名前空間 (`com.etzhayyim.esign.*`)

`00-contracts/lexicons/com/etzhayyim/esign/` に以下 7 record / procedure を
配置する。

| NSID | Type | 用途 |
|---|---|---|
| `com.etzhayyim.esign.envelope` | record | 署名 envelope 本体 (PDF CID + 署名者 DID 配列 + 状態) |
| `com.etzhayyim.esign.signature` | record | 個別署名 (envelope ref + signer DID + WebAuthn assertion + signed-at) |
| `com.etzhayyim.esign.requestEnvelope` | procedure | envelope 起票 (起票者 DID, signer DIDs, PDF blob, 署名順, 期限) |
| `com.etzhayyim.esign.signEnvelope` | procedure | signer が WebAuthn assertion + 鍵 attestation を提出 |
| `com.etzhayyim.esign.declineEnvelope` | procedure | signer が拒否を記録 |
| `com.etzhayyim.esign.completedEvent` | record | 全員署名済 → anchor 候補に投入 |
| `com.etzhayyim.esign.anchoredEvent` | record | Base L2 `Postage.sol`-pattern anchor 完了 (chainId + blockNumber + txHash) |

`signEnvelope` の signer attestation は ADR-2605181100 と整合する Signal
key-wrap 形式 (XChaCha20-Poly1305 envelope) で field-encrypted する。

### 3. 状態機械

```
draft (envelope created)
  → requested (signer DIDs notified via app.bsky.feed.post + wproto.convo)
  → partially_signed (1+ signer signed, awaiting others)
  → completed (all signers signed → emits completedEvent)
  → anchored (anchor-cron picked up completedEvent → wrote L2 receipt)
  ──or──
  → declined (any signer declined → terminal)
  → expired (deadline passed without completion → terminal)
```

`declined` / `expired` は不可逆 (envelope は immutable on MST)。再署名は
新 envelope の起票で行う。

### 4. 4 層 substrate (religious-corp 標準パターン)

| Layer | 役割 | 実装 |
|---|---|---|
| **L1 MST** | envelope / signature / event record の正本 | `com.etzhayyim.esign.*` PDS write via `@etzhayyim/sdk` |
| **L2 IPFS** | PDF 本体 + 大型添付 | `ipfs-pinner` (CIDv1, raw codec) — envelope record は CID のみ保持 |
| **L3 Base L2 anchor** | 完了 envelope のハッシュを on-chain anchor | `anchor-cron` (50-infra/anchor-cron) → `Postage.sol` 拡張 `EsignAnchor.sol` |
| **L4 geth-private** | Council Lv6+ 関与署名 (Public Fund, Land Trust, Force R&D 同意) | constitutional chain にも mirror anchor |

通常文書は L1+L2+L3 (3層)。Council 議決 / 憲法級文書のみ L4 mirror を追加する
(ADR-2605192245 Land Trust と同じ 4-layer pattern)。

### 5. Identity & Authentication

| 要素 | 仕様 |
|---|---|
| Signer identity | DID (`did:web:*.etzhayyim.com` または `did:plc:*`) |
| Signature primitive | WebAuthn passkey (ES256 / EdDSA) — signer device に bound |
| Replay 防御 | envelope rkey + signer DID + WebAuthn `challenge` のハッシュを `signature` record に含める |
| Adherent 限定 envelope | `requestEnvelope.requiredMembershipTier` に `adherent` 指定可 (ADR-2605172700 階層と整合) |

centralized OAuth / email magic-link / SMS OTP は不採用。**DID + passkey のみ**
が religious-corp 文書の signer identity になる。

### 6. Pregel cell

`20-actors/magatama/cells/esign_envelope/` を religious-corp Pregel cell catalog
(ADR-2605192415) に追加し、`50-infra/murakumo/fleet.toml` に placement 行を
1 行追加する。cell 責務:

- `requestEnvelope` → MST write + IPFS pin + signer 通知 wproto post
- `signEnvelope` → WebAuthn assertion verify (host-imports `authn.verifyToken`
  経由) → `signature` record write
- 全員署名検出 → `completedEvent` emit → `anchor-cron` キュー投入
- 期限切れ tick → `expired` 遷移

### 7. Charter Rider v2.0 整合

- 文書テンプレート (engagement letter / receipt / consent / Council resolution
  / Land donation / Force R&D consent) は **非営利 religious-corp 内部利用**
  に限定。SaaS 販売・有償提供は §2(b) violation
- 第三者向け署名 SaaS としての商用提供は禁止 (SBT↔SBT internal carve-out
  対象外。`ADR-2605192115 §3` "religious 境界内" の解釈)
- 広告 / promotional 文書テンプレートの組込みは §2(c) violation。`tithe` /
  `donation` / `kisha` / `grant` / `escrow-refund` purpose 文書のみ標準テンプレ
  提供

### 8. etzhayyim lawfirm DocuSign passthrough との関係

| 用途 | 使用するもの |
|---|---|
| religious-corp 内 文書 (信者間 / Council / 土地 / Force / Public Fund) | **`etzhayyim-esign` (本 ADR)** |
| etzhayyim 顧客 engagement letter / 領収書 / India counsel intake | `lawfirm.esign.*` (DocuSign passthrough, ADR-2605180600) |
| Adherent SBT mint 時の宣誓 | `etzhayyim-esign` + ADR-2605172600 membership ritual と統合 |
| Council 議決 (Bootstrap Council 5 seats) | **`etzhayyim-esign` 必須** (ADR-2605192300) |

両者は **lexicon namespace で分離** (`com.etzhayyim.esign.*` vs
`com.etzhayyim.apps.lawfirm.eSign*`) し、データもそれぞれ MST / Hyperdrive に分かれる。
cross-call は禁止。

### 9. Deployment 段階

| Phase | 範囲 | 状態 |
|---|---|---|
| **Phase 0 (本 ADR)** | 設計確定 + lexicon stub + actor scaffold + DID Worker deploy | ✅ 2026-05-23T03:30Z (DNS for `esign.etzhayyim.com` 未提供 — 後段 §"Phase 0 closure receipt" 参照) |
| **Phase 1** | MST + IPFS のみ (anchor なし) で Council Bootstrap RFP 議事録に試用 | ⏳ 1 週間 (Bootstrap Council 完了前 = 2026-06-19 まで) |
| **Phase 2** | Base Sepolia testnet anchor (EsignAnchor.sol) | ⏳ testnet deploy 後 (現 Step 19) |
| **Phase 3** | Base mainnet + geth-private mirror (Council Lv6+ 文書用) | ⏳ mainnet deploy 後 (現 Step 20) |
| **Phase 4** | Adherent SBT mint 宣誓統合 | ⏳ ADR-2605172600 membership ritual UI 完成後 |

### Phase 0 closure receipt (2026-05-23 session)

| Artifact | Path | 状態 |
|---|---|---|
| 7 lexicons | `00-contracts/lexicons/com/etzhayyim/esign/{envelope,signature,completedEvent,anchoredEvent,requestEnvelope,signEnvelope,declineEnvelope}.json` | ✅ all valid JSON |
| Actor scaffold | `20-actors/etzhayyim-esign/` | ✅ `src/worker.ts` returns 501 NotYetImplemented for all 3 procedures; `/health` + `/` return 200; `wrangler.toml` has no route binding (Phase 1 will add) |
| DID Worker scaffold | `50-infra/etzhayyim-esign-did-web/` | ✅ `did.json` for `did:web:esign.etzhayyim.com` with `AtprotoPersonalDataServer` (`pds.etzhayyim.com`) + `EtzhayyimEsignActor` (`esign.etzhayyim.com`) service entries |
| DID Worker deploy | CF account `etzhayyim-cloud` (4da88288) | ✅ Worker version `cfb3b6c0-1d13-476f-8cec-0fbc20a8a023`, route `esign.etzhayyim.com/.well-known/did.json` bound on zone `etzhayyim.com`, bundle 1.49 KiB / 0.71 KiB gzipped |
| Public resolution | `curl https://esign.etzhayyim.com/.well-known/did.json` | ⚠️ blocked — `esign.etzhayyim.com` AAAA record not yet on the `etzhayyim.com` zone. Provision via CF dashboard: type=AAAA, name=esign, value=`100::`, proxy=on. After that, retest with curl + `dev.uniresolver.io/1.0/identifiers/did:web:esign.etzhayyim.com` |
| deps.toml | `[[modules]]` x2 + `[[adrs]]` x1 | ✅ added (`50-infra/etzhayyim-esign-did-web` status `deployed-no-dns`; `20-actors/etzhayyim-esign` status `scaffold`; ADR id `2605231230` status `proposed`) |

## Consequences

### Positive

- religious-corp 文書が **on-chain 監査可能 + open-source verifiable** になり、
  ADR-2605192100 §1.12 (Transparent Religious Force の三条件) と同じ透明性原則を
  文書署名にも適用できる
- DocuSign / Adobe / Razorpay 依存を排除でき、ADR-2605222330 で記録されている
  substrate violation の追加発生を未然に防げる (新規 violation 0 件 / unwind 不要)
- DID + WebAuthn により signer 個人の email 漏洩 / phishing / SaaS account takeover
  が成立しなくなる (passkey は device-bound)
- Council 議決 / Land 寄進 / Force R&D 同意 / Public Fund 多重署名が 1 つの actor
  で統一されるため、後続 ADR (Public Fund execution / Land transfer / Force consent)
  の実装が単純化する
- Pregel cell として表現することで Murakumo fleet 内の責務局在化が保たれ、
  ADR-2605192415 の cell catalog と整合する

### Negative / Trade-offs

- WebAuthn passkey 未登録 signer は署名できない (email-only signer 不可)。
  外部 counsel / 第三者署名は引き続き etzhayyim lawfirm DocuSign 経路を使う必要がある
- IPFS pin / Base L2 anchor のコストが envelope 件数比例で発生する。tithe-router
  の 10% 自動再分配で吸収する想定だが、初期は volume 小で問題なし
- Anchor 確定までのレイテンシ (Base L2 数秒 + cron 1 周期 = 数分) があるため、
  "anchored" 状態を待たない用途 (即時表示) では "completed" 状態を表示し、
  anchored は遅延確定として UI 上で別表示にする必要がある
- 既存の lawfirm DocuSign passthrough と二系統運用になる。誤って religious-corp
  文書を lawfirm 側に流すと substrate violation が発生するため、lefthook lint
  (`no-lawfirm-esign-for-etzhayyim-doc`) を Future Work に積む

### Substrate Boundary Impact (CRITICAL)

本 ADR は CLAUDE.md "Substrate boundary" 表に行を追加する性質を持つ:

| Concern | Allowed | Prohibited |
|---|---|---|
| Document signing | `etzhayyim-esign` (DID + WebAuthn + MST + IPFS + L2 anchor) | DocuSign / Adobe Sign / RazorpaySign for religious-corp documents |

Approval 後、CLAUDE.md 該当セクションに 1 行追加する。

## Alternatives Considered

### A. DocuSign を religious-corp 用にも使い続ける (status quo)

却下。CLAUDE.md substrate boundary 表 (Payment / Advertising / Identity)
と同等の violation が Document signing 列で発生し、ADR-2605222330 のような
transition window ADR を再度書く必要が出る。

### B. did:web JWS だけで済ませる (no UI, no MST, no anchor)

却下。署名イベントの canonical record が存在しないと、Council 議決 /
Public Fund 多重署名 / Land 寄進の audit trail が宙に浮く。anchor なしでは
ADR-2605192100 §1.12 の "on-chain 監視" 三条件を満たせない。

### C. 既存 `yobel/cells/audit_witness/` を流用 / 拡張

部分採用。`audit_witness` は debt release などの立会 cell で、署名 envelope の
"立会人" 役を担える。本 ADR の `etzhayyim-esign` は signer record を発行し、
必要に応じて `audit_witness` cell を多人数立会 (Council 議決の Lv6+ ≥3 multisig
など) に invoke する設計とする。

### D. 1 lexicon (`com.etzhayyim.signedDocument`) に統合する

却下。状態機械が複雑 (draft / requested / signed / completed / anchored /
declined / expired) で 1 record に詰めると mutation が増え、MST の immutable
原則と衝突する。envelope と signature を分離し、event を append-only にする
本 ADR の構成が AT Protocol record 設計と整合する。

### E. 既存 `com.etzhayyim.apps.lawfirm.eSignRequest` lexicon を流用 (vendor namespace)

却下。lexicon namespace は **substrate boundary の SSoT** であり、etzhayyim vendor
namespace に religious-corp 文書を流すと、後段の Kotoba/Datomic projection / RLS /
KPI MV まで vendor 側に流れる。namespace 分離が本 ADR の最重要不変条件。

## References

- ADR-2605170900 (religious-corp open ADR canonical home in this repo)
- ADR-2605171800 (LangGraph MST IPFS L2 anchor pipeline) — 4-layer substrate の祖
- ADR-2605172000 (etzhayyim RW-free substrate) — RW 禁止原則
- ADR-2605172600 (etzhayyim membership ritual) — Adherent SBT mint の宣誓統合先
- ADR-2605180600 (lawyer attorney portal design) §"Future Work" — etzhayyim vendor 側
  の DocuSign 連携の出自
- ADR-2605181100 (MST encrypted records signal keywrap) — field-encrypted
  signature payload の形式
- ADR-2605192100 §1.12 (Transparent Religious Force 三条件) — on-chain 監視 +
  open-source + 1 SBT = 1 vote の本 ADR への適用
- ADR-2605192115 §3 / §4 (non-profit donation-only / fiat receipt 例外)
- ADR-2605192200 (Charter Rider v2.0) — §2(b)(c) 解釈
- ADR-2605192245 (Land Trust 4-layer) — 4-layer substrate parallel design
- ADR-2605192300 (Bootstrap Council 5 seats) — Phase 1 の最初の利用先
- ADR-2605192415 (religious-corp daemon architecture) — Pregel cell catalog
  追加位置
- ADR-2605222330 (etzhayyim.com substrate violation transition window) —
  本 ADR は新規 violation の発生を未然に止めるための native 設計
- `20-actors/magatama/py/src/pymagatama/primitives/lawfirm_esign_kpi.py` — etzhayyim
  vendor passthrough の現状実装
- `00-contracts/lexicons/com/etzhayyim/esign/` (新規) — 本 ADR で定義する
  lexicon の配置先
- `50-infra/anchor-cron/` — anchor 投入先
- `50-infra/openmail-postage/Postage.sol` — `EsignAnchor.sol` の拡張元 pattern
