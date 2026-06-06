"""test_registry.py — 系図 (keizu) source-registry access + runtime deny guard. ADR-2606066000."""
from __future__ import annotations

from _t import expect_raises, run
from registry import (assert_source_allowed, get_source, source_ids,
                      sourcing_for)


def test_source_ids_nonempty_and_known():
    ids = source_ids()
    assert "jpn-procurement-pportal" in ids
    assert "usa-fec" in ids


def test_get_source_fields():
    s = get_source("eu-ted")
    assert s["jurisdiction"] == "eu" and s["sourceKind"] == "procurement"


def test_get_source_unknown_raises():
    expect_raises(lambda: get_source("no-such"), contains="no such source")


def test_sourcing_for_seed_is_representative():
    # every seed source is unverified-seed → :representative (G11, never auto-authoritative)
    for sid in source_ids():
        assert sourcing_for(sid) == ":representative", sid


def test_sourcing_for_unknown_is_representative():
    assert sourcing_for("ghost") == ":representative"


def test_assert_source_allowed_passes_public():
    assert_source_allowed("https://www.usaspending.gov/", "https://www.fec.gov/")


def test_assert_source_allowed_refuses_terminal():
    expect_raises(lambda: assert_source_allowed("https://bloomberg.com/gov/x"),
                  contains="prohibited")


if __name__ == "__main__":
    run("registry", [(k, v) for k, v in sorted(globals().items())
                     if k.startswith("test_") and callable(v)])
