---
id: adr-2606071238-session-close-nondual-experience-conversion-charter-1-17
title: "ADR-2606071238: Session close — Charter §1.17 自他非分離の直接体験 (doctrine) + §1.17.6 guidance UI (yoro deployed live, maps built+pending)"
status: active
doc_type: adr
topic: session-close-nondual-experience-conversion
authoritative: true
last_verified: 2026-06-07
priority: 4.0
axis: governance
weight: 0.40
priority_note: "Documentation-only closure of the 2026-06-07 session. Authoritative design = ADR-2606071009 (Charter §1.17). This ADR records what landed, what deployed, and the honest remaining gaps; it makes no new decision and amends no invariant."
authoritative_for:
  - session-close record for the Charter §1.17 non-dual-experience wave (2026-06-07)
depends_on:
  - ADR-2606071009 (Charter §1.17 — the authoritative doctrine this session shipped)
related:
  - adr-2606071009-nondual-direct-experience-conversion-core
  - adr-2605302357-etzhayyim-social-security-for-humanity
  - adr-2605192100-etzhayyim-mission-charter
supersedes: []
superseded_by: []
---

# ADR-2606071238: Session close — Charter §1.17 自他非分離の直接体験 + §1.17.6 guidance UI

**Status**: active
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

Documentation-only closure of the 2026-06-07 session. The authoritative design record is **ADR-2606071009** (Charter §1.17); this note records what landed, what deployed, and the honest remaining gaps. It makes no new decision and amends no invariant.

# Context

Author directive (2026-06-07): *"宗教法人のコアなので国家規制は前提にしない。あくまでも合法管轄を前提として違法行為は推奨しないが、宗教的段階としては要する、前提とする。宗教は国家を超越する。"* — make the direct experience of 自他非分離 (non-duality) / 変性意識 a **required religious stage** of 回心, presupposing legal jurisdictions and never recommending illegal acts, and surface a pre-registration guide on the yoro + maps onboarding surfaces.

# Decision (what landed)

Authored **ADR-2606071009 — Charter §1.17** (proposed; identity-level §1.17.1–.3 require Council Lv7+ unanimity + 30-day objection): authentic 回心 (metanoia, §1.16.3) presupposes a **direct experience of 自他非分離** as a constitutive, required religious stage — the experiential ground of §1.8 anti-individualist ontology and §0 Kingdom. Two never-weakened lines:

- **§1.17.3 means-agnostic** — the requirement is the **EXPERIENCE**, never any substance; lawful contemplative paths (観想 / 沈黙 / 断食 / 坐禅 / 祈り / 自然での孤独) are always shown and co-recommended.
- **§1.17.4 legality floor (NEVER-amendable)** — entheogenic means are lawful-jurisdiction-only and member-chosen; etzhayyim never procures / supplies / arranges / instructs unlawful acquisition. "宗教は国家を超越する" governs the *source of authority* (§0.1 not-state-granted / §1.12 routing-around), **not** a license to commit or recommend crimes.
- **§1.17.5** preserves and strengthens §1.16.8 anti-coercion: the stage gates **spiritual advancement**, never **Level-0 social-security entry** (benefits-not-hostage).

## Shipped artifacts

| Item | PR | State |
|---|---|---|
| ADR-2606071009 (Charter §1.17 doctrine) | #1354 | merged to `main`; **proposed** (Council Lv7+ to ratify identity-level §§1.17.1–.3) |
| yoro §1.17.6 pre-registration guide (`NondualExperienceGuide.svelte` + `/welcome` phase) | #1355 | merged + **deployed live** to `yoro.etzhayyim.com` (Worker `magatama-yoro`, Version `e941f164-efec-4ad6-acf0-ada44944b469`); `/` and `/welcome` → HTTP 200 |
| maps §1.17.6 pre-entry guide (self-contained port + `/welcome` + first-visit overlay) | #1357 | merged + **built & wrangler@4 dry-run-validated**; production deploy **pending** |

## UI behaviour (both apps, §1.17.6)

- means-agnostic legal contemplative paths **always** shown;
- `retreat.guru` shown **only** when the viewer's jurisdiction is lawful, resolved client-side via Cloudflare `/cdn-cgi/trace` `loc`, **fail-closed** (JP / US / unresolved → legal paths only); allowlist `BR/PE/EC/CO/BO/CR/NL/JM/CH/AU/CA` (advisory, Council/legal-review-gated);
- mandatory contraindication warning (MAOI × SSRI/SNRI, cardiac, psychiatric, pregnancy, minors) + third-party disclaimer (no booking / brokerage / procurement);
- geo-**unresolved** distinguished from resolved-but-**excluded** (a failed geo probe asserts no jurisdictional/legal conclusion);
- maps renders guide **XOR** map (no heavy WebGL behind the overlay; no flash).

These refinements were applied after an independent code review (geo mis-assertion, behind-overlay map mount, CRLF regex tolerance).

# Consequences

- yoro carries the §1.17.6 guidance live; maps carries the merged code but is not yet serving it.
- ADR §1.17 is recorded as proposed doctrine; it is **not ratified** — no benefit, ladder gate, or live behaviour treats the experience as binding until Council Lv7+ acts.
- No invariant changed (N1/N4/N7/N8 and §1.1–§1.16 untouched); §1.16.8 strengthened.

## Honest remaining gaps (operator-coordinated)

1. **maps production deploy** — blocked from the isolated worktree by (a) maps not being a `pnpm-workspace.yaml` member (worked around with a temporary, reverted edit to build), (b) raw `wrangler@4` auto-provisioning the shared R2 bucket `etzhayyim-cache` twice (`YATA_R2` + `CACHE_R2`) → "already exists" failure **before** worker upload (production worker unchanged, no harm), and (c) the maps app's own bundled wrangler is 3.114 (drops `secrets_store_secrets`). Deploy via the operator's established maps procedure (pre-linked resources / matching wrangler) once resolved.
2. **maps.etzhayyim.com DNS** — currently does not resolve (yoro does); pre-existing condition to verify (the failed deploy never reached the route/DNS step).
3. **yoro edge-cache purge** — skipped: `CACHE_PURGE_API_KEY` not available in this environment (non-critical; edge TTL expires; Worker code is already live).
4. **CLAUDE.md fix** — the documented yoro deploy path `wasm/yoro-ui-g00h5zto` is stale; the real deployable is `appview/yoro-ui-g00h5zto` (`wrangler.jsonc`, main `src/worker.ts`).

# Alternatives Considered

- **No session-close record** — rejected; the repo's closing ritual (cf. ADR-2606070030, ADR-2606065000) keeps the next operator oriented and the honest deploy gaps visible.

# References

- ADR-2606071009 (Charter §1.17 — authoritative doctrine)
- ADR-2605302357 (Charter §1.16 Social Security — §1.16.3 conversion gate, §1.16.8 anti-coercion preserved)
- ADR-2605192100 (Mission Charter — §1.8 anti-individualist ontology, §1.12 routing-around, §1.15 non-eschatology)
- ADR-2605252300 (Charter §0 Preamble — §0.1 not-state-granted)
- PRs #1354 (ADR), #1355 (yoro UI, deployed), #1357 (maps UI, pending)
