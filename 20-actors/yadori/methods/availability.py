"""yadori (宿り) domain-availability classifier — RDAP-based, stdlib only (ADR-2606038400).

RDAP (RFC 7482/9082) is the structured, rate-limit-friendly successor to WHOIS port-43 and the
IANA-mandated availability primitive. The public contract is simple:

    GET {rdap_base}/domain/{ascii_fqdn}
      200  -> the domain is REGISTERED
      404  -> the domain is AVAILABLE
      429  -> rate-limited (unknown)

This module does the offline-safe parts purely and deterministically: IDN/punycode normalization,
TLD extraction, RDAP-endpoint resolution from a :representative IANA bootstrap table, RDAP-URL
construction, status -> availability classification, and cross-TLD alternative generation. The live
HTTP fetch is OFF by default (G7 outward-gated); enabling it is a Council Lv6+ + operator action.

G1 read-only · G7 live fetch gated · G8 :representative bootstrap (bounded subset).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

# ── :representative IANA RDAP bootstrap (subset; G8). Source of truth at runtime is
#    https://data.iana.org/rdap/dns.json — fetched only when live mode is operator-enabled. ──
RDAP_BOOTSTRAP: dict[str, str] = {
    "com": "https://rdap.verisign.com/com/v1",
    "net": "https://rdap.verisign.com/net/v1",
    "org": "https://rdap.publicinterestregistry.org/rdap",
    "info": "https://rdap.identitydigital.services/rdap",
    "io": "https://rdap.identitydigital.services/rdap",
    "dev": "https://www.registry.google/rdap",
    "app": "https://www.registry.google/rdap",
    "ai": "https://rdap.nic.ai",
    "xyz": "https://rdap.centralnic.com/xyz",
    "jp": "https://rdap.jprs.jp/rdap",
}

# A status this module can report without ever touching the network.
STATUS_AVAILABLE = "available"
STATUS_REGISTERED = "registered"
STATUS_UNSUPPORTED_TLD = "unsupported-tld"
STATUS_INVALID = "invalid"
STATUS_RATE_LIMITED = "rate-limited"
STATUS_UNKNOWN = "unknown"


@dataclass
class AvailabilityResult:
    fqdn: str                       # as supplied
    ascii_fqdn: str                 # IDNA/punycode-normalized
    tld: str
    status: str
    rdap_url: str | None = None
    source: str = "none"            # "fixture" | "live" | "none"
    representative: bool = True
    note: str = ""


def normalize(fqdn: str) -> str:
    """Lowercase + strip + IDNA(punycode) encode. Raises ValueError on an invalid name."""
    name = (fqdn or "").strip().rstrip(".").lower()
    if not name or "." not in name:
        raise ValueError(f"invalid domain: {fqdn!r}")
    labels = name.split(".")
    out = []
    for label in labels:
        if not label:
            raise ValueError(f"invalid domain (empty label): {fqdn!r}")
        try:
            # ASCII labels pass through; unicode labels become xn--... (RFC 5890).
            out.append(label.encode("idna").decode("ascii"))
        except UnicodeError as exc:
            raise ValueError(f"invalid domain label {label!r}: {exc}") from exc
    return ".".join(out)


def tld_of(ascii_fqdn: str) -> str:
    return ascii_fqdn.rsplit(".", 1)[-1]


def rdap_url(ascii_fqdn: str, bootstrap: dict[str, str] | None = None) -> str | None:
    """Construct the RDAP query URL, or None if the TLD is not in the bootstrap table."""
    table = bootstrap if bootstrap is not None else RDAP_BOOTSTRAP
    base = table.get(tld_of(ascii_fqdn))
    if not base:
        return None
    return f"{base.rstrip('/')}/domain/{ascii_fqdn}"


def classify_status(http_status: int) -> str:
    """Map an RDAP HTTP status to an availability verdict."""
    if http_status == 404:
        return STATUS_AVAILABLE
    if http_status == 200:
        return STATUS_REGISTERED
    if http_status == 429:
        return STATUS_RATE_LIMITED
    return STATUS_UNKNOWN


def check_availability(
    fqdn: str,
    *,
    fixtures: dict[str, int] | None = None,
    bootstrap: dict[str, str] | None = None,
    allow_live: bool = False,
) -> AvailabilityResult:
    """Classify a domain's availability.

    Offline-default: `fixtures` maps ascii_fqdn -> RDAP HTTP status. Live RDAP fetch only runs when
    `allow_live=True` (G7 outward-gated; operator + Council). With neither a fixture nor live mode,
    the result is STATUS_UNKNOWN with source "none".
    """
    try:
        ascii_fqdn = normalize(fqdn)
    except ValueError as exc:
        return AvailabilityResult(fqdn, fqdn, "", STATUS_INVALID, note=str(exc))

    tld = tld_of(ascii_fqdn)
    url = rdap_url(ascii_fqdn, bootstrap)
    if url is None:
        return AvailabilityResult(
            fqdn, ascii_fqdn, tld, STATUS_UNSUPPORTED_TLD,
            note=f"TLD '.{tld}' not in :representative RDAP bootstrap (G8)",
        )

    fixtures = fixtures or {}
    if ascii_fqdn in fixtures:
        return AvailabilityResult(
            fqdn, ascii_fqdn, tld, classify_status(fixtures[ascii_fqdn]),
            rdap_url=url, source="fixture",
        )

    if allow_live:
        status = _live_rdap_status(url)
        return AvailabilityResult(
            fqdn, ascii_fqdn, tld, classify_status(status),
            rdap_url=url, source="live", representative=False,
        )

    return AvailabilityResult(
        fqdn, ascii_fqdn, tld, STATUS_UNKNOWN, rdap_url=url, source="none",
        note="offline: no fixture and live RDAP is G7-gated (allow_live=False)",
    )


# A descriptive User-Agent is required: several RDAP servers (e.g. PIR/.org) return 403 to bare
# requests. Identifying the client is also good-citizen practice for a read-only lookup (G1).
RDAP_USER_AGENT = "yadori-rdap/0.1 (+https://etzhayyim.com/actor/yadori)"


def _live_rdap_status(url: str) -> int:
    """Live RDAP GET — only reached when allow_live=True (G7)."""
    import urllib.error
    import urllib.request

    req = urllib.request.Request(
        url,
        method="GET",
        headers={"Accept": "application/rdap+json", "User-Agent": RDAP_USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310 (gated path)
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code


def suggest_alternatives(
    sld: str,
    *,
    tlds: tuple[str, ...] = ("com", "org", "dev", "io", "app"),
    taken: set[str] | None = None,
) -> list[str]:
    """Generate cross-TLD candidate FQDNs for a second-level label, excluding known-taken names.

    Pure + deterministic (no network, no LLM — naming *brief* expansion is the name_suggest cell's
    Murakumo job; this is the mechanical TLD fan-out used when a preferred name is taken).
    """
    taken = taken or set()
    label = normalize(f"{sld}.com").split(".")[0]  # normalize the label via a throwaway fqdn
    out = []
    for tld in tlds:
        cand = f"{label}.{tld}"
        if cand not in taken:
            out.append(cand)
    return out


def _main(argv: list[str]) -> int:
    names = argv or ["example.com", "etzhayyim.org", "totally-free-xyz-name.dev"]
    # A tiny built-in fixture so the demo prints something meaningful offline.
    demo_fixtures = {"example.com": 200, "etzhayyim.org": 200, "totally-free-xyz-name.dev": 404}
    for n in names:
        r = check_availability(n, fixtures=demo_fixtures)
        tag = "[representative]" if r.representative else "[live]"
        extra = f"  ({r.note})" if r.note else ""
        print(f"{r.fqdn:35s} {r.status:16s} {tag} via {r.source}{extra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
