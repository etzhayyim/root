;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/hakoniwa/methods/world.py (unit_refactor stage 0)
;; hakoniwa 箱庭 — world-graph loader for the forward-simulation scenario.
(ns root.hakoniwa.methods.world
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare tok tokens atom end parse read-edn assert-synthetic load personas signals outcomes)

;; TODO: port-failed unit _TOK (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp9f17l4mv/scratch.clj:2:61: e)
;; _TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')
;; FORBIDDEN_PERSONA_FIELDS = {
;;     ":person/id", ":person/name", ":individual/id", ":user/id", ":account/id",
;;     ":email", ":phone", ":address", ":geo/point", ":device/id", ":biometric",
;;     ":real-name", ":dob", ":ssn", ":handle",
;; }
(def tok nil) ;; TODO: port-failed const

;; TODO: port-failed unit _tokens (assembled-lint error)
;; def _tokens(s: str):
;;     for m in _TOK.finditer(s):
;;         t = m.group(1)
;;         if t is not None:
;;             yield t
(defn tokens [& _]
  (throw (ex-info "TODO: port-failed" {:from "_tokens"})))

;; TODO: port-failed unit _atom (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp8lifnmjw/scratch.clj:24:1: e)
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
;;         return t  # keep keywords as ":ns/name" strings
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

;; TODO: port-failed unit _parse (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp7oqldvyv/scratch.clj:5:13: e)
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
;;             out[k] = _parse(it)
;;         return out
;;     if t in (']', '}'):
;;         return _END
;;     return _atom(t)
(defn parse [& _]
  (throw (ex-info "TODO: port-failed" {:from "_parse"})))

;; TODO: port-failed unit read_edn (judah: timed out)
;; def read_edn(text: str):
;;     return _parse(_tokens(text))
(defn read-edn [& _]
  (throw (ex-info "TODO: port-failed" {:from "read_edn"})))

;; TODO: port-failed unit assert_synthetic (assembled-lint error)
;; def assert_synthetic(nodes: dict):
;;     """G1: every persona MUST be synthetic and MUST carry no PII-class field. Raises on breach."""
;;     for nid, n in nodes.items():
;;         if n.get(":sim/kind") != ":persona":
;;             continue
;;         if n.get(":persona/synthetic") is not True:
;;             raise ValueError(f"G1 violation: persona {nid} is not marked :persona/synthetic true")
;;         leaked = set(n) & FORBIDDEN_PERSONA_FIELDS
;;         if leaked:
;;             raise ValueError(f"G1 violation: persona {nid} carries PII-class field(s) {leaked}")
(defn assert-synthetic [& _]
  (throw (ex-info "TODO: port-failed" {:from "assert_synthetic"})))

;; TODO: port-failed unit load (assembled-lint error)
;; def load(path: pathlib.Path):
;;     """Return (nodes_by_id, edges) from a scenario EDN graph; enforces G1 (synthetic personas)."""
;;     forms = read_edn(path.read_text(encoding="utf-8"))
;;     nodes, edges = {}, []
;;     for f in forms:
;;         if not isinstance(f, dict):
;;             continue
;;         if ":sim/id" in f:
;;             nodes[f[":sim/id"]] = f
;;         elif ":en/from" in f and ":en/to" in f:
;;             edges.append(f)
;;     assert_synthetic(nodes)
;;     return nodes, edges
(defn load [& _]
  (throw (ex-info "TODO: port-failed" {:from "load"})))

(defn personas [nodes]
  (into {} (filter (fn [[_ n]] (= (:sim/kind n) :persona)) nodes)))

(defn signals [nodes]
  (into {} (filter (fn [[_ n]] (= (:sim/kind n) :signal)) nodes)))

(defn outcomes [nodes]
  (into {} (filter (fn [[_ n]] (= (:sim/kind n) :outcome)) nodes)))

