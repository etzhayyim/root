---
id: transparency-worked-examples
title: "Covenant Transparency Doctrine — worked examples (for Council ratification review)"
status: proposed
doc_type: explanation
topic: covenant-transparency-doctrine
authoritative: false
last_verified: 2026-05-31
authoritative_for: []
depends_on:
  - adr-2605310100-covenant-transparency-doctrine-anti-anonymity-and-ingress-logging
related:
  - adr-2605181100-etzhayyim-confidentiality-encrypted-records
supersedes: []
superseded_by: []
---

# Covenant Transparency Doctrine — worked examples

**Status**: illustrative, `proposed-unratified`. These records are NOT live data;
they exist to make ADR-2605310100 concrete for Council Lv7+ ratification review
(Charter §0.4). They show how the §3 ingress-consent rule and the §4 non-waivable
floor behave on real access shapes — especially the hardest case the ADR flagged
(an inbound email that mixes a fourth party's data and a leaked secret).

Every example carries `ratificationStatus: "proposed-unratified"`. Until a
`councilRatificationCid` exists, none of this is published from real access.

---

## Example A — `redactionMethodNote`: the §4 floor filter (the door key, never published)

```json
{
  "$type": "com.etzhayyim.transparency.redactionMethodNote",
  "createdAt": "2026-05-31T00:00:00Z",
  "methodId": "floor-secret-redaction",
  "version": "v1.0.0",
  "title": "§4 non-waivable-floor secret + outbound-PII redaction filter",
  "definition": "Applied to every accessLogPublication BEFORE publication. Detects and strips access-control material and outbound third-party PII from the content/headers of any logged access. Fail-closed: on ANY detection uncertainty the field is redacted, never published. Rationale: publishing access-control material would hand the substrate to the very threat actors the doctrine targets; outbound third-party PII was never brought into etzhayyim's domain by ingress (§4(2)) and stays under the tadori/danjo/himotoki gates.",
  "redactedCategories": [
    "did-private-key",
    "cacao-signature-as-bearer",
    "auth-token",
    "session-secret",
    "kotoba-env-secret",
    "api-credential",
    "outbound-third-party-pii"
  ],
  "detectionPatterns": "{\"headers\":[\"authorization\",\"cookie\",\"x-kotoba-token\"],\"keyPrefixes\":[\"sk-\",\"AKIA\",\"ghp_\",\"KOTOBA_\"],\"entropyBitsPerCharMin\":3.5,\"schemaFields\":[\"cacaoB64\",\"privateKey\"],\"outboundPii\":\"any natural-person identifier naming someone OTHER than the accessing party\"}",
  "failClosed": true,
  "knownFalseNegativeModes": [
    "novel credential format not in keyPrefixes (a false NEGATIVE here is a SECURITY incident, not a privacy one — drives hardening)",
    "secret embedded in an image/attachment rather than text"
  ],
  "appliesToAccessKinds": ["http-request", "xrpc", "mcp", "wallet-tx", "inbound-email"],
  "outboundGateReferenceCids": [
    "<cid:ADR-2605301400-tadori>",
    "<cid:ADR-2605301600-danjo>",
    "<cid:ADR-2605302130-himotoki>"
  ],
  "ratificationStatus": "proposed-unratified",
  "attestingDid": "did:web:etzhayyim.com"
}
```

---

## Example B — `accessLogPublication`: inbound email from a NON-member (the hard case)

A non-member emails a member. The email body contains (1) the sender's own message
(publishable — they reached into etzhayyim's domain, §3), (2) a leaked API key the
sender pasted by accident (`api-credential` → redacted, §4(1)), and (3) a sentence
naming the sender's **child** who never touched etzhayyim (`outbound-third-party-pii`
→ redacted, §4(2)).

```json
{
  "$type": "com.etzhayyim.transparency.accessLogPublication",
  "createdAt": "2026-05-31T00:00:00Z",
  "accessKind": "inbound-email",
  "actorClass": "non-member",
  "peerIp": "203.0.113.7",
  "requestAuditCid": "<cid:kotoba/audit/requests/v1/...>",
  "contentDigest": "<blake3-of-redacted-body>",
  "publishedContent": "From: outsider@example.com\nSubject: question about membership\n\nHi — I'm interested in how etzhayyim works. [API KEY REDACTED — §4(1) api-credential] [NAME REDACTED — §4(2) outbound-third-party-pii] Please reply when you can.",
  "ingressConsentBasis": "ingress-act",
  "secretsRedacted": true,
  "withheldUnderFloor": ["api-credential", "outbound-third-party-pii"],
  "redactionMethodNoteCid": "<cid:Example-A>",
  "ratificationStatus": "proposed-unratified",
  "attestingDid": "did:web:etzhayyim.com"
}
```

**What this demonstrates**

- The sender's own words are published — they chose to reach in (§3). The standing
  notice (`/90-docs/transparency/ingress-disclosure-notice.md`) is their warning.
- The leaked secret is stripped, not published — §4(1) is non-waivable even though
  the sender "consented" by sending. Consent cannot waive the door key.
- The **child's name** is stripped — §4(2). The child never entered etzhayyim's
  domain; ingress-consent does not reach them. **This is exactly the
  innocent-fourth-party cascade the ADR flagged as the sharpest Wellbecoming
  tension** — the schema resolves it by classing such data as `outbound-third-party-pii`
  and routing any actual access request through the himotoki/danjo/tadori gates,
  not through §3 publication. **Council should confirm or revise this resolution at
  ratification.**

---

## Example C — `accessLogPublication`: ordinary HTTP request (no content, IP + path only)

```json
{
  "$type": "com.etzhayyim.transparency.accessLogPublication",
  "createdAt": "2026-05-31T00:00:00Z",
  "accessKind": "http-request",
  "actorClass": "non-member",
  "peerIp": "198.51.100.22",
  "method": "GET",
  "path": "/xrpc/com.etzhayyim.apps.kotoba.graph.sparql",
  "requestAuditCid": "<cid:kotoba/audit/requests/v1/...>",
  "ingressConsentBasis": "ingress-act",
  "secretsRedacted": true,
  "withheldUnderFloor": ["auth-token"],
  "redactionMethodNoteCid": "<cid:Example-A>",
  "ratificationStatus": "proposed-unratified",
  "attestingDid": "did:web:etzhayyim.com"
}
```

The `Authorization` header that accompanied this request is withheld
(`auth-token`); the method/path/IP/time — the existing `fingerprint_middleware`
datom — become publishable.

---

## Example D — `covenantTransparencyAttestation`: a member accepts §1/§2

```json
{
  "$type": "com.etzhayyim.transparency.covenantTransparencyAttestation",
  "createdAt": "2026-05-31T00:00:00Z",
  "memberDid": "did:plc:examplemember",
  "acceptsAnonymityAbolished": true,
  "acceptsFullMemberVisibility": true,
  "acknowledgesNoMemberSecrecy": true,
  "doctrineAdrCid": "<cid:ADR-2605310100>",
  "charterRiderVersion": "v2.0",
  "ratificationStatus": "proposed-unratified",
  "attestingDid": "did:plc:examplemember"
}
```

A member who cannot attest all three `const: true` flags does not join under this
doctrine — partial acceptance is unrepresentable. Per founder direction, those who
require individuated/anonymous protection seek another community (§5).

---

## Open question carried to Council (unchanged from ADR §5)

Examples B's resolution of the fourth-party cascade, and whether "full member
visibility" (§2) extends to §1.13 Eros / pastoral (kokoro) / ceremony (musubi)
content, are **not pre-decided** by these examples. They are the substance of the
Lv7+ ratification vote.
