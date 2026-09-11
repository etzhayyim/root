(ns did-web.codec
  "Content-address codec for the trustless /ipfs gateway — a faithful cljs port of
  src/cid.ts + src/car.ts (ADR-2606014600 / 2606015200). Operates directly on
  js/Uint8Array for Worker performance.

  cljs-ONLY (not .cljc): the byte math relies on JavaScript 32-bit bit-operation
  semantics (<<, >>>, | all truncate to int32). ClojureScript's bit-shift-left /
  unsigned-bit-shift-right compile to those exact JS operators, so this matches
  cid.ts/car.ts bit-for-bit — but babashka's JVM long ops would NOT truncate, so
  this logic is verified by the node smoke harness (against a copy of the TS
  base32), not by bb.

  sha2-256 is async (crypto.subtle.digest) and lives in did-web.ipfs; everything
  here is synchronous byte parsing/reassembly."
  (:require [clojure.string :as str]))

(def ^:private b32 "abcdefghijklmnopqrstuvwxyz234567")

(defn base32
  "RFC4648 base32 lower, no padding — faithful to cid.ts/car.ts. `bytes` is a
  js/Uint8Array."
  [bytes]
  (let [n (alength bytes)]
    (loop [i 0, bits 0, val 0, out ""]
      (cond
        ;; drain 5-bit groups first (mirrors the inner `while (bits >= 5)`)
        (>= bits 5)
        (recur i (- bits 5) val
               (str out (.charAt b32 (bit-and (unsigned-bit-shift-right val (- bits 5)) 31))))
        ;; consume the next input byte
        (< i n)
        (recur (inc i) (+ bits 8)
               (bit-or (bit-shift-left val 8) (aget bytes i)) out)
        ;; final partial group
        (pos? bits)
        (str out (.charAt b32 (bit-and (bit-shift-left val (- 5 bits)) 31)))
        :else out))))

;; CID string predicates (mirror cid.ts regexes).
(defn raw-cid-v1?    [cid] (boolean (re-matches #"bafkrei[a-z2-7]{52}" cid)))
(defn dag-pb-cid-v1? [cid] (boolean (re-matches #"bafybei[a-z2-7]{52}" cid)))

(def ^:private RAW 0x55)
(def ^:private DAG-PB 0x70)
(def ^:private SHA2-256 0x12)

;; ── varint / CID / protobuf readers (return [value next-pos]) ────────────────

(defn read-varint
  "LEB128 varint at `pos` → [value next-pos]. Faithful to car.ts (int32 result)."
  [buf pos]
  (loop [result 0, shift 0, p pos]
    (let [b (aget buf p)
          p (inc p)
          result (bit-or result (bit-shift-left (bit-and b 0x7f) shift))]
      (if (zero? (bit-and b 0x80))
        [(unsigned-bit-shift-right result 0) p]   ; >>> 0 → uint32
        (do (when (> (+ shift 7) 35) (throw (js/Error. "varint too long")))
            (recur result (+ shift 7) p))))))

(defn parse-cid
  "Parse a CIDv1 at `pos` → {:cid-str :codec :mh-code :digest :end}. `digest` is a
  js/Uint8Array subarray. Faithful to car.ts parseCid."
  [buf pos]
  (let [start pos
        [version pos] (read-varint buf pos)]
    (when (not= version 1) (throw (js/Error. (str "only CIDv1 supported, got v" version))))
    (let [[codec pos]  (read-varint buf pos)
          [mh-code pos] (read-varint buf pos)
          [mh-len pos]  (read-varint buf pos)
          digest (.subarray buf pos (+ pos mh-len))
          pos (+ pos mh-len)
          cid-bytes (.subarray buf start pos)]
      {:cid-str (str "b" (base32 cid-bytes))
       :codec codec :mh-code mh-code :digest digest :end pos})))

(defn eq-bytes? [a b]
  (and (= (alength a) (alength b))
       (loop [i 0]
         (cond (>= i (alength a)) true
               (not= (aget a i) (aget b i)) false
               :else (recur (inc i))))))

(defn read-proto
  "Minimal protobuf reader (wire types 0 varint, 2 len-delimited) → vector of
  {:field :wire :bytes? :varint?}. Faithful to car.ts readProto."
  [buf]
  (let [n (alength buf)]
    (loop [pos 0, out []]
      (if (>= pos n)
        out
        (let [[tag pos] (read-varint buf pos)
              field (unsigned-bit-shift-right tag 3)
              wire (bit-and tag 7)]
          (cond
            (= wire 0) (let [[v pos] (read-varint buf pos)]
                         (recur pos (conj out {:field field :wire wire :varint v})))
            (= wire 2) (let [[len pos] (read-varint buf pos)]
                         (recur (+ pos len)
                                (conj out {:field field :wire wire
                                           :bytes (.subarray buf pos (+ pos len))})))
            :else (throw (js/Error. (str "unsupported protobuf wire type " wire)))))))))

(defn- concat-bytes [parts]
  (let [n (reduce + 0 (map alength parts))
        out (js/Uint8Array. n)]
    (loop [ps parts, o 0]
      (if (empty? ps)
        out
        (let [p (first ps)]
          (.set out p o)
          (recur (rest ps) (+ o (alength p))))))))

(defn reassemble
  "Reassemble the UnixFS file rooted at `cid-str` from a verified block map
  {cid-str → {:data <Uint8Array> :codec n}}. Faithful to car.ts reassemble."
  [cid-str blocks]
  (let [blk (get blocks cid-str)]
    (when-not blk (throw (js/Error. (str "missing block " cid-str " in CAR"))))
    (let [codec (:codec blk) data (:data blk)]
      (cond
        (= codec RAW) data
        (not= codec DAG-PB) (throw (js/Error. (str "unsupported codec 0x" (.toString codec 16) " for " cid-str)))
        :else
        (let [fields (read-proto data)
              links (filter #(and (= (:field %) 2) (:bytes %)) fields)]
          (if (seq links)
            (concat-bytes
             (for [lk links]
               (let [lf (read-proto (:bytes lk))
                     hash (some #(when (and (= (:field %) 1) (:bytes %)) (:bytes %)) lf)]
                 (when-not hash (throw (js/Error. "PBLink without Hash")))
                 (reassemble (:cid-str (parse-cid hash 0)) blocks))))
            ;; leaf: dag-pb Data → UnixFS message → field 2 = file bytes
            (let [unixfs (some #(when (and (= (:field %) 1) (:bytes %)) (:bytes %)) fields)]
              (if-not unixfs
                (js/Uint8Array. 0)
                (let [u (read-proto unixfs)]
                  (or (some #(when (and (= (:field %) 2) (:bytes %)) (:bytes %)) u)
                      (js/Uint8Array. 0)))))))))))

;; constants exposed for the async CAR verifier in did-web.ipfs
(def sha2-256-code SHA2-256)
