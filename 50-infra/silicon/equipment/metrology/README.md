# equipment/metrology — overlay + CD-SEM + particle inspection reference design

Per **ADR-2605242545** §"Decision 1 row 6".

## Reference vendors

KLA. 1-company near-monopoly (~75% overlay + CD-SEM).

## Religious-corp design scope

| Layer | Self-design target |
|---|---|
| Overlay scanner | optical interferometer + image processing pipeline |
| CD-SEM | electron column reference design (filament + Wehnelt + condenser + objective) + detector |
| Particle inspector | dark-field / bright-field optical inspection + LED illumination + image AI |
| Inspection AI | **runs on iwakura** — defect classification model is BitNet 1.58 ternary |
| Wafer handler | shared with packaging — common alignment chuck |

The inspection AI being **iwakura-native** is the key architectural
choice: defect classification is a vision task that fits baien's
edge invariant (small model, real-time inference). This means
`silicon_metrology` Pregel cell calls iwakura via the regular
`kotodama.AgentChat` path with a vision-only model registry entry.

## Pregel cell

`silicon_metrology`. Co-located with iwakura sim node (`simeon` in
Murakumo fleet) so inspection AI inference is local.

## Charter Rider §2(a)(c) gate

**§2(c) risk**: CD-SEM imaging AI can be retargeted to face recognition
or generic person-identification. Inspection AI training data MUST be
restricted to wafer-defect samples; commits adding human/face datasets
trigger Council review.

## Phase 1 scope

README only. Phase 2b priority per ADR-2605242545 §Decision 7 (AI side
first, hardware later).
