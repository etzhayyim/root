"""Tests for the yadori RDAP availability classifier (ADR-2606038400)."""

import pytest

from availability import (
    STATUS_AVAILABLE,
    STATUS_INVALID,
    STATUS_RATE_LIMITED,
    STATUS_REGISTERED,
    STATUS_UNKNOWN,
    STATUS_UNSUPPORTED_TLD,
    check_availability,
    classify_status,
    normalize,
    rdap_url,
    suggest_alternatives,
    tld_of,
)


def test_classify_status_mapping():
    assert classify_status(404) == STATUS_AVAILABLE
    assert classify_status(200) == STATUS_REGISTERED
    assert classify_status(429) == STATUS_RATE_LIMITED
    assert classify_status(500) == STATUS_UNKNOWN


def test_available_from_fixture():
    r = check_availability("free-name.dev", fixtures={"free-name.dev": 404})
    assert r.status == STATUS_AVAILABLE
    assert r.source == "fixture"
    assert r.rdap_url == "https://www.registry.google/rdap/domain/free-name.dev"


def test_registered_from_fixture():
    r = check_availability("example.com", fixtures={"example.com": 200})
    assert r.status == STATUS_REGISTERED


def test_unsupported_tld_degrades_honestly():
    r = check_availability("name.quux", fixtures={})
    assert r.status == STATUS_UNSUPPORTED_TLD
    assert "G8" in r.note


def test_invalid_domain_rejected():
    assert check_availability("nodot", fixtures={}).status == STATUS_INVALID
    assert check_availability("", fixtures={}).status == STATUS_INVALID
    assert check_availability("a..b.com", fixtures={}).status == STATUS_INVALID


def test_idn_punycode_normalization():
    # café.com -> xn--caf-dma.com ; the classifier keys on the ascii form.
    assert normalize("café.com") == "xn--caf-dma.com"
    r = check_availability("café.com", fixtures={"xn--caf-dma.com": 404})
    assert r.ascii_fqdn == "xn--caf-dma.com"
    assert r.status == STATUS_AVAILABLE


def test_normalize_strips_trailing_dot_and_case():
    assert normalize("Example.COM.") == "example.com"


def test_tld_and_rdap_url():
    assert tld_of("foo.bar.io") == "io"
    assert rdap_url("foo.io") == "https://rdap.identitydigital.services/rdap/domain/foo.io"
    assert rdap_url("foo.unknowntld") is None


def test_offline_without_fixture_is_unknown_not_a_lie():
    # G1/G7: with no fixture and live disabled, we must NOT claim available.
    r = check_availability("mystery.com", fixtures={})
    assert r.status == STATUS_UNKNOWN
    assert r.source == "none"
    assert r.rdap_url is not None  # url is still constructible


def test_live_is_gated_by_default():
    # allow_live defaults False; a supported-TLD name with no fixture stays UNKNOWN (no network).
    r = check_availability("mystery.org")
    assert r.status == STATUS_UNKNOWN


def test_suggest_alternatives_fans_out_and_excludes_taken():
    alts = suggest_alternatives("etzhayyim", tlds=("com", "org", "dev"), taken={"etzhayyim.com"})
    assert "etzhayyim.com" not in alts
    assert "etzhayyim.org" in alts
    assert "etzhayyim.dev" in alts


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
