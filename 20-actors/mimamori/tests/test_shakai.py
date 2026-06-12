#!/usr/bin/env python3
"""mimamori social-capital bridge tests — moyai-family invariants + keeper-only mint."""
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "methods"))
from bond import Mishmeret, load_seed, replay  # noqa: E402
from shakai import (EARN_CAP_PER_EPOCH, HALF_LIFE_EPOCHS, MoyaiLedger,  # noqa: E402
                    grants_benefit_or_stage, grants_governance_weight,
                    mint_from_keeping, redeemable_usd_micros, social_capital_datoms)
from autorun import run_cycle  # noqa: E402

SEED = load_seed(HERE / "data" / "seed-mimamori-bonds.json")
A = "did:web:etzhayyim.com:member:fictional:aleph"
B = "did:web:etzhayyim.com:member:fictional:bet"
PASS = []


def t(name, fn):
    fn()
    PASS.append(name)
    print(f"  ok  {name}")


def test_mint_per_consented_act():
    eng = replay(SEED)               # seed has 2 heartbeats (aleph→bet, vav→he)
    led = MoyaiLedger()
    s = mint_from_keeping(eng, led, epoch=1)
    assert s["acts"] == 2 and s["minted_units"] == 2 and s["keepers_minted"] == 2
    assert led.total_minted() == 2   # one unit per content-free keeping act


def test_mint_to_keeper_never_kept():
    eng = Mishmeret()
    eng.offer(A, B)
    eng.consent(A, B)
    eng.heartbeat(A, B)
    led = MoyaiLedger()
    mint_from_keeping(eng, led, epoch=1)
    assert led.balance(A, 1) == 1.0      # the keeper earned
    assert led.balance(B, 1) == 0.0      # the kept has NO entry — not even zero-units
    assert all(e.holder_did == A for e in led._log)


def test_earn_cap():
    eng = Mishmeret()
    eng.offer(A, B)
    eng.consent(A, B)
    for _ in range(EARN_CAP_PER_EPOCH + 2):
        eng.heartbeat(A, B)
    led = MoyaiLedger()
    s = mint_from_keeping(eng, led, epoch=1)
    assert s["minted_units"] == EARN_CAP_PER_EPOCH and s["capped_acts"] == 2


def test_decay_flow_not_store():
    led = MoyaiLedger()
    led.mint(A, 4, 1, "keep:test")
    assert abs(led.balance(A, 1 + HALF_LIFE_EPOCHS) - 2.0) < 1e-9  # half-life halves it


def test_non_transferable_and_firewalls():
    led = MoyaiLedger()
    assert not hasattr(led, "transfer") and not hasattr(led, "gift") \
        and not hasattr(led, "pool")                       # the verb does not exist
    assert redeemable_usd_micros() == 0                    # cash≡0 / BHI firewall
    assert grants_governance_weight() is False             # 1 SBT = 1 vote untouched
    assert grants_benefit_or_stage() is False              # 救済 floor unconditional


def test_ref_opacity_no_kept_did():
    eng = replay(SEED)
    led = MoyaiLedger()
    mint_from_keeping(eng, led, epoch=1)
    for e in led._log:
        assert "did:" not in e.ref and e.ref.startswith("keep:")  # provenance, not registry


def test_datoms_and_autorun_integration():
    log = pathlib.Path(tempfile.mkdtemp()) / "log.kotoba.edn"
    s1 = run_cycle(SEED, log)
    assert s1["shakai"]["minted_units"] == 2
    s2 = run_cycle(SEED, log)
    assert s2["cid"] != s1["cid"]                          # prev-linked
    eng = replay(SEED)
    led = MoyaiLedger()
    mint_from_keeping(eng, led, epoch=1)
    ds = social_capital_datoms(led, 1)
    attrs = {d[2] for d in ds}
    assert ":social.capital/holder" in attrs and ":social.capital/units" in attrs
    assert all(d[0] == ":db/add" for d in ds)              # append-only


if __name__ == "__main__":
    t("mint = 1 unit per consented keeping act", test_mint_per_consented_act)
    t("mint to keeper, never the kept (G2)", test_mint_to_keeper_never_kept)
    t("per-keeper earn cap (no mining surface)", test_earn_cap)
    t("decay — a flow, never a store", test_decay_flow_not_store)
    t("non-transferable + cash≡0 + no-vote/no-stage", test_non_transferable_and_firewalls)
    t("refs opaque — no kept DID in the ledger", test_ref_opacity_no_kept_did)
    t("datoms emit + autorun integration", test_datoms_and_autorun_integration)
    print(f"test_shakai: {len(PASS)}/7 green")
