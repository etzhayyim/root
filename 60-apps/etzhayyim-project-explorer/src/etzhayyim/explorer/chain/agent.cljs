(ns etzhayyim.explorer.chain.agent
  "Browser-side verification of a Holochain-iso AGENT registration (the
   agent-centric way; ADR-2605231400 / 2606015600). Given an agent's
   self-published genesis source-chain doc, the browser independently verifies,
   with NO server in the trust path:

     1. content-address — recompute the genesis :cid from its datoms via the
        canonical kotoba.datom codec (commit-DAG integrity),
     2. self-signature  — the agent's OWN ed25519 key (decoded from its did:key)
        signed that :cid  (Web Crypto, proves authorship),
     3. membrane        — a witness ed25519 key attested the same :cid
        (proves it passed the validation membrane).

   This is exactly Holochain's 'validate a source-chain entry from its author's
   key' — done client-side."
  (:require [kotoba.datom :as kd]
            [clojure.string :as str]))

;; ── base58btc decode (no BigInteger in cljs — base-256 accumulation) ─────────
(def ^:private B58 "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")

(defn base58-decode
  "base58btc string → Uint8Array of bytes."
  [s]
  (let [bytes (volatile! [0])]
    (doseq [c s]
      (let [val (.indexOf B58 (str c))]
        (when (neg? val) (throw (js/Error. (str "bad base58 char: " c))))
        (let [b @bytes
              carried (loop [i 0 carry val acc (transient [])]
                        (if (< i (count b))
                          (let [x (+ (* (nth b i) 58) carry)]
                            (recur (inc i) (bit-shift-right x 8)
                                   (conj! acc (bit-and x 0xff))))
                          [(persistent! acc) carry]))
              [b' carry] carried
              b' (loop [b b' carry carry]
                   (if (pos? carry)
                     (recur (conj b (bit-and carry 0xff)) (bit-shift-right carry 8))
                     b))]
          (vreset! bytes b'))))
    ;; leading '1's → leading zero bytes; result is little-endian, reverse it
    (let [zeros (count (take-while #(= \1 %) s))
          rev (vec (reverse @bytes))
          ;; drop a possible extra leading 0 from the seed, then re-pad
          trimmed (drop-while zero? rev)]
      (js/Uint8Array.from (clj->js (concat (repeat zeros 0) trimmed))))))

(defn did-key->raw-pub
  "did:key:z… → Uint8Array of the raw 32-byte ed25519 public key (drop the
   0xed 0x01 multicodec prefix)."
  [did]
  (let [mb (subs did (count "did:key:z"))
        decoded (base58-decode mb)]
    (.slice decoded 2)))                       ; drop multicodec 0xed01

(defn- b64->bytes [b64]
  (let [bin (js/atob b64)
        n (.-length bin)
        arr (js/Uint8Array. n)]
    (dotimes [i n] (aset arr i (.charCodeAt bin i)))
    arr))

(defn- utf8 [s] (.encode (js/TextEncoder.) s))

(defn- verify-sig
  "Web Crypto Ed25519 verify → Promise<bool>. Resolves false if the host lacks
   Ed25519 in SubtleCrypto (older browsers) — surfaced as :crypto-unsupported."
  [did msg-str sig-b64]
  (let [subtle (.. js/crypto -subtle)]
    (-> (.importKey subtle "raw" (did-key->raw-pub did)
                    #js {:name "Ed25519"} false #js ["verify"])
        (.then (fn [key]
                 (.verify subtle #js {:name "Ed25519"} key
                          (b64->bytes sig-b64) (utf8 msg-str))))
        (.catch (fn [_] ::unsupported)))))

(defn- vouch-preimage [{:keys [att aud exp iss]}]
  (kd/canonical-json {"att" att "aud" aud "exp" exp "iss" iss}))

(defn verify-doc
  "Independently verify an agent's registration the way the validating membrane
   does, in-browser, against the published member roster + validator set →
   Promise of {:handle :did :cid-ok :self-signed :vouch-ok :quorum :dht-replicas
   :validated? :reasons :crypto?}.

   roster = set of member did:keys, validators = set of validator did:keys."
  [doc {:keys [roster validators] :or {roster #{} validators #{}}}]
  (let [g (first (:chain doc))
        {:keys [datoms cid prev author-sig]} g
        cid-ok (= cid (kd/tx-cid datoms (or prev "")))
        membrane (:membrane doc)
        vouch (:vouch membrane)
        atts (or (:attestations membrane) [])
        warrants (or (:warrants membrane) [])
        threshold (get-in membrane [:quorum :threshold] 2)
        self-p (verify-sig (:agent/did doc) cid author-sig)
        ;; member vouch: signature valid AND issuer is a roster member AND aud=agent
        vouch-p (if vouch
                  (-> (verify-sig (:iss vouch) (vouch-preimage vouch) (:sig vouch))
                      (.then (fn [ok] (and (true? ok)
                                           (contains? roster (:iss vouch))
                                           (= (:aud vouch) (:agent/did doc))))))
                  (js/Promise.resolve false))
        ;; each attestation: validator signed the cid AND is in the validator set
        att-ps (mapv (fn [a]
                       (-> (verify-sig (:validator a) cid (:sig a))
                           (.then (fn [ok] (and (true? ok) (contains? validators (:validator a)))))))
                     atts)]
    (-> (js/Promise.all (clj->js (concat [self-p vouch-p] att-ps)))
        (.then (fn [results]
                 (let [r (vec (array-seq results))
                       self (nth r 0)
                       vouch-ok (nth r 1)
                       att-results (subvec r 2)
                       valid-count (count (filter true? att-results))]
                   {:handle (:agent/handle doc)
                    :did (:agent/did doc)
                    :cid-ok cid-ok
                    :crypto? (not= self ::unsupported)
                    :self-signed (true? self)
                    :vouch-ok (true? vouch-ok)
                    :vouch-iss (:iss vouch)
                    :quorum {:valid-count valid-count :threshold threshold
                             :met? (>= valid-count threshold)}
                    :dht-replicas (count (get-in doc [:dht :replicas]))
                    :validated? (get-in membrane [:quorum :met?])
                    :reasons (vec (distinct (map :reason warrants)))}))))))
