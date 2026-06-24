;; etzhayyim.kotoba.pages-store — GitHubPagesBlockStore: a read/query tier that
;; serves content-addressed kotoba blocks as a STATIC GitHub Pages asset.
;;
;; ADR-2606242400 (the follow-up to ADR-2606241500). kotoba's blocks are CIDv1
;; content-addressed and IPFS/B2 are *export tiers, not the system of record*
;; (ADR-2605312345) — so the blocks can live ANYWHERE addressable. This tier
;; commits them as one CARv1 bundle (`<graph>.car`) + an index (`.car.idx.edn`)
;; + a `head.json` to a repo's Pages root; a client then resolves a graph **by
;; its root CID** over plain HTTPS (no IPFS daemon, no server):
;;
;;   query = GET head.json -> root CID
;;         -> Range-GET the root block from <graph>.car (one block, not the file)
;;         -> read its child CIDs -> Range-GET + sha2-256-VERIFY each
;;         -> reassemble the Datom log -> run the datom query locally
;;
;; GitHub Pages (Fastly) honours HTTP Range, so the index lets a browser/peer
;; fetch a single block from a large CAR. Integrity is trustless: every fetched
;; block's CID is recomputed and checked, so the static host is untrusted.
;;
;; PUBLISH writes files only; committing/pushing them is the actor:evolve /
;; actor:publish git path (no-server-key). clj/bb; HTTP via babashka.http-client.

(ns etzhayyim.kotoba.pages-store
  (:require [clojure.string :as str]
            [clojure.edn :as edn]
            [clojure.java.io :as io]
            [cheshire.core :as json]
            [babashka.http-client :as http]
            [etzhayyim.kotoba.cid :as cid]
            [etzhayyim.kotoba.car :as car]
            [etzhayyim.kotoba.prolly :as prolly]
            [etzhayyim.kotoba.log :as klog])
  (:import (java.io RandomAccessFile)))

;; ── log <-> blocks (each datom a block; a root manifest links them) ──────────

(defn- ->bytes ^bytes [s] (.getBytes ^String s "UTF-8"))

(defn blocks-of-log
  "Map a kotoba Datom log (vector of [e a v tx op]) to content-addressed blocks:
   one block per datom (addressed over its pr-str, like cid-of-edn) plus a ROOT
   MANIFEST block listing the child CIDs in log order + the log head-cid.
   Returns {:root <manifest-cid> :head <log-head-cid> :blocks ([cid ^bytes]…)}.
   The manifest's CID is the graph's published root (the prolly/commit-DAG head
   analogue: resolve it, walk its children)."
  [graph logv]
  (let [datom-blocks (mapv (fn [dm]
                             (let [b (->bytes (pr-str (vec dm)))]
                               [(cid/cid b) b]))
                           logv)
        head (klog/head-cid (vec logv))
        manifest {:kotoba/car-root true
                  :graph graph
                  :head head
                  :count (count datom-blocks)
                  :blocks (mapv first datom-blocks)}
        man-bytes (->bytes (pr-str manifest))
        man-cid (cid/cid man-bytes)]
    {:root man-cid :head head
     :blocks (into [[man-cid man-bytes]] datom-blocks)}))

(defn blocks-of-log-prolly
  "Map a kotoba Datom log to a PROLLY-TREE Merkle DAG (etzhayyim.kotoba.prolly):
   a multi-level, content-defined, history-independent B-tree. Returns
   {:root <prolly-root-cid> :head <log-head-cid> :blocks ([cid ^bytes]…)
    :levels :nodes}. For large graphs a seek descends one spine (O(log n) Range
   fetches) instead of pulling a flat manifest of every datom CID."
  [_graph logv & {:keys [bits]}]
  (let [t (apply prolly/build logv (when bits [:bits bits]))]
    (assoc (select-keys t [:root :blocks :levels :nodes])
           :head (klog/head-cid (vec logv)))))

;; ── publish (write the static Pages asset) ───────────────────────────────────

(defn publish!
  "Pack `logv` into <dir>/<graph>.car (+ .car.idx.edn + head.json + .nojekyll).
   `:layout` ∈ {:flat (default — root manifest lists every datom CID, exact-log
   reassembly) | :prolly (multi-level Merkle B-tree, O(log n) seek for large
   graphs)}. Returns {:root :head :car :idx :head-json :n-blocks :layout}.
   Side-effect = file writes only; commit/push is the git tier."
  [dir graph logv & {:keys [layout bits] :or {layout :flat}}]
  (let [{:keys [root head blocks levels]}
        (case layout
          :prolly (blocks-of-log-prolly graph logv :bits bits)
          (blocks-of-log graph logv))
        {:keys [car index]} (car/pack [root] blocks)
        car-path (str dir "/" graph ".car")
        idx-path (str dir "/" graph ".car.idx.edn")
        head-path (str dir "/head.json")]
    (io/make-parents (io/file car-path))
    (with-open [o (io/output-stream car-path)] (.write o ^bytes car))
    (spit idx-path (pr-str (cond-> {:graph graph :root root :head head
                                    :layout layout :version 1 :index index}
                             levels (assoc :levels levels))))
    (spit head-path (str (json/generate-string
                          (cond-> {:graph graph :root root :head head :layout layout
                                   :car (str graph ".car") :idx (str graph ".car.idx.edn")}
                            levels (assoc :levels levels))
                          {:pretty true}) "\n"))
    (spit (str dir "/.nojekyll") "")
    {:root root :head head :car car-path :idx idx-path :head-json head-path
     :n-blocks (count blocks) :layout layout :levels levels}))

;; ── index loaders ────────────────────────────────────────────────────────────

(defn index-from-file [idx-path] (edn/read-string (slurp idx-path)))

(defn index-from-http
  "GET the small .car.idx.edn over HTTPS (full, not ranged) and parse it."
  [idx-url]
  (edn/read-string (:body (http/get idx-url {:as :string}))))

;; ── transports (the Range-fetch seam) ────────────────────────────────────────

(defn file-ranger
  "A (fn [offset len] -> ^bytes) reading a slice of a local .car file — the
   offline/test analogue of an HTTP Range GET."
  [car-path]
  (fn [offset len]
    (with-open [raf (RandomAccessFile. (io/file car-path) "r")]
      (let [buf (byte-array len)]
        (.seek raf (long offset))
        (.readFully raf buf)
        buf))))

(defn http-ranger
  "A (fn [offset len] -> ^bytes) issuing `Range: bytes=offset-(offset+len-1)`
   against a CAR URL on GitHub Pages (Fastly serves 206 Partial Content)."
  [car-url]
  (fn [offset len]
    (let [end (+ offset len -1)
          resp (http/get car-url {:headers {"Range" (str "bytes=" offset "-" end)}
                                  :as :bytes})]
      (when-not (#{200 206} (:status resp))
        (throw (ex-info "range GET failed" {:status (:status resp) :url car-url})))
      (:body resp))))

;; ── block-level read (CID-verified) ──────────────────────────────────────────

(defn get-block
  "Fetch ONE block by CID via `ranger`, using `index` ({:index {cid [off len]}}).
   Recomputes the CID over the bytes and refuses a mismatch (trustless host)."
  ^bytes [ranger index cid-str]
  (let [[off len] (get-in index [:index cid-str])]
    (when-not off
      (throw (ex-info "CID not in index" {:cid cid-str})))
    (car/verify-block cid-str (ranger off len))))

;; ── graph query (resolve root -> walk -> reassemble the log) ─────────────────

(defn get-fn
  "A (fn [cid] -> ^bytes) CID-verifying block reader bound to ranger+index —
   the seam the prolly walker/seeker consumes."
  [ranger index]
  (fn [cid-str] (get-block ranger index cid-str)))

(defn fetch-log
  "Resolve the graph's root CID and reassemble its Datom log — over `ranger`,
   every block CID-checked. `:flat` walks the root manifest's child list (exact
   log order); `:prolly` descends the Merkle B-tree (sorted, set-equal). This is
   `query a static site by CID`, end to end."
  [ranger index]
  (if (= :prolly (:layout index))
    (prolly/walk (get-fn ranger index) (:root index))
    (let [root (:root index)
          manifest (edn/read-string (String. (get-block ranger index root) "UTF-8"))]
      (when-not (:kotoba/car-root manifest)
        (throw (ex-info "root is not a kotoba CAR manifest" {:root root})))
      (mapv (fn [cid-str]
              (edn/read-string (String. (get-block ranger index cid-str) "UTF-8")))
            (:blocks manifest)))))

(defn seek
  "Prolly point lookup over the Pages store: descend ONE spine (O(log n) Range
   fetches) to find `datom`. Returns {:found? :datom :fetched}. :prolly only."
  [ranger index datom]
  (when-not (= :prolly (:layout index))
    (throw (ex-info "seek requires a :prolly-layout graph" {:layout (:layout index)})))
  (prolly/seek-datom (get-fn ranger index) (:root index) datom))

;; ── CLI ──────────────────────────────────────────────────────────────────────

(defn -publish
  "bb pages:publish <graph> <journal.edn> [out-dir] [--prolly] [--bits=N]. Packs a
   kotoba journal into a static Pages CAR bundle (out-dir default
   80-data/pages/<graph>). --prolly = multi-level Merkle B-tree (O(log n) seek)."
  [& args]
  (let [[graph journal out] (remove #(str/starts-with? % "--") args)
        layout (if (contains? (set args) "--prolly") :prolly :flat)
        bits (some->> args (filter #(str/starts-with? % "--bits=")) first
                      (drop 7) (apply str) not-empty Integer/parseInt)]
    (when-not (and graph journal)
      (println "usage: bb pages:publish <graph> <journal.edn> [out-dir] [--prolly] [--bits=N]") (System/exit 2))
    (let [dir (or out (str "80-data/pages/" graph))
          logv (klog/read-log journal)
          r (publish! dir graph logv :layout layout :bits bits)]
      (println "published" graph "->" (:car r) (str "(" (name (:layout r)) ")"))
      (println "  root  " (:root r))
      (println "  head  " (:head r))
      (println "  blocks" (:n-blocks r)
               (when (:levels r) (str "| levels " (:levels r)))
               "| idx" (:idx r) "| head.json" (:head-json r))
      (println "  serve : commit" dir "-> GitHub Pages; query by root CID over HTTPS Range"))))

(defn -query
  "bb pages:query <dir-or-base> [--http]. Reconstructs + summarizes a published
   graph by its root CID. Default reads local files; --http treats the arg as a
   base URL (…/<graph>) and uses HTTP Range."
  [& args]
  (let [http? (contains? (set args) "--http")
        base (first (remove #(str/starts-with? % "--") args))]
    (when-not base
      (println "usage: bb pages:query <dir-or-base> [--http]   (--http: base=URL/<graph>)") (System/exit 2))
    (let [[index ranger]
          (if http?
            [(index-from-http (str base ".car.idx.edn")) (http-ranger (str base ".car"))]
            (let [head (json/parse-string (slurp (str base "/head.json")) true)
                  graph (:graph head)]
              [(index-from-file (str base "/" graph ".car.idx.edn"))
               (file-ranger (str base "/" graph ".car"))]))
          logv (fetch-log ranger index)]
      (println "graph " (:graph index) " root " (:root index))
      (println "head  " (:head index) " (recomputed:" (klog/head-cid logv) ")")
      (println "datoms" (count logv) "— reassembled + CID-verified from"
               (if http? "HTTPS Range" "local CAR")))))
