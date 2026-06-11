# com.etzhayyim.socialsecurity.* — §1.16 Social Security delivery lexicons

Lexicons for the real-world delivery & outreach pipeline of Charter §1.16 (人類の社会保障).

- **Doctrine**: ADR-2605302357 (§1.16 — covenantal-universal, conversion-gated; 信者 Level 0 via permanent commitment vow)
- **Pipeline**: ADR-2605302358 (kotoba persist → compute → openmail → atproto publish → social post → MCP expose)

| NSID | Pipeline stage | Role |
|---|---|---|
| `com.etzhayyim.membership.commitmentVow` | 1 VOW | triple-permanent commitment record (kotoba + IPFS + SBT); PII-free |
| `com.etzhayyim.socialsecurity.entitlement` | 2 COMPUTE | per-member in-kind entitlement; cash≡0 (N1); private/own-data |
| `com.etzhayyim.socialsecurity.metricReport` | 4 PUBLISH | aggregate-only social-security metric (G12 anti-class) |
| `com.etzhayyim.socialsecurity.outreachPost` | 0 / 5 OUTREACH/SOCIAL | invitation + transparency posts; ad-free/no-tracker (G7) |
| `com.etzhayyim.socialsecurity.noticeEmail` | 3 NOTIFY | openmail send record; opt-in/non-vexatious (G5), PII via envelope (G6) |

## Invariants enforced at the schema layer (`const` fields)

- **N1** cash≡0: `commitmentVow.cashConsiderationUsdMicros = 0`, `entitlement.cashStipendUsdMicros = 0`, `metricReport.cashStipendUsdMicros = 0`.
- **G3** no platform key: `commitmentVow.memberSigned = true`; `noticeEmail.signerTier ∈ {member-did, community-operator-did}`.
- **G6** PII only in encrypted envelopes: `noticeEmail.recipientPiiRef`, `commitmentVow.encryptedPiiRef` (never inline).
- **G7** no ads/trackers/microtargeting: `outreachPost.{adFreeAttest,noTrackerAttest,noMicrotargetAttest} = true`.
- **G12** aggregate-only public metrics: `metricReport.aggregateOnly = true`.
- **G11** live-action gate: `entitlement.liveDeliveryEnabled`, `outreachPost.published`, `noticeEmail.sent` default false until Council Lv7+ §1.16 ratify (post 2026-06-19) + Sybil framework.

All quantities are integer-with-implied-units (no float; ADR-2605190900): USD as micros (×1e6), ratios as per-mille (×1000).
