;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/danjo/methods/budget_ledger.py (unit_refactor stage 0)
;; budget_ledger.py — 弾正 (danjo) budget_ledger ingest method (the coded R0 method).
(ns root.danjo.methods.budget-ledger
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare record-cid normalize-record build-ledger load-seed)

;; TODO: port-failed unit record_cid (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp7hrzi0p6/scratch.clj:16:1: e)
;; def record_cid(rec: dict[str, Any]) -> str:
;;     """Deterministic gov.dataset record CID: locator + sha256 content digest (G5 provenance)."""
;;     canonical = json.dumps(rec, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
;;     digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
;;     fy = rec.get("fiscalYear", "0")
;;     rid = rec.get("recordId", "unknown")
;;     sensor = rec.get("sourceSensor", "unknown")
;;     return f"gov.dataset.budgetRecord:{sensor}:{fy}:{rid}#{digest}"
(defn record-cid [& _]
  (throw (ex-info "TODO: port-failed" {:from "record_cid"})))

;; TODO: port-failed unit normalize_record (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpkloxkfw7/scratch.clj:5:14: e)
;; def normalize_record(rec: dict[str, Any]) -> dict[str, Any]:
;;     """One ledger line from a budgetRecord. Pure; carries its own CID (G5)."""
;;     kind = rec.get("recordKind")
;;     if kind not in ("appropriation", "obligation", "outlay", "subaward"):
;;         raise ValueError(f"unknown recordKind {kind!r} (budgetRecord lexicon enum)")
;;     amount = rec.get("amountLocal")
;;     if not isinstance(amount, int) or amount < 0:
;;         raise ValueError(f"amountLocal must be a non-negative integer (minor units), got {amount!r}")
;;     return {
;;         "cid": record_cid(rec),
;;         "recordKind": kind,
;;         "jurisdiction": rec.get("jurisdiction", "jpn"),
;;         "programName": rec.get("programName", ""),
;;         "programCode": rec.get("programCode", ""),
;;         "amountLocal": amount,
;;         "currencyIso4217": rec.get("currencyIso4217", "JPY"),
;;         "fiscalYear": int(rec.get("fiscalYear", 0)),
;;         "recipientName": rec.get("recipientName", ""),
;;         "recipientLocalId": rec.get("recipientLocalId", ""),
;;         "recipientLei": rec.get("recipientLei", ""),
;;         "awardDateUtc": rec.get("awardDateUtc", ""),
;;         "sourceUrl": rec.get("sourceUrl", ""),
;;         "stateAlignedFlag": bool(rec.get("stateAlignedFlag", False)),
;;     }
(defn normalize-record [& _]
  (throw (ex-info "TODO: port-failed" {:from "normalize_record"})))

;; TODO: port-failed unit build_ledger (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpdc3kmt1h/scratch.clj:5:17: e)
;; def build_ledger(records: list[dict[str, Any]]) -> dict[str, Any]:
;;     """Ingest budgetRecords → a budget ledger grouped by (programCode, fiscalYear).
;; 
;;     Returns:
;;       {
;;         "lines": [normalized line, ...],          # every record, with CID
;;         "groups": {                                # appropriation/outlay split per program-year
;;           "JP-MEXT-EDUSCI|2024": {
;;             "programCode", "programName", "fiscalYear", "jurisdiction",
;;             "appropriations": [line, ...], "outlays": [line, ...]
;;           }, ...
;;         }
;;       }
;;     """
;;     lines = [normalize_record(r) for r in records]
;;     groups: dict[str, Any] = {}
;;     for ln in lines:
;;         key = f"{ln['programCode']}|{ln['fiscalYear']}"
;;         g = groups.setdefault(
;;             key,
;;             {
;;                 "programCode": ln["programCode"],
;;                 "programName": ln["programName"],
;;                 "fiscalYear": ln["fiscalYear"],
;;                 "jurisdiction": ln["jurisdiction"],
;;                 "appropriations": [],
;;                 "outlays": [],
;;             },
;;         )
;;         if ln["recordKind"] == "appropriation":
;;             g["appropriations"].append(ln)
;;         elif ln["recordKind"] in ("outlay", "obligation", "subaward"):
;;             g["outlays"].append(ln)
;;     return {"lines": lines, "groups": groups}
(defn build-ledger [& _]
  (throw (ex-info "TODO: port-failed" {:from "build_ledger"})))

;; TODO: port-failed unit load_seed (bb-compile error)
;; def load_seed(path: str) -> list[dict[str, Any]]:
;;     with open(path, encoding="utf-8") as fh:
;;         doc = json.load(fh)
;;     return doc.get("records", doc if isinstance(doc, list) else [])
(defn load-seed [& _]
  (throw (ex-info "TODO: port-failed" {:from "load_seed"})))

