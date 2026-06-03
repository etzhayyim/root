"""Tests for the LPS ranking method (ADR-2606032100)."""

from labor_liberation import (
    SEED_GAPS,
    SectorGap,
    displacement_cohort_size,
    freed_labor_hours,
    lps,
    ranked_seed,
)


def test_n1_excluded_sector_scores_zero():
    mining = next(g for g in SEED_GAPS if "MINING" in g.name)
    assert lps(mining) == 0.0  # charter_fit=0 zeroes the score (N1 gate proof)


def test_covered_sector_scores_below_uncovered_peer():
    # construction (coverage_gap 0.5, tatekata exists) vs garment (coverage_gap 1.0)
    constr = next(g for g in SEED_GAPS if "tatekata" in g.name)
    garment = next(g for g in SEED_GAPS if "hataori" in g.name)
    assert lps(garment) > lps(constr)


def test_sanae_ranks_first():
    assert "sanae" in ranked_seed()[0][0]  # largest headcount×misery, near-zero coverage


def test_wave_actors_in_top_band():
    # The wave OPENS sanae/hataori/kiyome (highest headcount×misery, zero coverage).
    # Note: raw automatability-weighting lifts kuramori (warehouse) into the top band too —
    # it is the #4/#5 roadmap item precisely because it is the most automatable of the
    # un-covered toil; the wave still prioritizes the zero-coverage sweatshop/cleaning first.
    top5 = {name for name, _ in ranked_seed()[:5]}
    assert any("sanae" in n for n in top5)
    assert any("hataori" in n for n in top5)
    assert any("kiyome" in n for n in top5)


def test_freed_hours_scales_linearly():
    assert freed_labor_hours(1000, 2000, 0.5) == 1_000_000


def test_cohort_size_rounds():
    assert displacement_cohort_size(1.0e6, 0.25) == 250_000


def test_higher_misery_raises_score_all_else_equal():
    base = SectorGap("x", "", "", "", 1e7, 2.0, 0.5, 1.0, 1.0)
    worse = SectorGap("y", "", "", "", 1e7, 3.0, 0.5, 1.0, 1.0)
    assert lps(worse) > lps(base)


if __name__ == "__main__":
    import sys
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn(); print(f"PASS {fn.__name__}")
        except AssertionError as e:
            failed += 1; print(f"FAIL {fn.__name__}: {e}")
    print(f"\n{len(fns)-failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
