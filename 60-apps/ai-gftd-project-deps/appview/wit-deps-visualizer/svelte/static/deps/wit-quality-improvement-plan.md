# WIT/WASM Quality Improvement Plan

- Generated: 2026-03-21T12:48:59Z
- Source graph generatedAt: 2026-03-21T12:48:56.800Z

## Global Findings

- total components: 3780
- isolated components: 346
- capability missing: 3439
- RBAC missing: 3623
- governance missing: 779
- capability+RBAC+governance all missing: 765
- critical components (risk>=100): 37

## P0 Target Projects (by critical count)

| project | critical | triple-missing | isolated | total |
| --- | ---: | ---: | ---: | ---: |
| ai-gftd-project-kyber-qzzg06nh | 8 | 19 | 8 | 20 |
| ai-gftd-project-yorishiro | 2 | 13 | 22 | 33 |
| ai-gftd-project-public-fund | 2 | 2 | 2 | 2 |
| ai-gftd-project-os | 1 | 13 | 1 | 17 |
| ai-gftd-project-tsukuru | 1 | 9 | 2 | 53 |
| ai-gftd-project-aima | 1 | 4 | 1 | 5 |
| ai-gftd-project-kareyanagi | 1 | 1 | 2 | 2 |
| ai-gftd-project-omise | 1 | 1 | 2 | 2 |
| ai-gftd-project-basic | 1 | 1 | 1 | 1 |
| ai-gftd-project-business-edge | 1 | 1 | 1 | 1 |
| ai-gftd-project-cad | 1 | 1 | 1 | 1 |
| ai-gftd-project-casino | 1 | 1 | 1 | 1 |
| ai-gftd-project-contacts | 1 | 1 | 1 | 1 |
| ai-gftd-project-denki | 1 | 1 | 1 | 1 |
| ai-gftd-project-deps | 1 | 1 | 1 | 1 |

## P0 Critical Components (Top 30)

| project | componentId | risk | isolated | cap | rbac | gov |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ai-gftd-project-aima | ai-gftd-wasm-laser-ls7s8t9u | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-basic | ai-gftd-wasm-basic-bs1c4l2f | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-business-edge | ai-gftd-wasm-business-edge-bz4x8m2w | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-cad | ai-gftd-wasm-cad-cd4dview | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-casino | casino-kq4h2ovt | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-contacts | contacts-mcp-component | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-denki | ai-gftd-wasm-denki-dk3n7k8p | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-deps | wit-deps-visualizer | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-food | ai-gftd-wasm-food-fd7o8d3n | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-food-processor | ai-gftd-wasm-food-processor-fp3k7m9q | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-gas | ai-gftd-wasm-gas-gs5a6s1m | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-gol-d-roger | ai-gftd-wasm-gol-d-roger-wy2zvdvd | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-hanrei | ai-gftd-wasm-hanrei-jp-h4nr31jp | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-kareyanagi | ai-gftd-wasm-kareyanagi-ui-kpat4bp7 | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-kyber-qzzg06nh | ai-gftd-wasm-kyber-ga-x4s6m1n7 | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-kyber-qzzg06nh | ai-gftd-wasm-kyber-legal-w9p5r2t6 | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-kyber-qzzg06nh | ai-gftd-wasm-kyber-marketing-r8v2k4m1 | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-kyber-qzzg06nh | ai-gftd-wasm-kyber-production-u2m4h7f5 | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-kyber-qzzg06nh | ai-gftd-wasm-kyber-sales-t3x7n9p2 | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-kyber-qzzg06nh | ai-gftd-wasm-kyber-scm-q5w8j6d3 | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-kyber-qzzg06nh | ai-gftd-wasm-kyber-service-v6n3k8g4 | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-kyber-qzzg06nh | ai-gftd-wasm-kyber-tech-olohwwce | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-music | music-mcp-component | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-omise | omise-taxonomy-bridge-component | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-os | os-cluster-component | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-public-fund | ai-gftd-wasm-pb-p8bl1cfn | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-public-fund | public-fund-orchestrator-component | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-real-estate | real-estate-mcp-component | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-robot | robot-mcp-component | 110 | yes | 0 | 0 | 0 |
| ai-gftd-project-sos | ai-gftd-wasm-systemofsystem-s0s5ys0s | 110 | yes | 0 | 0 | 0 |

## ISCO Focus (Top 30 by risk)

| componentId | risk | isolated | cap | rbac | gov |
| --- | ---: | ---: | ---: | ---: | ---: |
| ai-gftd-wasm-isco-bankruptcy-bkzibt0j | 85 | yes | 0 | 0 | 10 |
| ai-gftd-wasm-isco-bm-i7n73l0x | 85 | yes | 0 | 0 | 30 |
| ai-gftd-wasm-isco-bm-mlk8x2p9 | 85 | yes | 0 | 0 | 15 |
| ai-gftd-wasm-isco-eng-i7n73l0x | 85 | yes | 0 | 0 | 30 |
| ai-gftd-wasm-isco-eng-mlk8x2p9 | 85 | yes | 0 | 0 | 15 |
| ai-gftd-wasm-isco-mk-i7n73l0x | 85 | yes | 0 | 0 | 30 |
| ai-gftd-wasm-isco-mk-mlk8x2p9 | 85 | yes | 0 | 0 | 15 |
| ai-gftd-wasm-isco-po-i7n73l0x | 85 | yes | 0 | 0 | 30 |
| ai-gftd-wasm-isco-po-mlk8x2p9 | 85 | yes | 0 | 0 | 15 |
| ai-gftd-wasm-isco-qa-i7n73l0x | 85 | yes | 0 | 0 | 15 |
| ai-gftd-wasm-isco-qa-mlk8x2p9 | 85 | yes | 0 | 0 | 15 |
| ai-gftd-wasm-isco-43-numerical-recording-clerks-i5c043rc | 35 | no | 0 | 0 | 38 |
| ai-gftd-wasm-isco-44-other-clerical-support-i5c044oc | 35 | no | 0 | 0 | 38 |
| ai-gftd-wasm-isco-51-personal-services-i5c051ps | 35 | no | 0 | 0 | 38 |
| ai-gftd-wasm-isco-52-sales-workers-i5c052sw | 35 | no | 0 | 0 | 38 |
| ai-gftd-wasm-isco-53-personal-care-i5c053pc | 35 | no | 0 | 0 | 38 |
| ai-gftd-wasm-isco-54-protective-services-i5c054pw | 35 | no | 0 | 0 | 38 |
| ai-gftd-wasm-isco-61-market-agriculture-i5c061ag | 35 | no | 0 | 0 | 38 |
| ai-gftd-wasm-isco-62-forestry-fishery-i5c062ff | 35 | no | 0 | 0 | 38 |
| ai-gftd-wasm-isco-63-subsistence-agriculture-i5c063sa | 35 | no | 0 | 0 | 38 |
| ai-gftd-wasm-isco-71-building-trades-i5c071bt | 35 | no | 0 | 0 | 38 |
| ai-gftd-wasm-isco-72-metal-machinery-trades-i5c072mm | 35 | no | 0 | 0 | 38 |
| ai-gftd-wasm-isco-73-handicraft-printing-i5c073hp | 35 | no | 0 | 0 | 38 |
| ai-gftd-wasm-isco-74-electrical-electronic-trades-i5c074ee | 35 | no | 0 | 0 | 38 |
| ai-gftd-wasm-isco-75-food-processing-trades-i5c075fw | 35 | no | 0 | 0 | 38 |
| ai-gftd-wasm-isco-81-stationary-plant-operators-i5c081sp | 35 | no | 0 | 0 | 38 |
| ai-gftd-wasm-isco-82-assemblers-i5c082as | 35 | no | 0 | 0 | 38 |
| ai-gftd-wasm-isco-83-drivers-mobile-operators-i5c083dm | 35 | no | 0 | 0 | 38 |
| ai-gftd-wasm-isco-91-cleaners-helpers-i5c091ch | 35 | no | 0 | 0 | 38 |
| ai-gftd-wasm-isco-92-agricultural-labourers-i5c092al | 35 | no | 0 | 0 | 38 |

## Improvement Plan

1. P0 (1-2 weeks): Add capability tags and Responsible/Accountable/RequireApproval metadata to all critical components, starting from the top 3 projects.
2. P1 (2-4 weeks): Remove isolation by wiring command/query links for components that are isolated but should participate in runtime/domain graph.
3. P2 (continuous): Add per-project CI gate to fail when new component has cap=0 or gov=0 without explicit allowlist.
4. P2 (continuous): Regenerate full-audit weekly and track trend of isolated/triple-missing/critical counts.

