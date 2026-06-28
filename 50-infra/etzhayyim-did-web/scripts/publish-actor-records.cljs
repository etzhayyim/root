#!/usr/bin/env nbb
;; publish-actor-records.cljs — materialize actor identity + profile from the
;; canonical kotoba seed into (a) CF KV (`actor:<handle>` → ActorRecord JSON,
;; read by the Worker for dynamic did.json + getProfile) and (b) the kotoba
;; `actors-v1` graph (kg.ingest_batch). Per ADR-2606013800.
;;
;; ClojureScript-on-Node (nbb) port of the legacy publish-actor-records.mjs
;; (repo rule: operational tooling = clj/cljs, not hand-JS). Output is
;; BYTE-IDENTICAL to the .mjs: it builds the same JS objects (ordered) and uses
;; the same js/JSON.stringify + sha2-256 → CIDv1(raw) so the content-addressed
;; did.json CID is unchanged. Verified by diffing both writers' ./out trees.
;;
;; SSoT: 00-contracts/schemas/actor-profile-seed.kotoba.edn
;;
;; Modes:
;;   (default)         parse seed, write materialized docs to ./out/, print summary
;;   --emit-dir <dir>  write per-actor record.json / did.json / profile.json to <dir>
;;   --put-kv          `wrangler kv key put` each ActorRecord (needs ACTOR_KV binding)
;;   --ingest-kotoba   POST kg.ingest_batch to $KOTOBA_ENDPOINT (operator-gated)
;;   --pin-did         `ipfs add` each canonical did.json, verify CID matches
;;   --actor <handle>  restrict to one actor (debug)
;;   --seed  <path>    override the canonical seed (repo-relative)
;;
;; The toDidDoc / toGetProfileView logic here MIRRORS src/registry/actor-profiles.ts
;; — keep them in sync (one is TS for the Worker, this is cljs for the publisher).
;;
;; Run:  npx nbb scripts/publish-actor-records.cljs [flags]
(ns publish-actor-records
  (:require [clojure.edn :as edn]
            [clojure.string :as str]))

(def fs (js/require "node:fs"))
(def path (js/require "node:path"))
(def crypto (js/require "node:crypto"))
(def child (js/require "node:child_process"))

;; ── CIDv1 (raw, sha2-256) — matches `ipfs add --cid-version=1` + the worker's
;; cid.ts/codec.cljs, so the canonical DID doc is IPFS-retrievable (ADR-2606015400).
(def ^:private b32 "abcdefghijklmnopqrstuvwxyz234567")

(defn- base32
  "RFC4648 base32 lower, no padding — faithful to cid.ts/_base32. `buf` is a
  node Buffer / Uint8Array."
  [buf]
  (let [n (.-length buf)]
    (loop [i 0, bits 0, val 0, out ""]
      (cond
        (>= bits 5)
        (recur i (- bits 5) val
               (str out (.charAt b32 (bit-and (unsigned-bit-shift-right val (- bits 5)) 31))))
        (< i n)
        (recur (inc i) (+ bits 8) (bit-or (bit-shift-left val 8) (aget buf i)) out)
        (pos? bits)
        (str out (.charAt b32 (bit-and (bit-shift-left val (- 5 bits)) 31)))
        :else out))))

(defn- cid-v1-raw
  "CIDv1(raw, sha2-256) string for the bytes in `buf` (a node Buffer)."
  [buf]
  (let [d (.digest (.update (.createHash crypto "sha256") buf))
        full (js/Buffer.concat #js [(js/Buffer.from #js [0x01 0x55 0x12 0x20]) d])]
    (str "b" (base32 full))))

;; ── paths ───────────────────────────────────────────────────────────────────
(def ^:private script-dir (.dirname path (.resolve path (aget js/process.argv 2))))
(def ^:private repo-root (.resolve path script-dir "../../.."))
(def ^:private default-seed
  (.resolve path repo-root "00-contracts/schemas/actor-profile-seed.kotoba.edn"))

;; ── helpers ───────────────────────────────────────────────────────────────────
(defn- kw
  "EDN keyword value → its plain string name; pass non-keywords through (mirror of
  the .mjs `kw()` __kw-flattening)."
  [v]
  (if (keyword? v) (name v) v))

(defn- some-val?
  "JS `!== undefined && !== null` — used to decide whether an optional key is set."
  [v]
  (and (some? v) (not (undefined? v))))

(defn- jset!
  "aset on a JS object, preserving insertion order (string keys). Returns the obj."
  [o k v] (aset o k v) o)

(defn- svc->js
  "Seed service entry (an ordered string-keyed EDN map) → a JS object with the same
  key order, keyword values flattened. Mirrors the .mjs `Object.entries` copy."
  [svc]
  (let [o #js {}]
    (doseq [k (keys svc)] (aset o k (kw (get svc k))))
    o))

;; ── seed entity → ActorRecord (internal clj map; ordered JS built later) ──────
(defn- record-from-seed [m]
  (let [g     (fn [k] (get m (keyword "actor" k)))
        handle (str (g "handle"))
        named  (boolean (g "glyph"))
        service (mapv svc->js (or (g "service") []))
        base {:handle      handle
              :did         (or (g "did") (str "did:web:etzhayyim.com:actor:" handle))
              :kind        (or (kw (g "kind")) (if named "tier-b" "substrate-service"))
              :status      (or (kw (g "status")) (if named "r0" "landed"))
              :description (or (g "description") "")
              :adr         (mapv str (or (g "adr") []))
              :service     service
              :vm          (vec (or (g "vm") []))
              :source      "kotoba"}
        ;; optional fields: seed-key → record-key (only set when present)
        opts [["tier" :tier] ["glyph" :glyph]
              ["display-name-ja" :displayNameJa] ["display-name-en" :displayNameEn]
              ["avatar" :avatar] ["banner" :banner]
              ["performer-type" :performerType] ["ui-type" :uiType]
              ["primary-lexicon" :primaryLexicon] ["primary-schema" :primarySchema]
              ["wasm-cid" :wasmCid] ["created-at" :createdAt]]]
    (reduce (fn [rec [sk rk]]
              (let [v (g sk)]
                (if (some-val? v) (assoc rec rk (kw v)) rec)))
            base opts)))

;; ── ActorRecord → ordered JS (mirror of recordFromSeed's object shape) ────────
(defn- record->js [rec]
  (let [o #js {}]
    (jset! o "handle" (:handle rec))
    (jset! o "did" (:did rec))
    (jset! o "kind" (:kind rec))
    (jset! o "status" (:status rec))
    (jset! o "description" (:description rec))
    (jset! o "adr" (clj->js (:adr rec)))
    (jset! o "service" (clj->js (:service rec)))   ;; entries already JS objs
    (jset! o "vm" (clj->js (:vm rec)))
    (doseq [[rk jk] [[:tier "tier"] [:glyph "glyph"]
                     [:displayNameJa "displayNameJa"] [:displayNameEn "displayNameEn"]
                     [:avatar "avatar"] [:banner "banner"]
                     [:performerType "performerType"] [:uiType "uiType"]
                     [:primaryLexicon "primaryLexicon"] [:primarySchema "primarySchema"]
                     [:wasmCid "wasmCid"] [:createdAt "createdAt"]]]
      (when (contains? rec rk) (jset! o jk (rk rec))))
    (jset! o "source" (:source rec))
    o))

;; ── mappers (MIRROR of src/registry/actor-profiles.ts) ────────────────────────
(defn- to-did-doc [rec authz-contract]
  (let [did   (str "did:web:etzhayyim.com:actor:" (:handle rec))
        vm    (:vm rec)
        chain-ref (some #(when (and (map? %) (get % "chainRef")) (get % "chainRef")) vm)
        also  (cond-> [(str "did:web:" (:handle rec) ".etzhayyim.com")]
                chain-ref (conj chain-ref)
                (and (not chain-ref) (seq authz-contract))
                (conj (str "did:erc725:base:" authz-contract "#__rootId-pending-chain-lookup__")))
        wasm-cid (:wasmCid rec)
        raw?  (and wasm-cid (boolean (re-matches #"bafkrei[a-z2-7]{52}" wasm-cid)))
        service (cond-> []
                  wasm-cid
                  (conj (doto #js {}
                          (jset! "id" (str did "#wasm"))
                          (jset! "type" "EtzhayyimWasmComponent")
                          (jset! "serviceEndpoint" (str "ipfs://" wasm-cid))
                          (jset! "x-exec" (if raw? "browser-local|donated-mesh" "donated-mesh"))
                          (jset! "x-cid-codec" (if raw? "raw" "dag-pb"))
                          (jset! "x-runtime" "kotoba-wasm")))
                  :always
                  (into (:service rec)))
        meta (doto #js {}
               (jset! "adr" (clj->js (into ["2605212030" "2605241800" "2606013800" "2606014500"]
                                           (:adr rec))))
               (jset! "source" (:source rec))
               (jset! "kind" (:kind rec))
               (jset! "status" (:status rec))
               (jset! "glyph" (if (contains? rec :glyph) (:glyph rec) js/undefined))
               (jset! "wasmCid" (if (some? wasm-cid) wasm-cid nil))
               (jset! "execModel" (if wasm-cid "wasm-local (browser/donated-mesh)" "service"))
               (jset! "primaryLexicon" (if (contains? rec :primaryLexicon) (:primaryLexicon rec) js/undefined))
               (jset! "primarySchema" (if (contains? rec :primarySchema) (:primarySchema rec) js/undefined))
               (jset! "note" (if (zero? (count vm))
                               "verificationMethod empty — on-chain ERC725 mirror pending; did:web trust root = TLS (no server-minted key, ADR-2605231525)"
                               "verificationMethod mirrors on-chain ERC725 Root.activeKey")))]
    (doto #js {}
      (jset! "@context" #js ["https://www.w3.org/ns/did/v1"
                             "https://w3id.org/security/suites/jws-2020/v1"])
      (jset! "id" did)
      (jset! "alsoKnownAs" (clj->js also))
      (jset! "verificationMethod" (clj->js (mapv #(js/Object.assign #js {} (clj->js %)) vm)))
      (jset! "service" (clj->js (vec service)))
      (jset! "_meta" meta))))

(defn- to-get-profile-view [rec]
  (let [display (or (:displayNameEn rec) (:displayNameJa rec) (:handle rec))
        o (doto #js {}
            (jset! "did" (:did rec))
            (jset! "handle" (str (:handle rec) ".etzhayyim.com"))
            (jset! "displayName" display)
            (jset! "description" (:description rec))
            (jset! "avatar" (if (some? (:avatar rec)) (:avatar rec) ""))
            (jset! "banner" (if (some? (:banner rec)) (:banner rec) ""))
            (jset! "followersCount" 0)
            (jset! "followsCount" 0)
            (jset! "postsCount" 0)
            (jset! "indexedAt" (if (:createdAt rec)
                                 (str (:createdAt rec) "T00:00:00.000Z")
                                 "1970-01-01T00:00:00.000Z"))
            (jset! "labels" #js [])
            (jset! "viewer" #js {})
            (jset! "performerType" (if (some? (:performerType rec)) (:performerType rec) "system"))
            (jset! "uiType" (if (some? (:uiType rec)) (:uiType rec) "appview")))]
    (when (:glyph rec) (jset! o "glyph" (:glyph rec)))
    (when (:displayNameJa rec) (jset! o "displayNameJa" (:displayNameJa rec)))
    (jset! o "_etzhayyim"
           (doto #js {}
             (jset! "kind" (:kind rec))
             (jset! "tier" (if (some? (:tier rec)) (:tier rec) nil))
             (jset! "status" (:status rec))
             (jset! "adr" (clj->js (:adr rec)))
             (jset! "primaryLexicon" (if (some? (:primaryLexicon rec)) (:primaryLexicon rec) nil))
             (jset! "primarySchema" (if (some? (:primarySchema rec)) (:primarySchema rec) nil))
             (jset! "didDocument" (str "https://etzhayyim.com/actor/" (:handle rec) "/did.json"))
             (jset! "source" (:source rec))))
    o))

;; ── kotoba kg.ingest_batch entity ─────────────────────────────────────────────
(defn- record->kg-entity [rec]
  (let [claims #js []
        add (fn [pred value]
              (when (and (some? value) (not (undefined? value)) (not= value ""))
                (.push claims #js {"pred" (str "actor/" pred) "value" (str value)})))]
    (add "handle" (:handle rec))
    (add "did" (:did rec))
    (add "kind" (:kind rec))
    (add "tier" (:tier rec))
    (add "status" (:status rec))
    (add "glyph" (:glyph rec))
    (add "display-name-ja" (:displayNameJa rec))
    (add "display-name-en" (:displayNameEn rec))
    (add "description" (:description rec))
    (add "avatar" (:avatar rec))
    (add "banner" (:banner rec))
    (add "wasm-cid" (:wasmCid rec))
    (add "performer-type" (:performerType rec))
    (add "ui-type" (:uiType rec))
    (add "primary-lexicon" (:primaryLexicon rec))
    (add "primary-schema" (:primarySchema rec))
    (add "created-at" (:createdAt rec))
    (add "service-json" (js/JSON.stringify (clj->js (:service rec))))
    (add "vm-json" (js/JSON.stringify (clj->js (:vm rec))))
    (doseq [a (:adr rec)] (.push claims #js {"pred" "actor/adr" "value" a}))
    (doto #js {}
      (jset! "id" (str "actor." (:handle rec)))
      (jset! "kind" "actor-profile")
      (jset! "label_en" (or (:displayNameEn rec) (:handle rec)))
      (jset! "label_ja" (or (:displayNameJa rec) js/undefined))
      (jset! "claims" claims)
      (jset! "relations" #js []))))

;; ── canonical (content-addressed) did doc: _meta.source → "ipfs" for a stable CID
(defn- canonicalize [did-doc]
  (let [c (js/Object.assign #js {} did-doc)
        m (js/Object.assign #js {} (.-_meta did-doc))]
    (aset m "source" "ipfs")
    (aset c "_meta" m)
    c))

(defn- did-cid [did-doc]
  (cid-v1-raw (js/Buffer.from (js/JSON.stringify (canonicalize did-doc)) "utf8")))

;; ── arg parsing ───────────────────────────────────────────────────────────────
(def ^:private args (vec *command-line-args*))
(defn- has? [f] (boolean (some #{f} args)))
(defn- val-of [f]
  (let [k (.indexOf (clj->js args) f)] (when (>= k 0) (nth args (inc k) nil))))

;; ── main ──────────────────────────────────────────────────────────────────────
(defn- main []
  (let [seed-path (if-let [s (val-of "--seed")] (.resolve path repo-root s) default-seed)
        seed (edn/read-string (.readFileSync fs seed-path "utf8"))
        entities (mapv record-from-seed (or (:seed seed) []))
        only (val-of "--actor")
        records (if only (filterv #(= (:handle %) only) entities) entities)]
    (when (zero? (count records))
      (js/console.error (str "no actors" (if only (str " matching '" only "'") "")))
      (js/process.exit 1))
    (let [authz (or (.. js/process -env -AUTHZ_CONTRACT_ADDRESS) "")
          out-dir (or (val-of "--emit-dir") (.resolve path script-dir "../out/actor-records"))]
      (.mkdirSync fs out-dir #js {:recursive true})
      (doseq [rec records]
        (let [did (to-did-doc rec authz)
              profile (to-get-profile-view rec)
              canonical-bytes (js/Buffer.from (js/JSON.stringify (canonicalize did)) "utf8")
              cid (cid-v1-raw canonical-bytes)
              j (fn [n] (.resolve path out-dir n))]
          (.writeFileSync fs (j (str (:handle rec) ".record.json"))
                          (str (js/JSON.stringify (record->js rec) nil 2) "\n"))
          (.writeFileSync fs (j (str (:handle rec) ".did.json"))
                          (str (js/JSON.stringify did nil 2) "\n"))
          (.writeFileSync fs (j (str (:handle rec) ".did.canonical.json")) canonical-bytes)
          (.writeFileSync fs (j (str (:handle rec) ".diddoc.cid")) (str cid "\n"))
          (.writeFileSync fs (j (str (:handle rec) ".profile.json"))
                          (str (js/JSON.stringify profile nil 2) "\n"))))
      (println (str "parsed " (count records) " actor(s) → " out-dir))
      (println (str/join "\n"
                         (map (fn [r]
                                (str "  " (if (:glyph r) (str (:glyph r) " ") "")
                                     (:handle r) "  (" (:kind r) "/" (:status r) ")"
                                     "  did.json CID " (did-cid (to-did-doc r authz))))
                              records)))

      (when (has? "--pin-did")
        (doseq [rec records]
          (let [f (.resolve path out-dir (str (:handle rec) ".did.canonical.json"))
                out (str/trim (.execFileSync child "ipfs"
                                             #js ["add" "-Q" "--cid-version=1" f]
                                             #js {:encoding "utf8"}))
                want (str/trim (.readFileSync fs (.resolve path out-dir (str (:handle rec) ".diddoc.cid")) "utf8"))]
            (println (str "pinned " (:handle rec) " did.json → " out
                          (if (= out want) " ✓" (str " ✗ MISMATCH " want)))))))

      (when (has? "--put-kv")
        (doseq [rec records]
          (let [key (str "actor:" (:handle rec))]
            (println (str "kv put " key " …"))
            (.execFileSync child "npx"
                           #js ["wrangler" "kv" "key" "put" "--binding" "ACTOR_KV"
                                key (js/JSON.stringify (record->js rec))]
                           #js {:stdio "inherit" :cwd (.resolve path script-dir "..")}))))

      (when (has? "--ingest-kotoba")
        (let [endpoint (.. js/process -env -KOTOBA_ENDPOINT)]
          (if-not endpoint
            (do (js/console.error "KOTOBA_ENDPOINT unset — cannot ingest") (js/process.exit 2))
            (let [batch #js {"entities" (clj->js (mapv record->kg-entity records))}
                  url (str (str/replace endpoint #"/$" "")
                           "/xrpc/com.etzhayyim.apps.kotobase.kg.ingest_batch")]
              (println (str "POST " url " (" (count records) " entities) …"))
              (-> (js/fetch url #js {:method "POST"
                                     :headers #js {"content-type" "application/json"}
                                     :body (js/JSON.stringify batch)})
                  (.then (fn [r] (-> (.text r) (.then (fn [t] (println (str "  → " (.-status r) " " t)))))))
                  (.catch (fn [e] (js/console.error "ingest failed:" (.-message e)) (js/process.exit 3)))))))))))

(main)
