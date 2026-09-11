;; etzhayyim.kotoba.cbor — canonical CBOR (RFC 8949 §4.2 deterministic encoding).
;;
;; The com.etzhayyim.encrypted.record wire spec (ADR-2605181100) is CBOR(plaintext);
;; the root-side reference (etzhayyim.kotoba.encrypted) defaulted to EDN. This
;; provides the production-wire codec so the sealed plaintext byte-matches a
;; Rust kotoba-crypto encoder. Deterministic: shortest-form ints, definite
;; lengths, map keys sorted by bytewise-lexicographic order of their encodings.
;;
;; Type mapping (the subset lexicon records use):
;;   long/int   -> major 0/1     keyword -> text string of its name (key convention)
;;   string     -> major 3       vector/seq -> array (major 4)
;;   bytes      -> major 2        map -> map (major 5, sorted keys)
;;   true/false -> 0xf5/0xf4      nil -> 0xf6
;; Decode turns map keys (text) back into keywords; string VALUES stay strings
;; (CBOR has no keyword type — keyword values are lossy, as in any JSON/CBOR wire).
;;
;; Validated against RFC 8949 Appendix A test vectors (see test_cbor).

(ns etzhayyim.kotoba.cbor
  (:require [clojure.string :as str])
  (:import (java.io ByteArrayOutputStream)))

;; ── encode ──
(defn- write-byte [^ByteArrayOutputStream o b] (.write o (int (bit-and b 0xff))))

(defn- write-head [^ByteArrayOutputStream o major n]
  (let [mj (bit-shift-left major 5)]
    (cond
      (< n 24)         (write-byte o (bit-or mj n))
      (< n 0x100)      (do (write-byte o (bit-or mj 24)) (write-byte o n))
      (< n 0x10000)    (do (write-byte o (bit-or mj 25))
                           (write-byte o (unsigned-bit-shift-right n 8)) (write-byte o n))
      (< n 0x100000000)(do (write-byte o (bit-or mj 26))
                           (doseq [s [24 16 8 0]] (write-byte o (unsigned-bit-shift-right n s))))
      :else            (do (write-byte o (bit-or mj 27))
                           (doseq [s [56 48 40 32 24 16 8 0]]
                             (write-byte o (unsigned-bit-shift-right n s)))))))

(declare encode-into)

(defn- enc-bytes ^bytes [v]
  (let [o (ByteArrayOutputStream.)] (encode-into o v) (.toByteArray o)))

(defn- bytes< [^bytes a ^bytes b]
  ;; bytewise lexicographic (RFC 8949 §4.2.1)
  (let [la (alength a) lb (alength b) n (min la lb)]
    (loop [i 0]
      (if (< i n)
        (let [x (bit-and (aget a i) 0xff) y (bit-and (aget b i) 0xff)]
          (cond (< x y) true (> x y) false :else (recur (inc i))))
        (< la lb)))))

(defn- encode-into [^ByteArrayOutputStream o v]
  (cond
    (nil? v)            (write-byte o 0xf6)
    (boolean? v)        (write-byte o (if v 0xf5 0xf4))
    (integer? v)        (if (neg? v) (write-head o 1 (dec (- v))) (write-head o 0 v))
    (keyword? v)        (let [s (subs (str v) 1)
                              b (.getBytes s "UTF-8")]
                          (write-head o 3 (alength b)) (.write o b))
    (string? v)         (let [b (.getBytes ^String v "UTF-8")]
                          (write-head o 3 (alength b)) (.write o b))
    (bytes? v)          (do (write-head o 2 (alength ^bytes v)) (.write o ^bytes v))
    (map? v)            (let [pairs (map (fn [[k val]] [(enc-bytes k) val k]) v)
                              sorted (sort-by first bytes< pairs)]
                          (write-head o 5 (count v))
                          (doseq [[kb val _] sorted] (.write o ^bytes kb) (encode-into o val)))
    (sequential? v)     (do (write-head o 4 (count v)) (doseq [x v] (encode-into o x)))
    :else (throw (ex-info "cbor: unsupported type" {:value v :type (type v)}))))

(defn encode ^bytes [v] (enc-bytes v))

;; ── decode ──
(defn- decode-at
  "Returns [value next-index] decoding from `^bytes b` at `i`."
  [^bytes b i]
  (let [ib (bit-and (aget b i) 0xff)
        major (unsigned-bit-shift-right ib 5)
        ai (bit-and ib 0x1f)
        [n j] (cond
                (< ai 24) [ai (inc i)]
                (= ai 24) [(bit-and (aget b (inc i)) 0xff) (+ i 2)]
                (= ai 25) [(bit-or (bit-shift-left (bit-and (aget b (inc i)) 0xff) 8)
                                   (bit-and (aget b (+ i 2)) 0xff)) (+ i 3)]
                (= ai 26) [(reduce (fn [acc k] (bit-or (bit-shift-left acc 8)
                                                       (bit-and (aget b (+ i 1 k)) 0xff)))
                                   0 (range 4)) (+ i 5)]
                (= ai 27) [(reduce (fn [acc k] (bit-or (bit-shift-left acc 8)
                                                       (bit-and (aget b (+ i 1 k)) 0xff)))
                                   0 (range 8)) (+ i 9)]
                :else (throw (ex-info "cbor: indefinite/reserved unsupported" {:ai ai})))]
    (case (int major)
      0 [n j]
      1 [(- (- n) 1) j]
      2 (let [bs (java.util.Arrays/copyOfRange b j (+ j n))] [bs (+ j n)])
      3 [(String. (java.util.Arrays/copyOfRange b j (+ j n)) "UTF-8") (+ j n)]
      4 (loop [k 0 idx j acc []]
          (if (< k n)
            (let [[v nx] (decode-at b idx)] (recur (inc k) nx (conj acc v)))
            [acc idx]))
      5 (loop [k 0 idx j acc {}]
          (if (< k n)
            (let [[kv kx] (decode-at b idx)
                  [vv vx] (decode-at b kx)
                  key (if (string? kv) (keyword kv) kv)]
              (recur (inc k) vx (assoc acc key vv)))
            [acc idx]))
      7 [(case (int ai) 20 false 21 true 22 nil
               (throw (ex-info "cbor: unsupported simple" {:ai ai}))) j])))

(defn decode [^bytes b] (first (decode-at b 0)))
