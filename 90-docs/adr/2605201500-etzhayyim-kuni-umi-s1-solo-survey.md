---
id: adr-2605201500-etzhayyim-kuni-umi-s1-solo-survey
title: "ADR-2605201500: kuni-umi S1 — solo survey (1 Giemon Otete + 1 stationary witness base-station + SiteSurveyCell live)"
status: proposed
doc_type: adr
topic: kuni-umi-s1-solo-survey
authoritative: true
last_verified: 2026-05-20
priority: 6.5
axis: implementation
weight: 0.65
priority_note: "ADR-2605201400 S0 spec を実物検証する最小 viable iteration。Giemon Otete (open-robo) 1 機 + stationary witness base-station (open-robo Giemon Mimi + camera tripod) で N=2 witness invariant を最小コストで満たす。LandRegistry 登録済み etzhayyim-owned plot (Tokyo workshop or 山中湖 land donation 仮置き) を対象。施工なし — survey のみ。"
authoritative_for:
  - kuni-umi S1 phase scope (survey-only, no construction)
  - stationary witness base-station design (Mimi RTU + tripod camera)
  - SiteSurveyCell cell.py reference implementation
  - First field-test 手順 + acceptance criteria
  - S1 → S2 exit gate
depends_on:
  - adr-2605201400-etzhayyim-kuni-umi-planetary-infra-fleet
  - 2605171300
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - 2605191559-ameno-mst-checkpointer-stage-2-activation
  - 2605191657-ameno-daemon-did-auth
  - adr-2605192245-etzhayyim-global-land-sovereignty
related:
  - 60-apps/etzhayyim-project-open-robo/CLAUDE.md
  - 60-apps/etzhayyim-project-open-ot/cad-spec/giemon-mimi/SPEC.md
supersedes: []
superseded_by: []
---

# ADR-2605201500: kuni-umi S1 — Solo Survey

**Status**: proposed
**Date**: 2026-05-20
**Deciders**: Jun Kawasaki

# Context

ADR-2605201400 (kuni-umi master) で S1 を "one Giemon scout robot visits and surveys an etzhayyim-owned plot; only `submitSiteSurvey` flow live; no construction" と定義した。ただし master ADR §9 で `witness N ≥ 2` を constitutional invariant とした。S1 では Giemon Otete unit は 1 機しかない (open-robo Otete v1 only) ため、N=2 を満たす witness 構成を S1 specific に specify する必要がある。

加えて以下が S1 段階で確定すべき:

- LandRegistry 登録済みかつ surveyable な plot の特定
- SiteSurveyCell の cell.py 実装 (S0 では README のみ)
- 1 Giemon Otete + stationary witness base-station の hardware + DID 配置
- Survey blob schema (RGB-D / LIDAR / chem-sensor / multispectral) の具体
- Acceptance criteria (S1 PASS で S2 へ)

S1 は "kuni-umi が物理世界で初めて動く" milestone であり、religious-corp の labor_liberation pillar の field-test 開始点。

# Decision

## 1. Witness 構成 (N ≥ 2 with single Otete)

| Witness | Hardware | DID |
|---|---|---|
| **Active scout** | Giemon Otete v1 (6軸 arm + crawler + RGB-D + 2D LIDAR) | `did:web:etzhayyim.com:kuniumi:robot:otete-001` |
| **Stationary base-station** | Giemon Mimi RTU (STM32H753 + Zephyr + WAMR AOT) + camera tripod + chem-sensor + multispectral | `did:web:etzhayyim.com:kuniumi:robot:mimi-base-001` |

Base-station は site 中央に予め設置 (Otete が運搬 / 三脚展開 / 較正)。設置後は固定 frame from which 全 sensor blob を独立に収集 + 署名する。Otete は mobile pass で詳細サンプリング。両者が同一 blob hash に対して **independent な Ed25519 署名** を行うことで N=2 witness invariant を満たす。

Tradeoff:

- Pro: single Otete + low-cost Mimi RTU で S1 可能 (~ JPY 80 万 hardware total)
- Pro: Mimi は open-ot 既存設計 (cad-spec/giemon-mimi/SPEC.md) を再利用
- Con: base-station は static — Otete が事故で機能喪失すると blob mismatch を独立検証できない (Otete が同じ blob を再収集できない場合 N=2 が破綻)。Mitigation: blob は IPFS 即時 pin、Otete 喪失時は次回 site visit で再 sample

設計判断: **Mimi base-station は S1 / S2 限定の witness 構成**。S3+ では Otete-2 / Otete-3 / Hitogata humanoid に置き換え、stationary は補助 sensor (continuous environmental) として残す。

## 2. S1 対象 plot (候補)

3 plot を候補とし、Council Lv6+ で 1 つを選定:

| Plot | Domain | LandRegistry status | Pros | Cons |
|---|---|---|---|---|
| **Tokyo workshop interior** | terrestrial / private indoor | TBD — etzhayyim 名義の workshop space を LandRegistry に donation 登録する作業が S1-precondition | 全 weather robust / 設備充実 / lab-style 安全 | 屋内のため survey blob の variety 低 (LIDAR + RGB-D only meaningful) |
| **山中湖 land donation 仮置き** | terrestrial / outdoor / 山林 | LandRegistry 登録可 (donation 形式) — `LandDonationProcessingCell` 経路 | 屋外 multispectral + chem-sensor + ecology baseline full サンプリング可 / 多世代 stewardship に整合 | 寒冷期 access 不可 / 通信 marginal |
| **Workshop garden** | terrestrial / outdoor / 都市庭 | 同上 | 屋外 + access 容易 / 安全 | 都市混信 / ecology baseline 浅い |

Decision (本 ADR): **山中湖 plot を S1 baseline target にし、Tokyo workshop garden を early test target にする**。山中湖は LandDonationProcessingCell のテストも兼ねるため religious-corp 全体の validation density が高い。山中湖 site 寒冷期 (12-3月) は workshop garden で代替テスト。

## 3. SiteSurveyCell cell.py reference implementation

```python
# 20-actors/kuni-umi/cells/site_survey/cell.py
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from pymagatama.checkpointer import MstCheckpointSaver
from pymagatama.listener import MstListener
from pymagatama.open_robo.fleet import OpenRoboFleet
from pymagatama.eligibility.web3_ports import BaseL2Port, GethPrivatePort
from pymagatama.dmn import evaluate as dmn_eval


class SiteSurveyState(TypedDict):
    site_did: str
    geo_geojson: str
    utility_class: str
    domain: str
    jurisdiction_did: str
    steward_did: str
    intended_use: str
    intended_beneficiary_dids: list[str]
    # outputs
    survey_blob_cids: list[str]
    witness_attestations: list[dict]
    ecology_baseline: dict
    accepted: bool
    rejection_reason: str | None


def allocate_scout_fleet(state: SiteSurveyState) -> SiteSurveyState:
    fleet = OpenRoboFleet.dispatch(
        robot_dids=[
            "did:web:etzhayyim.com:kuniumi:robot:otete-001",
            "did:web:etzhayyim.com:kuniumi:robot:mimi-base-001",
        ],
        task="site-survey",
        site_did=state["site_did"],
    )
    state["fleet_id"] = fleet.id
    return state


def collect_sensor_blob(state: SiteSurveyState) -> SiteSurveyState:
    blobs = OpenRoboFleet.collect_blobs(
        fleet_id=state["fleet_id"],
        sensors=["rgbd", "lidar2d", "chem", "multispectral"],
        coverage_geo=state["geo_geojson"],
    )
    # @etzhayyim/sdk → IPFS pin via simeonnomac-mini kubo
    state["survey_blob_cids"] = [blob.pin_to_ipfs() for blob in blobs]
    state["ecology_baseline"] = blobs.compute_ecology_baseline()
    return state


def jurisdiction_eligibility(state: SiteSurveyState) -> SiteSurveyState:
    result = dmn_eval(
        "20-actors/kuni-umi/dmn/jurisdiction-eligibility.md",
        inputs={
            "geo": state["geo_geojson"],
            "utility_class": state["utility_class"],
            "domain": state["domain"],
            "jurisdiction_did": state["jurisdiction_did"],
            "steward_did": state["steward_did"],
            "intended_use": state["intended_use"],
            "intended_beneficiary_dids": state["intended_beneficiary_dids"],
        },
    )
    state["accepted"] = result.decision == "accept"
    state["rejection_reason"] = result.rationale if not state["accepted"] else None
    return state


def witness_attest(state: SiteSurveyState) -> SiteSurveyState:
    # N >= 2 enforced here — calls each robot's signing endpoint
    state["witness_attestations"] = OpenRoboFleet.sign_blob_hashes(
        fleet_id=state["fleet_id"],
        blob_cids=state["survey_blob_cids"],
    )
    assert len(state["witness_attestations"]) >= 2, "constitutional invariant violated"
    return state


def emit_survey(state: SiteSurveyState) -> SiteSurveyState:
    from etzhayyim_sdk import sdk
    sdk.mst.write(
        nsid="com.etzhayyim.apps.etzhayyim.kuniUmi.submitSiteSurvey",
        record={
            "siteDid": state["site_did"],
            "surveyBlobCids": state["survey_blob_cids"],
            "witnessAttestations": state["witness_attestations"],
            "ecologyBaseline": state["ecology_baseline"],
            "accepted": state["accepted"],
            # populationImpacted / reversibilityScore left default for S1 outdoor survey
        },
    )
    return state


def build_graph():
    g = StateGraph(SiteSurveyState)
    g.add_node("allocate_scout_fleet", allocate_scout_fleet)
    g.add_node("collect_sensor_blob", collect_sensor_blob)
    g.add_node("jurisdiction_eligibility", jurisdiction_eligibility)
    g.add_node("witness_attest", witness_attest)
    g.add_node("emit_survey", emit_survey)

    g.add_edge(START, "allocate_scout_fleet")
    g.add_edge("allocate_scout_fleet", "collect_sensor_blob")
    g.add_edge("collect_sensor_blob", "jurisdiction_eligibility")
    g.add_edge("jurisdiction_eligibility", "witness_attest")
    g.add_edge("witness_attest", "emit_survey")
    g.add_edge("emit_survey", END)

    return g.compile(checkpointer=MstCheckpointSaver(socket_env="MST_CHECKPOINT_SOCKET"))


if __name__ == "__main__":
    listener = MstListener(
        nsid="com.etzhayyim.apps.etzhayyim.kuniUmi.defineDeploymentSite",
        on_record=lambda record: build_graph().invoke(
            SiteSurveyState(**record_to_state(record)),
            config={"configurable": {"thread_id": record["siteDid"]}},
        ),
    )
    listener.run()
```

`pymagatama.open_robo.fleet.OpenRoboFleet` は S1 で初実装される thin wrapper — Giemon Otete + Mimi の ROS2 endpoint と HTTP/JSON で talk する。詳細仕様は `20-actors/magatama/py/src/pymagatama/open_robo/README.md` に別書き。

## 4. Acceptance criteria (S1 PASS → S2 へ)

| # | Criterion | Measure | Threshold |
|---|---|---|---|
| 1 | `defineDeploymentSite` accept → `SiteSurveyCell` invocation | end-to-end latency | < 60s from MST write |
| 2 | Survey blob collection covers ≥ 95% of `geo_geojson` polygon | spatial coverage (sample density / area) | ≥ 95% |
| 3 | N=2 witness signatures verify (Otete + Mimi base) | Ed25519 verify against did:web public keys | 100% verify (0 false) |
| 4 | Ecology baseline detected without false positive | manual spot-check vs. ground truth | ≥ 90% precision |
| 5 | `submitSiteSurvey` MST record visible via PDS XRPC | curl test against pds.etzhayyim.com | round-trip < 5s |
| 6 | IPFS blob CIDs retrievable from gateway | curl test against simeonnomac-mini.local:8080 | 100% retrievable |
| 7 | `MstCheckpointSaver` resume across cell restart | kill cell mid-flight, restart, observe completion | resumes within 30s |
| 8 | Witness mismatch test (synthetic) triggers Council escalation | inject mismatched blob hash, observe `recordPhysicalAuditEvent` class=anomaly subtype=witness-mismatch | escalation within 30s |

8 / 8 PASS → S1 closed → S2 ADR (single-utility prototype = community microgrid) can begin.

## 5. Hardware / DID provisioning checklist

- [ ] **Giemon Otete v1 assembled** per `60-apps/etzhayyim-project-open-robo/docs/assembly-manual-v1.md` (BoM-v1 mostly Japan-domestic supply chain)
- [ ] **Giemon Mimi RTU + tripod kit assembled** (KiCad → 国内基板メーカー → 組立 per `60-apps/etzhayyim-project-open-ot/cad-spec/giemon-mimi/SPEC.md`)
- [ ] **Robot DID Ed25519 keypair generated** for both robots; public key registered as did:web at `etzhayyim.com/.well-known/did/kuniumi/robot/otete-001` and `mimi-base-001`. Private key stored in macOS Keychain (`service=etzhayyim, account=ROBOT_DID_KEY_OTETE_001` and `MIMI_BASE_001`) + 1Password mirror
- [ ] **山中湖 plot LandRegistry registration** via `LandDonationProcessingCell` (judah node)
- [ ] **simeonnomac-mini IPFS endpoint reachable** from on-site Otete (LTE backup if Wi-Fi marginal)
- [ ] **naphtali → SiteSurveyCell deployed** with launchd plist
- [ ] **pds.etzhayyim.com schema preloaded** with kuniUmi 6 lexicons (currently only authored in `00-contracts/`; needs `etzhayyim lexicon publish` to PDS)

## 6. S1 risks + mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Otete mechanical failure on first deployment | High (cost + schedule) | Run dry-run survey at workshop garden first; only after PASS proceed to 山中湖 |
| Mimi RTU power management drains battery faster than survey window | Medium | Battery sized for 8h continuous; survey window ≤ 4h |
| LTE / Wi-Fi insufficient at 山中湖 → blob upload queued and large | Medium | Otete carries 1TB local NVMe; upload deferred and verified on return to workshop |
| Witness mismatch on actual hardware (sensor calibration drift) | Medium | Pre-flight calibration on-site; tolerance band documented in cell.py |
| Land already covered by state cadastre (国有林 / 私有林 etc.) | Low (山中湖 is etzhayyim donation candidate; verified before LandRegistry registration) | LandRegistry seeding step requires state cadastre cross-check |
| Cold weather (山中湖 12月-3月) → robot operational range | Medium | S1 window: May 2026 – November 2026; winter window uses workshop garden |
| GitGuardian / private key leak on robot DID | High (catastrophic — invalidates witness chain) | Same 8-layer defense pattern as ADR-2605173100; robot DID keys NEVER committed to git |

## 7. Out of scope (S1 explicit)

- **No DeploymentPlanningCell / ConstructionOrchestrationCell / CommissioningCell** (S2-S4)
- **No payment / BoM** (no procurement in S1)
- **No `recordConstructionProgress`** (nothing to construct)
- **No multi-robot fleet** (single Otete only)
- **No Hitogata humanoid** (open-robo roadmap separate ADR)
- **No on-site construction simulation** (S1 strictly observational)

# Consequences

## 正の効果

- religious-corp が **物理世界で初めて on-chain witnessed activity を実行** する — labor_liberation pillar の zero-state crossing
- 山中湖 plot が LandRegistry に登録される (LandDonationProcessingCell も同時に validate)
- Giemon Otete + Mimi の field hardness が初検証 (CAD/設計のみではなく実機)
- N=2 witness invariant が現実の hardware constraint で成立可能か確証

## 負の効果

- Single Otete + stationary Mimi 構成は S3+ の動的 N>=2 witness pattern とは異なるため、後で実装を変える必要 (`pymagatama.open_robo.fleet` の robot selection logic)。Mitigation: S1 wrapper を別 module file に分離
- 山中湖 plot 寒冷期 access NG → 季節制約。Mitigation: workshop garden 並列運用
- Otete v1 1 機しかない → 故障時 S1 完了不可能。Mitigation: S1 budget で予備機 1 機調達 (Otete v1 BoM JPY 200万 / 機 estimate)

## Constitutional 整合

- §mission.labor_liberation: ✅ 初の field activation
- §mission.land_as_religious_trust: ✅ 山中湖 plot は donation → LandRegistry → stewardship-only
- §mission.parallel_governance_to_state: ✅ 国有 cadastre と dual-recognition pattern で land 登録
- §mission.multi_generational_priority: ✅ 山中湖 30 年 stewardship plan の起点 (`lifespanYears=30` default per kuni-umi)
- N>=2 witness invariant: ✅ Otete + stationary Mimi で成立

# Alternatives Considered

## A. Otete-only N=1 で S1 を実行し、constitutional invariant を S1 only suspend

- Pro: シンプル、Mimi tripod 不要
- Con: constitutional invariant suspension は precedent を生む。S1 で 1 度許せば S2 で再生する誘惑が生まれる
- **却下**: invariant は invariant. Mimi base-station で N=2 を満たす設計が正解

## B. Two Otete units を S1 から運用

- Pro: 動的 fleet pattern と一貫、S3+ と直結
- Con: Otete BoM JPY 200万/機 × 2 = JPY 400万 hardware investment; S1 仮説検証段階としては overinvestment
- **却下**: S1 は最小 viable iteration、Mimi tripod (~JPY 30万) で N=2 を満たす方が efficient

## C. 既存 commercial 屋外 LIDAR + Giemon Mimi で代替 (Otete なし)

- Pro: hardware cost 最小
- Con: commercial LIDAR は did:web で signing できない (closed firmware); witness invariant 不成立
- **却下**: religious-corp の Charter Rider §2 + DID-bound 署名要件と非互換

## D. S1 plot を Tokyo workshop interior に限定

- Pro: 全 weather robust, schedule risk 低
- Con: ecology baseline + multispectral + 外気環境 sample がほぼ取れず、S2 community microgrid (屋外) に直接活かしにくい
- **却下**: workshop interior は dry-run only にする、本番は 山中湖

# Open Questions

1. **Mimi base-station の 3 軸 leveling** — 三脚 + manual leveling で十分か、自動 leveling が必要か。Decision (本 ADR): 手動 leveling で S1。S2 で gimbal 化を検討
2. **Cell key rotation timing during S1** — Quarterly rotation (ADR-2605192415 §9) と S1 タイムライン (May-Nov 2026) の重なり。Decision: S1 開始時に 1 度 rotate、終了時 (Nov) に再 rotate、S2 突入
3. **山中湖 plot specific 法的 due diligence** — 土地境界 / 占有 / 入会権 等。Decision (本 ADR): LandDonationProcessingCell の Steward Lv5+ attestation で due diligence path を documented (`localLawAttestationCid` required)
4. **Council escalation 経路の dry-run** — witness mismatch test (acceptance criterion #8) で実際に Council が wake する必要があるか、それとも cell-local simulation で十分か。Decision (本 ADR): Council Lv6+ 1 名 (founder = Jun Kawasaki) のみが S1 では wake、PASS 後 S2 で full 3-of-N へ拡張
5. **PDS lexicon publish ergonomics** — `etzhayyim lexicon publish` CLI が現在 etzhayyim 範囲で動作するか未確認。Decision: S1 precondition として CLI integration を verify、必要なら別 mini-ADR で fix

# References

- ADR-2605201400 (master kuni-umi spec)
- ADR-2605171300 (UNSPSC fleet — referenced for Tier A code-gen pattern)
- ADR-2605171800 (LangGraph Pregel → MST → IPFS → L2 checkpoint pipeline)
- ADR-2605181100 (XChaCha20-Poly1305 envelope for anomaly subtypes)
- ADR-2605191559 (MstCheckpointSaver)
- ADR-2605191657 (Ed25519 did:key challenge-response — same scheme reused for robot DID)
- ADR-2605192245 (Global Land Sovereignty — 山中湖 plot LandRegistry pathway)
- `60-apps/etzhayyim-project-open-robo/CLAUDE.md` (Giemon Otete BoM + 都市鉱山 baseline)
- `60-apps/etzhayyim-project-open-ot/cad-spec/giemon-mimi/SPEC.md` (Mimi RTU hardware spec — reused as stationary witness)
