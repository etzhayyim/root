;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/ake/methods/ingest.py (unit_refactor stage 0)
;; ingest.py — 朱 (ake) genesis-revision bridge over the REAL actor-profile SSoT. ADR-2606052100.
(ns root.ake.methods.ingest
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare repo genesis-edit genesis-revisions report)

;; TODO: port-failed unit _REPO (assembled-lint error)
;; _REPO = pathlib.Path(__file__).resolve().parents[3]
;; _PROFILE_SEED = _REPO / "00-contracts" / "schemas" / "actor-profile-seed.kotoba.edn"
;; GENESIS_BY = "did:web:etzhayyim.com:operator:genesis"
;; GENESIS_FIELDS = (":actor/description", ":actor/display-name-ja", ":actor/display-name-en")
;; GENESIS_AS_OF_BASE = 1_000_000
(def repo nil) ;; TODO: port-failed const

;; TODO: port-failed unit _genesis_edit (assembled-lint error)
;; def _genesis_edit(handle: str, attr: str, value: str) -> dict:
;;     return {
;;         ":edit/id": f"genesis:{handle}:{attr.split('/')[-1]}",
;;         ":edit/target-kind": ":actor-profile",
;;         ":edit/target-entity": handle,
;;         ":edit/target-attr": attr,
;;         ":edit/op": ":assert",
;;         ":edit/proposed-value": value,
;;         ":edit/author": GENESIS_BY,
;;         ":edit/author-kind": ":member",
;;         ":edit/provenance": "00-contracts/schemas/actor-profile-seed.kotoba.edn",
;;         ":edit/sourcing": ":authoritative",   # mirrors the committed SSoT
;;     }
(defn genesis-edit [& _]
  (throw (ex-info "TODO: port-failed" {:from "_genesis_edit"})))

;; TODO: port-failed unit genesis_revisions (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp9ucrrh03/scratch.clj:9:18: e)
;; def genesis_revisions(profile_seed_path: pathlib.Path = _PROFILE_SEED,
;;                       as_of_base: int = GENESIS_AS_OF_BASE) -> dict:
;;     """Build the genesis append-only revision history from the REAL actor-profile SSoT."""
;;     seed = load_edn(profile_seed_path)
;;     records = [r for r in seed.get(":seed", []) if isinstance(r, dict) and r.get(":actor/handle")]
;; 
;;     history: list[dict] = []
;;     as_of = as_of_base
;;     actors = []
;;     for rec in records:
;;         handle = rec[":actor/handle"]
;;         actors.append(handle)
;;         for attr in GENESIS_FIELDS:
;;             val = rec.get(attr)
;;             if not val:
;;                 continue
;;             as_of += 1
;;             history = append_revision(history, _genesis_edit(handle, attr, str(val)), as_of)
;;     return {"history": history, "actors": actors, "records": len(records)}
(defn genesis-revisions [& _]
  (throw (ex-info "TODO: port-failed" {:from "genesis_revisions"})))

;; TODO: port-failed unit _report (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp18afe8rg/scratch.clj:6:18: e)
;; def _report(res: dict) -> str:
;;     out = ["# 朱 (ake) — genesis revision history from the REAL actor-profile SSoT\n",
;;            f"Bootstrapped {len(res['history'])} genesis revisions across {res['records']} actor "
;;            f"profiles (read from `00-contracts/schemas/actor-profile-seed.kotoba.edn`).\n",
;;            "Member edits via the membrane append ON TOP of these (the log only grows). NO ingest "
;;            "into the canonical kotoba Datom log (G8).\n",
;;            "| actor | description revisions | current sourcing |",
;;            "|---|---|---|"]
;;     for h in res["actors"]:
;;         n = len(history_of(res["history"], h, "description"))
;;         cur = current(res["history"], h, "description")
;;         src = (cur or {}).get(":revision/sourcing", "—")
;;         out.append(f"| {h} | {n} | {src} |")
;;     return "\n".join(out) + "\n"
(defn report [& _]
  (throw (ex-info "TODO: port-failed" {:from "_report"})))

