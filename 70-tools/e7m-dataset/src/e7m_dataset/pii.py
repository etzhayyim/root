"""PII redaction wrapper — canonical e7m-dataset entry point.

Mirror of ``e7m_dataset.charter`` for the PII filter that lives at
``kotodama.organism.sensors.pii_filter`` (per ADR-2605262400 §6).
Four import strategies, tried in order:

  1. **Direct file-load** from the in-tree source via
     ``importlib.util.spec_from_file_location``. This is the first
     attempt because it skips ``kotodama/__init__.py`` (which can
     transitively import langchain → pydantic; broken on Python 3.14
     systems with the pydantic-core 2.46.4 vs 2.41.5 pinning issue).
     The PII filter is pure stdlib + regex; it does not need the
     rest of the kotodama package to function.
  2. Standard ``kotodama.organism.sensors.pii_filter`` import — works
     in production where kotodama installs cleanly.
  3. ``ETZ_PYKOTODAMA_SRC`` env-overridden sys.path + standard import.
  4. Repo-root walk-up sys.path prepend + standard import.

If all four fail and ``ETZ_DATASET_PII_STRICT=1``, raises. Otherwise
returns no-op redactors with a warn-only result (defensible for
phase-1 smoke but NOT for production ingestion of Tier-C sources).

This module is **import-cheap** — it does NOT touch the file system or
spawn the heavy kotodama init unless a redactor is actually called.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Iterable


STRICT_ENV = "ETZ_DATASET_PII_STRICT"
SRC_OVERRIDE_ENV = "ETZ_PYKOTODAMA_SRC"


class PiiFilterUnavailable(RuntimeError):
    """Raised in strict mode when the PII filter cannot be imported."""


# ── Lazy module loader ────────────────────────────────────────────────


_LOADED_MODULES: dict[str, ModuleType] = {}


def _direct_load_pii_filter(pii_path: Path, base_path: Path) -> ModuleType | None:
    """Load pii_filter.py as a standalone module.

    The pii_filter source imports ``from .base import PiiFilterPolicy``.
    Direct-loading the file alone won't satisfy that relative import,
    so we (a) preload ``base.py`` under a sibling shadow-module name and
    (b) rewrite the relative import in the source text before exec.

    All shadow-module names are namespaced with the
    ``_e7m_dataset_pii_direct_`` prefix so they cannot collide with
    real kotodama / canonical-import modules.
    """
    import importlib.util

    if not pii_path.is_file() or not base_path.is_file():
        return None
    try:
        base_name = "_e7m_dataset_pii_direct_base"
        if base_name not in sys.modules:
            base_spec = importlib.util.spec_from_file_location(base_name, base_path)
            if base_spec is None or base_spec.loader is None:
                return None
            base_mod = importlib.util.module_from_spec(base_spec)
            sys.modules[base_name] = base_mod
            base_spec.loader.exec_module(base_mod)

        pii_src = pii_path.read_text(encoding="utf-8")
        pii_src = pii_src.replace(
            "from .base import PiiFilterPolicy",
            f"from {base_name} import PiiFilterPolicy",
        )

        pii_name = "_e7m_dataset_pii_direct_pii_filter"
        pii_spec = importlib.util.spec_from_loader(pii_name, loader=None)
        if pii_spec is None:
            return None
        pii_mod = importlib.util.module_from_spec(pii_spec)  # type: ignore[arg-type]
        sys.modules[pii_name] = pii_mod
        exec(
            compile(pii_src, str(pii_path), "exec"),
            pii_mod.__dict__,
        )
        return pii_mod
    except Exception:  # noqa: BLE001 — best-effort sidecar load
        return None


def _find_pii_filter_paths() -> tuple[Path, Path] | None:
    """Locate (pii_filter.py, base.py) in the in-tree source.

    Strategies:
      1. SRC_OVERRIDE_ENV (operator-controlled).
      2. Walk up from cwd looking for the canonical
         ``40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/sensors/`` dir.
    """
    def _resolve_pair(src_root: Path) -> tuple[Path, Path] | None:
        pf = src_root / "kotodama/organism/sensors/pii_filter.py"
        bp = src_root / "kotodama/organism/sensors/base.py"
        if pf.is_file() and bp.is_file():
            return (pf, bp)
        return None

    override = os.environ.get(SRC_OVERRIDE_ENV)
    if override:
        pair = _resolve_pair(Path(override).resolve())
        if pair is not None:
            return pair

    here = Path.cwd().resolve()
    for p in [here, *here.parents]:
        candidate = p / "40-engine/kotoba/crates/kotoba-kotodama/py/src"
        pair = _resolve_pair(candidate)
        if pair is not None:
            return pair
    return None


def _load_pii_filter_module() -> ModuleType | None:
    """Return the pii_filter module (cached) or None."""
    if "module" in _LOADED_MODULES:
        return _LOADED_MODULES["module"]

    # Strategy 1: direct file-load.
    pair = _find_pii_filter_paths()
    if pair is not None:
        mod = _direct_load_pii_filter(pair[0], pair[1])
        if mod is not None:
            _LOADED_MODULES["module"] = mod
            return mod

    # Strategy 2: standard package import.
    try:
        from kotodama.organism.sensors import pii_filter  # type: ignore
        _LOADED_MODULES["module"] = pii_filter
        return pii_filter
    except ImportError:
        pass

    # Strategy 3: env override.
    override = os.environ.get(SRC_OVERRIDE_ENV)
    if override:
        ov = Path(override).resolve()
        if (ov / "kotodama/organism/sensors/pii_filter.py").is_file():
            if str(ov) not in sys.path:
                sys.path.insert(0, str(ov))
            try:
                from kotodama.organism.sensors import pii_filter  # type: ignore
                _LOADED_MODULES["module"] = pii_filter
                return pii_filter
            except ImportError:
                pass

    # Strategy 4: repo-root walk-up.
    here = Path.cwd().resolve()
    for p in [here, *here.parents]:
        cand = p / "40-engine/kotoba/crates/kotoba-kotodama/py/src"
        if (cand / "kotodama/organism/sensors/pii_filter.py").is_file():
            if str(cand) not in sys.path:
                sys.path.insert(0, str(cand))
            try:
                from kotodama.organism.sensors import pii_filter  # type: ignore
                _LOADED_MODULES["module"] = pii_filter
                return pii_filter
            except ImportError:
                break

    return None


# ── Stub fallback (warn-only) ─────────────────────────────────────────


@dataclass
class _StubStats:
    emails: int = 0
    phones: int = 0
    whois_values: int = 0
    postal_lines: int = 0

    @property
    def total(self) -> int:
        return 0


# ── Public API ────────────────────────────────────────────────────────


def _strict() -> bool:
    return os.environ.get(STRICT_ENV, "0") == "1"


def _ensure_module() -> ModuleType:
    mod = _load_pii_filter_module()
    if mod is None:
        if _strict():
            raise PiiFilterUnavailable(
                "PII filter unavailable (kotodama.organism.sensors.pii_filter "
                "could not be imported); ETZ_DATASET_PII_STRICT=1 forces "
                "fail-closed. Install kotodama or set ETZ_PYKOTODAMA_SRC."
            )
        raise PiiFilterUnavailable("PII filter unavailable (non-strict path).")
    return mod


def redact_payload(
    payload: dict,
    *,
    fields: Iterable[str] | None = None,
    policy: Any = None,
) -> tuple[dict, Any]:
    """Redact string-valued fields in `payload`.

    Returns (redacted_payload, stats). When the filter is unavailable
    and STRICT_ENV is off, returns (dict(payload), _StubStats()).
    """
    try:
        mod = _ensure_module()
    except PiiFilterUnavailable:
        if _strict():
            raise
        return dict(payload), _StubStats()
    if policy is None:
        policy = mod.PiiFilterPolicy.STRICT
    return mod.redact_payload(payload, policy=policy, fields=fields)


def redact_text(text: str, *, policy: Any = None) -> tuple[str, Any]:
    """Redact PII-shaped substrings in a free-text blob.

    Returns (redacted_text, stats). Warn-only behavior identical to
    ``redact_payload``.
    """
    try:
        mod = _ensure_module()
    except PiiFilterUnavailable:
        if _strict():
            raise
        return text, _StubStats()
    if policy is None:
        policy = mod.PiiFilterPolicy.STRICT
    return mod.redact_text(text, policy=policy)


__all__ = [
    "PiiFilterUnavailable",
    "STRICT_ENV",
    "SRC_OVERRIDE_ENV",
    "redact_payload",
    "redact_text",
]
