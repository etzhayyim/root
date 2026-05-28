"""Cross-layer composition smoke test for kawase-yui R0.

Asserts the layers laid down in iterations 1-6 actually compose:

- Iter 1: G7 lint hook exists and is executable
- Iter 1: 8 Lexicons live under 00-contracts/lexicons/app/etzhayyim/kawase/
- Iter 2: ConstitutionKeys.sol carries KAWASE_MAX_BAND_BPS + KAWASE_PER_MONTH_CAP_USD_MINOR
- Iter 3: KawaseYuiPool.sol scaffold exists and references the Constitution keys
- Iter 4: kotoba_kawase package importable and raises NotYetImplemented on send/claim
- Iter 5: each of the 5 kawase_* Pregel cells raises RuntimeError on import
- Iter 6: 20-actors/kawase-yui/ has README + manifest.jsonld with DID
           did:web:kawase-yui.etzhayyim.com

This test does NOT need a running Murakumo fleet, a Foundry / forge
install, or network access. It only validates that the kawase-yui R0
surface is structurally consistent across the 7 layers.

Why this matters: any future commit that breaks a cross-layer
constitutional invariant (e.g., removes the G7 lint hook without
landing R1, or drops a Lexicon, or unguards a cell prematurely) will
fail one of these assertions BEFORE the more expensive forge / pytest
suites run.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------
#  Iter 1: G7 lint hook
# ---------------------------------------------------------------------


def test_g7_lint_hook_exists_and_runs_clean() -> None:
    hook = _REPO_ROOT / "70-tools/scripts/lint/verify_no_commercial_remittance.py"
    assert hook.is_file(), f"G7 lint hook missing at {hook}"
    # Hook should exit 0 on a clean tree.
    result = subprocess.run(
        [sys.executable, str(hook)],
        capture_output=True,
        text=True,
        cwd=_REPO_ROOT,
    )
    assert result.returncode == 0, (
        f"G7 lint hook failed unexpectedly. stdout={result.stdout!r} "
        f"stderr={result.stderr!r}"
    )
    assert "gate: clean" in result.stdout


# ---------------------------------------------------------------------
#  Iter 1: 8 Lexicons under app.etzhayyim.kawase.*
# ---------------------------------------------------------------------


_EXPECTED_LEXICONS = (
    "depositAttestation",
    "withdrawIntent",
    "matchExecution",
    "fxRateAttestation",
    "poolStateReport",
    "rebalanceAttestation",
    "jurisdictionAttestation",
    "silenKawaseReview",
)


def test_all_eight_lexicons_present() -> None:
    base = _REPO_ROOT / "00-contracts/lexicons/app/etzhayyim/kawase"
    assert base.is_dir(), f"Lexicon dir missing at {base}"
    for name in _EXPECTED_LEXICONS:
        lex_path = base / f"{name}.json"
        assert lex_path.is_file(), f"Lexicon missing: {lex_path}"
        # Each Lexicon parses as JSON and carries the canonical id.
        with lex_path.open() as f:
            data = json.load(f)
        expected_id = f"app.etzhayyim.kawase.{name}"
        assert data.get("id") == expected_id, (
            f"{lex_path}: id={data.get('id')!r} expected={expected_id!r}"
        )


# ---------------------------------------------------------------------
#  Iter 2: Constitution wiring
# ---------------------------------------------------------------------


def test_constitution_keys_carries_kawase_constants() -> None:
    keys_sol = _REPO_ROOT / (
        "50-infra/etzhayyim-chain-contracts/src/ConstitutionKeys.sol"
    )
    text = keys_sol.read_text(encoding="utf-8")
    assert "KAWASE_MAX_BAND_BPS" in text, (
        "ConstitutionKeys.sol must declare KAWASE_MAX_BAND_BPS (G4)"
    )
    assert "KAWASE_PER_MONTH_CAP_USD_MINOR" in text, (
        "ConstitutionKeys.sol must declare KAWASE_PER_MONTH_CAP_USD_MINOR (G9)"
    )


def test_deploy_scripts_wire_kawase_constants() -> None:
    for script_rel in (
        "50-infra/etzhayyim-chain-contracts/script/Deploy.s.sol",
        "50-infra/etzhayyim-chain-contracts/script/DeployReligiousCorp.s.sol",
    ):
        script = _REPO_ROOT / script_rel
        text = script.read_text(encoding="utf-8")
        assert "KAWASE_MAX_BAND_BPS" in text, (
            f"{script_rel} must wire KAWASE_MAX_BAND_BPS"
        )
        assert "KAWASE_PER_MONTH_CAP_USD_MINOR" in text, (
            f"{script_rel} must wire KAWASE_PER_MONTH_CAP_USD_MINOR"
        )


# ---------------------------------------------------------------------
#  Iter 3: KawaseYuiPool.sol scaffold
# ---------------------------------------------------------------------


def test_kawase_pool_scaffold_present_and_references_constitution_keys() -> None:
    pool = _REPO_ROOT / "50-infra/etzhayyim-kawase-pool/src/KawaseYuiPool.sol"
    assert pool.is_file(), f"KawaseYuiPool.sol scaffold missing at {pool}"
    text = pool.read_text(encoding="utf-8")
    # The scaffold must reference both Constitution keys via the
    # maxBandBpsKey / monthlyCapKey immutables — not hard-code the
    # keccak hashes.
    assert "maxBandBpsKey" in text, "Pool must read max-band via Constitution key"
    assert "monthlyCapKey" in text, "Pool must read monthly cap via Constitution key"
    # The R0 scaffold must revert NotYetImplemented on all 3 entry points.
    assert text.count("NotYetImplemented") >= 3, (
        "Pool R0 scaffold must revert NotYetImplemented on deposit/claim/rebalance"
    )
    # The onlyAdherent and onlyCouncilSafe modifiers must be defined.
    assert "modifier onlyAdherent" in text
    assert "modifier onlyCouncilSafe" in text


# ---------------------------------------------------------------------
#  Iter 4: kotoba_kawase Python facade
# ---------------------------------------------------------------------


def test_kotoba_kawase_send_raises_not_yet_implemented() -> None:
    # We're running from inside the kotoba_kawase package's tests/ dir,
    # so import works directly via the package's own conftest.
    import kotoba_kawase as kk
    from kotoba_kawase.exceptions import NotYetImplemented

    try:
        kk.send(
            from_did="did:web:alice.etzhayyim.com",
            to_did="did:web:bob.etzhayyim.com",
            src_amount_minor=10_000_000,
            src_stable="USDC",
            tgt_stable="EURC",
        )
    except NotYetImplemented as e:
        assert "Bootstrap-Council" in e.phase
    else:
        raise AssertionError("kotoba_kawase.send must raise NotYetImplemented at R0")


def test_kotoba_kawase_claim_raises_not_yet_implemented() -> None:
    import kotoba_kawase as kk
    from kotoba_kawase.exceptions import NotYetImplemented

    try:
        kk.claim(intent_cid="b" * 46, as_did="did:web:bob.etzhayyim.com")
    except NotYetImplemented as e:
        assert "Bootstrap-Council" in e.phase
    else:
        raise AssertionError("kotoba_kawase.claim must raise NotYetImplemented at R0")


# ---------------------------------------------------------------------
#  Iter 5: 5 Pregel cells all raise RuntimeError on import
# ---------------------------------------------------------------------


_EXPECTED_CELLS = (
    "kawase_pool_match",
    "kawase_fx_oracle_watcher",
    "kawase_rebalance_proposer",
    "kawase_jurisdiction_compliance",
    "kawase_silen_review",
)


def test_every_kawase_cell_raises_runtime_error_on_import() -> None:
    base = _REPO_ROOT / "20-actors/magatama/cells"
    for cell_name in _EXPECTED_CELLS:
        cell_dir = base / cell_name
        assert cell_dir.is_dir(), f"Cell dir missing: {cell_dir}"
        cell_py = cell_dir / "cell.py"
        assert cell_py.is_file(), f"cell.py missing: {cell_py}"

        # Subprocess so each cell starts with a fresh import context
        # (avoids the import-cache contamination across cells in one
        # Python process).
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                f"import sys; sys.path.insert(0, '{cell_dir}'); import cell",
            ],
            capture_output=True,
            text=True,
            cwd=_REPO_ROOT,
        )
        assert result.returncode != 0, (
            f"{cell_name}.cell imported cleanly — expected RuntimeError "
            f"(stdout={result.stdout!r})"
        )
        # The error message must mention scaffold-only + the ADR id so
        # reviewers see the R0-honesty marker.
        combined = result.stdout + result.stderr
        assert "scaffold-only" in combined, (
            f"{cell_name}.cell raised but message missing 'scaffold-only': "
            f"{combined!r}"
        )
        assert "ADR-2605282200" in combined, (
            f"{cell_name}.cell raised but message missing 'ADR-2605282200': "
            f"{combined!r}"
        )


# ---------------------------------------------------------------------
#  Iter 6: actor root README + manifest.jsonld
# ---------------------------------------------------------------------


def test_actor_root_readme_and_manifest_present() -> None:
    root = _REPO_ROOT / "20-actors/kawase-yui"
    assert root.is_dir(), f"Actor root missing: {root}"

    readme = root / "README.md"
    assert readme.is_file(), f"README.md missing: {readme}"
    readme_text = readme.read_text(encoding="utf-8")
    assert "did:web:kawase-yui.etzhayyim.com" in readme_text
    assert "ADR-2605282200" in readme_text

    manifest = root / "manifest.jsonld"
    assert manifest.is_file(), f"manifest.jsonld missing: {manifest}"
    with manifest.open() as f:
        data = json.load(f)
    assert data.get("id") == "did:web:kawase-yui.etzhayyim.com"
    assert data.get("@type") == "ActorManifest"
    assert data.get("tier") == "Tier-B"


# ---------------------------------------------------------------------
#  Cross-cutting: all 7 R0 layers materialized (no remaining (reserved)
#  markers in deps.toml for kawase-* paths)
# ---------------------------------------------------------------------


def test_deps_toml_has_no_kawase_reserved_markers() -> None:
    deps_text = (_REPO_ROOT / "deps.toml").read_text(encoding="utf-8")
    # The (reserved) marker convention is "<path> (reserved)" inside a
    # path = "..." assignment. We check there's no kawase line carrying
    # the marker — every kawase scaffold should be materialized by R0.
    for line in deps_text.splitlines():
        if "kawase" in line and "(reserved)" in line:
            raise AssertionError(
                f"deps.toml still has a (reserved) marker on a kawase path "
                f"after R0 completion: {line!r}"
            )
