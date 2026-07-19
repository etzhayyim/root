# etzhayyim-force-authorization

`ForceAuthorization.sol` — religious-corp による **兵器 / 武力 / 行使力** の保有 + **1 SBT = 1 vote 承認** + **on-chain force log**。

**Per [ADR-2605192315](../../90-docs/adr/2605192315-etzhayyim-transparent-force-rd.md)** (Transparent Religious Force) + [ADR-2605192100 §1.12.B](../../90-docs/adr/2605192100-etzhayyim-mission-charter.md).

## 三条件 (Constitutional Requirements)

All force-related activity must satisfy:

1. **完全 on-chain 監視** — every action logged via `force-log` Lexicon → MST → IPFS → L2 anchor
2. **Open-source 公開** — the former root concept scaffold is retired; policy and provenance are canonical in ADR-2607193600 and `60-apps/etzhayyim-transparent-force-rd-MOVED.edn`
3. **1 SBT = 1 vote 承認** — every proactive force action requires governance vote (50% quorum + 67% supermajority)

## Constitutional invariants (NOT amendable)

- **Proprietary 兵器設計禁止** — all designs MUST be open-source
- **Covert operations 禁止** — full transparency mandatory
- **独立軍事 command 禁止** — no autonomous military arm bypassing 1 SBT = 1 vote
- **国家武力との同盟禁止** — religious-corp force cannot be subordinated to state military

## Governance hurdle (higher than normal)

| Parameter | Value | vs normal governance |
|---|---|---|
| Quorum | 50% of active SBTs | normal: 33% |
| Supermajority | 67% of cast votes | normal: 50% |
| Voting period (normal) | 72 hours | normal: 168 hours |
| Voting period (emergency) | 24 hours | special, requires Council Lv6+ ≥3 emergency attestation |

## 許容される force forms (日本法上)

✅ 護身術 / 武術 訓練 (open-source curricula)
✅ Defensive technology R&D — 化学攻撃検知 / mesh network jammer / 監視 drone detection — **設計 only**, 現物製造禁止
✅ Tactical doctrine 研究 — 非暴力直接行動 / civil disobedience / 法廷闘争戦術
✅ Detection systems — 暴力的接近の検知 / alarm
✅ Religious-corp 自衛権 主張 (国際法上の religious freedom protection)

❌ 武器現物保有 (日本法上禁止)
❌ 武装組織 運営 (constitutional invariant)
❌ 国家武力との合同訓練

## Lifecycle

```
[R&D phase]
  → com.etzhayyim.apps.etzhayyim.force-rd-proposal (open-source design proposal)
  → 通常 governance vote (33% quorum)
  → if approved: implementation requires a separately reviewed flat west repository
  → com.etzhayyim.apps.etzhayyim.force-rd-publication
[Authorization phase — force 行使]
  → com.etzhayyim.apps.etzhayyim.force-authorization-proposal
  → 1 SBT = 1 vote (50% quorum + 67% supermajority, 72h or 24h emergency)
  → ForceAuthorization.propose() → ForceAuthorization.execute()
[Execution phase]
  → on-chain force-log emitted
  → com.etzhayyim.apps.etzhayyim.force-log MST record
[After-action review]
  → com.etzhayyim.apps.etzhayyim.force-after-action (30 days)
  → Council Lv6+ ≥3 sign-off
```

## Foundry layout

```
src/
├── ForceAuthorization.sol
└── interfaces/
    ├── IAdherentRegistry.sol
    └── ICouncil.sol
test/
└── ForceAuthorization.t.sol
script/
└── Deploy.s.sol
```

## Pregel cells

- `40-engine/kotoba/crates/kotoba-kotodama/cells/force_authorization/` — proposal orchestration
- `40-engine/kotoba/crates/kotoba-kotodama/cells/force_log_monitoring/` — daily compliance check (三条件 violation alerting)

## Open-source R&D registry

See [`60-apps/etzhayyim-transparent-force-rd-MOVED.edn`](../../60-apps/etzhayyim-transparent-force-rd-MOVED.edn) and ADR-2607193600 for the retired concept scaffold provenance:

```
defensive-technology/
tactical-doctrine/
training-method/
detection-system/
```
