# LICENSE boundary — maxwell/mmdiffusion (Path A, ADR-2606172300)

This directory ships a **two-layer** license, per ADR-2606172300 D2 and the Path A
decision (ImageBind internal-only, non-redistributed).

| Artifact | License | Ships as commons? |
|---|---|---|
| **This scaffold code** (`*.py`, `README.md`) | Apache 2.0 + Charter Rider (→ ECL-on-Apache once ratified) | ✅ yes |
| **Trained projection / graft weights** | OpenRAIL-M + Charter §2 Attachment (commons) **or** CC-BY-NC (if ImageBind-derived) | depends on encoder |
| **ImageBind weights** | CC-BY-NC 4.0 — `vendor/imagebind-fork/`, NOTICE preserved, **no Rider** | ❌ never redistributed |
| **ImageBind-derived embeddings / outputs** | CC-BY-NC 4.0 | ❌ Maxwell-internal only |
| **LanguageBind weights / outputs** | MIT / ECL-on-Apache | ✅ commons path |

## Rules

1. **Do NOT vendor ImageBind into this repo.** It stays in `vendor/imagebind-fork/`
   (gitignored / out-of-tree), CC-BY-NC NOTICE intact, no Charter Rider added
   (CLAUDE.md: "Do not add Charter Rider to 3rd-party vendored code").
2. **ImageBind path = internal only.** Its embeddings/outputs are CC-BY-NC and MUST NOT
   be published as commons nor feed the SBT↔SBT internal economy (G4, enforced in
   `conditioning.py::assert_charter_gates`).
3. **Commons path = LanguageBind (MIT).** When the graft is to be released, use the
   LanguageBind encoder; outputs carry ECL-on-Apache.
4. **Inference is Murakumo-only** (Rider §2(i), ADR-2605215000) — frozen-encoder forward
   passes run on the fleet, never on a commercial GPU backend.

See `90-docs/papers/2606171500-license-charter-fit-evaluation/` for the numeric basis
and ADR-2606172300 for the ECL design.
