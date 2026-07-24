#!/usr/bin/env python3
"""Actor-registry parity drift-lock — ADR-2606052100 (ake) follow-on.

ake's genesis-revision bridge (orgs/etzhayyim/com-etzhayyim-ake/methods/ingest.py) surfaced that an actor can be
registered in the apex Worker's compiled `INFRA_ACTORS` (50-infra/etzhayyim-did-web/src/registry/
infra-actors.ts) WITHOUT a record in the kotoba SSoT `actor-profile-seed.kotoba.edn` (or vice
versa). Either half of that drift means an actor is not uniformly resolvable / searchable: the
Worker serves a compiled fallback for one set, the profile publisher materializes did.json +
getProfile from the other.

This audit locks the two registries against NEW drift. The CURRENTLY-KNOWN gaps are recorded as an
explicit baseline (with the goal of driving it to empty); the hard assertion is that no actor
drifts BEYOND that baseline — so any newly-added actor must be registered in BOTH places. When a
known gap is fixed, drift simply shrinks (still within baseline) — no edit to this file required.

Standalone-runnable AND pytest-compatible:
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_actor_registry_parity.py
    python3 test_actor_registry_parity.py
"""
from __future__ import annotations

import pathlib
import re

_REPO = pathlib.Path(__file__).resolve().parents[3]
_INFRA = _REPO / "50-infra" / "etzhayyim-did-web" / "src" / "registry" / "infra-actors.ts"
_SEED = _REPO / "00-contracts" / "schemas" / "actor-profile-seed.kotoba.edn"

# ── baseline drift: EMPTY (driven to zero 2026-06-05) ────────────────────────────
# The original 2026-06-05 baseline {kanjo, todoke, watari} (infra-only) + {nusa, yadori}
# (profile-only) was CLOSED in the same commit that empties this set: kanjo/todoke/watari gained
# actor-profile-seed records, nusa/yadori gained INFRA_ACTORS entries. Parity is now strict —
# every actor MUST be registered in BOTH the apex Worker's INFRA_ACTORS and the kotoba SSoT
# actor-profile-seed, or these tests fail. Do not re-populate these sets to paper over new drift;
# register the actor in both places instead.
KNOWN_INFRA_ONLY: set[str] = set()
KNOWN_PROFILE_ONLY: set[str] = set()


def infra_handles() -> set[str]:
    body = _INFRA.read_text(encoding="utf-8")
    body = body.split("export const INFRA_ACTORS", 1)[1].split("} as const;", 1)[0]
    # top-level entries at 2-space indent: `  handle: {` or `  "dataset-pinner": {`
    return set(re.findall(r'(?m)^  "?([a-zA-Z][\w-]*)"?:\s*\{', body))


def profile_handles() -> set[str]:
    return set(re.findall(r':actor/handle\s+"([^"]+)"', _SEED.read_text(encoding="utf-8")))


def test_both_registries_are_non_trivial():
    assert len(infra_handles()) >= 20
    assert len(profile_handles()) >= 20


def test_no_new_infra_only_drift():
    infra_only = infra_handles() - profile_handles()
    new = infra_only - KNOWN_INFRA_ONLY
    assert not new, (
        f"actors registered in INFRA_ACTORS but missing an actor-profile-seed record: {sorted(new)}. "
        "Add a {:actor/handle …} record to 00-contracts/schemas/actor-profile-seed.kotoba.edn."
    )


def test_no_new_profile_only_drift():
    profile_only = profile_handles() - infra_handles()
    new = profile_only - KNOWN_PROFILE_ONLY
    assert not new, (
        f"actors with an actor-profile-seed record but absent from INFRA_ACTORS: {sorted(new)}. "
        "Add an entry to 50-infra/etzhayyim-did-web/src/registry/infra-actors.ts."
    )


def test_baseline_does_not_grow_overall():
    # the total documented drift must not exceed the recorded baseline size
    infra, prof = infra_handles(), profile_handles()
    drift = (infra - prof) | (prof - infra)
    assert len(drift) <= len(KNOWN_INFRA_ONLY) + len(KNOWN_PROFILE_ONLY), (
        f"registry drift grew beyond baseline: {sorted(drift)}"
    )


def test_ake_is_registered_in_both():
    # ake (this ADR) must be parity-clean — the actor that motivated the lock leads by example
    assert "ake" in infra_handles()
    assert "ake" in profile_handles()


# ── schema-reference integrity: no registry may point at a non-existent ontology ──
def _path_like(ref: str) -> str | None:
    """The leading token of `ref` if it looks like a real file path (`…/x.edn`), else None.

    Skips prose notes (e.g. todoke/tsuzuri use a descriptive primary-schema string), so only
    genuine path references are dereferenced.
    """
    head = ref.strip().split()[0] if ref.strip() else ""
    return head if (head.endswith(".edn") and "/" in head) else None


def test_profile_seed_schema_refs_resolve():
    refs = re.findall(r':actor/primary-schema\s+"([^"]+)"', _SEED.read_text(encoding="utf-8"))
    missing = [p for r in refs if (p := _path_like(r)) and not (_REPO / p).is_file()]
    assert not missing, f"actor-profile-seed primary-schema refs point at missing files: {missing}"


def test_infra_actors_schema_refs_resolve():
    body = _INFRA.read_text(encoding="utf-8").split("export const INFRA_ACTORS", 1)[1]
    refs = re.findall(r'primarySchema:\s*"([^"]+)"', body)
    missing = [p for r in refs if (p := _path_like(r)) and not (_REPO / p).is_file()]
    assert not missing, f"INFRA_ACTORS primarySchema refs point at missing files: {missing}"


if __name__ == "__main__":
    import sys
    infra, prof = infra_handles(), profile_handles()
    print(f"INFRA_ACTORS={len(infra)}  profile-seed={len(prof)}")
    print(f"infra-only drift : {sorted(infra - prof)}")
    print(f"profile-only drift: {sorted(prof - infra)}")
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"{len(fns) - failed}/{len(fns)} passed in test_actor_registry_parity.py")
    sys.exit(1 if failed else 0)
