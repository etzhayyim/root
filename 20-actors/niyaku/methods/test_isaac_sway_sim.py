"""Tests for isaac_sway_sim — anti-sway transfer through the clean-room
``isaacsim.core.api`` surface.

Skips gracefully when the kotoba submodule (kotodama.nv_compat) is not checked
out / importable, so the niyaku suite stays green in a bare worktree. Set
``NIYAKU_KOTODAMA_SRC`` to the kotoba ``py/src`` to force-enable.
"""

import math

import pytest

import isaac_sway_sim as sim

isaac = pytest.mark.skipif(
    not sim.isaac_available(),
    reason="kotodama.nv_compat.isaacsim not importable (kotoba submodule absent)",
)


def test_hang_constant_is_pi():
    assert sim.HANG == pytest.approx(math.pi)


def test_anti_sway_force_signs():
    """All four feedback terms reduce sway / drive toward target."""
    c = sim.StsAntiSway(kp=1, kd=1, k_phi=1, k_phid=1, max_force=1e9)
    # cart left of target, at rest, no sway → push +x
    assert c.force([0.0, 0.0, math.pi, 0.0], x_target=1.0) > 0
    # positive sway (theta>π) at target → force goes negative to bleed it
    assert c.force([1.0, 0.0, math.pi + 0.1, 0.0], x_target=1.0) < 0
    # force saturates
    assert abs(c.force([1e6, 0, math.pi, 0], 0.0)) <= 1e9


@isaac
def test_isaac_surface_drives_cartpole_crane():
    """Mirror of isaac_world_cartpole_lifecycle: build via the public API,
    step, and read back joint positions — the trolley moves."""
    api = sim.load_isaac()
    assert {"World", "Articulation", "Cartpole"} <= set(api)
    r = sim.run_sts_transfer(x_target=1.0, anti_sway=True, steps=4000)
    assert r.reached
    assert abs(r.final_x - 1.0) <= 0.10


@isaac
def test_anti_sway_quietens_load_vs_naive():
    """The whole point: closed-loop anti-sway lands the box far quieter than a
    naive position push, which rings the load wildly."""
    good = sim.run_sts_transfer(x_target=1.5, anti_sway=True, steps=4000)
    naive = sim.run_sts_transfer(x_target=1.5, anti_sway=False, steps=4000)
    assert good.residual_sway_rad < 0.05
    assert good.residual_sway_rad < naive.residual_sway_rad
    assert good.peak_sway_rad < naive.peak_sway_rad
    assert good.reached


def test_resolve_py_src_env_override(monkeypatch, tmp_path):
    """_resolve_py_src honours NIYAKU_KOTODAMA_SRC when it points at a valid tree."""
    good = tmp_path / "src"
    (good / "kotodama" / "nv_compat").mkdir(parents=True)
    monkeypatch.setenv("NIYAKU_KOTODAMA_SRC", str(good))
    assert sim._resolve_py_src() == str(good.resolve())


def test_resolve_py_src_walks_when_env_invalid(monkeypatch):
    """A bogus env value is ignored; resolution falls through to the dir walk."""
    monkeypatch.setenv("NIYAKU_KOTODAMA_SRC", "/nonexistent/path/xyz")
    out = sim._resolve_py_src()
    assert out.endswith("py/src") or "kotoba" in out  # a path string, not a crash


def test_isaac_available_returns_bool():
    assert isinstance(sim.isaac_available(), bool)


@isaac
def test_boom_luff_small_step_converges():
    """Double-pendulum boom crane: a small luff step lands the load quiet."""
    r = sim.run_boom_luff(0.15, steps=4000)
    assert r.reached
    assert abs(r.final_boom_rad - 0.15) <= 0.05
    assert r.residual_load_rad < 0.05


@isaac
def test_boom_luff_large_step_reports_honestly():
    """Outside the small-angle envelope the underactuated PD does NOT pretend to
    converge — reached is False rather than a faked success."""
    r = sim.run_boom_luff(1.2, steps=1500)
    assert r.reached is False


@isaac
def test_report_to_datoms_shape():
    r = sim.run_sts_transfer(x_target=1.0, anti_sway=True, steps=4000)
    datoms = sim.report_to_datoms(r, "t1")
    assert all(len(d) == 3 for d in datoms)
    attrs = {a for _, a, _ in datoms}
    assert ":niyaku.sim/residual-sway-rad" in attrs
    assert all(e == "niyaku/sim/t1" for e, _, _ in datoms)
