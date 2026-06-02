# com.etzhayyim.transparency.* — Covenant Transparency Doctrine Lexicons

**ADR**: ADR-2605310100 (R0 scaffold)
**Status**: R0 schema skeletons, **`proposed-unratified`**. These Lexicons
are DESIGN INTENT only. The doctrine MATERIALLY AMENDS the confidentiality
invariant (ADR-2605181100) + the Substrate-boundary Confidentiality row, and
INTERSECTS §1.13 Eros / Wellbecoming — so it **requires Council Lv7+ unanimity
(Charter §0.4)** before any member-facing rollout. Every record type carries a
`ratificationStatus` field pinned to `const: "proposed-unratified"`: until a
`councilRatificationCid` exists on-chain, NO live logging/publication change is
executed (ADR-2605310100 §5).

## Doctrine in one line

The X-style failure mode (anonymous fraud / slander / threat actors) is solved
by abolishing **anonymity** (every act bound to an accountable DID+SBT), not
privacy-in-the-abstract. Within the covenant: no member-to-member secrecy —
every believer sees every member action (§1/§2). At the boundary: **ingress
consent** — anyone (member or non-member) who reaches into etzhayyim/kotoba
resources consents to full logging + public publication of that access,
inbound email included; *don't consent → don't access* (§3). The **§4 floor**
is non-waivable: secrets/keys are never published, and outbound third-party
data not brought in by ingress stays under the tadori/danjo/himotoki gates.

## 4 Lexicons

| # | Lexicon | Purpose |
|---|---|---|
| L1 | `ingressDisclosureNotice` | The standing notice served on every ingress surface (http/xrpc/mcp/wallet-tx/inbound-email). States the §3 ingress-consent rule + the §4 floor. `ratificationStatus=proposed-unratified`. Canonical text (ja/en): `/90-docs/transparency/ingress-disclosure-notice.md` |
| L2 | `accessLogPublication` | A published access-log record — promotes the kotoba `fingerprint_middleware` audit datom (`kotoba/audit/requests/v1`) + inbound-email ingest to publishable. `secretsRedacted=true` (§4); `ingressConsentBasis=ingress-act` |
| L3 | `covenantTransparencyAttestation` | A member's voluntary acceptance of §1/§2 (anonymity abolished + full member visibility + no member secrecy). Voluntary-covenant model; §1.13 visibility reserved to Council |
| L4 | `redactionMethodNote` | Open, versioned spec of the §4 floor redaction filter (what `accessLogPublication` strips before publishing). `failClosed=true`; the membership audits the redactor itself, not only its output. Referenced by `accessLogPublication.redactionMethodNoteCid` |

## Schema Discipline — CONSTITUTIONAL anchors (R0)

- **Ratification gate (§5)**: every record's `ratificationStatus` is
  `const: "proposed-unratified"`. The doctrine cannot self-execute; flipping to
  a ratified state requires a recorded Council Lv7+ unanimity amending
  ADR-2605181100. Until then these records are inert scaffolds.
- **§4 floor is structural**: `accessLogPublication.secretsRedacted` is
  `const: true`; `withheldUnderFloor[]` records what transparency did NOT
  publish (credentials / CACAO-as-bearer / private-key / outbound-third-party-pii).
  Access-control material is never publishable — publishing it would hand the
  substrate to the very threat actors the doctrine targets.
- **Ingress consent is territorial, not membership-based**:
  `accessLogPublication.ingressConsentBasis` is `const: "ingress-act"` — consent
  is constituted by the act of access, so non-members are in scope by §3.
- **Anonymity abolished (§1)**: the attestation's
  `acceptsAnonymityAbolished` / `acceptsFullMemberVisibility` /
  `acknowledgesNoMemberSecrecy` are all `const: true` — partial acceptance is
  unrepresentable; the covenant terms are accepted whole or not at all.
- **`additionalProperties: false`** at top-level + nested objects is the R1
  closure step (repo-wide convention).

## OPEN QUESTION reserved to Council (§5)

Whether "every believer sees every member action" extends to **§1.13 Eros**,
pastoral care (kokoro), and covenant ceremony (musubi) — the sharpest
Wellbecoming / anti-harm tension. The schemas do NOT pre-decide this;
ratification must rule whether such content is in-scope or is a §4-style floor
carve-out.

## Related Files

- `/90-docs/adr/2605310100-covenant-transparency-doctrine-anti-anonymity-and-ingress-logging.md` — master ADR
- `/90-docs/transparency/ingress-disclosure-notice.md` — canonical standing notice text (ja/en)
- `/90-docs/transparency/worked-examples.md` — worked records (§4 floor + fourth-party cascade) for Council ratification review
- `/90-docs/transparency/ratification-dossier.md` — Council Lv7+ decision sheet: threat model + what-flips-on-YES + open questions + legal/reversibility risk register
- `/90-docs/adr/2605181100-*` (ADR-2605181100 confidentiality — **amended by this doctrine**)
- `/00-contracts/lexicons/com/etzhayyim/encrypted/` — `com.etzhayyim.encrypted.*`, re-scoped by §4/§6 to the floor only (secrets + outbound third-party PII), not member privacy
- `/40-engine/kotoba/crates/kotoba-server/src/fingerprint.rs` — request audit trail (`kotoba/audit/requests/v1`) promoted to publishable by §3 (post-ratification)
- `/70-tools/scripts/lint/transparency-floor-and-gate.mjs` — enforcement guard (Check A §5 ratification gate · Check B §4 floor anchors · Check C no premature execution in code) + `.test.mjs` 9-test regression suite. Machine-enforces that the doctrine stays `proposed-unratified` until a `councilRatificationCid` exists
