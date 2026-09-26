(ns did-web.ipfs
  "Trustless /ipfs/<cid> gateway — faithful cljs port of the inline handler in
  src/worker.ts (ADR-2606014600 / 2606015200). Fetches content-addressed bytes
  from UNTRUSTED upstream gateways and VERIFIES they hash to the requested CID
  before serving (raw single-block via sha2-256; dag-pb UnixFS via CAR + DAG
  walk). The CID is the trust anchor — no server key (ADR-2605231525)."
  (:require [clojure.string :as str]
            [goog.object :as gobj]
            [did-web.codec :as codec]))

(def ^:private actor-json-headers
  {"content-type" "application/json; charset=utf-8"
   "cache-control" "public, max-age=60, must-revalidate"
   "access-control-allow-origin" "*"
   "x-content-type-options" "nosniff"
   "strict-transport-security" "max-age=31536000; includeSubDomains"
   "x-etzhayyim-no-cookie" "1"})

(defn- json-resp [obj status headers]
  (js/Response. (str (js/JSON.stringify obj) "\n")
                #js {:status status :headers (clj->js headers)}))

(defn- ipfs-headers [cid len content-type verified]
  {"content-type" content-type
   "content-length" (str len)
   "cache-control" "public, max-age=31536000, immutable"
   "access-control-allow-origin" "*"
   "x-content-type-options" "nosniff"
   "x-etzhayyim-cid" cid
   "x-etzhayyim-cid-verified" verified
   "x-etzhayyim-no-cookie" "1"
   "strict-transport-security" "max-age=31536000; includeSubDomains"})

(defn- detect-ct [^js buf]
  (let [n (min 4 (.-byteLength buf))
        b (js/Uint8Array. buf 0 n)]
    (if (and (>= n 4)
             (= (aget b 0) 0x00) (= (aget b 1) 0x61)
             (= (aget b 2) 0x73) (= (aget b 3) 0x6d))
      "application/wasm"
      "application/octet-stream")))

;; ── sha2-256 content-address (async) ─────────────────────────────────────────

(defn- cid-v1-raw
  "Promise<string> — the raw/sha2-256 CIDv1 of `buf` (ArrayBuffer|Uint8Array)."
  [buf]
  (.then (js/crypto.subtle.digest "SHA-256" buf)
         (fn [d]
           (let [digest (js/Uint8Array. d)
                 cid (js/Uint8Array. (+ 4 (alength digest)))]
             (.set cid #js [0x01 0x55 0x12 0x20] 0)
             (.set cid digest 4)
             (str "b" (codec/base32 cid))))))

(defn- verify-raw-cid [cid buf]
  (.then (cid-v1-raw buf) (fn [computed] (= computed cid))))

(defn- parse-and-verify-car
  "Promise<{cid-str → {:data :codec}}> — parse a CARv1, verifying every block's
  sha2-256 multihash. Faithful to car.ts parseAndVerifyCar."
  [car]
  (let [[hdr-len pos0] (codec/read-varint car 0)
        start (+ pos0 hdr-len)
        n (alength car)]
    (letfn [(step [pos blocks]
              (if (>= pos n)
                (js/Promise.resolve blocks)
                (let [[sec-len pos] (codec/read-varint car pos)
                      sec-end (+ pos sec-len)
                      cid (codec/parse-cid car pos)
                      data (.subarray car (:end cid) sec-end)]
                  (when (not= (:mh-code cid) codec/sha2-256-code)
                    (throw (js/Error. (str "unsupported multihash 0x" (.toString (:mh-code cid) 16)))))
                  (.then (js/crypto.subtle.digest "SHA-256" data)
                         (fn [d]
                           (let [got (js/Uint8Array. d)]
                             (when-not (codec/eq-bytes? got (:digest cid))
                               (throw (js/Error. (str "block hash mismatch for " (:cid-str cid)))))
                             (step sec-end (assoc blocks (:cid-str cid)
                                                  {:data data :codec (:codec cid)}))))))))]
      (step start {}))))

(defn- verify-car-to-bytes
  "Promise<Uint8Array> — verify a CARv1 + trustlessly reconstruct `root-cid`."
  [root-cid car]
  (.then (parse-and-verify-car car)
         (fn [blocks]
           (when-not (contains? blocks root-cid)
             (throw (js/Error. (str "requested root " root-cid " not present in CAR"))))
           (codec/reassemble root-cid blocks))))

;; ── gateway fetch loop ───────────────────────────────────────────────────────

(defn- default-gateways []
  ["https://{cid}.ipfs.dweb.link" "https://ipfs.io/ipfs/{cid}"])

(defn- gateways-from-env [env]
  (let [raw (gobj/get env "IPFS_GATEWAYS")]
    (if (and raw (seq raw))
      (->> (str/split raw #",") (map str/trim) (remove empty?) vec)
      (default-gateways))))

(defn- ->ab
  "Normalize a reassembled Uint8Array to a tight ArrayBuffer (matches the TS
  bytes.buffer.slice(byteOffset, byteOffset+byteLength))."
  [u]
  (.slice (.-buffer u) (.-byteOffset u) (+ (.-byteOffset u) (.-byteLength u))))

(defn- serve-bytes [request cid out dagpb?]
  (let [hdrs (ipfs-headers cid (.-byteLength out) (detect-ct out)
                           (if dagpb? "car-dag-pb" "sha256"))]
    (js/Response. (if (= (.-method request) "HEAD") nil out)
                  #js {:status 200 :headers (clj->js hdrs)})))

(defn- try-gateways [request cid dagpb? gateways idx last-err]
  (if (>= idx (count gateways))
    (js/Promise.resolve
     (json-resp #js {:error "IpfsUnavailable" :message last-err :cid cid} 502 actor-json-headers))
    (let [tmpl (nth gateways idx)
          base (if (str/includes? tmpl "{cid}")
                 (str/replace tmpl "{cid}" cid)
                 (str (str/replace tmpl #"/$" "") "/ipfs/" cid))
          upstream (if dagpb?
                     (str base (if (str/includes? base "?") "&" "?") "format=car")
                     base)
          next-gw (fn [err] (try-gateways request cid dagpb? gateways (inc idx) err))]
      (-> (js/fetch upstream
                    #js {:headers #js {"accept" (if dagpb?
                                                  "application/vnd.ipld.car"
                                                  "application/octet-stream")}
                         :signal (js/AbortSignal.timeout (if dagpb? 20000 8000))})
          (.then
           (fn [res]
             (if-not (.-ok res)
               (next-gw (str "upstream " (.-status res)))
               (.then (.arrayBuffer res)
                      (fn [raw-buf]
                        (if dagpb?
                          (-> (verify-car-to-bytes cid (js/Uint8Array. raw-buf))
                              (.then (fn [bytes] (serve-bytes request cid (->ab bytes) true)))
                              (.catch (fn [ve]
                                        (next-gw (str "car verify failed: "
                                                      (if (instance? js/Error ve) (.-message ve) ve))))))
                          (.then (verify-raw-cid cid raw-buf)
                                 (fn [ok?]
                                   (if ok?
                                     (serve-bytes request cid raw-buf false)
                                     (next-gw "cid mismatch (untrusted gateway content rejected)"))))))))))
          (.catch (fn [e]
                    (next-gw (if (instance? js/Error e) (.-message e) "fetch failed"))))))))

(defn handle-ipfs
  "Entry for GET/HEAD /ipfs/<cid>. Returns Promise<Response>. The method check is
  done by the router/core before dispatch."
  [request env cid]
  (let [raw? (codec/raw-cid-v1? cid)
        dagpb? (codec/dag-pb-cid-v1? cid)]
    (if (and (not raw?) (not dagpb?))
      (json-resp #js {:error "CidNotVerifiable"
                      :message "trustless gateway supports CIDv1 with sha2-256 only: raw single-block (bafkrei…) verified directly, dag-pb UnixFS (bafybei…) verified via CAR. Other CIDs need a full IPFS node."
                      :cid cid}
                 501 actor-json-headers)
      (try-gateways request cid dagpb? (gateways-from-env env) 0 "no gateway configured"))))
