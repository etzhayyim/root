;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/danjo/methods/kotoba.py (unit_refactor stage 0)
;; kotoba.py — danjo kotoba Datom-log writer (local, content-addressed). ADR-2605301600
(ns root.danjo.methods.kotoba
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare log-default add graph-datoms obs-id derived-datoms canonical tx-cid make-tx edn-val tx-to-edn append-tx tok tokens atom parse read-log head-cid verify-chain)

;; TODO: port-failed unit LOG_DEFAULT (naphtali: timed out)
;; LOG_DEFAULT = (pathlib.Path(__file__).resolve().parents[1] / "data" / "persisted"
;;                / "danjo.datoms.kotoba.edn")
;; _FORBIDDEN_VERDICT_TOKENS = ("verdict", "guilt", "wrongdoing", "finding", "culprit",
;;                              "illegal", "crime", "violation", "unlawful", "fraud", "sanction")
(def log-default nil) ;; TODO: port-failed const

(defn _add [entity attr value]
  "One append-only EAVT assertion: [:db/add <entity> <attr> <value>]."
  [":db/add" entity attr value])

;; TODO: port-failed unit graph_datoms (zebulun: timed out)
;; def graph_datoms(records: list[dict]) -> list[list]:
;;     """Flatten the public procurement corpus into append-only EAVT assertions. E = the record's
;;     public-record CID; attrs are namespaced :gov.procurement/*. Public pre-published record only
;;     (G3) — danjo re-fetches nothing."""
;;     out: list[list] = []
;;     for r in records:
;;         if not isinstance(r, dict):
;;             continue
;;         e = r.get("cid")
;;         if not e:
;;             continue
;;         for k, v in r.items():
;;             if k == "cid":
;;                 continue
;;             out.append(_add(e, f":gov.procurement/{k}", v))
;;     return out
(defn graph-datoms [& _]
  (throw (ex-info "TODO: port-failed" {:from "graph_datoms"})))

(defn _obs-id [o]
  (let [source-record-cids (or (:sourceRecordCids o) ["?"])
        cid0 (first source-record-cids)
        category (or (:category o) "?")]
    (str "danjo-obs:" category ":" cid0)))

;; TODO: port-failed unit derived_datoms (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp22f5g7xs/scratch.clj:5:24: e)
;; def derived_datoms(observations: list[dict]) -> list[list]:
;;     """Flatten danjo.discrepancyObservation records into append-only EAVT assertions, each carrying
;;     :danjo.obs/non-adjudicating true (G4 — a FACT, never a verdict), ≥2 source CIDs (G5), and the
;;     open method-note CID (G6). RAISES if a verdict token ever creeps into an attr (G4 structural)."""
;;     out: list[list] = []
;;     for o in observations:
;;         e = _obs_id(o)
;;         out += [
;;             _add(e, ":danjo.obs/category", ":" + str(o.get("category", "?")).lstrip(":")),
;;             _add(e, ":danjo.obs/non-adjudicating", True),
;;             _add(e, ":danjo.obs/pattern", o.get("observedPattern", "")),
;;             _add(e, ":danjo.obs/source-record-cids", list(o.get("sourceRecordCids", []))),
;;             _add(e, ":danjo.obs/method-note-cid", o.get("methodNoteCid", "")),
;;             _add(e, ":danjo.obs/known-false-positive-modes", list(o.get("knownFalsePositiveModes", []))),
;;             _add(e, ":danjo.obs/sourcing", ":representative"),
;;         ]
;;     # G4 structural self-check: no verdict token may appear in any attribute we persist.
;;     for d in out:
;;         attr = str(d[2]).lower()
;;         if any(tok in attr for tok in _FORBIDDEN_VERDICT_TOKENS):
;;             raise ValueError(f"G4: verdict attr {d[2]!r} is unrepresentable in a danjo observation")
;;     return out
(defn derived-datoms [& _]
  (throw (ex-info "TODO: port-failed" {:from "derived_datoms"})))

(defn _canonical [datoms prev-cid]
  (let [json-str (str "{\"datoms\":[" (clojure.string/join "," (map str datoms)) "],\"prev\":" prev-cid "}")]
    json-str))

;; TODO: port-failed unit tx_cid (assembled-lint error)
;; def tx_cid(datoms: list[list], prev_cid: str = "") -> str:
;;     """Content address = sha256 over (prev_cid, datoms) → a commit-DAG."""
;;     return "b" + hashlib.sha256(_canonical(datoms, prev_cid)).hexdigest()
(defn tx-cid [& _]
  (throw (ex-info "TODO: port-failed" {:from "tx_cid"})))

(defn make-tx [datoms & args]
  (let [{:keys [tx-id as-of prev-cid]} (into {} args)
        prev-cid (or prev-cid "")]
    {:tx/id tx-id
     :tx/as-of as-of
     :tx/prev prev-cid
     :tx/cid (tx-cid datoms prev-cid)
     :tx/count (count datoms)
     :tx/datoms datoms}))

;; TODO: port-failed unit _edn_val (bb-compile error)
;; def _edn_val(v: Any) -> str:
;;     if isinstance(v, bool):
;;         return "true" if v else "false"
;;     if isinstance(v, (int, float)):
;;         return repr(v)
;;     if isinstance(v, str):
;;         return v if v.startswith(":") else json.dumps(v, ensure_ascii=False)
;;     if isinstance(v, list):
;;         return "[" + " ".join(_edn_val(x) for x in v) + "]"
;;     return json.dumps(str(v), ensure_ascii=False)
(defn edn-val [& _]
  (throw (ex-info "TODO: port-failed" {:from "_edn_val"})))

;; TODO: port-failed unit _tx_to_edn (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpcl5jcut7/scratch.clj:3:8: er)
;; def _tx_to_edn(tx: dict) -> str:
;;     datoms = " ".join("[" + " ".join(_edn_val(x) for x in d) + "]" for d in tx[":tx/datoms"])
;;     return (f'{{:tx/id {tx[":tx/id"]} :tx/as-of {tx[":tx/as-of"]} '
;;             f':tx/prev {json.dumps(tx[":tx/prev"])} :tx/cid {json.dumps(tx[":tx/cid"])} '
;;             f':tx/count {tx[":tx/count"]} :tx/datoms [{datoms}]}}')
(defn tx-to-edn [& _]
  (throw (ex-info "TODO: port-failed" {:from "_tx_to_edn"})))

;; TODO: port-failed unit append_tx (assembled-lint error)
;; def append_tx(tx: dict, log_path: pathlib.Path = LOG_DEFAULT) -> str:
;;     """Append ONE transaction to the append-only log (never rewrites). Returns the tx CID."""
;;     log_path.parent.mkdir(parents=True, exist_ok=True)
;;     if not log_path.exists():
;;         log_path.write_text(";; danjo kotoba Datom log — append-only EAVT transactions "
;;                             "(content-addressed DAG). The censor's EYE, never the SWORD: "
;;                             "non-adjudicating observations only (G4). DO NOT hand-edit. ADR-2605301600.\n",
;;                             encoding="utf-8")
;;     with log_path.open("a", encoding="utf-8") as fh:
;;         fh.write(_tx_to_edn(tx) + "\n")
;;     return tx[":tx/cid"]
(defn append-tx [& _]
  (throw (ex-info "TODO: port-failed" {:from "append_tx"})))

;; TODO: port-failed unit _TOK (assembled-lint error)
;; _TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')
;; _END = object()
(def tok nil) ;; TODO: port-failed const

;; TODO: port-failed unit _tokens (assembled-lint error)
;; def _tokens(s: str):
;;     for m in _TOK.finditer(s):
;;         t = m.group(1)
;;         if t is not None:
;;             yield t
(defn tokens [& _]
  (throw (ex-info "TODO: port-failed" {:from "_tokens"})))

;; TODO: port-failed unit _atom (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp4pzw1nwg/scratch.clj:22:1: e)
;; def _atom(t: str):
;;     if t.startswith('"'):
;;         return t[1:-1].replace('\\"', '"').replace('\\\\', '\\')
;;     if t == 'true':
;;         return True
;;     if t == 'false':
;;         return False
;;     if t == 'nil':
;;         return None
;;     if t.startswith(':'):
;;         return t
;;     try:
;;         return int(t)
;;     except ValueError:
;;         try:
;;             return float(t)
;;         except ValueError:
;;             return t
(defn atom [& _]
  (throw (ex-info "TODO: port-failed" {:from "_atom"})))

;; TODO: port-failed unit _parse (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpq3g0lg9y/scratch.clj:28:18: )
;; def _parse(it):
;;     t = next(it)
;;     if t == '[':
;;         out = []
;;         while (x := _parse(it)) is not _END:
;;             out.append(x)
;;         return out
;;     if t == '{':
;;         out = {}
;;         while (k := _parse(it)) is not _END:
;;             v = _parse(it)
;;             out[k] = v
;;         return out
;;     if t in (']', '}'):
;;         return _END
;;     return _atom(t)
(defn parse [& _]
  (throw (ex-info "TODO: port-failed" {:from "_parse"})))

;; TODO: port-failed unit read_log (assembled-lint error)
;; def read_log(log_path: pathlib.Path = LOG_DEFAULT) -> list[dict]:
;;     if not log_path.exists():
;;         return []
;;     txs = []
;;     for line in log_path.read_text(encoding="utf-8").splitlines():
;;         line = line.strip()
;;         if not line or line.startswith(";"):
;;             continue
;;         txs.append(_parse(_tokens(line)))
;;     return txs
(defn read-log [& _]
  (throw (ex-info "TODO: port-failed" {:from "read_log"})))

;; TODO: port-failed unit head_cid (assembled-lint error)
;; def head_cid(log_path: pathlib.Path = LOG_DEFAULT) -> str:
;;     txs = read_log(log_path)
;;     return txs[-1][":tx/cid"] if txs else ""
(defn head-cid [& _]
  (throw (ex-info "TODO: port-failed" {:from "head_cid"})))

;; TODO: port-failed unit verify_chain (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpsc8s_gkl/scratch.clj:6:15: e)
;; def verify_chain(log_path: pathlib.Path = LOG_DEFAULT) -> dict:
;;     """Recompute every CID from its datoms + prev; verify the DAG is intact. {ok, length, broken_at}."""
;;     txs = read_log(log_path)
;;     prev = ""
;;     for i, tx in enumerate(txs):
;;         expect = tx_cid(tx.get(":tx/datoms", []), prev)
;;         if tx.get(":tx/cid") != expect or tx.get(":tx/prev") != prev:
;;             return {"ok": False, "length": len(txs), "broken_at": i}
;;         prev = tx[":tx/cid"]
;;     return {"ok": True, "length": len(txs), "broken_at": -1}
(defn verify-chain [& _]
  (throw (ex-info "TODO: port-failed" {:from "verify_chain"})))

