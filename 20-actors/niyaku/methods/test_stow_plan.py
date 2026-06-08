"""Tests for stow_plan — stowage slotting + discharge sequencing."""

import pytest

from stow_plan import (
    Container,
    Slot,
    StowError,
    build_stow_plan,
    discharge_sequence,
    validate_no_rehandle,
)


def _rot_index(rotation):
    return {p: i for i, p in enumerate(rotation)}


def test_simple_plan_places_all():
    rotation = ["SHA", "SIN", "ROT"]
    # weight must agree with discharge order for a single stack to be feasible:
    # earliest-discharge (SHA) sits on top, so it must be the lightest.
    boxes = [
        Container("A", 22.0, "ROT"),  # last off → heaviest → bottom
        Container("B", 18.0, "SIN"),
        Container("C", 14.0, "SHA"),  # first off → lightest → top
    ]
    plan = build_stow_plan(boxes, rotation, bays=1, rows=1, tiers=3)
    assert set(plan.assignments) == {"A", "B", "C"}
    # later-discharge ROT (A) must be at the bottom (tier 0)
    assert plan.slot_of("A").tier < plan.slot_of("B").tier
    assert plan.slot_of("B").tier < plan.slot_of("C").tier
    box_port = {b.box_id: b.discharge_port for b in boxes}
    assert validate_no_rehandle(plan, _rot_index(rotation), box_port)


def test_weight_on_top_not_violated():
    rotation = ["P1"]
    boxes = [
        Container("light", 5.0, "P1"),
        Container("heavy", 25.0, "P1"),
    ]
    plan = build_stow_plan(boxes, rotation, bays=1, rows=1, tiers=2)
    # heavy must end up below light (lower tier)
    assert plan.slot_of("heavy").tier < plan.slot_of("light").tier


def test_capacity_exceeded_raises():
    rotation = ["P1"]
    boxes = [Container(f"b{i}", 10.0, "P1") for i in range(5)]
    with pytest.raises(StowError):
        build_stow_plan(boxes, rotation, bays=1, rows=1, tiers=4)


def test_reefer_only_in_reefer_rows():
    rotation = ["P1"]
    boxes = [Container("r", 10.0, "P1", reefer=True)]
    plan = build_stow_plan(boxes, rotation, bays=1, rows=2, tiers=1, reefer_rows=[1])
    assert plan.slot_of("r").row == 1


def test_reefer_infeasible_when_no_reefer_row():
    rotation = ["P1"]
    boxes = [Container("r", 10.0, "P1", reefer=True)]
    with pytest.raises(StowError):
        build_stow_plan(boxes, rotation, bays=1, rows=1, tiers=1, reefer_rows=[])


def test_hazmat_segregation_separates_classes():
    rotation = ["P1"]
    boxes = [
        Container("flam", 10.0, "P1", hazmat="3"),
        Container("oxid", 10.0, "P1", hazmat="5.1"),
    ]
    # two classes cannot share a column; need ≥2 columns
    plan = build_stow_plan(boxes, rotation, bays=2, rows=1, tiers=2)
    assert (plan.slot_of("flam").bay, plan.slot_of("flam").row) != (
        plan.slot_of("oxid").bay, plan.slot_of("oxid").row
    )
    # only one column ⇒ infeasible
    with pytest.raises(StowError):
        build_stow_plan(boxes, rotation, bays=1, rows=1, tiers=2)


def test_unknown_port_raises():
    with pytest.raises(StowError):
        build_stow_plan([Container("x", 1.0, "ZZZ")], ["P1"], 1, 1, 1)


def test_empty_rotation_raises():
    with pytest.raises(StowError):
        build_stow_plan([], [], 1, 1, 1)


def test_discharge_sequence_top_first():
    rotation = ["P1"]
    boxes = [Container(f"b{i}", 10.0 - i, "P1") for i in range(3)]
    plan = build_stow_plan(boxes, rotation, bays=1, rows=1, tiers=3)
    seq = discharge_sequence(plan, "P1")
    # top tier discharged first
    tiers = [plan.slot_of(bid).tier for bid in seq]
    assert tiers == sorted(tiers, reverse=True)


def test_weight_on_top_forces_new_column():
    """A heavy early-discharge box cannot sit on a light late-discharge box, so
    it is pushed to a fresh column (exercises the weight-on-top skip)."""
    rotation = ["P0", "P1"]
    boxes = [
        Container("late_light", 10.0, "P1"),  # placed bottom of col0 first
        Container("early_heavy", 20.0, "P0"),  # heavier → can't top col0 → col1
    ]
    plan = build_stow_plan(boxes, rotation, bays=2, rows=1, tiers=2)
    assert plan.slot_of("late_light").bay != plan.slot_of("early_heavy").bay


def test_validate_no_rehandle_detects_violation():
    """A hand-built plan with a later-discharge box stacked above an earlier one
    is flagged (returns False)."""
    from stow_plan import StowagePlan
    plan = StowagePlan()
    plan.assignments["below_early"] = Slot(0, 0, 0)  # P0 (early) at bottom — bad
    plan.assignments["above_late"] = Slot(0, 0, 1)   # P1 (late) on top — buries early
    rot_index = {"P0": 0, "P1": 1}
    box_port = {"below_early": "P0", "above_late": "P1"}
    assert validate_no_rehandle(plan, rot_index, box_port) is False


def test_slot_key():
    assert Slot(1, 2, 3).key() == (1, 2, 3)
