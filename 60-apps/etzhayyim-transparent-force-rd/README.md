# etzhayyim-transparent-force-rd

Open-source R&D registry for **Transparent Religious Force** (per [ADR-2605192315](../../90-docs/adr/2605192315-etzhayyim-transparent-force-rd.md)).

## Constitutional principles

- All designs are **Apache 2.0 + Charter Compliance Rider v2.0** (NO proprietary, ever)
- All R&D must pass through 1 SBT = 1 vote authorization
- Dual-use analysis is **mandatory** for every R&D proposal
- 国家武力 (state military) との合同研究は禁止

## Directory structure

```
defensive-technology/      ← detection / counter-weapon / shielding
tactical-doctrine/         ← nonviolent direct action / civil disobedience / legal battle
training-method/           ← self-defense curricula / meditation under duress
detection-system/          ← proximity alert / verbal de-escalation
```

## Per R&D project structure

```
<project-name>/
├── README.md              # purpose, dual-use analysis, target outcome
├── design.md              # technical design + reasoning
├── safety-analysis.md     # risk assessment + mitigation
├── dual-use-analysis.md   # adversary use analysis + Charter Rider §3 exposure
├── source/                # implementation source (if any)
├── test/
└── com.etzhayyim.apps.etzhayyim.force-rd-publication.json  # publication record
```

## Initial seed projects (S0)

None — all projects come through 1 SBT = 1 vote proposal flow. This README itself is the only initial content.

## How to propose a new R&D project

1. Draft a `force-rd-proposal` AT Record on your PDS
2. Include:
   - category (`defensive-tech` / `tactical-doctrine` / `training-method` / `detection-system`)
   - description
   - designSpecCid (IPFS, can be draft)
   - safetyAnalysisCid
   - dualUseAnalysis (text — what adversary use is possible?)
3. Submit via `ForceAuthorization.propose()` (Base L2) — normal governance vote (33% quorum, 168h voting)
4. If approved: commit final design to this directory in a PR
5. Final design becomes Apache 2.0 + Charter Rider v2.0 by default

## Prohibited topics

❌ Proprietary or covert designs
❌ Mass-casualty weapons (chemical / biological / nuclear / autonomous lethal at scale)
❌ Designs whose primary effect is offensive at-scale (per ADR-2605192100 §1.12.B)
❌ Designs not satisfying Charter Rider §2 (especially §2(a) weapons in commercial-scale context)

## Permitted topics (examples)

✅ Self-defense martial arts curricula (open-source video + text)
✅ Chemical attack detection (sensor design + ML classifier)
✅ Drone detection (acoustic / RF / visual)
✅ Mesh network resilience against jamming
✅ Verbal de-escalation training (LLM-assisted, religious context)
✅ Legal battle templates for religious freedom defense
✅ Civil disobedience nonviolent training (Gandhi / King / Havel traditions)
✅ Religious-corp 自衛権 international law analysis

## See also

- [ADR-2605192315](../../90-docs/adr/2605192315-etzhayyim-transparent-force-rd.md) — Transparent Religious Force ADR
- [ADR-2605192100 §1.12.B](../../90-docs/adr/2605192100-etzhayyim-mission-charter.md) — Mission Charter
- [`50-infra/etzhayyim-force-authorization/`](../../50-infra/etzhayyim-force-authorization/) — Solidity authorization contract
- `40-engine/kotoba/crates/kotoba-kotodama/cells/force_authorization/` — governance Pregel cell
- `40-engine/kotoba/crates/kotoba-kotodama/cells/force_log_monitoring/` — daily compliance check
