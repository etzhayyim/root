---
id: doc-2606022500-organism-axis-affiliation-convention
title: "Organism-axis affiliation convention for first-party package READMEs"
status: active
doc_type: reference
topic: organism-axis-affiliation-convention
authoritative: true
last_verified: 2026-06-02
authoritative_for:
  - the one-line organism-axis affiliation declaration each first-party package README carries
related:
  - adr-2605221411-etzhayyim-artificial-organism-ecosystem
---

# Organism-axis affiliation convention

The root `README.md` § "As Artificial Organism Ecosystem" evaluates repo health across
**10 living-system axes** (each an organism property paired with a constitutional invariant).
Axis #10 **Sanctification 聖化** names a standing next-action:

> *Propagate organism-axis affiliation to 39 first-party package READMEs.*

This doc is the **SSoT for what that line looks like**, so the propagation is a mechanical,
drift-free edit rather than 39 independent inventions.

## The line

Each first-party package README carries **one** organism-axis affiliation line in its header
block, declaring the axis the package primarily serves (mirroring the
`20-actors/etzhayyim-organism/README.md` header style):

```
**Organism axis**: Axis <N> — <Name> (<漢字> / <religious correspondence>) — <one-clause why>.
```

A package MAY add a secondary axis after an em-dash if a second axis is clearly load-bearing,
but the **primary** axis is mandatory and comes first.

## The 10 axes (from root README)

| # | Axis | 漢字 | Religious correspondence | Typical package fit |
|---|---|---|---|---|
| 1 | Autopoiesis | 自己創出 | 無教会 / 万人祭司 | governance / harness / self-organizing tooling |
| 2 | Metabolism | 代謝 | 産霊 (musuhi — generative cycle) | **producer / manufacturing actors** (feedstock→product→donation) |
| 3 | Homeostasis | 恒常性 | 和 (substrate-boundary harmony) | substrate / infra / enforcement |
| 4 | Active Inference | 能動推論 | 縁起 (model ↔ observation) | observation / sensor / KG actors |
| 5 | Reproduction | 生殖 | 八百万 propagation | fork / scaffold / template tooling |
| 6 | Symbiosis | 共生 | Tree of Life branches | multi-substrate / integration actors |
| 7 | Diversity | 多様性 | 八百万-kami | variety / catalogue / many-cell actors |
| 8 | Wellbecoming | 動的軌跡 | 子・孫 priority | care / education / multi-generation actors |
| 9 | Anti-fragility | 反脆弱 | Reformed resilience | disaster / security / redundancy actors |
| 10 | Sanctification | 聖化 | Sola Scriptura → Charter Rider | license / doctrine / compliance |

## Propagation status (incremental)

The 39-README propagation runs incrementally; this section is the checklist.

- ✅ `20-actors/himawari` — Axis 2 Metabolism (PV module production feeding the energy chain)
- ✅ `20-actors/funadaiku` — Axis 2 Metabolism (zero-emission cargo-ship production)
- ✅ `20-actors/sarutahiko` — Axis 2 Metabolism (heavy-truck production)
- ⬜ remaining first-party packages — follow-up (same one-line edit; pick the primary axis from the table above)

> First slice applied 2026-06-02 (the three R0 manufacturing actors matured in the same session).
> Any subsequent session/agent extends the checklist by adding the line to one more package README
> and ticking it here — no new convention needed.
