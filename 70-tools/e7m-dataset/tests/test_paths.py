"""paths.resolve — env / TOML / error precedence."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from e7m_dataset import paths as paths_mod


def _isolate_env(monkeypatch):
    for k in ("ETZ_DATASET_ROOT", "ETZ_KUBO_API", "ETZ_NODE_DID"):
        monkeypatch.delenv(k, raising=False)


def test_env_wins(tmp_path, monkeypatch):
    _isolate_env(monkeypatch)
    monkeypatch.setenv("ETZ_DATASET_ROOT", str(tmp_path / "root"))
    monkeypatch.setenv("ETZ_KUBO_API", "http://kubo:9999")
    monkeypatch.setenv("ETZ_NODE_DID", "did:web:env.example")

    monkeypatch.setattr(paths_mod, "CONFIG_PATH", tmp_path / "missing.toml")
    p = paths_mod.resolve()
    assert p.root == (tmp_path / "root").resolve()
    assert p.ipfs_data == (tmp_path / "root" / "ipfs-data").resolve()
    assert p.kubo_api == "http://kubo:9999"
    assert p.node_did == "did:web:env.example"


def test_toml_fallback(tmp_path, monkeypatch):
    _isolate_env(monkeypatch)
    cfg = tmp_path / "local-paths.toml"
    cfg.write_text(textwrap.dedent(
        """\
        [machine.somehost]
        dataset_root = "%s"
        kubo_api     = "http://kubo:5001"
        node_did     = "did:web:toml.example"
        """ % (tmp_path / "via-toml")
    ).strip() + "\n", encoding="utf-8")
    monkeypatch.setattr(paths_mod, "CONFIG_PATH", cfg)
    # Force hostname match by patching gethostname.
    monkeypatch.setattr(paths_mod.socket, "gethostname", lambda: "somehost.local")

    p = paths_mod.resolve()
    assert p.root == (tmp_path / "via-toml").resolve()
    assert p.kubo_api == "http://kubo:5001"
    assert p.node_did == "did:web:toml.example"


def test_single_machine_fallback(tmp_path, monkeypatch):
    """When hostname doesn't match but exactly one [machine.*] exists, use it."""
    _isolate_env(monkeypatch)
    cfg = tmp_path / "local-paths.toml"
    cfg.write_text(textwrap.dedent(
        """\
        [machine.only]
        dataset_root = "%s"
        kubo_api     = "http://kubo:5001"
        node_did     = "did:web:only.example"
        """ % (tmp_path / "via-toml")
    ).strip() + "\n", encoding="utf-8")
    monkeypatch.setattr(paths_mod, "CONFIG_PATH", cfg)
    monkeypatch.setattr(paths_mod.socket, "gethostname", lambda: "different-host")

    p = paths_mod.resolve()
    assert p.root == (tmp_path / "via-toml").resolve()
    assert p.node_did == "did:web:only.example"


def test_no_config_raises(tmp_path, monkeypatch):
    _isolate_env(monkeypatch)
    monkeypatch.setattr(paths_mod, "CONFIG_PATH", tmp_path / "absent.toml")
    with pytest.raises(SystemExit):
        paths_mod.resolve()


def test_subdataset_annex_dir(tmp_path, monkeypatch):
    _isolate_env(monkeypatch)
    monkeypatch.setenv("ETZ_DATASET_ROOT", str(tmp_path))
    monkeypatch.setattr(paths_mod, "CONFIG_PATH", tmp_path / "absent.toml")
    p = paths_mod.resolve()
    assert p.subdataset_annex_dir("HF/owner-repo") == (tmp_path / "annex-store" / "HF" / "owner-repo").resolve()
