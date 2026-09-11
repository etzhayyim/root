(ns etzhayyim.pds.repo
  "atproto repo federation primitives — the com.atproto.sync.* read surface so the
  repo can be crawled by a relay / AppView.

  The repo DATA-STRUCTURE layer (deterministic DAG-CBOR, CIDv1(dag-cbor/sha2-256),
  the Merkle Search Tree, and the unsigned-commit object it anchors) is DELEGATED to
  the canonical, golden-verified library `etzhayyim.aozora.repo.*` (app-aozora-repo) —
  whose MST root CIDs are byte-identical to the official `@atproto/repo`
  `MST.create(...).getPointer()` (its mst_test golden vectors were produced by a node
  harness against @atproto/repo + multiformats). This namespace keeps ONLY the
  PDS-specific glue: blob raw-CIDs (codec 0x55), did:key Multikey publication, the
  persisted Ed25519 signing keypair, the inbound CAR→records import, and the
  build-repo / CAR / firehose orchestration.

  Consolidation note: this was previously a SECOND, from-scratch
  implementation of the same primitives. A byte-for-byte conformance gate proved the
  DAG-CBOR / CID / signed-commit encoders were already identical to the lib, but the
  two MSTs DIVERGED — and the prior in-house MST was unverified (its own docstring
  flagged byte-exact validation as 'the remaining federation step'), producing
  non-spec roots. Delegating to the golden-verified lib both removes the duplication
  (~160 LOC) AND fixes spec-conformance. Safe to change: the PDS is not yet
  relay-registered, so no cached external CID depends on the old (wrong) roots.
  A regression test (`repo-conformance-test`) pins this namespace to the lib's
  @atproto golden vectors."
  (:require [clojure.string :as str]
            [clojure.java.io :as io]
            [clojure.edn :as edn]
            [etzhayyim.aozora.repo.dag-cbor :as dc]
            [etzhayyim.aozora.repo.cid :as acid]
            [etzhayyim.aozora.repo.mst :as amst]
            [etzhayyim.aozora.repo.blockstore :as abs]
            [etzhayyim.pds.datom :as d])
  (:import [java.io ByteArrayOutputStream]
           [java.math BigInteger]
           [java.security MessageDigest KeyPairGenerator Signature KeyFactory]
           [java.security.spec PKCS8EncodedKeySpec X509EncodedKeySpec]
           [java.util Base64 Arrays]))

;; ── hashing / base64 ─────────────────────────────────────────────────────────

(defn- sha256 ^bytes [^bytes b]
  (.digest (MessageDigest/getInstance "SHA-256") b))

(defn- b64e [^bytes b] (.encodeToString (Base64/getEncoder) b))
(defn- b64d ^bytes [^String s] (.decode (Base64/getDecoder) s))

;; ── DAG-CBOR + CID (delegated to the canonical lib) ──────────────────────────
;; This namespace threads a CID link as {::cid <binary-cid-bytes>} (the form the
;; CAR / commit-frame / import glue uses); the lib threads it as a CidLink wrapping
;; the base32 cid STRING. `->lib` / `->b` bridge the two reprs at the encode/decode
;; boundary so the glue is unchanged but the bytes are the lib's (golden) bytes.

(defn cid-link [^bytes cid-bytes] {::cid cid-bytes})
(defn cid-link? [x] (and (map? x) (contains? x ::cid)))

(defn cid-str
  "Base32 'b'-multibase string of binary CID bytes (version‖codec‖multihash)."
  [^bytes cid-bytes] (dc/binary->cid-str cid-bytes))

(defn- ->lib
  "Recursively rewrite this ns's {::cid bytes} links to the lib's CidLink(string)."
  [v]
  (cond
    (cid-link? v)   (dc/cid-link (cid-str (::cid v)))
    (map? v)        (into (empty v) (map (fn [[k val]] [k (->lib val)])) v)
    (sequential? v) (mapv ->lib v)
    :else v))

(defn- ->b
  "Recursively rewrite the lib's decoded CidLink(string) back to {::cid bytes}."
  [v]
  (cond
    (dc/cid-link? v) {::cid (dc/cid-str->binary (:cid v))}
    (map? v)         (into {} (map (fn [[k val]] [k (->b val)])) v)
    (sequential? v)  (mapv ->b v)
    :else v))

(defn dag-cbor ^bytes [v] (dc/encode (->lib v)))
(defn dag-cbor-decode [^bytes ba] (->b (dc/decode ba)))

(defn cid-of-bytes
  "Binary CIDv1(dag-cbor / sha2-256) of already-encoded dag-cbor `block`."
  ^bytes [^bytes block]
  (dc/cid-str->binary (acid/cid-of-cbor block)))

(defn raw-cid-of-bytes
  "CIDv1 raw (codec 0x55) / sha2-256 — for blobs (opaque bytes, not dag-cbor).
  PDS-local: the lib is dag-cbor-only, blobs are not repo records."
  ^bytes [^bytes block]
  (let [d (sha256 block)
        b (byte-array (+ 4 (alength d)))]
    (aset-byte b 0 (byte 0x01)) (aset-byte b 1 (byte 0x55))   ; cidv1, raw
    (aset-byte b 2 (byte 0x12)) (aset-byte b 3 (byte 0x20))   ; sha2-256, 32 bytes
    (System/arraycopy d 0 b 4 (alength d))
    b))

(defn block-cid ^bytes [v] (cid-of-bytes (dag-cbor v)))

;; ── MST (delegated to the golden-verified lib over an in-memory blockstore) ───

(defn build-mst
  "Build the AT-Proto MST over record entries → [root-cid-bytes blocks].
  entries = seq of [key value-cid-bytes]; key = 'collection/rkey'. `blocks` is a
  map cid-str→{:cid <bytes> :bytes <bytes>} of the MST NODE blocks (record blocks
  are added by build-repo). Delegates to etzhayyim.aozora.repo.mst (spec-exact)."
  [entries]
  (let [store (abs/->mem-blockstore)
        kvs   (mapv (fn [[k vbytes]] {:key k :val (cid-str vbytes)}) entries)
        root  (amst/data-root! store kvs)
        blocks (into {} (for [[cid a b64] (abs/datoms store) :when (= a :block/bytes)]
                          [cid {:cid (dc/cid-str->binary cid) :bytes (b64d b64)}]))]
    [(dc/cid-str->binary root) blocks]))

;; ── Ed25519 signing key (present-only; sealed off-platform in production) ─────

(defn gen-keypair []
  (let [kpg (KeyPairGenerator/getInstance "Ed25519")] (.generateKeyPair kpg)))

(defn sign ^bytes [priv ^bytes msg]
  (let [s (Signature/getInstance "Ed25519")] (.initSign s priv) (.update s msg) (.sign s)))

(defn verify [pub ^bytes msg ^bytes sig]
  (let [s (Signature/getInstance "Ed25519")] (.initVerify s pub) (.update s msg) (.verify s sig)))

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

(defn- base58btc-decode ^bytes [^String s]
  (let [zeros (count (take-while #(= % \1) s))
        fifty8 (BigInteger/valueOf 58)
        ;; String.indexOf returns -1 (not an exception) for a character
        ;; outside the alphabet, which BigInteger/valueOf happily accepts as
        ;; a valid (negative) digit -- an invalid character used to silently
        ;; decode into a wrong BigInteger instead of raising anything. The
        ;; sibling copy of this function in keys.clj already guards this;
        ;; this copy had drifted out of sync.
        bi (reduce (fn [acc c]
                     (let [d (.indexOf b58-alphabet (int c))]
                       (when (neg? d)
                         (throw (ex-info "bad base58 character" {:char c})))
                       (.add (.multiply acc fifty8) (BigInteger/valueOf d))))
                   BigInteger/ZERO (seq s))
        ba (.toByteArray bi)
        ba (if (and (> (alength ba) 1) (zero? (aget ba 0))) (Arrays/copyOfRange ba 1 (alength ba)) ba)]
    (byte-array (concat (repeat zeros (byte 0)) (seq ba)))))

(defn multibase->pubkey
  "Reconstruct the Ed25519 public key a RELAY derives from the did:web Multikey
  `publicKeyMultibase` — the inverse of pubkey-multibase. Lets a relay verify the
  repo commit `sig` using only the published did.json."
  [^String mb]
  (let [decoded (base58btc-decode (subs mb 1))                ; drop 'z'
        raw (Arrays/copyOfRange decoded 2 (alength decoded))  ; drop 0xed01 multicodec
        x509 (byte-array (map unchecked-byte
                              (concat [0x30 0x2a 0x30 0x05 0x06 0x03 0x2b 0x65 0x70 0x03 0x21 0x00]
                                      (seq raw))))]
    (.generatePublic (KeyFactory/getInstance "Ed25519") (X509EncodedKeySpec. x509))))

;; ── commit ───────────────────────────────────────────────────────────────────

(defn make-commit
  "Build + sign the repo commit. Returns [commit-cid-bytes commit-block-bytes commit-map].
  `signer` is either an Ed25519 PrivateKey (the PDS self-repo key, signed via `sign`) OR
  a fn `(fn [^bytes msg] -> ^bytes sig)` — pass the latter to sign the commit with the
  ACTOR's own sealed P-256 key (Path B), so a relay verifies the commit against the
  actor's published did:web Multikey, not a shared PDS key. The unsigned-commit shape
  and signed bytes are byte-identical to etzhayyim.aozora.repo.commit (conformance-pinned)."
  [did ^bytes data-cid rev prev signer]
  (let [unsigned (cond-> {:did did :version 3 :data (cid-link data-cid) :rev rev}
                   prev (assoc :prev (cid-link prev))
                   (not prev) (assoc :prev nil))
        sig (if (fn? signer) (signer (dag-cbor unsigned)) (sign signer (dag-cbor unsigned)))
        commit (assoc unsigned :sig sig)
        cb (dag-cbor commit)]
    [(cid-of-bytes cb) cb commit]))

;; ── CAR v1 (PDS-local: A has no inbound CAR parser; B owns the import side) ───

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

(defn- read-varint [^bytes ba pos]
  (loop [shift 0 pos pos acc 0]
    (let [b (bit-and (aget ba pos) 0xff)]
      (if (zero? (bit-and b 0x80))
        [(bit-or acc (bit-shift-left b shift)) (inc pos)]
        (recur (+ shift 7) (inc pos) (bit-or acc (bit-shift-left (bit-and b 0x7f) shift)))))))

(defn car-parse
  "Parse a CAR v1 → {:header <decoded> :blocks {cid-str → bytes}}."
  [^bytes ba]
  (let [[hlen p0] (read-varint ba 0)
        header (dag-cbor-decode (Arrays/copyOfRange ba p0 (+ p0 hlen)))]
    (loop [pos (+ p0 hlen) blocks {}]
      (if (>= pos (alength ba))
        {:header header :blocks blocks}
        (let [[blen bp] (read-varint ba pos)
              end (+ bp blen)
              ;; CIDv1: version, codec, hash-fn, digest-len varints, then digest
              [_ p1] (read-varint ba bp)
              [_ p2] (read-varint ba p1)
              [_ p3] (read-varint ba p2)
              [dlen p4] (read-varint ba p3)
              cid-end (+ p4 dlen)
              cid (cid-str (Arrays/copyOfRange ba bp cid-end))
              block (Arrays/copyOfRange ba cid-end end)]
          (recur end (assoc blocks cid block)))))))

;; ── MST walk + repo import (inverse of build-repo) ───────────────────────────

(defn- cidk [link] (cid-str (::cid link)))   ; cid-str of a decoded cid-link

(defn mst-records
  "In-order [key value-cid-str] pairs from an MST rooted at `node-cid`, undoing the
  prefix compression (entry `p` = bytes shared with the previous key in the node)."
  [blocks node-cid]
  (let [node (dag-cbor-decode (get blocks node-cid))
        l (get node "l")]
    (loop [es (get node "e")
           prevkey ""
           out (if l (vec (mst-records blocks (cidk l))) [])]
      (if (empty? es)
        out
        (let [e (first es)
              ;; key = prevkey[0:p] ‖ suffix-bytes (p counts UTF-8 BYTES, lib-canonical)
              prevb (.getBytes ^String prevkey "UTF-8")
              keyb (let [pfx (Arrays/copyOfRange prevb 0 (int (get e "p")))
                         suf ^bytes (get e "k")
                         out (byte-array (+ (alength pfx) (alength suf)))]
                     (System/arraycopy pfx 0 out 0 (alength pfx))
                     (System/arraycopy suf 0 out (alength pfx) (alength suf))
                     out)
              key (String. ^bytes keyb "UTF-8")
              t (get e "t")
              out (conj out [key (cidk (get e "v"))])
              out (if t (into out (mst-records blocks (cidk t))) out)]
          (recur (rest es) key out))))))

(defn import-records
  "Parse an incoming repo CAR → {:did :rev :records [[collection rkey value] …]}.
  Walks the commit → MST root → record blocks. Inverse of repo-car."
  [^bytes car-bytes]
  (let [{:keys [header blocks]} (car-parse car-bytes)
        commit (dag-cbor-decode (get blocks (cidk (first (get header "roots")))))
        did (get commit "did")
        records (for [[key vcid] (mst-records blocks (cidk (get commit "data")))
                      :let [[collection rkey] (str/split key #"/" 2)]]
                  [collection rkey (dag-cbor-decode (get blocks vcid))])]
    {:did did :rev (get commit "rev") :records (vec records)}))

;; ── assemble a full repo CAR from PdsStore records ───────────────────────────

(defn build-repo
  "Assemble the signed-commit + MST + record blocks for one repo.
  records = seq of {:uri :value}. Returns
  {:commit-cid str :root str :rev str :blocks {cid-str→{:cid :bytes}}
   :record-cids {collection/rkey→cid-str}}. `signer` = an Ed25519 PrivateKey OR an
  actor sign-fn `(fn [^bytes msg] -> ^bytes sig)` (see make-commit)."
  [did records rev signer]
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
        [commit-cid commit-bytes _] (make-commit did root rev nil signer)
        all (merge @rec-blocks mst-blocks {(cid-str commit-cid) {:cid commit-cid :bytes commit-bytes}})]
    {:commit-cid (cid-str commit-cid) :commit-cid-bytes commit-cid
     :root (cid-str root) :rev rev :blocks all :record-cids @rec-cids}))

(defn repo-car
  "Full repo CAR (commit root). Returns {:car bytes :commit-cid :root :rev :blocks}.
  `signer` = an Ed25519 PrivateKey OR an actor sign-fn (see build-repo / make-commit)."
  [did records rev signer]
  (let [{:keys [commit-cid-bytes commit-cid root rev blocks]} (build-repo did records rev signer)]
    {:car (car commit-cid-bytes blocks)
     :commit-cid commit-cid :root root :rev rev :blocks (count blocks)}))

(defn blocks-car
  "CAR carrying a chosen subset of blocks (root = commit). `want` = set of cid-strs;
  nil → all blocks. For sync.getBlocks / sync.getRecord."
  [{:keys [commit-cid-bytes blocks]} want]
  (car commit-cid-bytes (if want (select-keys blocks want) blocks)))

;; ── subscribeRepos firehose frame ────────────────────────────────────────────
;; Wire format: dag-cbor(header {:op 1 :t "#commit"}) ++ dag-cbor(body). Sent as
;; one binary websocket message. `blocks` carries the commit as a CAR so a relay
;; can ingest without a follow-up getRepo.

(defn- concat-bytes [^bytes a ^bytes b]
  (let [out (byte-array (+ (alength a) (alength b)))]
    (System/arraycopy a 0 out 0 (alength a))
    (System/arraycopy b 0 out (alength a) (alength b))
    out))

(defn commit-frame
  "A #commit firehose frame for the current head of `build` (from build-repo).
  `ops` = seq of {:action :path :cid-bytes-or-nil}."
  [seq did build ops time-iso]
  (let [header (dag-cbor {:op 1 :t "#commit"})
        body (dag-cbor {:seq seq :rebase false :tooBig false
                        :repo did
                        :commit (cid-link (:commit-cid-bytes build))
                        :rev (:rev build) :since nil
                        :blocks (blocks-car build nil)
                        :ops (vec (for [{:keys [action path cid-bytes]} ops]
                                    {:action action :path path
                                     :cid (if cid-bytes (cid-link cid-bytes) nil)}))
                        :blobs [] :time time-iso})]
    (concat-bytes header body)))
