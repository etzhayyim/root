;; ported from 20-actors/keizu/methods/_edn.py (unit_refactor stage 0)
;; Minimal EDN reader (subset: [] {} :kw "str" num bool nil) — ported from ake/noroshi/watatsuna.
(ns keizu.methods.edn
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare tok tokens atom parse load-edn)

;; TODO: port-failed unit _TOK (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpcoqhuhv5/scratch.clj:2:12: w)
;; _TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')
;; _END = object()
(def tok nil) ;; TODO: port-failed const

;; TODO: port-failed unit _tokens (judah: timed out)
;; def _tokens(s: str):
;;     for m in _TOK.finditer(s):
;;         t = m.group(1)
;;         if t is not None:
;;             yield t
(defn tokens [& _]
  (throw (ex-info "TODO: port-failed" {:from "_tokens"})))

;; TODO: port-failed unit _atom (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpxojpiw3p/scratch.clj:12:42: )
;; def _atom(t: str):
;;     if t.startswith('"'):
;;         return t[1:-1].replace('\\"', '"').replace('\\\\', '\\')
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

;; TODO: port-failed unit _parse (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpc_c8wq0t/scratch.clj:3:11: w)
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
;;             v = _parse(it)
;;             out[k] = v
;;         return out
;;     if t in ("]", "}"):
;;         return _END
;;     return _atom(t)
(defn parse [& _]
  (throw (ex-info "TODO: port-failed" {:from "_parse"})))

;; TODO: port-failed unit load_edn (assembled-lint error)
;; def load_edn(path: pathlib.Path):
;;     return _parse(_tokens(pathlib.Path(path).read_text(encoding="utf-8")))
(defn load-edn [& _]
  (throw (ex-info "TODO: port-failed" {:from "load_edn"})))

