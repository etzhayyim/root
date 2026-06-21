# etzhayyim-project-yobel — Collective Debt Release Rites (etzhayyim activity)

集合的・教義的・政治的な債務免除 rite (`yobel.etzhayyim.com`) — שמיטה (shmita 7yr) / יובל (yobel 49yr) / 徳政令 / Catholic Jubilee / modern political amnesty。

**設計 SSoT**: `90-docs/adr/2605201700-yobel-jubilee-shmita-debt-release-actor.md`

## Operating Boundary

| 項目 | 値 |
|---|---|
| Operating entity | **etzhayyim** (運営宗教法人。Etzhayyim Japan vendor の関与なし) |
| Destination repo | `github.com/etzhayyim/root` (Apache 2.0) |
| License | Apache 2.0 |
| Substrate | AT MST + IPFS + Base L2 (kotoba, ADR-2605172000) |
| Settlement | USDC on Base L2 via ERC725 Smart Wallet (ADR-0074)。fiat / Stripe 禁止 |
| 3-axis split | etzhayyim 3/3 clean (Liability=doctrine / Custody=collective records / Settlement=on-chain) |

## Status

**proposed / pre-seed.** 本 directory はマーカー stub。実装 scaffolding は etzhayyim/root への seed PR で生成する。登記変更後の cutover (Step 11, 220-file sed) と同期する。

## Rite Catalog

→ ADR-2605201700 §"Rite Catalog" を参照。

| Rite | 周期/契機 | 教義的根拠 |
|---|---|---|
| `shmita_7yr` | 7 年毎 | Lev 25:1-7 / Deut 15:1-2 |
| `yobel_50yr` | 49/50 年毎 | Lev 25:8-13 |
| `tokusei_rei` | 政治契機 | 室町/鎌倉幕府慣行 |
| `religious_jubilee` | 25 年毎 | Boniface VIII 1300 / Indulgentiarum doctrina 1967 |
| `political_amnesty` | ad-hoc | HIPC 1996 / Jubilee 2000 / Paris Club |

## NSID

- Canonical (post-cutover): `org.etzhayyim.yobel.*`
- Transitional alias (本 repo 期間): `ai.etzhayyim.apps.yobel.*`

## Cluster Integration

→ ADR-2605201700 §"Cluster Integration" を参照。

```
yobel.etzhayyim.com (voluntary doctrinal)
 ├─ fallback     → bankruptcy.etzhayyim.com  (mandatory legal procedure)
 ├─ represented  → lawfirm.etzhayyim.com     (creditor consent, court filing)
 ├─ eligibility  ← trust.etzhayyim.com       (kyu/dan filter, optional)
 ├─ settlement   → ERC725 + Base L2 USDC release tx
 ├─ audit        → AT MST + IPFS append-only
 └─ publication  → app.bsky.feed.post (#shmita / #yobel / #徳政令 / #jubilee)
```

## Boundaries (CRITICAL)

- **Voluntary opt-in only.** 強制力なし。secular creditor が無視した場合は `bankruptcy.etzhayyim.com` fallback
- **Religious-corp doctrinal authority のみ.** secular law を override する主張は出さない
- **Tax/regulatory warning.** debt forgiveness は jurisdiction によって課税所得 (e.g. US IRC §61(a)(11) cancellation-of-debt income)。`jurisdictionNotes` で warning を返す。税務 advice は提供しない (→ lawfirm.etzhayyim.com に delegate)
- **No fiat settlement.** USDC on Base L2 only (ADR-2605172000 etzhayyim substrate)
- **No RisingWave.** etzhayyim substrate boundary により AT MST + IPFS + Base L2 のみ
