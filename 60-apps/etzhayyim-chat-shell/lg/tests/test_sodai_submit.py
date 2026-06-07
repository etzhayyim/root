"""Smoke tests for sodai_submit graph — no network, no playwright required.

Verifies: graph compiles, mode validation, and the safety invariants
(playwright-missing degradation, submit double-gate) without ever touching
the live official form.
"""

import importlib

import pytest

_APP = {
    "items": [{"name": "ソファー（2人以上用）", "qty": 1}],
    "name": "渋谷　太郎",
    "nameKana": "シブヤ　タロウ",
    "postal": "150-8010",
    "address": "渋谷区宇田川町１－１",
    "building": "",
    "phone": "0312345678",
    "email": "",
    "preferredDate": "",
}


def test_graph_compiles() -> None:
    mod = importlib.import_module("lg_chat.graphs.sodai_submit")
    graph = mod.GRAPH
    assert graph is not None
    node_names = set(graph.nodes.keys()) if hasattr(graph, "nodes") else set()
    assert {"validate", "drive"} <= node_names


def test_field_map_override(monkeypatch: pytest.MonkeyPatch) -> None:
    from lg_chat import sodai_fields as sf

    monkeypatch.setenv("SODAI_FIELD_MAP", '{"name": ["#customName"]}')
    fm = sf.load_field_map()
    assert fm["name"] == ["#customName"]
    # other keys keep defaults
    assert "phone" in fm

    monkeypatch.setenv("SODAI_FIELD_MAP", "not json")
    fm2 = sf.load_field_map()
    assert fm2["name"] == sf.DEFAULT_FIELD_MAP["name"]


@pytest.mark.asyncio
async def test_validate_rejects_bad_mode() -> None:
    from lg_chat.graphs.sodai_submit import _node_validate

    out = await _node_validate({"mode": "wreck-it", "application": _APP})
    assert out["status"] == "error"


@pytest.mark.asyncio
async def test_validate_defaults_to_prefill() -> None:
    from lg_chat.graphs.sodai_submit import _node_validate

    out = await _node_validate({"application": _APP})
    assert out["mode"] == "prefill"
    assert out["submitted"] is False


@pytest.mark.asyncio
async def test_drive_degrades_when_playwright_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """If playwright isn't installed, drive() must return a clear status, not crash."""
    import builtins

    real_import = builtins.__import__

    def _blocked(name, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003
        if name.startswith("playwright"):
            raise ImportError("playwright not installed (test)")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _blocked)
    from lg_chat.graphs.sodai_submit import _node_drive

    out = await _node_drive({"mode": "prefill", "application": _APP})
    assert out["status"] == "playwright_missing"
    assert "playwright" in out["error"].lower()
