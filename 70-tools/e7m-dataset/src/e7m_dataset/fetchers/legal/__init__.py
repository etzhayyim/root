"""Global legal-corpus fetchers — the ``law/`` bucket family (ADR-2605262800).

W1 ships the 5 anchor sources (all Tier-A: public-domain or open-government
license, so no ``_acceptance`` Tier-C gate applies):

  * ``jp_egov``        — e-Gov 法令 API (Japan statutes; CC-BY 4.0)
  * ``uk_legislation`` — legislation.gov.uk (UK statutes; OGL v3.0)
  * ``us_usc``         — US Code / OLRC USLM XML (US statutes; public domain)
  * ``us_cfr``         — eCFR / GPO (US regulations; public domain)
  * ``eu_eurlex``      — EUR-Lex CELLAR (EU treaties/regs/directives; free reuse w/ citation)

Each fetcher writes a normalized statute NDJSON into the staging dir and returns
a ``FetchResult``; the operator then runs ``datalad save`` + ``e7m-dataset
publish-ipfs`` to land the bytes in git-annex + IPFS + PDS (the
content-addressed ``law/<bucket>/<jurisdiction>/<rev>/`` substrate). The
normalized rows are consumed by ``kotodama.organism.sensors.legal.*`` sensors.

Invariant boundaries (inherited from ADR-2605262400 §7 + Charter Rider §2):

  * **Passive-only** — operator-triggered, NOT organism-tick; network mode
    requires explicit bounds (no implicit full-archive scrape).
  * **No proprietary commentary feeds** — Westlaw / LexisNexis / Bloomberg Law
    are CONSTITUTIONALLY PROHIBITED (Charter Rider §2(e) anti-gatekeeping +
    §2(c) covert-ops vendor concern). These fetchers only touch primary
    public-law sources.
"""

from __future__ import annotations

__all__: list[str] = []
