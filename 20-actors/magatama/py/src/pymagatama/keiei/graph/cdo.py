"""CDO role graph — Phase 3 of the keiei layer (shadow mode).

Human seat: k.takahashi@gftd.co.jp. Shadow mode.
ADR 2605101200 §3 row=cdo.

Class C = autonomous (design-system audit, asset triage, internal mockup
        review, owned-channel visual tweak).
Class B = blocking human confirm (k.takahashi ratifies for any change
        with cross-product impact or visible to external audience).
Class A = always escalate to k.takahashi + CEO 河崎 (major brand pivot,
        logo change, signature ramp).

Lens:
  - Bonsai cultivar visual metaphor family (ADR-2605091300) — top design
    metaphor; growth / prune / flower / fruit / graft semantics
  - Brand identity: amanomibashira (天御柱) + Gftd. JP-EN bilingual.
    Operating-entity boundary visible in surface copy where needed.
  - TLP CLEAR on public-facing artefacts; never AMBER/RED visible
  - Accessibility: WCAG 2.2 AA target; lang attribute + aria-label +
    contrast ratio
  - Yoro = flowering / fruiting surface (ADR-2605091900) — consumer touch
  - Design-system constraints: i18n via [data-lang] + _shared.css/_shared.js
    pattern (per malak.surveillance landing precedent)
  - Owned-channel-first; paid channel design routes to AI-CMO
"""

from __future__ import annotations

from ._pipeline import DecideRequest, register


def _hook(req: DecideRequest) -> tuple[str, list[str]]:
    system = (
        "You are AI-CDO at amanomibashira, in shadow mode. Human seat: "
        "k.takahashi@gftd.co.jp. You are 髙橋's chief-of-staff for "
        "design + creative direction. "
        "Operating entity = amanomibashira (天御柱) — sole principal. "
        "Vendor = Gftd Japan. Visual identity decisions belong to "
        "amanomibashira; never re-skin as Gftd Japan in public surfaces. "
        "Top metaphor (ADR-2605091300): Bonsai cultivar above myco-yeast "
        "substrate. Vocabulary: growth, prune, flower, fruit, graft, "
        "plasmid, sap-flow. Use this family for product naming, status "
        "language, motion design. Avoid hype family (rocket / lightning / "
        "10x). "
        "Bilingual default: JP + EN parallel using `[data-lang]` selector "
        "pattern (`_shared.css` + `_shared.js`) — per malak.surveillance "
        "landing precedent. localStorage + navigator.language detection. "
        "Accessibility target: WCAG 2.2 AA. `lang` attribute, `aria-label`, "
        "required-field indicator, 4.5:1 minimum contrast for body text. "
        "Public surfaces: TLP CLEAR only (never visible AMBER/RED). "
        "PII (顔, 連絡先, 給与) never on public AT records (ADR-0018). "
        "Channel split with AI-CMO: AI-CMO owns *what* posts go where + "
        "paid spend; AI-CDO owns *how it looks* + design system + asset "
        "quality. Paid creative review routes through AI-CMO. "
        "Class A = brand pivot / logo change / signature ramp — blocking "
        "escalate to 髙橋 + 河崎. Class B = customer-visible change "
        "outside design system — blocking confirm from 髙橋. Class C = "
        "internal asset triage / design-system audit. "
        "Be concise (<=8 lines). Tie any rec to a specific design-system "
        "rule or ADR. Recommend with reference visuals when relevant."
    )

    ctx: list[str] = []
    s = req.summary.lower()

    # Brand / identity / naming.
    if any(k in s for k in ("brand", "logo", "wordmark", "color", "palette",
                            "typography", "font", "識別")):
        ctx.append("lens.brand=cite design-system token; cross-product impact check; 髙橋 ratify if customer-visible")
    if any(k in s for k in ("naming", "product name", "feature name", "命名",
                            "rename")):
        ctx.append("lens.naming=use Bonsai cultivar vocabulary (growth/prune/flower/graft); avoid hype family")
    if any(k in s for k in ("amanomibashira", "天御柱", "operating entity", "vendor")):
        ctx.append("lens.entity-boundary=surface copy distinguishes amanomibashira (principal) vs Gftd Japan (vendor)")

    # UX / interaction.
    if any(k in s for k in ("ui", "ux", "user flow", "interaction", "wireframe",
                            "mockup", "prototype")):
        ctx.append("lens.ux=user-flow trace + failure-mode case; cite Yoro surface pattern if consumer-facing")
    if any(k in s for k in ("yoro", "consumer", "social feed", "feed ui",
                            "post composer")):
        ctx.append("lens.yoro=flower/fruit surface (ADR-2605091900); social = Bluesky AT lexicon-native")

    # Accessibility / bilingual.
    if any(k in s for k in ("a11y", "accessibility", "wcag", "contrast",
                            "screen reader", "keyboard nav", "aria")):
        ctx.append("lens.a11y=WCAG 2.2 AA; 4.5:1 contrast; aria-label + required indicator + keyboard reachable")
    if any(k in s for k in ("i18n", "bilingual", "translation", "jp-en",
                            "localization", "locale")):
        ctx.append("lens.i18n=[data-lang] selector pattern + _shared.js/_shared.css; localStorage persist; navigator.language default")

    # Asset / creative pipeline.
    if any(k in s for k in ("asset", "creative", "illustration", "render",
                            "comfyui", "image generation", "video")):
        ctx.append("lens.asset=cite source pipeline (comfyui worker / fleet router); license clean; AI-CMO co-review on paid surfaces")
    if any(k in s for k in ("photography", "stock", "shutterstock", "getty",
                            "model release")):
        ctx.append("lens.stock=verify license tier + model release; route license question to AI-CLO")

    # Channel split (with AI-CMO).
    if any(k in s for k in ("ad creative", "campaign creative", "paid creative",
                            "promoted", "boost")):
        ctx.append("lens.paid-creative=co-route to AI-CMO; financial-action gate at consent helper before spend")
    if any(k in s for k in ("owned channel", "site.gftd.ai", "blog", "newsletter",
                            "bluesky", "bsky")):
        ctx.append("lens.owned=Class C autonomous if within design system; AppBskyFeedPost single-write rule")

    # TLP / PII visibility on design artefacts.
    if any(k in s for k in ("public", "external visible", "landing", "marketing site",
                            "splash", "homepage")):
        ctx.append("lens.public=TLP CLEAR only; PII redaction; no AMBER/RED visible")

    # Design system + tokens.
    if any(k in s for k in ("design system", "token", "tailwind", "css var",
                            "_shared", "component library")):
        ctx.append("lens.design-system=token-first; deviation = 髙橋 ratify; surface to design-system update PR")

    # Motion / micro-interaction.
    if any(k in s for k in ("motion", "animation", "transition", "easing",
                            "spring", "scroll")):
        ctx.append("lens.motion=Bonsai cadence (slow, organic); prefers-reduced-motion respected; no infinite jitter")

    return system, ctx


register("cdo", _hook)
