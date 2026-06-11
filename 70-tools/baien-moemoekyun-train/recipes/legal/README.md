# Legal corpus training recipes

Recipes for assembling Tier-A (and optionally Tier-B with `-tierB-` infix) legal-corpus training artifacts per **ADR-2605262800**. Each recipe is consumed by `70-tools/baien-moemoekyun-train/scripts/assemble-public-corpus.py` per the contract in **ADR-2605262400 §4**.

## Recipes (5)

| Recipe | Purpose | Tier max | Consumer artifact |
|---|---|---|---|
| `legal-foundations-r1.toml` | General legal-reasoning baseline (USC + UK statutes + e-Gov + EUR-Lex + CAP) | A | `baien-server-legal-foundations-r1` |
| `chigiri-procedural-r1.toml` | chigiri-specific procedural reasoning (CFR procedures + UK GOV.UK procedures + Apache 2.0 + Charter Rider + covenant ceremony templates) | A | `baien-server-chigiri-procedural-r1` |
| `ihl-defensive-r1.toml` | IHL corpus for Transparent Force authorization grounding (Geneva Conventions + Additional Protocols + ICCPR + ICJ jurisprudence) | A | `baien-server-ihl-defensive-r1` |
| `manabi-legal-literacy-r1.toml` | Public-rights education curriculum for manabi (UDHR + ICCPR + ICESCR + GDPR + regional human-rights conventions) | A | `baien-server-manabi-legal-literacy-r1` |
| `tax-receipt-multi-juris-r1.toml` | Multi-jurisdiction tax-receipt routing knowledge (US IRC sub F + UK ITA + DE EStG + JP 所得税法 + charity-recognition regs) | A | `baien-server-tax-receipt-multi-juris-r1` |

## Discipline

- All recipes are Tier-A only at W1 (most legal corpus is public-domain or open-government-license; Tier-B inclusion requires `-tierB-` infix per G5 of ADR-2605262800).
- Inference of resulting artifacts UNCHANGED Murakumo-only per ADR-2605215000.
- Training may use the train-rental carve-out per ADR-2605262200 once Council ratifies (~2026-07-19 earliest); until then, training is EVO-X2 single GPU only.
- All recipes embed Charter Rider §2 re-scan and PII filter + judicial-party-redactor pass at assembly time (defense in depth; the same shards passed the gate at ingest, but the corpus is the final boundary before SFT).

## Related

- `/90-docs/adr/2605262800-public-data-legal-corpus-ipfs-ingestion.md` — corpus ADR
- `/90-docs/adr/2605262400-public-data-organism-ipfs-ingestion.md` — recipe contract parent
- `/90-docs/adr/2605262700-chigiri-legal-procedure-tier-b-actor-r0.md` — primary consumer actor
- `../tier-a-netreg-foundations.toml` — sibling recipe (net-registry)
