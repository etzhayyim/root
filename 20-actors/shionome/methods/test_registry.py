"""test_registry.py — 潮目 (shionome) registry access + sourcing honesty. ADR-2606072200."""
from __future__ import annotations

import registry
from _t import expect_raises, run


def test_source_ids_nonempty():
    assert len(registry.source_ids()) >= 10


def test_get_source_known():
    s = registry.get_source("us-fred")
    assert s["jurisdiction"] == "us"


def test_get_source_unknown_raises():
    expect_raises(lambda: registry.get_source("nope"), contains="no such source")


def test_sourcing_unverified_is_representative():
    assert registry.sourcing_for("us-fred") == ":representative"


def test_sourcing_unknown_is_representative():
    assert registry.sourcing_for("nope") == ":representative"


def test_assert_source_allowed_blocks_terminal():
    expect_raises(lambda: registry.assert_source_allowed("via refinitiv eikon"), contains="Rider")


def test_assert_source_allowed_passes_public():
    registry.assert_source_allowed("https://fred.stlouisfed.org/")


if __name__ == "__main__":
    run("registry", [(n, f) for n, f in sorted(globals().items())
                     if n.startswith("test_") and callable(f)])
