# etzhayyim-project-yobel — Collective Debt Release Rites

集合的・教義的・政治的な債務免除 rite (`yobel.etzhayyim.com` / `yobel.etzhayyim.com` federation alias)。
שמיטה (shmita 7yr) / יובל (yobel 49yr) / 徳政令 / Catholic Jubilee / modern political amnesty を統一データモデルで扱う。

**設計 SSoT**: `90-docs/adr/2605201800-etzhayyim-yobel-debt-release-actor.md`
**Twin design ADR (vendor side)**: `etzhayyim:90-docs/adr/2605201700-yobel-jubilee-shmita-debt-release-actor.md`

## Identity & Boundary

| 項目 | 値 |
|---|---|
| Operating entity | **etzhayyim** (3-axis split clean: liability=doctrine / custody=AT MST+IPFS / settlement=USDC on Base L2) |
| DID | `did:web:yobel.etzhayyim.com` (primary), `did:web:yobel.etzhayyim.com` (federation alias) |
| License | Apache-2.0 + Charter Compliance Rider v2.0 (`/CHARTER-RIDER.md`) |
| Charter alignment | Mission §1 (構造的労働解放) の monetary-debt 局面 doctrinal runtime |
| Substrate | AT MST + IPFS + Base L2 (RW-free) |
| Settlement | USDC on Base L2 via ERC725 Smart Wallet。fiat / Stripe / 銀行決済 禁止 |
| Eligibility gate | SBT membership (Council Lv1+) + rite type 別追加条件 |
| Ratification gate | rite declaration = Council Lv6+ ratification |

## Status

**proposed / pre-seed.** 本 directory は marker stub。実装 (`magatama.jsonld` / `src/app.ts` / Pregel cell) は本 ADR 採択後の follow-up PR で seed する。

## Rite Catalog

| Rite | 周期/契機 | 教義的根拠 | 範囲 |
|---|---|---|---|
| `shmita_7yr` | 7 年毎 | Lev 25:1-7 / Deut 15:1-2 | 共同体員間 monetary debt |
| `yobel_50yr` | 49/50 年毎 | Lev 25:8-13 | debt + land + bondage release |
| `tokusei_rei` | 政治契機 | 室町/鎌倉幕府慣行 | 借券無効化 |
| `religious_jubilee` | 25 年毎 | Boniface VIII 1300 + Paul VI 1967 | spiritual + temporal punishment |
| `political_amnesty` | ad-hoc | HIPC 1996 / Jubilee 2000 / Paris Club | sovereign / institutional |

## NSID

- Current (kuniUmi precedent と整合): `com.etzhayyim.apps.etzhayyim.yobel.*`
- Canonical (post-org-rename cutover): `org.etzhayyim.yobel.*`

Path: `00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/yobel/{declareRite,enrollCreditor,enrollDebtor,verifyEligibility,recordRelease,listRites,getRite,listReleases}.json`

## Cluster Integration

```
etzhayyim/yobel (voluntary doctrinal, USDC on Base L2)
 ├─ fallback     → vendor:bankruptcy.etzhayyim.com  (mandatory legal procedure, 84 jurisdictions)
 ├─ represented  → vendor:lawfirm.etzhayyim.com     (creditor consent letters, court filings)
 ├─ eligibility  ← council SBT registry       (Lv1+ membership gate)
 ├─ ratification ← council Lv6+               (rite declaration approval)
 ├─ settlement   → ERC725 Smart Wallet + Base L2 USDC release tx
 ├─ audit        → AT MST + IPFS append-only  (Charter §1.3 transparent)
 ├─ anchor       → MstCheckpointSaver + AnchorBridge (ADR-2605171800)
 └─ publication  → app.bsky.feed.post (#shmita / #yobel / #徳政令 / #jubilee)
```

## Invariants (CRITICAL — Charter §1 + Rider §2(b) compliance)

- **One-way debt forgiveness only.** 新規貸付・利息計算・margin・liquidation・arbitrage は不実装。schema レベルで担保 (lexicon に貸付メソッドなし)
- **Voluntary opt-in only.** secular creditor が無視した場合は vendor:bankruptcy.etzhayyim.com fallback
- **Religious-corp doctrinal authority のみ.** secular law を override する主張は出さない
- **Tax warning は出すが税務 advice は出さない.** `jurisdictionNotes` field で per-jurisdiction COD income warning を返却、税務 advice は vendor:lawfirm.etzhayyim.com に delegate
- **No fiat settlement.** USDC on Base L2 only
- **No RisingWave.** etzhayyim substrate boundary (vendor:ADR-2605172000) により AT MST + IPFS + Base L2 のみ
- **Council Lv6+ ratification for rite declaration.** Three-Tier Enforcement (ADR-2605192230) tier 3 と同等の重要性を持つため
