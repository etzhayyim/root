# equipment/packaging — wire-bond / flip-chip / CoWoS / chiplet bonder reference design

Per **ADR-2605242545** §"Decision 1 row 8".

## Reference vendors

ASE / Amkor / TSMC AP / Samsung AP. 4-company ~60% share.

## Religious-corp design scope

| Layer | Self-design target |
|---|---|
| Wire bonder | gold/copper wire feed + ultrasonic welder driver + 6-DoF stage |
| Flip-chip bonder | bump alignment optics + reflow profile controller |
| CoWoS / chiplet | interposer alignment + thermocompression bond (TCB) head |
| Underfill dispenser | needle dispenser + auto-fill volumetric control |
| Inspection | X-ray for void / overlap inspection (AI runs on iwakura) |
| Reliability | thermal cycling + HTOL chamber control |

## Pregel cell

`silicon_packaging`. Phase 2c priority per ADR-2605242545 §Decision 7 —
needed for fuigo chiplet construction (4-die HBM3e + CoWoS layout).

## Charter Rider §2(a)(c) gate

Low §2(a) risk. §2(c) risk minimal. Normal commit flow.

## Phase 1 scope

README only.
