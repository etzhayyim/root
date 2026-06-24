(ns etzhayyim.pds.repo
  "atproto repo federation primitives — the com.atproto.sync.* read surface so the
  repo can be crawled by a relay / AppView.

  Implements, from scratch (no SDK): deterministic DAG-CBOR encoding, CIDv1
  (dag-cbor / sha2-256), a Merkle Search Tree over the repo's records following
  the atproto reference layering (2 leading-zero-bits per level), an Ed25519-signed
  commit object, and CAR v1 serialization.

  Conformance note (R1): the MST + commit follow the atproto reference algorithm
  and the encoders are round-trip + cross-checked in tests (CID determinism, CAR
  parse, sign/verify). Byte-exact validation against a LIVE relay + publishing the
  commit signing key in the did:web document (so a relay can verify `sig`) is the
  remaining federation step — until then this PDS *serves* a well-formed repo CAR
  but is not yet registered with a relay."
  (:require [clojure.string :as str]
            [clojure.java.io :as io]
            [clojure.edn :as edn]
            [etzhayyim.pds.datom :as d])
  (:import [java.io ByteArrayOutputStream]
           [java.math BigInteger]
           [java.security MessageDigest KeyPairGenerator Signature KeyFactory]
           [java.security.spec PKCS8EncodedKeySpec X509EncodedKeySpec]
           [java.util Base64 Arrays]))

;; ── hashing / base32 ─────────────────────────────────────────────────────────

(defn- sha256 ^bytes [^bytes b]
  (.digest (MessageDigest/getInstance "SHA-256") b))

(def ^:private b32 "abcdefghijklmnopqrstuvwxyz234567")

(defn- base32-lower [^bytes raw]
  (let [bits (mapcat (fn [byte] (map #(bit-and (bit-shift-right (bit-and (int byte) 0xff) %) 1) [7 6 5 4 3 2 1 0])) (seq raw))]
    (->> (partition 5 5 (repeat 0) bits)
         (map (fn [c] (.charAt b32 (reduce #(+ (* %1 2) %2) 0 c))))
         (apply str))))

;; ── DAG-CBOR (deterministic) ─────────────────────────────────────────────────
;; A CID link is represented as {::cid <byte-array>}.

(defn cid-link [^bytes cid-bytes] {::cid cid-bytes})
(defn cid-link? [x] (and (map? x) (contains? x ::cid)))

(defn- w-type [^ByteArrayOutputStream out major n]
  (let [m (bit-shift-left major 5)]
    (cond
      (< n 24)         (.write out (int (+ m n)))
      (< n 0x100)      (do (.write out (int (+ m 24))) (.write out (int n)))
      (< n 0x10000)    (do (.write out (int (+ m 25)))
                           (.write out (int (bit-and (bit-shift-right n 8) 0xff)))
                           (.write out (int (bit-and n 0xff))))
      (< n 0x100000000) (do (.write out (int (+ m 26)))
                            (doseq [s [24 16 8 0]] (.write out (int (bit-and (bit-shift-right n s) 0xff)))))
      :else            (do (.write out (int (+ m 27)))
                           (doseq [s [56 48 40 32 24 16 8 0]] (.write out (int (bit-and (bit-shift-right n s) 0xff))))))))

(defn- map-key-order
  "DAG-CBOR sorts map keys length-first, then bytewise."
  [ks]
  (sort-by (fn [k] (let [b (.getBytes ^String k "UTF-8")] [(alength b) (vec b)])) ks))

(defn- encode! [^ByteArrayOutputStream out v]
  (cond
    (cid-link? v)
    (do (w-type out 6 42)                                  ; tag 42
        (let [cb ^bytes (::cid v)
              wrapped (byte-array (inc (alength cb)))]
          (aset-byte wrapped 0 (byte 0))                   ; 0x00 multibase identity prefix
          (System/arraycopy cb 0 wrapped 1 (alength cb))
          (w-type out 2 (alength wrapped))
          (.write out wrapped)))

    (string? v)
    (let [b (.getBytes ^String v "UTF-8")] (w-type out 3 (alength b)) (.write out b))

    (bytes? v)
    (do (w-type out 2 (alength ^bytes v)) (.write out ^bytes v))

    (integer? v)
    (if (>= v 0) (w-type out 0 v) (w-type out 1 (dec (- v))))

    (boolean? v)
    (.write out (int (if v 0xf5 0xf4)))

    (nil? v)
    (.write out (int 0xf6))

    (map? v)
    (let [ks (map-key-order (map name (keys v)))]
      (w-type out 5 (count ks))
      (doseq [k ks]
        (encode! out k)
        (encode! out (or (get v k) (get v (keyword k))))))

    (sequential? v)
    (do (w-type out 4 (count v)) (doseq [x v] (encode! out x)))

    :else (throw (ex-info "dag-cbor: unencodable" {:v v}))))

(defn dag-cbor ^bytes [v]
  (let [out (ByteArrayOutputStream.)] (encode! out v) (.toByteArray out)))

;; ── CIDv1 (dag-cbor / sha2-256) ──────────────────────────────────────────────

(defn cid-of-bytes ^bytes [^bytes block]
  (let [d (sha256 block)
        b (byte-array (+ 4 (alength d)))]
    (aset-byte b 0 (byte 0x01)) (aset-byte b 1 (byte 0x71))  ; cidv1, dag-cbor
    (aset-byte b 2 (byte 0x12)) (aset-byte b 3 (byte 0x20))  ; sha2-256, 32 bytes
    (System/arraycopy d 0 b 4 (alength d))
    b))

(defn cid-str [^bytes cid-bytes] (str "b" (base32-lower cid-bytes)))
(defn block-cid ^bytes [v] (cid-of-bytes (dag-cbor v)))

;; ── MST (atproto reference layering) ─────────────────────────────────────────

(defn leading-zeros
  "atproto MST depth of a key: 2 leading-zero-bits per level on sha256(key)."
  [^String key]
  (let [digest (sha256 (.getBytes key "UTF-8"))]
    (loop [i 0 z 0]
      (if (>= i (alength digest))
        z
        (let [b (bit-and (aget digest i) 0xff)]
          (cond
            (zero? b)  (recur (inc i) (+ z 4))
            (< b 4)    (+ z 3)
            (< b 16)   (+ z 2)
            (< b 64)   (+ z 1)
            :else      z))))))

(defn- common-prefix-len [^String a ^String b]
  (let [n (min (count a) (count b))]
    (loop [i 0] (if (and (< i n) (= (.charAt a i) (.charAt b i))) (recur (inc i)) i))))

;; A node is built recursively: entries at the current layer, with subtrees for
;; keys that hash to a deeper layer slotted between them.

(defn- build-layer
  "entries = sorted seq of [key value-cid-bytes]. Returns [node-map blocks] where
  blocks is a map of cid-str→{:cid bytes :bytes bytes :node map}. Recursively emits
  child nodes. layer = current tree layer."
  [entries layer blocks*]
  (let [at-layer (filter #(= layer (leading-zeros (first %))) entries)
        ;; split the remaining (deeper) entries into the gaps around at-layer keys
        boundaries (map first at-layer)
        deeper (filter #(< (leading-zeros (first %)) layer) entries)  ; never (sorted)
        subtree (fn [lo hi]
                  (let [sub (filter (fn [[k _]]
                                      (and (or (nil? lo) (pos? (compare k lo)))
                                           (or (nil? hi) (neg? (compare k hi)))
                                           (< (leading-zeros k) layer))) entries)]
                    (when (seq sub)
                      (let [[child cblocks] (build-layer sub (dec layer) blocks*)
                            cb (dag-cbor child)
                            cid (cid-of-bytes cb)
                            cs (cid-str cid)]
                        (swap! blocks* assoc cs {:cid cid :bytes cb :node child})
                        (cid-link cid)))))
        ks (vec boundaries)
        ;; left subtree (before first key)
        l (subtree nil (first ks))
        es (loop [i 0 acc [] prevk nil]
             (if (>= i (count at-layer))
               acc
               (let [[k v] (nth at-layer i)
                     pfx (if prevk (common-prefix-len prevk k) 0)
                     t (subtree k (when (< (inc i) (count ks)) (nth ks (inc i))))]
                 (recur (inc i)
                        (conj acc (cond-> {:p pfx
                                           :k (.getBytes (subs k pfx) "UTF-8")
                                           :v (cid-link v)}
                                    t (assoc :t t)))
                        k))))]
    [{:l l :e es} blocks*]))

(defn build-mst
  "Build the MST over record entries → [root-cid-bytes blocks]. entries = seq of
  [key value-cid-bytes]; key = 'collection/rkey'."
  [entries]
  (let [entries (sort-by first entries)
        blocks* (atom {})]
    (if (empty? entries)
      (let [node {:l nil :e []} cb (dag-cbor node) cid (cid-of-bytes cb)]
        [cid {(cid-str cid) {:cid cid :bytes cb :node node}}])
      (let [maxlayer (apply max (map #(leading-zeros (first %)) entries))
            [root _] (build-layer entries maxlayer blocks*)
            cb (dag-cbor root) cid (cid-of-bytes cb)]
        (swap! blocks* assoc (cid-str cid) {:cid cid :bytes cb :node root})
        [cid @blocks*]))))

;; ── Ed25519 signing key (present-only; sealed off-platform in production) ─────

(defn gen-keypair []
  (let [kpg (KeyPairGenerator/getInstance "Ed25519")] (.generateKeyPair kpg)))

(defn sign ^bytes [priv ^bytes msg]
  (let [s (Signature/getInstance "Ed25519")] (.initSign s priv) (.update s msg) (.sign s)))

(defn verify [pub ^bytes msg ^bytes sig]
  (let [s (Signature/getInstance "Ed25519")] (.initVerify s pub) (.update s msg) (.verify s sig)))

(defn- b64e [^bytes b] (.encodeToString (Base64/getEncoder) b))
(defn- b64d ^bytes [^String s] (.decode (Base64/getDecoder) s))

(defn load-or-create-keypair
  "Stable signing key persisted (PKCS8 priv + X509 pub, base64) at `path` — created
  present-only on first boot, reloaded after, so the commit `sig` is stable across
  restarts and the did:web doc can pin its public key. Returns {:private :public}."
  [path]
  (let [f (io/file path)
        kf (KeyFactory/getInstance "Ed25519")]
    (if (.exists f)
      (let [m (edn/read-string (slurp f))]
        {:private (.generatePrivate kf (PKCS8EncodedKeySpec. (b64d (:priv m))))
         :public  (.generatePublic  kf (X509EncodedKeySpec. (b64d (:pub m))))})
      (let [kp (gen-keypair)]
        (io/make-parents f)
        (spit f (pr-str {:priv (b64e (.getEncoded (.getPrivate kp)))
                         :pub  (b64e (.getEncoded (.getPublic kp)))}))
        {:private (.getPrivate kp) :public (.getPublic kp)}))))

;; ── did:key multibase publication of the Ed25519 public key ──────────────────

(def ^:private b58-alphabet "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")

(defn- base58btc [^bytes data]
  (let [zeros (count (take-while zero? (seq data)))
        sb (StringBuilder.)
        fifty8 (BigInteger/valueOf 58)]
    (loop [n (BigInteger. 1 data)]
      (when (pos? (.signum n))
        (.append sb (.charAt b58-alphabet (.intValue (.mod n fifty8))))
        (recur (.divide n fifty8))))
    (dotimes [_ zeros] (.append sb (.charAt b58-alphabet 0)))
    (str/reverse (str sb))))

(defn- raw-ed25519-pub ^bytes [pub]
  (let [enc (.getEncoded pub)] (Arrays/copyOfRange enc (- (alength enc) 32) (alength enc))))

(defn pubkey-multibase
  "atproto did:key Multikey `publicKeyMultibase` for an Ed25519 public key:
  z + base58btc(0xed01 multicodec ++ raw32). Always begins `z6Mk`."
  [pub]
  (let [raw (raw-ed25519-pub pub)
        prefixed (byte-array (+ 2 (alength raw)))]
    (aset-byte prefixed 0 (unchecked-byte 0xed))
    (aset-byte prefixed 1 (unchecked-byte 0x01))
    (System/arraycopy raw 0 prefixed 2 (alength raw))
    (str "z" (base58btc prefixed))))

;; ── commit ───────────────────────────────────────────────────────────────────

(defn make-commit
  "Build + sign the repo commit. Returns [commit-cid-bytes commit-block-bytes commit-map]."
  [did ^bytes data-cid rev prev priv]
  (let [unsigned (cond-> {:did did :version 3 :data (cid-link data-cid) :rev rev}
                   prev (assoc :prev (cid-link prev))
                   (not prev) (assoc :prev nil))
        sig (sign priv (dag-cbor unsigned))
        commit (assoc unsigned :sig sig)
        cb (dag-cbor commit)]
    [(cid-of-bytes cb) cb commit]))

;; ── CAR v1 ───────────────────────────────────────────────────────────────────

(defn- write-varint [^ByteArrayOutputStream out n]
  (loop [n n]
    (if (< n 0x80)
      (.write out (int n))
      (do (.write out (int (bit-or (bit-and n 0x7f) 0x80))) (recur (unsigned-bit-shift-right n 7))))))

(defn- car-block! [^ByteArrayOutputStream out ^bytes cid ^bytes block]
  (let [body (ByteArrayOutputStream.)]
    (.write body cid) (.write body block)
    (let [ba (.toByteArray body)]
      (write-varint out (alength ba))
      (.write out ba))))

(defn car
  "CAR v1 of {root-cid-bytes → block-bytes}, header roots = [root]."
  [^bytes root blocks]
  (let [out (ByteArrayOutputStream.)
        header (dag-cbor {:version 1 :roots [(cid-link root)]})]
    (write-varint out (alength header))
    (.write out header)
    (doseq [[_ {:keys [cid bytes]}] blocks] (car-block! out cid bytes))
    (.toByteArray out)))

;; ── assemble a full repo CAR from PdsStore records ───────────────────────────

(defn build-repo
  "Assemble the signed-commit + MST + record blocks for one repo.
  records = seq of {:uri :value}. Returns
  {:commit-cid str :root str :rev str :blocks {cid-str→{:cid :bytes}}
   :record-cids {collection/rkey→cid-str}}."
  [did records rev priv]
  (let [rec-blocks (atom {})
        rec-cids (atom {})
        entries (for [{:keys [uri value]} records
                      :let [key (->> (str/split uri #"/") (drop 3) (str/join "/"))  ; collection/rkey
                            cb (dag-cbor value)
                            cid (cid-of-bytes cb)]]
                  (do (swap! rec-blocks assoc (cid-str cid) {:cid cid :bytes cb})
                      (swap! rec-cids assoc key (cid-str cid))
                      [key cid]))
        [root mst-blocks] (build-mst (vec entries))
        [commit-cid commit-bytes _] (make-commit did root rev nil priv)
        all (merge @rec-blocks mst-blocks {(cid-str commit-cid) {:cid commit-cid :bytes commit-bytes}})]
    {:commit-cid (cid-str commit-cid) :commit-cid-bytes commit-cid
     :root (cid-str root) :rev rev :blocks all :record-cids @rec-cids}))

(defn repo-car
  "Full repo CAR (commit root). Returns {:car bytes :commit-cid :root :rev :blocks}."
  [did records rev priv]
  (let [{:keys [commit-cid-bytes commit-cid root rev blocks]} (build-repo did records rev priv)]
    {:car (car commit-cid-bytes blocks)
     :commit-cid commit-cid :root root :rev rev :blocks (count blocks)}))

(defn blocks-car
  "CAR carrying a chosen subset of blocks (root = commit). `want` = set of cid-strs;
  nil → all blocks. For sync.getBlocks / sync.getRecord."
  [{:keys [commit-cid-bytes blocks]} want]
  (car commit-cid-bytes (if want (select-keys blocks want) blocks)))
