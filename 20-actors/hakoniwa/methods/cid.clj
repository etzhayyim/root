;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/hakoniwa/methods/cid.py (unit_refactor stage 0)
;; hakoniwa 箱庭 — kotoba IPFS content-address (CIDv1, raw, sha2-256, base32).
(ns root.hakoniwa.methods.cid
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare b32 base32 cidv1-raw single-block-limit)

(def b32 "abcdefghijklmnopqrstuvwxyz234567")

;; TODO: port-failed unit _base32 (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpk3wp09y9/scratch.clj:15:10: )
;; def _base32(data: bytes) -> str:
;;     bits = val = 0
;;     out = []
;;     for b in data:
;;         val = (val << 8) | b
;;         bits += 8
;;         while bits >= 5:
;;             out.append(_B32[(val >> (bits - 5)) & 31])
;;             bits -= 5
;;     if bits > 0:
;;         out.append(_B32[(val << (5 - bits)) & 31])
;;     return "".join(out)
(defn base32 [& _]
  (throw (ex-info "TODO: port-failed" {:from "_base32"})))

;; TODO: port-failed unit cidv1_raw (assembled-lint error)
;; def cidv1_raw(data: bytes) -> str:
;;     """CIDv1 / raw (0x55) / sha2-256 — matches `ipfs add --cid-version=1 --raw-leaves`."""
;;     mh = bytes([0x12, 0x20]) + hashlib.sha256(data).digest()  # sha2-256, 32-byte digest
;;     cid = bytes([0x01, 0x55]) + mh                            # CIDv1, raw codec
;;     return "b" + _base32(cid)
(defn cidv1-raw [& _]
  (throw (ex-info "TODO: port-failed" {:from "cidv1_raw"})))

(def single-block-limit 268435456)

