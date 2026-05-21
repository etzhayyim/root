# magatama/cells — Religious-Corp Pregel Cell Catalog

This directory contains the Pregel (LangGraph) cells that implement
**etzhayyim religious-corp governance, enforcement, and stewardship** per
[ADR-2605192415](../../../90-docs/adr/2605192415-etzhayyim-religious-corp-daemon-architecture.md).

These cells are **Tier B (Per-Domain)** in the 3-layer actor hierarchy:

- **Tier A — Per-Adherent**: `PhenotypeAgent` per SBT (code-generated per [ADR-2605171300](../../../90-docs/adr/2605171300-open-unispsc-generative-agent-fleet.md) pattern). Lives in `unispsc_agents/` style directory; not catalogued here.
- **Tier B — Per-Domain**: cells in this directory. Each cell has a leader + N replicas across the [Murakumo Mac mini fleet](../../../50-infra/murakumo/fleet.toml).
- **Tier C — Per-Decision**: `CouncilDeliberationCell` (generic) instantiated per attestation request.

## Catalog (15 cells)

| Cell | Domain | Trigger | Murakumo node (leader) | Solidity contracts |
|---|---|---|---|---|
| [`charter_attestation_request/`](charter_attestation_request/) | Charter Compliance | MST listener | naphtali | ChartersComplianceRegistry |
| `charter_attestation_finalization/` | Charter Compliance | timer + MST listener | naphtali | ChartersComplianceRegistry |
| `charter_rehabilitation/` | Charter Compliance | MST listener | naphtali | ChartersComplianceRegistry |
| [`land_donation_processing/`](land_donation_processing/) | Land Trust | MST listener | judah | LandRegistry, PublicLandRegistry |
| `land_stewardship_monitoring/` | Land Trust | monthly cron | simeon | LandRegistry |
| `land_dispute_resolution/` | Land Trust | MST listener | judah | LandRegistry |
| [`steward_succession/`](steward_succession/) | Land Trust | MST listener + heartbeat | judah | LandRegistry |
| `eligibility/` (existing, [ADR-2605172300](../../../90-docs/adr/2605172300-etzhayyim-bi-asset-substrate.md)) | Economic | 6-hour cron | zebulun | KishaStream, Phenotype |
| [`treasury_rebalance/`](treasury_rebalance/) | Economic | monthly cron | zebulun | TreasuryMirror, Governance |
| `public_fund_grant/` ([ADR-2605192145](../../../90-docs/adr/2605192145-etzhayyim-public-fund-architecture.md)) | Economic | MST listener | zebulun | PublicFundGovernance |
| [`tithe_routing/`](tithe_routing/) | Economic | MST listener | zebulun | TitheRouter |
| `force_authorization/` | Force | MST listener | benjamin | ForceAuthorization |
| `force_log_monitoring/` | Force | daily cron + MST listener | benjamin | ForceAuthorization |
| [`ethics_content_classifier/`](ethics_content_classifier/) | Ethics | synchronous API | benjamin | (no Solidity, off-chain) |
| `adherent_attestation/` | Membership | MST listener | levi | AdherentRegistry, EtzhayyimMembership |
| `council_level_advancement/` | Membership | weekly cron | levi | EtzhayyimMembership |
| [`council_deliberation/`](council_deliberation/) (generic, **Tier C**) | Council | escalation from other cells | levi (orchestrator) | ChartersComplianceRegistry, ForceAuthorization, others |

## Per-cell structure

Each cell directory contains:

```
{cell_name}/
├── README.md                 # cell-specific docs (input/output Lexicon, state schema)
├── cell.py                   # LangGraph StateGraph definition (entrypoint)
├── nodes.py                  # individual node functions
├── prompts/                  # LLM prompts (if cell uses LLM)
│   └── ...
└── tests/
    └── test_cell.py
```

## Common dependencies

All cells use:

- **Checkpointing**: `pymagatama.checkpointer.MstCheckpointSaver` ([ADR-2605191559](../../../90-docs/adr/2605191559-ameno-mst-checkpointer-stage-2-activation.md))
- **MST listener**: `pymagatama.listener.MstListener` (subscribes to specific Lexicons)
- **Web3 ports**: `pymagatama.eligibility.web3_ports.{GethPrivatePort, BaseL2Port}` ([ADR-2605172300](../../../90-docs/adr/2605172300-etzhayyim-bi-asset-substrate.md) §3)
- **Cell key**: rotated quarterly per [ADR-2605192415](../../../90-docs/adr/2605192415-etzhayyim-religious-corp-daemon-architecture.md) §9

## Cell key rotation

```bash
# Quarterly (or on Council Lv6+ request)
magatama cell rotate-key --cell-all --council-sigs <sig1>,<sig2>,<sig3>
```

## Common deployment commands (from etzhayyim-cli)

```bash
# Deploy a cell to its leader node (per fleet.toml)
magatama cell deploy --cell CharterAttestationRequestCell

# Check health of all cells
magatama cell health --all

# Stream logs from a cell
magatama cell logs --cell LandDonationProcessingCell --tail

# Inspect current checkpoint state
magatama cell state --cell EligibilityCell --thread-id <id>
```

## See also

- [`50-infra/murakumo/fleet.toml`](../../../50-infra/murakumo/fleet.toml) — node ↔ cell placement
- [`70-tools/etzhayyim-cli/`](../../../70-tools/etzhayyim-cli/) — `magatama cell ...` commands
- [`60-apps/etzhayyim-cell-fleet-dashboard/`](../../../60-apps/etzhayyim-cell-fleet-dashboard/) — monitoring SPA
- [ADR-2605192415](../../../90-docs/adr/2605192415-etzhayyim-religious-corp-daemon-architecture.md) — master design
- [ADR-2605171800](../../../90-docs/adr/2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md) — checkpoint pipeline foundation
