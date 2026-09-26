(ns did-web.kotoba
  "kotoba member-signed block CAS — faithful cljs port of src/kotoba-publish.ts
  (ADR-2605312345 / 2605231525). The browser kotoba node member-SIGNS its Datom
  log root (ed25519); this verifies the signature (the server never signs — it
  cannot mint a root), stores content-addressed delta blocks in KV, advances the
  published head under check-and-set, and records a suppressable encrypted IP
  attestation. All LOGIC is cljs; only the host primitives (Web Crypto, the KV
  binding) are called via interop — exactly as the TS did.

  KV layout (ACTOR_KV with prefixes):
    kblk:<cid>             → block bytes (hex)
    kroot:<graph>          → manifest {root, blocks[], did, updatedAt, ipnsRecord?}
    kattest:<graph>:<root> → {did, ts, ipHash, ipPrefix, ipEnc?}
    kstats:<graph> / krl:<graph>:<did> → best-effort counters / token bucket"
  (:require [goog.object :as gobj]))

;; ── KV interop (rename-safe; .call binds `this` to the KV namespace) ──────────
(defn- kv-get
  ([kv k]   (.call (gobj/get kv "get") kv k))
  ([kv k t] (.call (gobj/get kv "get") kv k t)))
(defn- kv-put [kv k v] (.call (gobj/get kv "put") kv k v))

(def ^:private json-headers
  {"content-type" "application/json; charset=utf-8" "x-kotoba-publish" "1"})

(defn- jr
  ([obj status] (jr obj status json-headers))
  ([obj status headers]
   (js/Response. (js/JSON.stringify (clj->js obj))
                 #js {:status status :headers (clj->js headers)})))

;; ── byte helpers (faithful to kotoba-publish.ts) ─────────────────────────────
(def ^:private b32 "abcdefghijklmnopqrstuvwxyz234567")

(defn base32-decode [s]
  (let [out #js []]
    (loop [chs (seq s), bits 0, value 0]
      (if (empty? chs)
        (js/Uint8Array.from out)
        (let [idx (.indexOf b32 (first chs))]
          (when (neg? idx)
            ;; A character outside the b32 alphabet used to be silently
            ;; SKIPPED instead of rejected -- unlike the sibling, already-
            ;; fixed decoder in kotoba-lang/io-multiformats. root-multibase
            ;; (the caller in verify-root-sig) is untrusted, attacker-
            ;; controlled HTTP request body: since a corrupted string with
            ;; extraneous junk characters spliced in could decode to the
            ;; SAME bytes as the original, an attacker could pair a
            ;; corrupted root string with a signature that's still valid
            ;; for the (unchanged) decoded bytes, while store-check-advance
            ;; stores the corrupted STRING (not the original) as the new
            ;; manifest root -- silently accepted instead of rejected as
            ;; malformed input.
            (throw (js/Error. (str "did-web: invalid base32 character: " (first chs)))))
          (let [value (bit-or (bit-shift-left value 5) idx)
                bits (+ bits 5)]
            (if (>= bits 8)
              (do (.push out (bit-and (unsigned-bit-shift-right value (- bits 8)) 0xff))
                  (recur (rest chs) (- bits 8) value))
              (recur (rest chs) bits value))))))))

(defn- hex->bytes [h]
  (let [clean (.trim h)
        n (quot (.-length clean) 2)
        a (js/Uint8Array. n)]
    (dotimes [i n]
      (aset a i (js/parseInt (.substr clean (* i 2) 2) 16)))
    a))

(defn- bytes->hex [b]
  (apply str (map (fn [x] (.padStart (.toString x 16) 2 "0")) (array-seq b))))

(defn- b64 [bytes]
  (js/btoa (apply str (map js/String.fromCharCode (array-seq bytes)))))

;; ── ed25519 verify of the member signature over the raw root CID bytes ────────
(defn verify-root-sig
  "Promise<boolean>. did = did:key:z<hex pubkey>; root = b<base32 CID>; sig = hex."
  [did root-multibase sig-hex]
  (-> (js/Promise.resolve nil)
      (.then
       (fn [_]
         (cond
           (not (.startsWith did "did:key:z")) (js/Promise.resolve false)
           :else
           (let [pub (hex->bytes (.slice did (.-length "did:key:z")))]
             (cond
               (not= (alength pub) 32) (js/Promise.resolve false)
               (not (.startsWith root-multibase "b")) (js/Promise.resolve false)
               :else
               (let [root-bytes (base32-decode (.slice root-multibase 1))
                     sig (hex->bytes sig-hex)]
                 (if (not= (alength sig) 64)
                   (js/Promise.resolve false)
                   (-> (js/crypto.subtle.importKey "raw" pub #js {:name "Ed25519"} false #js ["verify"])
                       (.then (fn [key]
                                (js/crypto.subtle.verify #js {:name "Ed25519"} key sig root-bytes)))))))))))
      (.catch (fn [_] false))))

(defn- sha256-hex [s]
  (-> (js/crypto.subtle.digest "SHA-256" (.encode (js/TextEncoder.) s))
      (.then (fn [d] (bytes->hex (js/Uint8Array. d))))))

(defn- encrypt-ip
  "Promise<{:iv :ct}|nil> — AES-256-GCM under the operator oversight key, if set."
  [env ip]
  (let [k (gobj/get env "KOTOBA_ATTEST_KEY")]
    (if-not k
      (js/Promise.resolve nil)
      (-> (js/Promise.resolve nil)
          (.then
           (fn [_]
             (let [raw (js/Uint8Array.from (js/atob k) (fn [c] (.charCodeAt c 0)))]
               (if (not= (alength raw) 32)
                 (js/Promise.resolve nil)
                 (-> (js/crypto.subtle.importKey "raw" raw #js {:name "AES-GCM"} false #js ["encrypt"])
                     (.then (fn [key]
                              (let [iv (js/crypto.getRandomValues (js/Uint8Array. 12))]
                                (-> (js/crypto.subtle.encrypt #js {:name "AES-GCM" :iv iv} key
                                                              (.encode (js/TextEncoder.) ip))
                                    (.then (fn [ct]
                                             #js {:iv (b64 iv)
                                                  :ct (b64 (js/Uint8Array. ct))})))))))))))
          (.catch (fn [_] nil))))))

(defn ip-prefix [ip]
  (cond
    (.includes ip ".") (str (.join (.slice (.split ip ".") 0 3) ".") ".0/24")
    (.includes ip ":") (str (.join (.slice (.split ip ":") 0 3) ":") "::/48")
    :else ""))

(defn- now-iso [] (.toISOString (js/Date.)))

;; ── block.put ────────────────────────────────────────────────────────────────

(defn- bump-stat [kv graph field extra]
  (-> (kv-get kv (str "kstats:" graph))
      (.then (fn [raw]
               (let [s (if raw (js/JSON.parse raw) #js {})
                     cur (or (gobj/get s field) 0)]
                 (gobj/set s field (inc cur))
                 (when extra (gobj/extend s extra))
                 (kv-put kv (str "kstats:" graph) (js/JSON.stringify s)))))
      (.catch (fn [_] nil))))

(defn- valid-blocks? [blocks]
  (every? (fn [b]
            (and b (string? (gobj/get b "cid")) (string? (gobj/get b "hex"))
                 (<= (.-length (gobj/get b "hex")) 4000000)))
          blocks))

(defn- consistent-ipns? [rec root did]
  (and rec (object? rec)
       (= (gobj/get rec "value") root)
       (let [c (gobj/get rec "controller_did")] (or (undefined? c) (= c did)))
       (string? (gobj/get rec "signature_multibase"))
       (string? (gobj/get rec "public_key_multibase"))))

(defn- rate-limit
  "Promise<{:limited bool :tokens n}>. Best-effort per-DID token bucket on actual
  head advances. Faithful to kotoba-publish.ts (CAP 12, refill 2500ms)."
  [kv graph did]
  (let [CAP 12, REFILL 2500
        now (js/Date.now)
        rl-key (str "krl:" graph ":" (or did "anon"))]
    (-> (kv-get kv rl-key)
        (.then (fn [raw] (if raw (js/JSON.parse raw) #js {:tokens CAP :ts now})))
        (.catch (fn [_] #js {:tokens CAP :ts now}))
        (.then (fn [b]
                 (let [refill (js/Math.floor (/ (- now (gobj/get b "ts")) REFILL))]
                   (when (pos? refill)
                     (gobj/set b "tokens" (js/Math.min CAP (+ (gobj/get b "tokens") refill)))
                     (gobj/set b "ts" now))
                   (if (< (gobj/get b "tokens") 1)
                     (-> (kv-put kv rl-key (js/JSON.stringify b))
                         (.then (fn [_] (bump-stat kv graph "rateLimited" nil)))
                         (.then (fn [_] {:limited true})))
                     (do (gobj/set b "tokens" (dec (gobj/get b "tokens")))
                         (-> (kv-put kv rl-key (js/JSON.stringify b))
                             (.then (fn [_] {:limited false :tokens (gobj/get b "tokens")})))))))))))

;; flat async helpers (each shallow) so the publish pipeline avoids deep nesting

(defn- store-blocks [kv blocks]
  (js/Promise.all
   (apply array (map (fn [b] (kv-put kv (str "kblk:" (gobj/get b "cid")) (gobj/get b "hex")))
                     (array-seq blocks)))))

(defn- advance-head [kv graph root did blocks body]
  (let [manifest #js {:graph graph :root root
                      :blocks (apply array (map #(gobj/get % "cid") (array-seq blocks)))
                      :did did :updatedAt (now-iso)}
        rec (gobj/get body "ipnsRecord")]
    (when (consistent-ipns? rec root did) (gobj/set manifest "ipnsRecord" rec))
    (-> (kv-put kv (str "kroot:" graph) (js/JSON.stringify manifest))
        (.then (fn [_] (bump-stat kv graph "advances" #js {:lastAdvanceAt (now-iso) :root root}))))))

(defn- record-attest
  "Promise<{:ip-hash :ip-prefix :ip-enc}> — suppressable encrypted IP attestation."
  [kv env graph did root body request]
  (let [ip (or (.get (.-headers request) "cf-connecting-ip")
               (.get (.-headers request) "x-forwarded-for") "")]
    (-> (if (seq ip) (sha256-hex (str graph ":" ip)) (js/Promise.resolve ""))
        (.then (fn [ip-hash]
                 (-> (if (seq ip) (encrypt-ip env ip) (js/Promise.resolve nil))
                     (.then (fn [ip-enc]
                              (let [attest #js {:did did :root root
                                                :edit (or (gobj/get body "edit") nil)
                                                :ts (now-iso) :ipHash ip-hash :ipPrefix (ip-prefix ip)}]
                                (when ip-enc (gobj/set attest "ipEnc" ip-enc))
                                (.then (kv-put kv (str "kattest:" graph ":" root) (js/JSON.stringify attest))
                                       (fn [_] {:ip-hash ip-hash :ip-prefix (ip-prefix ip) :ip-enc ip-enc})))))))))))

(defn- advance-and-respond
  "Rate-limit → advance head → attest → 200. Returns Promise<Response>."
  [kv env graph root did blocks body request]
  (-> (rate-limit kv graph did)
      (.then (fn [rl]
               (if (:limited rl)
                 (jr {:error "RateLimited" :message "publish rate exceeded — retry later" :retryAfterMs 2500}
                     429 (assoc json-headers "retry-after" "3"))
                 (-> (advance-head kv graph root did blocks body)
                     (.then (fn [_] (record-attest kv env graph did root body request)))
                     (.then (fn [a]
                              (jr {:ok true :root root :storedBlocks (alength blocks) :rlTokens (:tokens rl)
                                   :attest {:ipHash (:ip-hash a) :ipPrefix (:ip-prefix a)
                                            :ipEncrypted (boolean (:ip-enc a))}} 200)))))))))

(defn- store-check-advance
  "After signature verify: store blocks, CAS-check the head, advance or 409."
  [kv env graph root did prev-root blocks body request]
  (-> (store-blocks kv blocks)
      (.then (fn [_] (kv-get kv (str "kroot:" graph))))
      (.then (fn [prev-raw]
               (let [cur (when prev-raw (try (js/JSON.parse prev-raw) (catch :default _ nil)))
                     cur-root (when cur (gobj/get cur "root"))]
                 (if (and cur-root (not= cur-root prev-root))
                   (-> (bump-stat kv graph "conflicts" nil)
                       (.then (fn [_] (jr {:error "Conflict" :message "root advanced — rebase and retry"
                                           :currentRoot cur-root} 409))))
                   (advance-and-respond kv env graph root did blocks body request)))))))

(defn handle-block-put [request env]
  (let [kv (gobj/get env "ACTOR_KV")]
    (if-not kv
      (js/Promise.resolve (jr {:error "PublishUnavailable" :message "ACTOR_KV not bound"} 503))
      (-> (.catch (.json request) (fn [_] ::bad-json))
          (.then
           (fn [body]
             (if (= body ::bad-json)
               (jr {:error "BadRequest" :message "invalid JSON"} 400)
               (let [graph (or (gobj/get body "graph") "yoro-social-v1")
                     root (gobj/get body "root")
                     did (gobj/get body "did")
                     sig (gobj/get body "sig")
                     prev-root (gobj/get body "prevRoot")
                     blocks-js (gobj/get body "blocks")
                     blocks (if (array? blocks-js) blocks-js #js [])]
                 (cond
                   (or (not root) (not did) (not sig))
                   (jr {:error "BadRequest" :message "root/did/sig required"} 400)
                   (> (alength blocks) 64)
                   (jr {:error "TooManyBlocks" :max 64} 413)
                   (not (valid-blocks? (array-seq blocks)))
                   (jr {:error "BadBlock"} 413)
                   :else
                   (.then (verify-root-sig did root sig)
                          (fn [ok?]
                            (if-not ok?
                              (jr {:error "BadSignature" :message "ed25519 verify failed"} 401)
                              (store-check-advance kv env graph root did prev-root blocks body request))))))))) ))))

;; ── block.has / root / stats / serve ─────────────────────────────────────────

(defn handle-block-has [request env]
  (let [kv (gobj/get env "ACTOR_KV")]
    (-> (.catch (.json request) (fn [_] ::bad))
        (.then
         (fn [body]
           (if (= body ::bad)
             (js/Promise.resolve (jr {:error "BadRequest"} 400))
             (let [cids-js (gobj/get body "cids")
                   cids (if (array? cids-js)
                          (->> (array-seq cids-js) (filter string?) (take 4096) vec)
                          [])]
               (if-not kv
                 (jr {:missing (apply array cids)} 200)
                 (-> (js/Promise.all (apply array (map (fn [c] (.then (kv-get kv (str "kblk:" c) "stream")
                                                                      (fn [v] (when v c)))) cids)))
                     (.then (fn [present]
                              (let [has (set (remove nil? (array-seq present)))]
                                (jr {:missing (apply array (remove has cids))} 200)))))))))))) )

(defn handle-root-get [url env]
  (let [kv (gobj/get env "ACTOR_KV")
        graph (or (.get (.-searchParams url) "graph") "yoro-social-v1")
        genesis {:graph graph :root ""
                 :note "no published root yet — client should fall back to the static genesis pointer"}]
    (if-not kv
      (js/Promise.resolve (jr genesis 200))
      (-> (kv-get kv (str "kroot:" graph))
          (.then (fn [raw]
                   (if raw
                     (js/Response. raw #js {:status 200 :headers (clj->js json-headers)})
                     (jr (assoc genesis :graph graph) 200))))))))

(defn handle-stats-get [url env]
  (let [kv (gobj/get env "ACTOR_KV")
        graph (or (.get (.-searchParams url) "graph") "yoro-social-v1")]
    (if-not kv
      (js/Promise.resolve (jr {:error "StatsUnavailable" :message "ACTOR_KV not bound"} 503))
      (-> (kv-get kv (str "kstats:" graph))
          (.then (fn [raw] (if raw (try (js/JSON.parse raw) (catch :default _ #js {})) #js {})))
          (.catch (fn [_] #js {}))
          (.then (fn [s]
                   (-> (kv-get kv (str "kroot:" graph))
                       (.then (fn [root-raw]
                                (let [m (when root-raw (try (js/JSON.parse root-raw) (catch :default _ nil)))
                                      out (js/Object.assign #js {:graph graph} s
                                                            #js {:root (or (when m (gobj/get m "root")) "")
                                                                 :updatedAt (or (when m (gobj/get m "updatedAt")) "")})]
                                  (js/Response. (js/JSON.stringify out)
                                                #js {:status 200 :headers (clj->js json-headers)}))))))))) ))

(defn serve-block-from-kv
  "Promise<Response|nil> — serve a dynamically published block from KV."
  [cid env]
  (let [kv (gobj/get env "ACTOR_KV")]
    (if-not kv
      (js/Promise.resolve nil)
      (-> (kv-get kv (str "kblk:" cid))
          (.then (fn [hex]
                   (when hex
                     (js/Response. (hex->bytes hex)
                                   #js {:status 200
                                        :headers #js {"content-type" "application/octet-stream"
                                                      "cache-control" "public, max-age=31536000, immutable"
                                                      "x-kotoba-block" "kv"}}))))))))
