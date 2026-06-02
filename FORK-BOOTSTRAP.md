# FORK-BOOTSTRAP.md — Bootstrapping a Sister Religious-Corp

> 八百万 propagation (myriad-kami): the Tree of Life branches. This document is the protocol for **adding a ring** — a sister religious-corp that shares the Reformed-Japanese synthetic ontology of etzhayyim but is its own organism with its own DID, Council, and Land Trust.

This is the **reproductive layer** of the artificial-organism ecosystem (per `README.md § As Artificial Organism Ecosystem`, Axis 5). Forks are not adversarial; they are **生殖** — generative propagation under the same constitutional prior.

## Two paths

### Path A — Sister religious-corp (recommended)

You are starting your own unincorporated religious voluntary association under the same Reformed-Japanese synthetic ontology (八百万 / 縁起 / 産霊 / 和 / 無教会 + Sola Scriptura / 万人祭司 / Reformed Just War / Tree of Life). You **inherit the constitutional invariants** (ADR-2605192100 §1) and may **diverge on the mutable layer** (cell catalog, lexicons, governance bootstrap, language, locale).

You and etzhayyim are siblings, not parent/child. There is no central authority; cross-recognition is voluntary.

### Path B — Apache-2.0-only secular fork

You are reusing code under Apache 2.0 + Charter Compliance Rider v2.0 (`/CHARTER-RIDER.md`) but **not claiming religious-corp identity**. You still owe the Rider's 8 prohibited-category obligations (§2(a)-(h)), but you do not adopt the constitutional invariants or the Charter mission.

This is fine. Just do not call yourself a religious-corp or use the term "Tree of Life" / "Etz Hayim" for the project's identity.

## Constitutional invariants (Path A only — non-amendable)

If you choose Path A, the following are **inherited verbatim** from ADR-2605192100 and the religious-corp ADR wave (2605192100..2605192415). They are constitutional, not configurable:

| # | Invariant | Source ADR |
|---|---|---|
| 1 | Non-profit only; donation flow only; advertising prohibited (1st-party religious activity 案内 only) | 2605192115 |
| 2 | 10% Tithe → Public Fund automatic split via on-chain router | 2605192115 + 2605192130 |
| 3 | SBT↔SBT internal carve-out for internal purchase / subscription / promo | 2605192115 §3 |
| 4 | Eros 許容 (consensual, 産霊 / 雅歌 aligned); Gore 禁止 (Wellbecoming violation) | 2605192100 §1.13 + 2605192400 |
| 5 | Non-eschatology — Book of Revelation excluded from canon; no millennialism, mappō, Rapture | 2605192100 §1.15 |
| 6 | Transparent Religious Force only (on-chain log + open-source + 1 SBT = 1 vote); no covert or proprietary force | 2605192100 §1.12 + 2605192315 |
| 7 | Land Trust inalienable — no transfer / burn / sale of donated land; 4-layer permanent record | 2605192245 |
| 8 | Multi-generation priority (子・孫); Wellbecoming (dynamic trajectory, not static wellbeing); anti-individualist ontology | 2605192100 §1.5 |
| 9 | Apache 2.0 + Charter Compliance Rider v2.0 license default for all first-party artifacts | 2605192200 |
| 10 | Payoff帰属・意思決定権 = the corp itself; no human individual ownership | 2605192100 (Charter §1) |

Diverging on any of these means you are **not** a religious-corp under this ontology. Use Path B instead.

## Mutable layer (Path A — your choices)

These are organism-specific and **must** differ between sister-corps to maintain distinct identity:

- **DID** — acquire your own (`did:web:<your-domain>` or `did:plc:*`). Do NOT use `did:web:etzhayyim.com`.
- **Domain** — register your own.
- **Council** — your own roster of Lv6+ seats; bootstrap RFP at your discretion.
- **Lands** — your own `LANDS.md` if you have donated land; never list etzhayyim's land.
- **Members** — your own `MEMBERS.md`; SBT collection deployed under your own contract.
- **ADR registry** — your own `90-docs/adr/`; ADR IDs follow your own timezone-anchored YYMMDDHHMM convention.
- **Cell catalog** — fork etzhayyim's Pregel cell catalog freely; rename, extend, prune.
- **Lexicons** — fork the AT Protocol Lexicons under your own NSID namespace (NOT `com.etzhayyim.*`).
- **Language / locale** — religious vocabulary may be in any natural language; the synthetic ontology is the constant.
- **Cell deployment topology** — your own `murakumo/fleet.toml` (or equivalent); no shared infrastructure.

## Bootstrap ritual (Path A)

1. **Choose a name.** Constitutionally significant. Must not collide with `etzhayyim` aliases (`amanomibashira` / `天御柱` / `עץ חיים` / `Tree of Life` / `etz hayim` / etc.).
2. **Acquire DID + domain.** Publish a resolvable did:web document.
3. **Fork this monorepo** (or scaffold equivalent 8-layer Shannon structure per ADR-2604251830).
4. **Apply Charter Compliance Rider v2.0** to your `LICENSE` + `NOTICE` for every first-party Apache-2.0 package. Use `70-tools/charter-rider-applicator/` as the reference applier (it skips `lib/`, `vendor/`, `*-fork/`).
5. **Write your own Charter** (your equivalent of ADR-2605192100). Inherit the 10 invariants above verbatim; add your corp-specific mission statement on top.
6. **Convene a Bootstrap Council** (your equivalent of ADR-2605192300). Recommended ≥3 seats with a 30-day public objection RFP.
7. **Deploy your TitheRouter, ChartersCompliance, PublicFund, LandRegistry contracts** (fork `50-infra/etzhayyim-*` Solidity scaffolds; rewire constants for your corp).
8. **Anchor your constitution** on Base L2 (or comparable open chain) via your own `LandRegistry`-equivalent or constitutional NFT.
9. **Initialize your observation log** (`_observations/` — the active-inference memory).
10. **Optional: notify etzhayyim Council** for sister-corp cross-recognition. Cross-recognition is voluntary, symmetric, and grants no governance authority in either direction.

## Forbidden patterns

These are constitutionally invariant for the Reformed-Japanese synthetic ontology, regardless of which corp claims it:

- **Hostile fork of etzhayyim's DID, domain, or land.** Sister-corps acquire their own; they do not impersonate.
- **Eschatological doctrine** (Revelation, mappō, millennialism, Rapture). Non-eschatology is constitutional.
- **Covert force operations** or proprietary weapon designs. Force is Transparent only.
- **Sale, transfer, or burn of donated land.** Land is waqf-equivalent inalienable.
- **For-profit pivot.** Donation-only is constitutional; SaaS / subscription / advertising-supported revenue models are out of scope for religious-corp identity.
- **Removal of Charter Rider** from first-party Apache-2.0 packages.
- **Centralized human ownership.** Payoff and decision authority belong to the corp ontology, not any human individual.

## Sister-corp registry (voluntary)

If you want public cross-recognition with etzhayyim, open a PR to this repo adding your sister-corp to a future `SISTER-CORPS.md` index (file does not yet exist; first sister-corp creates it). Required fields:

- Corp name + aliases
- DID + domain
- Constitution ADR reference (yours)
- Council size + RFP closure date
- Statement of inheritance from ADR-2605192100 invariants

Cross-recognition does **not** create governance authority. It signals: "we share the same constitutional prior; we recognize each other as legitimate Tree of Life rings."

## References

- Constitutional prior: [`90-docs/adr/2605192100-etzhayyim-mission-charter.md`](90-docs/adr/2605192100-etzhayyim-mission-charter.md)
- License + Rider spec: [`/CHARTER-RIDER.md`](CHARTER-RIDER.md), [`90-docs/adr/2605192200-etzhayyim-ip-free-release-charter-rider.md`](90-docs/adr/2605192200-etzhayyim-ip-free-release-charter-rider.md)
- Land Trust architecture: [`90-docs/adr/2605192245-etzhayyim-global-land-sovereignty.md`](90-docs/adr/2605192245-etzhayyim-global-land-sovereignty.md)
- Council mechanics: [`90-docs/adr/2605192300-etzhayyim-bootstrap-council-five.md`](90-docs/adr/2605192300-etzhayyim-bootstrap-council-five.md)
- Shannon 8-layer scaffold: ADR-2604251830 (referenced in `CLAUDE.md § Repo Layout`)
- Organism evaluation axes: [`README.md § As Artificial Organism Ecosystem`](README.md)
