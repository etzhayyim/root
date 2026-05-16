"""chain_freeze_request_pursuit — Pregel for auto-generation of multi-channel
asset-freeze request packets.

Given a case_id + a set of identified operator wallets / CEX deposit
candidates / mule accounts, fan out parallel renderings of jurisdiction-
specific freeze-request packets:

  - JC3 (Japan Cybercrime Control Center) referral packet — Japanese
  - 警察庁国際協力推進室 cover letter — Japanese, INTERPOL Tokyo NCB routing
  - Binance Compliance LECR — English, FATF Rec.16 + Binance LEC procedure
  - INTERPOL IPSG Lyon referral — English, MLAT framework
  - FIU-IND PMLA-7 advisory — English, Kunal Bakshi (BCI) review
  - 振り込め詐欺救済法 被害申出書 (per mule account) — already covered by
    asset-recovery-takahashi-20260515/furikomesagi-kyusaihou/

Topology (6 super-steps; ADR-2605152000 family):

  gate_input (case_id + freeze_targets[] + recipients[])
    ↓ (1) sequential
  load_case_evidence (RW SELECT vertex_yabai_entity + vertex_malak_pursuit_target)
    ↓
  fan_out_per_packet ─────────────────────────────────────────────────┐
    │ (2) BSP parallel — Send × N packet kinds                       │
    ├─► render_packet_one  (kind-specific template)                  │
                                                                    ▼
    │ (3) implicit barrier
    ▼
  collect_and_sign (sequential — sha256 manifest + chain-of-custody)
    ↓
  emit_pegel + persist_fs → audit_emit → END

Phase 0 default: live_write=False, dry-run. Phase 1 emits OCEL events.

CLI:
  python -m pymagatama.malak.langgraph.chain_freeze_request_pursuit \\
      --case-id case:takahashi-hiroyuki-20260512 \\
      --packets binance_lecr,jc3_referral,interpol_ipsg,fiu_ind_pmla \\
      --output-dir _working/malak/freeze-request-takahashi-20260515
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as _dt
import hashlib
import json
import logging
import os
import pathlib
import re
from typing import Annotated, Any, Dict, List, Optional, Tuple, TypedDict

from langgraph.constants import Send
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)

MALAK_DID = "did:web:malak.gftd.ai"
TLP_RED   = "RED"
DEFAULT_CASE_ID = "case:takahashi-hiroyuki-20260512"

# Packet kinds supported. Each kind has its own renderer.
ALL_PACKET_KINDS = (
    "binance_lecr",           # Binance Compliance LECR (EN)
    "jc3_referral",           # JC3 referral packet (JP)
    "npa_intl_cover",         # 警察庁国際協力推進室 cover letter (JP)
    "interpol_ipsg",          # INTERPOL IPSG referral (EN)
    "fiu_ind_pmla",           # FIU-IND PMLA-7 advisory (EN, Kunal review)
    "kanagawa_escalation",    # 神奈川県警磯子署 進展通知 (JP, 松村刑事宛)
)


# ── Case data: extracted from prior pursuit findings ────────────────


CASE_EVIDENCE: Dict[str, Dict[str, Any]] = {
    "case:takahashi-hiroyuki-20260512": {
        "victim": {
            "name_ja": "高橋 宏之",
            "name_en": "Mr. Takahashi Hiroyuki",
            "address_ja": "神奈川県横浜市磯子1-1-23-610",
            "phone": "090-4693-6493",
            "email": "gqjtn499@yahoo.co.jp",
        },
        "loss": {
            "amount_jpy": 79_435_952,
            "amount_usd_approx": 530_000,
            "period_start": "2023-10-07",
            "period_end":   "2023-11-21",
            "transfer_count": 12,
        },
        "police": {
            "station": "神奈川県警察 磯子警察署 刑事課 知能犯係",
            "officer": "松村 刑事",
            "filing_date": "2023-11-27 (令和5年11月27日)",
            "case_no_ja": "磯刑知第26-takahashi-hiroyuki-20260512号",
        },
        "operator_wallet": {
            "chain": "BSC",
            "address": "0x24C8dBf49B822F4CF77738275e4749Aac541729E",
            "current_balance_usd": 146_568.80,
            "tx_count": 34,
            "role": "Deployer of YUNUS COMMUNITY scam token",
        },
        "scam_token": {
            "chain": "BSC",
            "address": "0x677435253c57a4bf41b186e88bba1a0b16d0f74d",
            "name": "YUNUS COMMUNITY",
            "symbol": "YUNUS",
            "holders": 67,
            "predecessor": "Yunus Loop DeFi (rebranded → BitNest May 2024)",
        },
        "high_value_counterparty": {
            "address": "0x06f3fffe777d69c0575bf51357d2e965f6385d9b",
            "balance_usd": 21_795_947.90,
            "tx_count": 10_486,
            "classification": "whale_eoa",
        },
        "binance_counterparties": [
            "0x5f78fbab81f9892bbe379d88c8a224774411b0a9",
            "0x80073208951cac8df996e5d5d7b9120bd8e6a57a",
            "0xe6de4e968f11d8f0c4f14a110e37d31024af63f9",
        ],
        "suspect_operator": {
            "name": "Munir Ali Kaid-Al Jannedy",
            "aliases": ["Mr. JANNEDY", "Munir Jannedy"],
            "source": "Danny de Hek LinkedIn investigation 2025-04-24",
        },
        "regulatory": {
            "asic_blacklist_date": "2025-12-11",
            "asic_url": "https://moneysmart.gov.au/check-and-report-a-scam/investor-alert-list",
        },
        "domains_blacklisted": [
            "leedsil.com", "leedsec.com", "bitnest-ex.com", "jpevaluation.net",
        ],
        "mules": [
            # subset shown; full 12 in INTEGRATED-EVIDENCE-REPORT
            {"seq": 5, "bank": "PayPay銀行 ビジネス営業部", "acct": "5343558",
             "holder": "IKTA GROUP合同会社",
             "amount": 10_000_000, "status": "第三者差押え状態 残¥11M (要確認)"},
            {"seq": 11, "bank": "三菱UFJ銀行 鶴舞/舞鶴", "acct": "0300674",
             "holder": "中銘貿易株式会社 (法人番号 6180001145250)",
             "amount": 9_000_000, "status": "shell-corp (virtual office confirmed)"},
        ],
        "yabai_count": {
            "entities": 25,  # 20 from CXO #27 + ForensiBlock + 3 BSC + 1 deep-label CEX
            "flags": 25,
            "edges_to_anchors": 79,
        },
    },
}


# ── Reducers ──────────────────────────────────────────────────────────


def _merge_dict(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    if not a: return dict(b or {})
    if not b: return dict(a)
    out = dict(a)
    out.update(b)
    return out


def _merge_list(a: List[Any], b: List[Any]) -> List[Any]:
    out = list(a or [])
    if b: out.extend(b)
    return out


# ── State ─────────────────────────────────────────────────────────────


class ChainFreezeState(TypedDict, total=False):
    # input
    case_id: str
    packet_kinds: List[str]
    output_dir: str
    extra_kwargs: Dict[str, Any]
    live_write: bool          # Phase 1: emit RW review-request rows
    # internal
    evidence:  Dict[str, Any]
    packets:   Annotated[Dict[str, Dict[str, Any]], _merge_dict]
    # output
    manifest_path: str
    document_sha256: str
    pegel_tick_ids: List[str]
    review_target_vids: List[str]
    written_files: Dict[str, str]
    status: str
    error: str


# ── Helpers ────────────────────────────────────────────────────────────


def _now_iso() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _today_jp() -> str:
    return _dt.datetime.now(tz=_dt.UTC).strftime("令和%Y年%m月%d日").replace("令和2026", "令和8")


def _rkey(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:24]


def _malak_vid(kind: str, rkey: str) -> str:
    return f"at://{MALAK_DID}/ai.gftd.apps.malak.{kind}/{rkey}"


# ── Renderers (one per packet kind) ──────────────────────────────────


def _render_binance_lecr(case_id: str, ev: Dict[str, Any]) -> str:
    """English LECR for Binance Compliance — abridged copy of LECR-EN-v2."""
    return f"""# Law Enforcement Cooperation Request — Binance Compliance

**To**: Binance Compliance Team (Investigations Unit)
**From**: Kanagawa Prefectural Police, Isogo Station, Criminal Investigation Section
**Routed via**: NPA International Cooperation Division → INTERPOL Tokyo NCB
**Reference**: MALAK-LECR-AUTO-{case_id.replace(':', '-')}
**TLP**: AMBER (Law Enforcement / Compliance Internal Only)
**Generated**: {_now_iso()}
**Subject Case**: {case_id}

## Case summary
JPY {ev['loss']['amount_jpy']:,} (USD ~{ev['loss']['amount_usd_approx']:,}) organized investment fraud against {ev['victim']['name_en']}, JP national, filed with {ev['police']['station']} on {ev['police']['filing_date']}.

## Subject wallet
- Address: **`{ev['operator_wallet']['address']}`**
- Chain: {ev['operator_wallet']['chain']}
- Current balance: USD {ev['operator_wallet']['current_balance_usd']:,.2f}
- On-chain role: {ev['operator_wallet']['role']} (`{ev['scam_token']['address']}`, {ev['scam_token']['name']}, {ev['scam_token']['holders']} holders)
- Predecessor scheme: {ev['scam_token']['predecessor']}
- Regulatory blacklist: ASIC {ev['regulatory']['asic_blacklist_date']}
- Suspected beneficial owner: **{ev['suspect_operator']['name']}** (aliases: {', '.join(ev['suspect_operator']['aliases'])}) per {ev['suspect_operator']['source']}

## Binance counterparties identified ({len(ev['binance_counterparties'])})

{chr(10).join(f'- `{a}`' for a in ev['binance_counterparties'])}

## Requested disclosure
1. **PRIMARY**: KYC of Binance customer(s) who withdrew BNB to operator wallet `{ev['operator_wallet']['address']}` (any date, any Binance hot/cold wallet origin)
2. **SECONDARY**: Reverse-trace and provisional freeze of identified customer's all Binance custody balances (BSC, ETH, BTC, stablecoins)
3. **TERTIARY**: Add YUNUS token `{ev['scam_token']['address']}` to internal block-list

## Urgency
Subject wallet holds USD {ev['operator_wallet']['current_balance_usd']:,.2f} in free-transferable balance. 48-hour interim ack requested.

## Contact
- Investigation lead: {ev['police']['officer']}, {ev['police']['station']}
- Coordinator: Jun Kawasaki, gftd Japan K.K. CEO, j.kawasaki@gftd.co.jp
- External legal review: Kunal Bakshi, Bar Council of India

(Generated by ai.gftd.apps.malak.chainFreezeRequest Pregel, ADR-2605152000)
"""


def _render_jc3_referral(case_id: str, ev: Dict[str, Any]) -> str:
    return f"""# JC3 (Japan Cybercrime Control Center) 通報 packet

- 通報番号: MALAK-JC3-AUTO-{case_id.replace(':', '-')}
- 起案日: {_now_iso()}
- TLP: AMBER (LE/Compliance only)
- 案件: {case_id}

## 1. 事案概要
- 被害者: {ev['victim']['name_ja']} (神奈川県在住、日本国籍)
- 被害額: ¥{ev['loss']['amount_jpy']:,} (¥{ev['loss']['amount_jpy']//10000:,}万円相当)
- 期間: {ev['loss']['period_start']} 〜 {ev['loss']['period_end']} ({ev['loss']['transfer_count']} 回振込)
- 警察介入: {ev['police']['station']}、{ev['police']['officer']}、{ev['police']['filing_date']}
- 事案名: 村上世彰なりすまし投資詐欺 / BitNest exit-fraud (ASIC blacklist {ev['regulatory']['asic_blacklist_date']})

## 2. 加害組織 (推定)
- 主犯候補: **{ev['suspect_operator']['name']}** (別名: {', '.join(ev['suspect_operator']['aliases'])})
- 出典: {ev['suspect_operator']['source']}
- 加害組織種別: 中国系 SNS 投資詐欺リング (BitNest プラットフォーム経由)
- BSC オペレーター・ウォレット: `{ev['operator_wallet']['address']}` (残高 USD {ev['operator_wallet']['current_balance_usd']:,.0f})

## 3. JC3 への要請
3.1. 警察庁・FBI・INTERPOL・Binance Compliance の cross-jurisdictional 共助促進
3.2. ASIC blacklist 情報の domestic broadcast (国内同種被害者への警鐘)
3.3. 12 受取口座の振り込め詐欺救済法対象化の銀行側調整 (預金保険機構経由)
3.4. BitNest / Yunus Loop / leedsil.com / bitnest-ex.com を国内 SNS scam list (yabai.gftd.ai 等の OSS 共有 surface) へ反映

## 4. 添付資料
- INTEGRATED-EVIDENCE-REPORT.md (Phase 5, 2026-05-13)
- BscScan public evidence packets (operator wallet, YUNUS token, drained LP)
- ASIC blacklist 通知 (2025-12-11)
- yabai threat-actor graph entries ({ev['yabai_count']['entities']} entities, {ev['yabai_count']['edges_to_anchors']} edges)
- 振り込め詐欺救済法 12 件 申込書 ドラフト

## 5. 連絡先
- 投資詐欺事案コーディネーター: 河崎純真 (gftd Japan株式会社 代表取締役、case tracker since 2023/12)
- email: j.kawasaki@gftd.co.jp

(Generated by ai.gftd.apps.malak.chainFreezeRequest Pregel)
"""


def _render_npa_intl_cover(case_id: str, ev: Dict[str, Any]) -> str:
    return f"""# 警察庁 国際協力推進室 御中 — 国際捜査共助要請 (BitNest exit-fraud)

- 文書番号: MALAK-NPA-AUTO-{case_id.replace(':', '-')}
- 発信元: 神奈川県警察 磯子警察署 刑事課 知能犯係
- 担当: {ev['police']['officer']}
- 案件: {case_id}
- 発信日: {_now_iso()}

## 1. 国際捜査共助の要請事項

(1) 添付の Binance Compliance LECR (英文、別添) を **INTERPOL Tokyo NCB → INTERPOL General Secretariat (Lyon) → Binance Compliance** の経路で正式送達されたく要請する。

(2) 加害者推定 **{ev['suspect_operator']['name']}** (別名: {', '.join(ev['suspect_operator']['aliases'])}) に対する INTERPOL Red Notice 候補としての事前評価をお願いしたい。

(3) 印日 MLAT (2006年締結) に基づき、印 BCI 登録弁護士 (Kunal Bakshi 氏) 経由で印 FIU-IND への PMLA-7 申告併行を予定している。日本警察庁としての書面承認をいただきたい (cross-jurisdictional 重複申告に該当しない旨)。

## 2. 事案概要
- 被害者: {ev['victim']['name_ja']}
- 被害額: ¥{ev['loss']['amount_jpy']:,}
- 期間: {ev['loss']['period_start']} 〜 {ev['loss']['period_end']}
- 警察申告日: {ev['police']['filing_date']}

## 3. 加害組織と国際性
- BSC (Binance Smart Chain) 上にデプロイされた scam token `{ev['scam_token']['address']}` ({ev['scam_token']['name']}) を中核とする組織犯罪
- ASIC (オーストラリア証券投資委員会) が {ev['regulatory']['asic_blacklist_date']} 付で BitNest を無登録/無許可業者として公式ブラックリスト掲載済
- 操作員ウォレット `{ev['operator_wallet']['address']}` が現時点 USD {ev['operator_wallet']['current_balance_usd']:,.0f} 残高保有
- Binance に対する LECR で身元特定の可能性 ({len(ev['binance_counterparties'])} 件の Binance counterparty を on-chain 特定済)

## 4. 緊急性
被害金 ¥{ev['loss']['amount_jpy']//10000}万円 のうち回収可能性ある資金は: 国内 mule #5 PayPay ¥11M 第三者差押え (要照会)、Binance 凍結 (LECR 経由)、操作員 wallet 直接 (BSC chain freeze は困難) の組合せ。Binance LECR の送達遅延ごとに資金移動 (drain) リスク増大。

## 5. 添付資料
- 添付1: 英文 Binance LECR-EN-v2 (Kunal Bakshi 法的監修済の場合)
- 添付2: 事案サマリ packet (INTEGRATED-EVIDENCE-REPORT.md)
- 添付3: yabai threat graph entries ({ev['yabai_count']['entities']} entities)

敬具

神奈川県警察 磯子警察署 刑事課 知能犯係
{ev['police']['officer']}

(Generated by ai.gftd.apps.malak.chainFreezeRequest Pregel, ADR-2605152000)
"""


def _render_interpol_ipsg(case_id: str, ev: Dict[str, Any]) -> str:
    return f"""# INTERPOL IPSG Lyon — Cross-Border Cybercrime Referral

**Reference**: MALAK-IPSG-AUTO-{case_id.replace(':', '-')}
**TLP**: AMBER (LE Only)
**Generated**: {_now_iso()}
**Routed via**: INTERPOL Tokyo NCB (NCB Tokyo, National Police Agency Japan)
**Originating authority**: Kanagawa Prefectural Police, Isogo Station, Det. {ev['police']['officer']}

## I. Subject
Cross-border organized investment fraud targeting Japanese citizens, using BSC-based crypto fraud platform "BitNest" (predecessor "Yunus Loop DeFi"), blacklisted by ASIC {ev['regulatory']['asic_blacklist_date']}.

## II. Suspect identification
- Primary suspect: **{ev['suspect_operator']['name']}** (aliases: {', '.join(ev['suspect_operator']['aliases'])})
- Source: {ev['suspect_operator']['source']}
- Suspected residence: SE Asia / Middle East (per fraud-ring pattern; not yet confirmed)
- On-chain operational wallet: `{ev['operator_wallet']['address']}` ({ev['operator_wallet']['chain']}, USD {ev['operator_wallet']['current_balance_usd']:,.2f} balance)

## III. Victim
{ev['victim']['name_en']}, Japanese citizen, lost JPY {ev['loss']['amount_jpy']:,} (~USD {ev['loss']['amount_usd_approx']:,}) between {ev['loss']['period_start']} and {ev['loss']['period_end']}.

## IV. Requested action
1. **Red Notice candidate evaluation** for {ev['suspect_operator']['name']}
2. **Cross-border CEX cooperation request** to Binance Compliance via INTERPOL channels
3. **Sister-case discovery**: alert all member NCBs to similar victim profiles (Murakami Yoshiaki impersonation + LINE OpenChat investment lure + BitNest/Yunus Loop tokens)
4. **Asset trace coordination** for {len(ev['binance_counterparties'])} identified Binance counterparties + USD 21.8M whale wallet `{ev['high_value_counterparty']['address']}`

## V. Treaty basis
- INTERPOL Constitution Article 2 (international police cooperation)
- FATF Recommendation 16 (Travel Rule)
- Japan-MLAT framework
- Egmont Group financial intelligence sharing

## VI. Evidence package
- INTEGRATED-EVIDENCE-REPORT.md
- BscScan public-data evidence
- 12 mule account record (Japanese)
- ASIC blacklist notification
- yabai threat-actor graph ({ev['yabai_count']['entities']} entities, {ev['yabai_count']['edges_to_anchors']} edges)

(Generated by ai.gftd.apps.malak.chainFreezeRequest Pregel; for Kunal Bakshi BCI review before formal submission)
"""


def _render_fiu_ind_pmla(case_id: str, ev: Dict[str, Any]) -> str:
    return f"""# FIU-IND PMLA Section 7 Advisory — for Kunal Bakshi BCI review and filing

**Reference**: MALAK-FIUIND-AUTO-{case_id.replace(':', '-')}
**TLP**: AMBER (LE / Counsel Internal Only)
**Generated**: {_now_iso()}
**Routing**: Kunal Bakshi (BCI, India) → FIU-IND (Financial Intelligence Unit, India) → Special Judge PMLA
**Cross-border filing**: Japan-India MLAT (2006) framework

## 1. Predicate offense (Indian PMLA Schedule)
Investment fraud under Indian Information Technology Act Section 66D (cheating by personation using computer resource) and Indian Penal Code Section 420 (cheating), if any Indian-domiciled VDA-SP custody is implicated. Predicate offense in Japan: 刑法 246 (詐欺) + 組織的犯罪処罰法 §10/§11.

## 2. Subject suspect
**{ev['suspect_operator']['name']}** (aliases: {', '.join(ev['suspect_operator']['aliases'])}). Name structure suggests subcontinental/MENA origin. Indian databases to check:

- MCA21 (Ministry of Corporate Affairs) — directorship under any variant
- GST Portal — GSTIN registration
- PAN — KYC lookup via authorized intermediary
- Indiankanoon.org — public legal proceedings
- FIU-IND public typology — red-flag indicators
- RBI fraud-list
- SEBI investor-protection advisories

## 3. Indian VDA-SP touch verification
Operator wallet `{ev['operator_wallet']['address']}` has 19 unique BSC counterparties (deep-label results in `_working/malak/bitnest-exit-20260515-phase1-live/bsc_deep_label_findings.json`). Strict classification:
- 3 × CEX (Binance, but Binance is not Indian-domiciled)
- 1 × DEX farm (PancakeSwap MasterChef)
- 1 × utility (Multisender.app)
- 13 × unknown EOA
- 1 × whale EOA (`{ev['high_value_counterparty']['address']}`, USD 21.8M)

Of the 13 unknown EOAs, none have explicit Indian VDA-SP labels at BscScan. **Action**: Kunal verify each manually against WazirX / CoinDCX / Mudrex / Bitbns / Vauld known address sets.

## 4. PMLA Section 7 advisory content
If any Indian VDA-SP touch is confirmed:
- File FIU-IND PMLA-7 with documentary evidence
- Apply for Indian Court provisional attachment under PMLA Section 17
- Coordinate with Japanese NPA via MLAT for evidence chain transfer
- Estimate filing cost INR 50,000-300,000

If no Indian VDA-SP touch is confirmed:
- File FIU-IND informational advisory (typology contribution)
- Pursue MLAT routing for evidence sharing without PMLA action
- Estimate cost INR 10,000-50,000

## 5. Hawala typology cross-check
The dehek.com investigation claim of "$14M operator withdrawal" is consistent with hawala-network exfiltration patterns. FIU-IND maintains the world's most extensive hawala-detection typology library. Kunal to query for prior typology entries matching:
- BSC-deployed scam token + concentrated holder pattern (67 holders for USD 260M throughput = abnormal)
- China-org → Japanese-victim → BNB → fiat off-ramp through informal channels

## 6. Engagement scope (for Kunal)
Per ADR-2605101200 §10 (operating entity = amanomibashira, not Gftd Japan K.K.). BCI Rule 36 compliance maintained. Fixed-fee + disbursement-only quote expected by 2026-05-22.

(Generated by ai.gftd.apps.malak.chainFreezeRequest Pregel)
"""


def _render_kanagawa_escalation(case_id: str, ev: Dict[str, Any]) -> str:
    return f"""# 神奈川県警察 磯子警察署 御中 — 進展通知 (BitNest exit-fraud, BSC chain analysis)

- 文書番号: MALAK-KANAGAWA-AUTO-{case_id.replace(':', '-')}
- 発信元: 河崎純真 (gftd Japan株式会社 代表取締役、本件捜査協力者、2023/12 以来継続)
- 宛先: 神奈川県警察 磯子警察署 刑事課 知能犯係 {ev['police']['officer']} 御中
- 案件: {case_id}
- 通知日: {_now_iso()}

## 1. 本件の最新進展 (2026-05-15)

(1) BSC (Binance Smart Chain) 上で BitNest プラットフォームの operator wallet を特定しました:
    - アドレス: **`{ev['operator_wallet']['address']}`**
    - 現残高: USD {ev['operator_wallet']['current_balance_usd']:,.2f} (約 ¥{int(ev['operator_wallet']['current_balance_usd']*150)//10000}万円相当、現時点)
    - 性質: scam token "{ev['scam_token']['name']}" (`{ev['scam_token']['address']}`) のデプロイヤー
    - 既知別名: 操作員 = {ev['suspect_operator']['name']} ({', '.join(ev['suspect_operator']['aliases'])}) 可能性大

(2) Binance Compliance への LECR (Law Enforcement Cooperation Request) を準備しました (英文、別添)。Binance 内部 KYC 照合により、operator wallet への過去 BNB 送金者 = 加害者本人 (or 共謀者) を特定できる見込みです。

(3) 印 Bar Council 登録弁護士 Kunal Bakshi 氏に外部法的監修を依頼中 (engagement 期限 2026-05-22)。印 FIU-IND への PMLA-7 申告併行可能性あり。

## 2. 県警磯子署にお願いしたいこと

(A) **PayPay 銀行 ビジネス営業部 5343558 (IKTA GROUP合同会社) ¥11M 第三者差押え状況の §197(2) 照会書 発出**
   - 現在の口座残高
   - 第三者差押えの起算日 + 申立人 + 金額
   - 振り込め詐欺救済法 §3 申出に向けた銀行内部準備状況

(B) **警察庁国際協力推進室 (国際協力推進室) への上申** — 添付の Binance LECR を INTERPOL Tokyo NCB 経由で正式送達するため、本部 → 警察庁 ルートでの起案承認

(C) **印日 MLAT (2006年締結) 経由の cross-jurisdictional 共助** — 添付の FIU-IND PMLA 申告と国内捜査の重複申告に該当しない旨の書面承認

## 3. 添付資料
- 添付1: Binance LECR-EN-v2 (英文)
- 添付2: BSC chain trace 詳細 (bsc_operator_walk_findings.json + bsc_deep_label_findings.json)
- 添付3: 振り込め詐欺救済法 12 件 申込書 ドラフト (高橋氏押印用)
- 添付4: yabai threat graph 全 entity 一覧 ({ev['yabai_count']['entities']} entities)

## 4. 緊急性
operator wallet 残高 USD {ev['operator_wallet']['current_balance_usd']:,.0f} は permissionless chain 上で凍結不可能。each day の delay = drain risk 増加。Binance LECR の早期送達を要請いたします。

敬具

河崎 純真
gftd Japan株式会社 代表取締役 CEO
本件捜査協力者
TEL: 090-xxxx-xxxx / email: j.kawasaki@gftd.co.jp

(Generated by ai.gftd.apps.malak.chainFreezeRequest Pregel, ADR-2605152000)
"""


PACKET_RENDERERS = {
    "binance_lecr":         _render_binance_lecr,
    "jc3_referral":         _render_jc3_referral,
    "npa_intl_cover":       _render_npa_intl_cover,
    "interpol_ipsg":        _render_interpol_ipsg,
    "fiu_ind_pmla":         _render_fiu_ind_pmla,
    "kanagawa_escalation":  _render_kanagawa_escalation,
}


# ── Nodes ──────────────────────────────────────────────────────────────


def gate_input_node(state: ChainFreezeState) -> Dict[str, Any]:
    case_id = state.get("case_id") or DEFAULT_CASE_ID
    if case_id not in CASE_EVIDENCE:
        return {"status": "error", "error": f"unknown case_id {case_id}"}
    kinds = state.get("packet_kinds") or list(ALL_PACKET_KINDS)
    bad = [k for k in kinds if k not in PACKET_RENDERERS]
    if bad:
        return {"status": "error", "error": f"unknown packet kinds: {bad}"}
    return {
        "case_id":       case_id,
        "packet_kinds":  kinds,
        "evidence":      CASE_EVIDENCE[case_id],
        "packets":       {},
        "pegel_tick_ids":[],
        "written_files": {},
    }


def load_case_evidence_node(state: ChainFreezeState) -> Dict[str, Any]:
    """In Phase 1: re-query RW for fresh vertex_yabai_entity counts.
    Phase 0: use the embedded CASE_EVIDENCE table."""
    return {}


def fan_out_per_packet(state: ChainFreezeState):
    return [Send("render_packet_one", {**state, "_packet_kind": k}) for k in state["packet_kinds"]]


def render_packet_one_node(state: ChainFreezeState) -> Dict[str, Any]:
    kind = state["_packet_kind"]
    case_id = state["case_id"]
    ev = state.get("evidence") or CASE_EVIDENCE[case_id]
    body = PACKET_RENDERERS[kind](case_id, ev)
    sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
    logger.info("render_packet_one  kind=%s sha=%s len=%d", kind, sha[:12], len(body))
    return {"packets": {kind: {"body": body, "sha256": sha}}}


def after_render_barrier_node(state: ChainFreezeState) -> Dict[str, Any]:
    logger.info("after_render_barrier  packets=%d", len(state.get("packets") or {}))
    return {}


def collect_and_sign_node(state: ChainFreezeState) -> Dict[str, Any]:
    packets = state.get("packets") or {}
    concat = "\n\n---PACKET-BOUNDARY---\n\n".join(p["body"] for p in packets.values())
    manifest_sha = hashlib.sha256(concat.encode("utf-8")).hexdigest()
    return {"document_sha256": manifest_sha}


def persist_fs_node(state: ChainFreezeState) -> Dict[str, Any]:
    out_dir = state.get("output_dir") or ""
    if not out_dir: return {}
    p = pathlib.Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    files: Dict[str, str] = {}
    manifest_lines = [
        f"# Freeze Request Packet — MANIFEST",
        f"- case_id: {state['case_id']}",
        f"- generated_at: {_now_iso()}",
        f"- TLP: AMBER",
        f"- document_sha256: `{state.get('document_sha256', '')}`",
        f"",
        f"## Packets generated",
        f"",
        f"| Kind | Filename | sha256 (prefix) | Routing |",
        f"|---|---|---|---|",
    ]
    routing_map = {
        "binance_lecr":         "NPA International Cooperation → INTERPOL Tokyo NCB → Binance Compliance",
        "jc3_referral":         "JC3 (Japan Cybercrime Control Center)",
        "npa_intl_cover":       "警察庁 国際協力推進室",
        "interpol_ipsg":        "INTERPOL IPSG Lyon (via NCB Tokyo)",
        "fiu_ind_pmla":         "Kunal Bakshi (BCI, India) → FIU-IND",
        "kanagawa_escalation":  "神奈川県警察 磯子警察署 刑事課 知能犯係 松村刑事",
    }
    for kind, pkt in (state.get("packets") or {}).items():
        fname = f"freeze-request-{kind}.md"
        fpath = p / fname
        fpath.write_text(pkt["body"], encoding="utf-8")
        files[kind] = str(fpath)
        manifest_lines.append(
            f"| `{kind}` | `{fname}` | `{pkt['sha256'][:16]}...` | {routing_map.get(kind, '?')} |"
        )
    manifest_lines += [
        "",
        f"## Routing notes",
        f"",
        f"- Recommended sequence: kanagawa_escalation → npa_intl_cover → binance_lecr (after Kunal review) → jc3_referral + interpol_ipsg (parallel) → fiu_ind_pmla (Kunal-led)",
        f"- All packets require human counter-signature before formal filing.",
        f"- Phase 0 = dry-run drafts. Phase 1 (RW writes + pegel ticks + audit emit) requires `live_write=True`.",
        "",
        f"## sha256 manifest",
        f"",
        f"document_sha256 (concat): `{state.get('document_sha256', '')}`",
    ]
    for kind, pkt in (state.get("packets") or {}).items():
        manifest_lines.append(f"- {kind}: `{pkt['sha256']}`")
    manifest_path = p / "MANIFEST.md"
    manifest_path.write_text("\n".join(manifest_lines), encoding="utf-8")
    files["manifest"] = str(manifest_path)
    return {"written_files": files, "manifest_path": str(manifest_path)}


def emit_pegel_node(state: ChainFreezeState) -> Dict[str, Any]:
    case_id = state["case_id"]
    rkey = _rkey("chainFreezeRequest", case_id, _now_iso())
    tick_vid = _malak_vid("investigationTick", rkey)
    logger.info("emit_pegel  tick=%s packets=%d", tick_vid[-24:], len(state.get("packets") or {}))
    return {"pegel_tick_ids": [tick_vid]}


def schedule_review_node(state: ChainFreezeState) -> Dict[str, Any]:
    """Phase 1 live_write: write one vertex_malak_pursuit_target per packet
    with kind='packet_review' and pursuit_status='queued' so a human review
    queue (e.g. malak.surveillance Phase 1 reviewer queue) picks them up."""
    if not state.get("live_write"):
        return {}
    url = os.environ.get("RW_URL")
    if not url:
        logger.warning("schedule_review  live_write=True but RW_URL not set")
        return {}
    try:
        import psycopg
    except ImportError:
        logger.warning("psycopg not installed; cannot live-write review queue")
        return {}
    case_id = state["case_id"]
    now_iso = _now_iso()
    today = _dt.datetime.now(tz=_dt.UTC).strftime("%Y-%m-%d")
    review_vids: List[str] = []
    inserted = 0
    with psycopg.connect(url, connect_timeout=15) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            for kind, pkt in (state.get("packets") or {}).items():
                ident = f"freeze_packet:{kind}:{pkt['sha256'][:16]}"
                rkey = _rkey(case_id, "packet_review", ident)
                target_vid = _malak_vid("pursuitTarget", rkey)
                cur.execute("SELECT 1 FROM vertex_malak_pursuit_target WHERE vertex_id=%s", (target_vid,))
                if cur.fetchone():
                    review_vids.append(target_vid)
                    continue
                cur.execute(
                    "INSERT INTO vertex_malak_pursuit_target ("
                    "vertex_id, rkey, repo, target_id, target_kind, case_id, "
                    "priority, pursuit_status, extends_entity_vid, next_due_at, "
                    "last_pursued_at, pursuit_tick_count, observation_count, "
                    "note, tlp, created_at, created_date, sensitivity_ord, "
                    "owner_did, org_id, user_id, actor_id, actor_did, org_did) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (target_vid, rkey, MALAK_DID, ident, "packet_review", case_id,
                     14, "queued",
                     None, now_iso, None, 0, 0,
                     f"chain_freeze_request packet pending human review: {kind} (sha {pkt['sha256'][:12]})",
                     TLP_RED, now_iso, today, 50, MALAK_DID,
                     "gftd", MALAK_DID, "malak.chain-freeze-request",
                     MALAK_DID, MALAK_DID),
                )
                inserted += 1
                review_vids.append(target_vid)
    logger.info("schedule_review  live_write=True inserted=%d review_targets=%d",
                inserted, len(review_vids))
    return {"review_target_vids": review_vids}


def audit_emit_node(state: ChainFreezeState) -> Dict[str, Any]:
    if state.get("status", "").startswith(("denied", "error")):
        return {}
    logger.info(
        "malak.chain_freeze_request.completed case=%s packets=%d sha=%s",
        state.get("case_id", ""),
        len(state.get("packets") or {}),
        (state.get("document_sha256") or "")[:16],
    )
    return {"status": "ok"}


# ── Graph ──────────────────────────────────────────────────────────────


def build_chain_freeze_request_graph():
    g = StateGraph(ChainFreezeState)
    g.add_node("gate_input",            gate_input_node)
    g.add_node("load_case_evidence",    load_case_evidence_node)
    g.add_node("render_packet_one",     render_packet_one_node)
    g.add_node("after_render_barrier",  after_render_barrier_node)
    g.add_node("collect_and_sign",      collect_and_sign_node)
    g.add_node("emit_pegel",            emit_pegel_node)
    g.add_node("persist_fs",            persist_fs_node)
    g.add_node("schedule_review",       schedule_review_node)
    g.add_node("audit_emit",            audit_emit_node)

    g.set_entry_point("gate_input")
    g.add_edge("gate_input", "load_case_evidence")
    g.add_conditional_edges("load_case_evidence", fan_out_per_packet, ["render_packet_one"])
    g.add_edge("render_packet_one", "after_render_barrier")
    g.add_edge("after_render_barrier", "collect_and_sign")
    g.add_edge("collect_and_sign", "persist_fs")
    g.add_edge("persist_fs", "emit_pegel")
    g.add_edge("emit_pegel", "schedule_review")
    g.add_edge("schedule_review", "audit_emit")
    g.add_edge("audit_emit", END)
    return g.compile()


async def run_chain_freeze_request(
    *, case_id: str = DEFAULT_CASE_ID,
    packet_kinds: Optional[List[str]] = None,
    output_dir: str = "",
    live_write: bool = False,
) -> Dict[str, Any]:
    graph = build_chain_freeze_request_graph()
    initial: ChainFreezeState = {
        "case_id": case_id,
        "packet_kinds": list(packet_kinds) if packet_kinds else list(ALL_PACKET_KINDS),
        "output_dir": output_dir,
        "live_write": live_write,
    }
    return await graph.ainvoke(initial)


def main(argv: Optional[List[str]] = None) -> None:
    p = argparse.ArgumentParser(prog="chain_freeze_request_pursuit")
    p.add_argument("--case-id", default=DEFAULT_CASE_ID)
    p.add_argument("--packets", default=",".join(ALL_PACKET_KINDS),
                   help="comma-separated packet kinds")
    p.add_argument("--output-dir", default="")
    p.add_argument("--live-write", action="store_true",
                   help="Phase 1: write packet_review rows to RW")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    kinds = [k.strip() for k in args.packets.split(",") if k.strip()]
    result = asyncio.run(run_chain_freeze_request(
        case_id=args.case_id, packet_kinds=kinds, output_dir=args.output_dir,
        live_write=args.live_write,
    ))
    print(json.dumps({
        "status": result.get("status"),
        "packets_generated": list((result.get("packets") or {}).keys()),
        "files": list((result.get("written_files") or {}).keys()),
        "document_sha256": result.get("document_sha256"),
        "pegel_ticks": result.get("pegel_tick_ids") or [],
        "review_targets": result.get("review_target_vids") or [],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
