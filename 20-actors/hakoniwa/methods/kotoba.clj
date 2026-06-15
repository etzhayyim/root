;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/hakoniwa/methods/kotoba.py (unit_refactor stage 0)
;; kotoba.py — hakoniwa 箱庭 kotoba Datom-log writer. ADR-2606111500 + ADR-2605312345.
(ns root.hakoniwa.methods.kotoba
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare log-default add world-datoms distribution-datoms post-datoms canonical tx-cid make-tx edn-val tx-to-edn append-tx read-tokens atom end parse read-log head-cid verify-chain)

;; TODO: port-failed unit LOG_DEFAULT (bb-compile error)
;; LOG_DEFAULT = pathlib.Path(__file__).resolve().parents[1] / "data" / "hakoniwa.datoms.kotoba.edn"
(def log-default nil) ;; TODO: port-failed const

(defn _add [entity attr value]
  [":db/add" entity attr value])

(defn world-datoms [nodes edges meta]
  "Flatten the box into append-only EAVT assertions (nodes, 縁, run config)."
  (let [out (clojure.core/vec [])
        ;; Process nodes
        node-assertions (for [[nid n] nodes
                               [a v] n]
                         (when-not (or (= a ":sim/id") (nil? v))
                           (_add nid a v)))
        ;; Process edges
        edge-assertions (for [e edges
                               [a v] e]
                         (let [eid (str "en." (:en/from e) 
                                        (.lstrip (:en/kind e) ":") 
                                        (:en/to e))]
                           (when (not (nil? v))
                             (_add eid a v))))
        ;; Process run config
        run-key "run.hakoniwa"
        run-config [[:run/steps] (:steps meta)
                    [:run/replicas] (:replicas meta)
                    [:run/seed] (:seed meta)
                    [:run/jitter] (:jitter meta)
                    [:run/kernel] ":friedkin-johnsen"]
        run-assertions (for [[a v] run-config]
                         (when (not (nil? v))
                           (_add run-key a v)))]
    (clojure.core/vec (concat node-assertions edge-assertions run-assertions))))

(defn _add [id key value]
  [(str id) key value])

;; TODO: port-failed unit distribution_datoms (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp426sre6j/scratch.clj:5:10: e)
;; def distribution_datoms(dist: dict, outcome: str = "outcome.adoption") -> list[list]:
;;     """The outcome DISTRIBUTION as append-only EAVT — quantiles + mean/stdev. NO point datom;
;;     :forecast/point-asserted false is the structural marker (G2 / 非終末論)."""
;;     out: list[list] = []
;;     for qk, qv in dist["quantiles"].items():
;;         out.append(_add(outcome, f":forecast/{qk.lstrip(':')}", round(qv, 6)))
;;     out.append(_add(outcome, ":forecast/mean", round(dist["mean"], 6)))
;;     out.append(_add(outcome, ":forecast/stdev", round(dist["stdev"], 6)))
;;     out.append(_add(outcome, ":forecast/kind", ":distribution"))
;;     out.append(_add(outcome, ":forecast/point-asserted", False))   # G2 — never a point
;;     return out
(defn distribution-datoms [& _]
  (throw (ex-info "TODO: port-failed" {:from "distribution_datoms"})))

;; TODO: port-failed unit post_datoms (levi: timed out)
;; def post_datoms(posts: list[dict], prefix: str = "post") -> list[list]:
;;     out: list[list] = []
;;     for i, p in enumerate(posts):
;;         pid = f"{prefix}-{p.get(':post/subject', i)}"
;;         for a, v in p.items():
;;             if v is None:
;;                 continue
;;             out.append(_add(pid, a, v))
;;     return out
(defn post-datoms [& _]
  (throw (ex-info "TODO: port-failed" {:from "post_datoms"})))

(defn _canonical [& _]
  (throw (ex-info "TODO: port" {:from "_canonical"})))

;; TODO: port-failed unit tx_cid (assembled-lint error)
;; def tx_cid(datoms: list[list], prev_cid: str = "") -> str:
;;     """Content address of a transaction = sha256 over (prev_cid, datoms). Linking prev_cid makes
;;     the log a commit-DAG (tampering any earlier tx breaks every later CID)."""
;;     return "b" + hashlib.sha256(_canonical(datoms, prev_cid)).hexdigest()
(defn tx-cid [& _]
  (throw (ex-info "TODO: port-failed" {:from "tx_cid"})))

;; TODO: port-failed unit make_tx (assembled-lint error)
;; def make_tx(datoms: list[list], *, tx_id: int, as_of: int, prev_cid: str = "") -> dict:
;;     return {
;;         ":tx/id": tx_id,
;;         ":tx/as-of": as_of,
;;         ":tx/prev": prev_cid,
;;         ":tx/cid": tx_cid(datoms, prev_cid),
;;         ":tx/count": len(datoms),
;;         ":tx/datoms": datoms,
;;     }
(defn make-tx [& _]
  (throw (ex-info "TODO: port-failed" {:from "make_tx"})))

;; TODO: port-failed unit _edn_val (assembled-lint error)
;; def _edn_val(v: Any) -> str:
;;     if isinstance(v, bool):
;;         return "true" if v else "false"
;;     if isinstance(v, (int, float)):
;;         return repr(v)
;;     if isinstance(v, str):
;;         if v.startswith(":"):
;;             return v
;;         return json.dumps(v, ensure_ascii=False)
;;     if isinstance(v, list):
;;         return "[" + " ".join(_edn_val(x) for x in v) + "]"
;;     return json.dumps(str(v), ensure_ascii=False)
(defn edn-val [& _]
  (throw (ex-info "TODO: port-failed" {:from "_edn_val"})))

;; TODO: port-failed unit _tx_to_edn (assembled-lint error)
;; def _tx_to_edn(tx: dict) -> str:
;;     datoms = " ".join("[" + " ".join(_edn_val(x) for x in d) + "]" for d in tx[":tx/datoms"])
;;     return (f'{{:tx/id {tx[":tx/id"]} :tx/as-of {tx[":tx/as-of"]} '
;;             f':tx/prev {json.dumps(tx[":tx/prev"])} :tx/cid {json.dumps(tx[":tx/cid"])} '
;;             f':tx/count {tx[":tx/count"]} :tx/datoms [{datoms}]}}')
(defn tx-to-edn [& _]
  (throw (ex-info "TODO: port-failed" {:from "_tx_to_edn"})))

;; TODO: port-failed unit append_tx (assembled-lint error)
;; def append_tx(tx: dict, log_path: pathlib.Path = LOG_DEFAULT) -> str:
;;     """Append ONE transaction to the append-only log (never rewrites). Returns the tx CID. This
;;     is the only mutation: the log only ever grows (非終末論)."""
;;     log_path.parent.mkdir(parents=True, exist_ok=True)
;;     if not log_path.exists():
;;         log_path.write_text(";; hakoniwa 箱庭 kotoba Datom log — append-only EAVT transactions "
;;                             "(content-addressed DAG). DO NOT hand-edit. ADR-2606111500.\n",
;;                             encoding="utf-8")
;;     with log_path.open("a", encoding="utf-8") as fh:
;;         fh.write(_tx_to_edn(tx) + "\n")
;;     return tx[":tx/cid"]
(defn append-tx [& _]
  (throw (ex-info "TODO: port-failed" {:from "append_tx"})))

;; TODO: port-failed unit _read_tokens (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpzofr4sc4/scratch.clj:1:5: er)
;; def _read_tokens(s: str):
;;     import re
;;     tok = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')
;;     for m in tok.finditer(s):
;;         t = m.group(1)
;;         if t is not None:
;;             yield t
(defn read-tokens [& _]
  (throw (ex-info "TODO: port-failed" {:from "_read_tokens"})))

;; TODO: port-failed unit _atom (bb-compile error)
;; def _atom(t: str):
;;     if t.startswith('"'):
;;         return json.loads(t)
;;     if t == "true":
;;         return True
;;     if t == "false":
;;         return False
;;     if t == "nil":
;;         return None
;;     if t.startswith(":"):
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

;; TODO: port-failed unit _END (assembled-lint error)
;; _END = object()
(def end nil) ;; TODO: port-failed const

;; TODO: port-failed unit _parse (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpu06_488f/scratch.clj:20:18: )
;; def _parse(it):
;;     t = next(it)
;;     if t == "[":
;;         out = []
;;         while (x := _parse(it)) is not _END:
;;             out.append(x)
;;         return out
;;     if t == "{":
;;         out = {}
;;         while (k := _parse(it)) is not _END:
;;             out[k] = _parse(it)
;;         return out
;;     if t in ("]", "}"):
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
;;         txs.append(_parse(_read_tokens(line)))
;;     return txs
(defn read-log [& _]
  (throw (ex-info "TODO: port-failed" {:from "read_log"})))

(defn head-cid [log-path]
  (let [txs (read-log log-path)]
    (if (seq txs)
      (get (last txs) ":tx/cid")
      "")))

(defn verify-chain [log-path]
  (let [txs (read-log log-path)]
    (loop [i 0
           prev ""]
      (if (= i (count txs))
        {:ok true :length (count txs) :broken-at -1}
        (let [tx (nth txs i)
              datoms (get tx :tx/datoms [])
              current-cid (:tx/cid tx)
              current-prev (:tx/prev tx)
              expect (tx-cid datoms prev)]
          (if (and (= current-cid expect) (= current-prev prev))
            (recur (inc i) current-cid)
            {:ok false :length (count txs) :broken-at i}))))))

