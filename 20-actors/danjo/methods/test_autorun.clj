;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/danjo/methods/test_autorun.py (unit_refactor stage 0)
;; test_autorun.py — danjo autonomous public-accountability heartbeat + kotoba Datom-log invariants.
(ns root.danjo.methods.test-autorun
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare pass ok tmp-log test-heartbeat-persists test-deterministic-resume-safe test-append-only-and-tamper test-g4-non-adjudicating-and-no-verdict test-g5-g6-provenance test-no-external-io)

(def PASS 0)
(def FAIL 0)

;; TODO: port-failed unit ok (assembled-lint error)
;; def ok(cond, msg):
;;     global PASS, FAIL
;;     if cond:
;;         PASS += 1
;;     else:
;;         FAIL += 1
;;         print(f"  ✗ {msg}")
(defn ok [& _]
  (throw (ex-info "TODO: port-failed" {:from "ok"})))

(defn _tmp-log []
  (let [path (java.io.File/createTempFile "tmp" ".datoms.kotoba.edn")]
    (try
      (.delete path)
      (throw (ex-info "TODO: port" {:from "_tmp_log"})))
    path))

;; TODO: port-failed unit test_heartbeat_persists (assembled-lint error)
;; def test_heartbeat_persists():
;;     log = _tmp_log()
;;     try:
;;         res = autorun.run_autonomous(cycles=3, log_path=log)
;;         ok(res["log_length"] == 3, "one tx per heartbeat")
;;         ok(all(b["datoms"] > 0 for b in res["beats"]), "every heartbeat persisted datoms")
;;         ok(all(b["observations"] >= 1 for b in res["beats"]), "discrepancy observations computed")
;;         ok(res["chain"]["ok"], "commit-DAG verifies (chain OK)")
;;         ok(res["head_cid"].startswith("b"), "head CID is content-addressed")
;;     finally:
;;         log.unlink(missing_ok=True)
(defn test-heartbeat-persists [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_heartbeat_persists"})))

;; TODO: port-failed unit test_deterministic_resume_safe (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp1_pqtdjt/scratch.clj:3:9: wa)
;; def test_deterministic_resume_safe():
;;     a, b = _tmp_log(), _tmp_log()
;;     try:
;;         ra = autorun.run_autonomous(cycles=3, log_path=a)
;;         rb = autorun.run_autonomous(cycles=3, log_path=b)
;;         ok([x["cid"] for x in ra["beats"]] == [x["cid"] for x in rb["beats"]],
;;            "same cycles → same CIDs (deterministic / resume-safe)")
;;     finally:
;;         a.unlink(missing_ok=True)
;;         b.unlink(missing_ok=True)
(defn test-deterministic-resume-safe [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_deterministic_resume_safe"})))

;; TODO: port-failed unit test_append_only_and_tamper (issachar: timed out)
;; def test_append_only_and_tamper():
;;     log = _tmp_log()
;;     try:
;;         autorun.run_cycle(1, log_path=log)
;;         first = kotoba.read_log(log)
;;         autorun.run_cycle(2, log_path=log)
;;         second = kotoba.read_log(log)
;;         ok(len(second) == len(first) + 1, "second heartbeat appends, does not rewrite")
;;         ok(second[1][":tx/prev"] == first[0][":tx/cid"], "tx 2 links tx 1's CID (commit-DAG)")
;;         lines = log.read_text(encoding="utf-8").splitlines()
;;         for i, ln in enumerate(lines):
;;             if ":tx/id 1 " in ln:
;;                 lines[i] = ln.replace(":danjo.obs/non-adjudicating true",
;;                                       ":danjo.obs/non-adjudicating false", 1)
;;                 break
;;         log.write_text("\n".join(lines) + "\n", encoding="utf-8")
;;         v = kotoba.verify_chain(log)
;;         ok(not v["ok"] and v["broken_at"] == 0, "tampering an earlier tx breaks the chain")
;;     finally:
;;         log.unlink(missing_ok=True)
(defn test-append-only-and-tamper [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_append_only_and_tamper"})))

;; TODO: port-failed unit test_g4_non_adjudicating_and_no_verdict (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp69bh4zqr/scratch.clj:6:7: er)
;; def test_g4_non_adjudicating_and_no_verdict():
;;     # the defining danjo invariant: the censor's EYE, never the SWORD.
;;     log = _tmp_log()
;;     try:
;;         autorun.run_cycle(1, log_path=log)
;;         tx = kotoba.read_log(log)[0]
;;         datoms = tx[":tx/datoms"]
;;         # every observation entity declares non-adjudicating true
;;         obs_ents = {d[1] for d in datoms if d[2] == ":danjo.obs/category"}
;;         ok(len(obs_ents) > 0, "observation entities persisted")
;;         for e in obs_ents:
;;             na = [d[3] for d in datoms if d[1] == e and d[2] == ":danjo.obs/non-adjudicating"]
;;             ok(na == [True], f"observation {e} carries :danjo.obs/non-adjudicating true (G4)")
;;         # NO verdict attr is representable anywhere in the log
;;         attrs = {str(d[2]).lower() for d in datoms}
;;         for tok in ("verdict", "guilt", "wrongdoing", "crime", "violation", "illegal", "fraud"):
;;             ok(not any(tok in a for a in attrs), f"no verdict token `{tok}` in any attr (G4)")
;;     finally:
;;         log.unlink(missing_ok=True)
(defn test-g4-non-adjudicating-and-no-verdict [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_g4_non_adjudicating_and_no_verdict"})))

;; TODO: port-failed unit test_g5_g6_provenance (simeon: timed out)
;; def test_g5_g6_provenance():
;;     log = _tmp_log()
;;     try:
;;         autorun.run_cycle(1, log_path=log)
;;         tx = kotoba.read_log(log)[0]
;;         datoms = tx[":tx/datoms"]
;;         obs_ents = {d[1] for d in datoms if d[2] == ":danjo.obs/category"}
;;         for e in obs_ents:
;;             cids = [d[3] for d in datoms if d[1] == e and d[2] == ":danjo.obs/source-record-cids"]
;;             mnote = [d[3] for d in datoms if d[1] == e and d[2] == ":danjo.obs/method-note-cid"]
;;             ok(cids and len(cids[0]) >= 2, f"observation {e} cites ≥2 source-record CIDs (G5)")
;;             ok(mnote and mnote[0], f"observation {e} carries a method-note CID (G6)")
;;         ops = {d[0] for d in datoms}
;;         ok(ops == {":db/add"}, "every datom is append-only :db/add (no :db/retract)")
;;     finally:
;;         log.unlink(missing_ok=True)
(defn test-g5-g6-provenance [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_g5_g6_provenance"})))

;; TODO: port-failed unit test_no_external_io (assembled-lint error)
;; def test_no_external_io():
;;     import inspect
;;     src = inspect.getsource(autorun) + inspect.getsource(kotoba)
;;     for banned in ("urllib", "http.client", "socket", "requests", "subprocess"):
;;         ok(banned not in src, f"autorun/kotoba does no external I/O (no `{banned}`)")
(defn test-no-external-io [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_no_external_io"})))

