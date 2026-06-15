;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/fuchi/methods/test_live_gate.py (unit_refactor stage 0)
;; Tests for 扶持 (fuchi) live_gate.py + the per-engine live legs — R1(live).
(ns root.fuchi.methods.test-live-gate
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare env full-gate test-unknown-leg-rejected test-all-four-legs-known test-couple-requires-lv7-others-lv6 test-default-gate-refused-every-leg test-missing-operator-flag-refused test-missing-attestation-refused test-insufficient-council-refused test-lv6-ok-for-provision-not-couple test-server-signer-refused test-full-gate-admissible-every-leg intents test-dispatch-live-refused-by-default test-dispatch-live-ok-when-gated test-dispatch-live-intent-stays-unpublished ballots test-finalize-binding-refused-by-default test-finalize-binding-ok-after-timelock test-finalize-binding-timelock-still-strict ledger test-write-live-refused-by-default test-write-live-ok-when-gated-cash-zero funded unfunded test-commit-live-refused-without-gate test-commit-live-ok-when-gated-and-funded test-commit-live-g2-refuses-unfunded-even-when-gated test-commit-live-g2-refuses-over-earmark run)

;; TODO: port-failed unit _env (assembled-lint error)
;; def _env(leg, on=True):
;;     flag = LEG_POLICY[leg][0]
;;     return {flag: "1"} if on else {}
(defn env [& _]
  (throw (ex-info "TODO: port-failed" {:from "_env"})))

;; TODO: port-failed unit _full_gate (assembled-lint error)
;; def _full_gate(leg, level=None):
;;     lvl = LEG_POLICY[leg][1] if level is None else level
;;     return LiveGate(leg=leg, operator_did="did:web:etzhayyim.com:operator:op1",
;;                     council_level=lvl, member_signature="sig:member:abel:ed25519:deadbeef")
(defn full-gate [& _]
  (throw (ex-info "TODO: port-failed" {:from "_full_gate"})))

;; TODO: port-failed unit test_unknown_leg_rejected (assembled-lint error)
;; def test_unknown_leg_rejected():
;;     try:
;;         LiveGate(leg="bogus")
;;         assert False, "unknown leg should raise"
;;     except ValueError:
;;         pass
(defn test-unknown-leg-rejected [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_unknown_leg_rejected"})))

;; TODO: port-failed unit test_all_four_legs_known (assembled-lint error)
;; def test_all_four_legs_known():
;;     assert set(LEG_POLICY) == {"provision", "vote", "book", "couple"}
(defn test-all-four-legs-known [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_all_four_legs_known"})))

;; TODO: port-failed unit test_couple_requires_lv7_others_lv6 (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmptwmbtuzv/scratch.clj:3:8: er)
;; def test_couple_requires_lv7_others_lv6():
;;     assert LEG_POLICY["couple"][1] == 7
;;     assert LEG_POLICY["provision"][1] == 6
;;     assert LEG_POLICY["vote"][1] == 6
;;     assert LEG_POLICY["book"][1] == 6
(defn test-couple-requires-lv7-others-lv6 [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_couple_requires_lv7_others_lv6"})))

;; TODO: port-failed unit test_default_gate_refused_every_leg (assembled-lint error)
;; def test_default_gate_refused_every_leg():
;;     for leg in LEG_POLICY:
;;         st = gate_status(LiveGate(leg=leg), env={})
;;         assert st["admissible"] is False
;;         try:
;;             require(LiveGate(leg=leg), env={})
;;             assert False, f"{leg} default must refuse"
;;         except LiveGateRefused:
;;             pass
(defn test-default-gate-refused-every-leg [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_default_gate_refused_every_leg"})))

;; TODO: port-failed unit test_missing_operator_flag_refused (assembled-lint error)
;; def test_missing_operator_flag_refused():
;;     for leg in LEG_POLICY:
;;         g = _full_gate(leg)
;;         try:
;;             require(g, env={})  # no env flag
;;             assert False
;;         except LiveGateRefused as e:
;;             assert "operator process flag" in str(e)
(defn test-missing-operator-flag-refused [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_missing_operator_flag_refused"})))

;; TODO: port-failed unit test_missing_attestation_refused (assembled-lint error)
;; def test_missing_attestation_refused():
;;     leg = "provision"
;;     g = LiveGate(leg=leg, operator_did="", council_level=6, member_signature="sig:x")
;;     try:
;;         require(g, env=_env(leg))
;;         assert False
;;     except LiveGateRefused as e:
;;         assert "operator attestation" in str(e)
(defn test-missing-attestation-refused [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_missing_attestation_refused"})))

;; TODO: port-failed unit test_insufficient_council_refused (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp6u7k2hse/scratch.clj:4:12: w)
;; def test_insufficient_council_refused():
;;     leg = "couple"  # needs Lv7
;;     g = LiveGate(leg=leg, operator_did="op", council_level=6, member_signature="sig:x")
;;     try:
;;         require(g, env=_env(leg))
;;         assert False
;;     except LiveGateRefused as e:
;;         assert "Lv7" in str(e)
(defn test-insufficient-council-refused [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_insufficient_council_refused"})))

;; TODO: port-failed unit test_lv6_ok_for_provision_not_couple (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp2y53o2gf/scratch.clj:4:13: w)
;; def test_lv6_ok_for_provision_not_couple():
;;     # Lv6 satisfies provision but not couple
;;     require(_full_gate("provision", level=6), env=_env("provision"))  # ok
;;     try:
;;         require(_full_gate("couple", level=6), env=_env("couple"))
;;         assert False
;;     except LiveGateRefused:
;;         pass
(defn test-lv6-ok-for-provision-not-couple [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_lv6_ok_for_provision_not_couple"})))

;; TODO: port-failed unit test_server_signer_refused (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp8ci0zy_5/scratch.clj:3:8: er)
;; def test_server_signer_refused():
;;     for sig in ("", "server", "did:server:x", ":server", "anon", "  "):
;;         leg = "vote"
;;         g = LiveGate(leg=leg, operator_did="op", council_level=6, member_signature=sig)
;;         try:
;;             require(g, env=_env(leg))
;;             assert False, f"signer {sig!r} must be refused"
;;         except LiveGateRefused as e:
;;             assert "member signature" in str(e) or "operator" in str(e)
(defn test-server-signer-refused [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_server_signer_refused"})))

;; TODO: port-failed unit test_full_gate_admissible_every_leg (assembled-lint error)
;; def test_full_gate_admissible_every_leg():
;;     for leg in LEG_POLICY:
;;         st = require(_full_gate(leg), env=_env(leg))
;;         assert st["admissible"] is True
(defn test-full-gate-admissible-every-leg [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_full_gate_admissible_every_leg"})))

;; TODO: port-failed unit _intents (assembled-lint error)
;; def _intents():
;;     rails = [{"kind": "food-mitsuho", "imputed_usd_micros_yr": 12_000_000_000},
;;              {"kind": "liquidity-warifu", "imputed_usd_micros_yr": 3_000_000_000,
;;               "member_principal": True}]
;;     return prov.provision(rails, "alloc:abel")
(defn intents [& _]
  (throw (ex-info "TODO: port-failed" {:from "_intents"})))

;; TODO: port-failed unit test_dispatch_live_refused_by_default (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpij_z9aig/scratch.clj:4:6: wa)
;; def test_dispatch_live_refused_by_default():
;;     try:
;;         prov.dispatch_live(_intents(), LiveGate(leg="provision"), env={})
;;         assert False
;;     except LiveGateRefused:
;;         pass
(defn test-dispatch-live-refused-by-default [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_dispatch_live_refused_by_default"})))

;; TODO: port-failed unit test_dispatch_live_ok_when_gated (assembled-lint error)
;; def test_dispatch_live_ok_when_gated():
;;     out = prov.dispatch_live(_intents(), _full_gate("provision"), env=_env("provision"))
;;     assert len(out) == 2
;;     # cash≡0 + no-server-key hold on the wrapped intent in live mode
;;     assert all(d.intent.cash_usd_micros == 0 for d in out)
;;     assert all(d.intent.server_held_key is False for d in out)
;;     # member-principal liquidity stays member-principal
;;     assert any(d.intent.member_principal for d in out)
(defn test-dispatch-live-ok-when-gated [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_dispatch_live_ok_when_gated"})))

;; TODO: port-failed unit test_dispatch_live_intent_stays_unpublished (assembled-lint error)
;; def test_dispatch_live_intent_stays_unpublished():
;;     out = prov.dispatch_live(_intents(), _full_gate("provision"), env=_env("provision"))
;;     assert all(d.intent.published is False for d in out)  # G10 structural on the intent
;;     assert all(d.authorized_to_publish for d in out)      # authorization on the receipt
(defn test-dispatch-live-intent-stays-unpublished [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_dispatch_live_intent_stays_unpublished"})))

;; TODO: port-failed unit _ballots (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpkebwcejp/scratch.clj::: erro)
;; def _ballots():
;;     return vote_mod.ballots_from_seed([
;;         {":ballot/voter": "did:m:a", ":ballot/choice": "yes", ":ballot/cast-at": 10},
;;         {":ballot/voter": "did:m:b", ":ballot/choice": "yes", ":ballot/cast-at": 11},
;;         {":ballot/voter": "did:m:c", ":ballot/choice": "yes", ":ballot/cast-at": 12},
;;     ])
(defn ballots [& _]
  (throw (ex-info "TODO: port-failed" {:from "_ballots"})))

;; TODO: port-failed unit test_finalize_binding_refused_by_default (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpry2mweap/scratch.clj:4:6: wa)
;; def test_finalize_binding_refused_by_default():
;;     try:
;;         vote_mod.finalize_binding(_ballots(), 0, 100, LiveGate(leg="vote"), env={})
;;         assert False
;;     except LiveGateRefused:
;;         pass
(defn test-finalize-binding-refused-by-default [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_finalize_binding_refused_by_default"})))

;; TODO: port-failed unit test_finalize_binding_ok_after_timelock (assembled-lint error)
;; def test_finalize_binding_ok_after_timelock():
;;     r = vote_mod.finalize_binding(_ballots(), 0, 100, _full_gate("vote"), env=_env("vote"))
;;     assert r["binding"] is True
;;     assert r["outcome"] == "accepted"
(defn test-finalize-binding-ok-after-timelock [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_finalize_binding_ok_after_timelock"})))

;; TODO: port-failed unit test_finalize_binding_timelock_still_strict (assembled-lint error)
;; def test_finalize_binding_timelock_still_strict():
;;     # gated, but before the 48h window closes → ValueError (the gate can't bypass the timelock)
;;     try:
;;         vote_mod.finalize_binding(_ballots(), 0, 10, _full_gate("vote"), env=_env("vote"))
;;         assert False
;;     except ValueError as e:
;;         assert "timelock" in str(e)
(defn test-finalize-binding-timelock-still-strict [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_finalize_binding_timelock_still_strict"})))

;; TODO: port-failed unit _ledger (bb-compile error)
;; def _ledger():
;;     rails = [{"kind": "food-mitsuho", "imputed_usd_micros_yr": 12_000_000_000}]
;;     return book.book_toritate(rails, "alloc:abel", "did:m:abel")
(defn ledger [& _]
  (throw (ex-info "TODO: port-failed" {:from "_ledger"})))

;; TODO: port-failed unit test_write_live_refused_by_default (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpdx4cg8ye/scratch.clj:4:6: wa)
;; def test_write_live_refused_by_default():
;;     try:
;;         book.write_live(_ledger(), LiveGate(leg="book"), env={})
;;         assert False
;;     except LiveGateRefused:
;;         pass
(defn test-write-live-refused-by-default [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_write_live_refused_by_default"})))

;; TODO: port-failed unit test_write_live_ok_when_gated_cash_zero (assembled-lint error)
;; def test_write_live_ok_when_gated_cash_zero():
;;     r = book.write_live(_ledger(), _full_gate("book"), env=_env("book"))
;;     assert r.committed is True
;;     assert all(e.cash_usd_micros == 0 for e in r.entries)
(defn test-write-live-ok-when-gated-cash-zero [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_write_live_ok_when_gated_cash_zero"})))

;; TODO: port-failed unit _funded (bb-compile error)
;; def _funded():
;;     ev = couple_mod.DisplacementEvent("sanae", "c-sanae", 12, 60_000_000_000, funded=True)
;;     return ev, couple_mod.earmark_from_surplus(ev)
(defn funded [& _]
  (throw (ex-info "TODO: port-failed" {:from "_funded"})))

;; TODO: port-failed unit _unfunded (bb-compile error)
;; def _unfunded():
;;     ev = couple_mod.DisplacementEvent("hataori", "c-hataori", 30, 0, funded=False)
;;     return ev, couple_mod.earmark_from_surplus(ev)
(defn unfunded [& _]
  (throw (ex-info "TODO: port-failed" {:from "_unfunded"})))

;; TODO: port-failed unit test_commit_live_refused_without_gate (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpnxkrn5sh/scratch.clj:3:8: er)
;; def test_commit_live_refused_without_gate():
;;     ev, em = _funded()
;;     try:
;;         couple_mod.commit_live(ev, em, 8_500_000_000, LiveGate(leg="couple"), env={})
;;         assert False
;;     except LiveGateRefused:
;;         pass
(defn test-commit-live-refused-without-gate [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_commit_live_refused_without_gate"})))

;; TODO: port-failed unit test_commit_live_ok_when_gated_and_funded (assembled-lint error)
;; def test_commit_live_ok_when_gated_and_funded():
;;     ev, em = _funded()
;;     c = couple_mod.commit_live(ev, em, 8_500_000_000, _full_gate("couple"), env=_env("couple"))
;;     assert c.admissible is True
;;     assert c.cohort_id == "c-sanae"
(defn test-commit-live-ok-when-gated-and-funded [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_commit_live_ok_when_gated_and_funded"})))

;; TODO: port-failed unit test_commit_live_g2_refuses_unfunded_even_when_gated (assembled-lint error)
;; def test_commit_live_g2_refuses_unfunded_even_when_gated():
;;     # gate passes (Lv7) but the G2 coupling gate refuses an unfunded cohort → ValueError
;;     ev, em = _unfunded()
;;     try:
;;         couple_mod.commit_live(ev, em, 1_000_000, _full_gate("couple"), env=_env("couple"))
;;         assert False
;;     except ValueError as e:
;;         assert "G2" in str(e)
(defn test-commit-live-g2-refuses-unfunded-even-when-gated [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_commit_live_g2_refuses_unfunded_even_when_gated"})))

;; TODO: port-failed unit test_commit_live_g2_refuses_over_earmark (assembled-lint error)
;; def test_commit_live_g2_refuses_over_earmark():
;;     ev, em = _funded()  # earmark = 54_000_000_000
;;     try:
;;         couple_mod.commit_live(ev, em, 99_000_000_000, _full_gate("couple"), env=_env("couple"))
;;         assert False
;;     except ValueError as e:
;;         assert "exceeds funded earmark" in str(e)
(defn test-commit-live-g2-refuses-over-earmark [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_commit_live_g2_refuses_over_earmark"})))

;; TODO: port-failed unit _run (bb-compile error)
;; def _run():
;;     fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
;;     for fn in fns:
;;         fn()
;;     print(f"test_live_gate.py: {len(fns)} passed")
;;     return 0
(defn run [& _]
  (throw (ex-info "TODO: port-failed" {:from "_run"})))

