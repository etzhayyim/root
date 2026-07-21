;; test_bb_migration_wave8a.clj — parity + request-shaping tests for
;; etzhayyim.cohort (cohort.cljc), etzhayyim.nono (nono.cljc),
;; etzhayyim.mitama (mitama.cljc), etzhayyim.yoroshiku (yoroshiku.cljc)
;;
;; Run with:
;;   bb 70-tools/src/etzhayyim/test_bb_migration_wave8a.clj
;;
;; from repo root. classpath 70-tools/src is in bb.edn :paths so no -cp needed.
;;
;; Coverage:
;;
;;   etzhayyim.cohort  PURE:
;;     - build-gen-segment (field names + values)
;;     - compute-dashboard (total/fissioned/base/rate/axis cardinalities)
;;     - build-coverage-matrix (2D matrix, row/col sets)
;;     - find-gaps (cells below min-count)
;;     - compute-snapshot-agg (group-by axes, count)
;;     - diff-snapshots (delta between two totals)
;;     - parse-segment-arg (@file → read-fn, plain JSON string)
;;     - render-lineage-tree (prefix characters, connector format)
;;
;;   etzhayyim.cohort  IO request-shaping (injectable fake, no network):
;;     - build-gen-request (method/url/body)
;;     - build-list-request (method/url/params filters)
;;     - build-fission-request (dry-run flag in body)
;;     - build-diff-request (from/to params)
;;     - gen-cohort dry-run returns request shape, no http-fn call
;;
;;   etzhayyim.nono  PURE:
;;     - parse-manifest-data (nil on missing nanoid, fields extracted)
;;     - find-manifest-by-nanoid (found/not-found)
;;     - build-deploy-reg-body (all JSON-LD fields present)
;;     - build-build-command (pnpm/npm/wrangler selection, nil fallback)
;;     - build-deploy-command (returns ["npx" "wrangler" "deploy"])
;;
;;   etzhayyim.nono  IO request-shaping (injectable fake, no network):
;;     - build-register-manifest-request (method/url/headers/body)
;;     - register-skills dry-run returns request shape, no http-fn call
;;     - run-build dry-run returns command shape, no proc-fn call
;;     - run-deploy dry-run returns command shape, no proc-fn call
;;     - load-manifests uses injectable :fs-fn (no real fs access)
;;
;;   etzhayyim.mitama  PURE:
;;     - build-schema-status-stmt (base stmt, table filter, state filter, all-tables?)
;;     - build-schema-status-stmt safe-quoting (single-quote in table/state)
;;     - clamp-timeout-ms (lower bound 1000, upper bound 60000, mid value)
;;     - build-set-status-body (id + status fields)
;;     - build-shinka-payload (empty model → {}, non-empty → {:model})
;;
;;   etzhayyim.mitama  IO request-shaping (injectable fake, no network):
;;     - build-register-request (method/url/headers/body)
;;     - build-list-actors-request (GET/url/params)
;;     - build-inspect-request (GET/params)
;;     - build-set-status-request (POST/body with id+status)
;;     - build-shinka-request (POST/body)
;;     - build-schema-status-request (POST/body stmt+timeoutMs)
;;     - set-actor-status dry-run returns request shape, no http-fn call
;;     - run-shinka dry-run returns request shape, no http-fn call
;;
;;   etzhayyim.yoroshiku  PURE:
;;     - compute-readiness-checks (4 checks, names + ok + detail text)
;;     - compute-readiness-checks with missing fields (boolean coercion, zero app-count)
;;     - build-register-request (method/url/headers/body)
;;     - format-check-line ([OK  ]/[WARN] format)
;;     - format-readiness-summary (passing/total string)
;;
;;   etzhayyim.yoroshiku  IO request-shaping (injectable fake, no network):
;;     - run-readiness-checks uses injectable :fs-fn (no real fs access)
;;     - register-workspace dry-run returns request shape, no http-fn call
;;     - register-workspace live path fires POST to correct URL
;;
;;   HONEST NOTE:
;;     Live behavioral parity (whether servers accept the requests) requires a
;;     live PDS / AT Proto endpoint and CANNOT be verified offline.
;;     Filesystem glob (load-manifests / run-readiness-checks default :fs-fn) and
;;     subprocess (run-build/run-deploy default :proc-fn) are injected in all tests
;;     and never touch real filesystem or processes.

(ns etzhayyim.test-bb-migration-wave8a
  (:require [clojure.test     :refer [deftest is testing run-tests]]
            [clojure.string   :as str]
            [cheshire.core    :as json]
            [etzhayyim.cohort   :as cohort]
            [etzhayyim.nono     :as nono]
            [etzhayyim.mitama   :as mitama]
            [etzhayyim.yoroshiku :as yoroshiku]))

;; ─── helpers ──────────────────────────────────────────────────────────────────

(defn- make-fake-http
  "Returns {:log atom :http-fn fn}.
  Fake records every call; returns fixed-responses in order (cycling)."
  ([] (make-fake-http []))
  ([fixed-responses]
   (let [log      (atom [])
         resp-idx (atom 0)]
     {:log    log
      :http-fn
      (fn [req]
        (swap! log conj req)
        (if (seq fixed-responses)
          (let [r (nth fixed-responses (mod @resp-idx (count fixed-responses)))]
            (swap! resp-idx inc)
            (if (string? r)
              {:status 200 :body r}
              r))
          {:status 200 :body "{}"}))})))

(defn- make-fake-proc
  "Returns {:log atom :proc-fn fn}.
  Always returns exit-code 0 unless error-responses is given."
  ([] (make-fake-proc nil))
  ([_] {:log (atom [])
        :proc-fn (fn [cmd-map]
                   {:exit-code 0 :stdout "" :stderr ""})}))

(defn- make-fake-fs
  "Returns a fake :fs-fn that returns fixed manifest entries.
  entries is a seq of {:path str :data map}."
  [entries]
  (fn [_workspace-dir] entries))

;; ─────────────────────────────────────────────────────────────────────────────
;; etzhayyim.cohort  PURE
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-build-gen-segment
  (testing "returns map with all fields"
    (let [seg (cohort/build-gen-segment "tech" "engineer" "fintech" "senior" "ja-JP" 10)]
      (is (= "tech"     (:pcf-l1 seg)))
      (is (= "engineer" (:role seg)))
      (is (= "fintech"  (:industry seg)))
      (is (= "senior"   (:seniority seg)))
      (is (= "ja-JP"    (:locale seg)))
      (is (= 10         (:k seg)))))

  (testing "nil/empty values preserved"
    (let [seg (cohort/build-gen-segment "" nil "finance" "" "en-US" 5)]
      (is (= "" (:pcf-l1 seg)))
      (is (nil? (:role seg)))
      (is (= 5 (:k seg))))))

(deftest test-compute-dashboard
  (let [cohorts [{:kind "base"     :pcfL1 "tech" :role "eng"  :industry "fin" :locale "ja"}
                 {:kind "fissioned" :pcfL1 "tech" :role "eng"  :industry "fin" :locale "en"}
                 {:kind "fissioned" :pcfL1 "biz"  :role "mgr"  :industry "hr"  :locale "ja"}
                 {:kind "base"     :pcfL1 "biz"  :role "eng"  :industry "hr"  :locale "en"}]]

    (testing "total count"
      (is (= 4 (:total (cohort/compute-dashboard cohorts)))))

    (testing "fissioned count (kind=fissioned)"
      (is (= 2 (:fissioned (cohort/compute-dashboard cohorts)))))

    (testing "base count = total - fissioned"
      (is (= 2 (:base (cohort/compute-dashboard cohorts)))))

    (testing "fission-rate = fissioned/total"
      (is (= 0.5 (:fission-rate (cohort/compute-dashboard cohorts)))))

    (testing "axis cardinalities (distinct values)"
      (let [d (cohort/compute-dashboard cohorts)]
        (is (= 2 (:axis-pcf-l1 d)))   ; tech, biz
        (is (= 2 (:axis-role d)))      ; eng, mgr
        (is (= 2 (:axis-industry d)))  ; fin, hr
        (is (= 2 (:axis-locale d)))))  ; ja, en

    (testing "empty cohorts → all zeros and rate 0.0"
      (let [d (cohort/compute-dashboard [])]
        (is (= 0 (:total d)))
        (is (= 0.0 (:fission-rate d)))))))

(deftest test-build-coverage-matrix
  (let [cohorts [{:role "eng" :pcfL1 "tech"}
                 {:role "eng" :pcfL1 "tech"}
                 {:role "mgr" :pcfL1 "tech"}
                 {:role "eng" :pcfL1 "biz"}]]

    (testing "matrix has correct counts"
      (let [{:keys [matrix]} (cohort/build-coverage-matrix cohorts :role :pcfL1)]
        (is (= 2 (get-in matrix ["eng" "tech"])))
        (is (= 1 (get-in matrix ["mgr" "tech"])))
        (is (= 1 (get-in matrix ["eng" "biz"])))
        (is (nil? (get-in matrix ["mgr" "biz"])))))

    (testing "rows and cols are vectors of sorted values"
      (let [{:keys [rows cols]} (cohort/build-coverage-matrix cohorts :role :pcfL1)]
        (is (= ["eng" "mgr"] rows))
        (is (= ["biz" "tech"] cols))))

    (testing "empty cohorts → empty matrix"
      (let [{:keys [matrix rows cols]} (cohort/build-coverage-matrix [] :role :pcfL1)]
        (is (empty? matrix))
        (is (empty? rows))
        (is (empty? cols))))))

(deftest test-find-gaps
  (let [matrix {"eng" {"tech" 3 "biz" 1}
                "mgr" {"tech" 0 "biz" 2}}
        rows   ["eng" "mgr"]
        cols   ["biz" "tech"]]

    (testing "gaps where count < min-count=2"
      (let [gaps (cohort/find-gaps matrix rows cols 2)]
        (is (some #(and (= "eng" (:row %)) (= "biz" (:col %)) (= 1 (:count %))) gaps))
        (is (some #(and (= "mgr" (:row %)) (= "tech" (:col %)) (= 0 (:count %))) gaps))
        ;; eng/tech = 3, mgr/biz = 2 → NOT gaps
        (is (not (some #(= "tech" (:col %)) (filter #(= "eng" (:row %)) gaps))))
        (is (not (some #(and (= "mgr" (:row %)) (= "biz" (:col %))) gaps)))))

    (testing "min-count=0 → no gaps (all counts >= 0)"
      (is (empty? (cohort/find-gaps matrix rows cols 0))))

    (testing "min-count=100 → all cells are gaps"
      (let [gaps (cohort/find-gaps matrix rows cols 100)]
        (is (= 4 (count gaps)))))))

(deftest test-compute-snapshot-agg
  (let [cohorts [{:role "eng" :locale "ja"}
                 {:role "eng" :locale "ja"}
                 {:role "mgr" :locale "en"}]]

    (testing "groups by single axis"
      (let [agg (cohort/compute-snapshot-agg cohorts [:role])]
        (is (= 2 (get agg "eng")))
        (is (= 1 (get agg "mgr")))))

    (testing "groups by multiple axes (pipe-separated key)"
      (let [agg (cohort/compute-snapshot-agg cohorts [:role :locale])]
        (is (= 2 (get agg "eng|ja")))
        (is (= 1 (get agg "mgr|en")))))))

(deftest test-diff-snapshots
  (testing "positive delta"
    (let [d (cohort/diff-snapshots {:total 100 :timestamp "2026-06-01"}
                                    {:total 150 :timestamp "2026-06-21"})]
      (is (= 100 (:from-total d)))
      (is (= 150 (:to-total d)))
      (is (= 50  (:delta d)))
      (is (= "2026-06-01" (:from-ts d)))
      (is (= "2026-06-21" (:to-ts d)))))

  (testing "negative delta (shrinkage)"
    (let [d (cohort/diff-snapshots {:total 200} {:total 180})]
      (is (= -20 (:delta d)))))

  (testing "string keys also work"
    (let [d (cohort/diff-snapshots {"total" 10} {"total" 20})]
      (is (= 10 (:delta d))))))

(deftest test-parse-segment-arg
  (testing "plain JSON string parsed directly"
    (let [result (cohort/parse-segment-arg "{\"role\":\"eng\"}")]
      (is (= "eng" (:role result)))))

  (testing "@file prefix triggers read-fn"
    (let [called (atom nil)
          fake-read (fn [path] (reset! called path) "{\"role\":\"mgr\"}")
          result (cohort/parse-segment-arg "@/some/path.json" {:read-fn fake-read})]
      (is (= "/some/path.json" @called))
      (is (= "mgr" (:role result)))))

  (testing "nil/empty arg returns nil"
    (is (nil? (cohort/parse-segment-arg nil)))
    (is (nil? (cohort/parse-segment-arg ""))))

  (testing "invalid JSON returns nil"
    (is (nil? (cohort/parse-segment-arg "not-json")))))

(deftest test-render-lineage-tree
  (let [chain [{:nanoid "abc123" :name "Root"}
               {:nanoid "def456" :name "Child"}
               {:nanoid "ghi789" :name "Leaf"}]]

    (testing "last item uses └── prefix"
      (let [lines (cohort/render-lineage-tree chain)]
        (is (str/starts-with? (last lines) "└── "))))

    (testing "non-last items use ├── prefix"
      (let [lines (cohort/render-lineage-tree chain)]
        (is (str/starts-with? (first lines) "├── "))
        (is (str/starts-with? (second lines) "├── "))))

    (testing "each line includes nanoid and name"
      (let [lines (cohort/render-lineage-tree chain)]
        (is (str/includes? (first lines) "abc123"))
        (is (str/includes? (first lines) "Root"))
        (is (str/includes? (last lines) "ghi789"))
        (is (str/includes? (last lines) "Leaf"))))

    (testing "single item chain"
      (let [lines (cohort/render-lineage-tree [{:nanoid "x" :name "Solo"}])]
        (is (= 1 (count lines)))
        (is (str/starts-with? (first lines) "└── "))))

    (testing "string-keyed maps also work"
      (let [lines (cohort/render-lineage-tree [{"nanoid" "n1" "name" "N1"}
                                                {"nanoid" "n2" "name" "N2"}])]
        (is (str/includes? (first lines) "n1"))
        (is (str/includes? (last lines) "n2"))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; etzhayyim.cohort  IO request-shaping
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-build-gen-request
  (testing "POST method and correct URL"
    (let [seg (cohort/build-gen-segment "tech" "eng" "fin" "senior" "ja" 5)
          req (cohort/build-gen-request "https://pds.example.com" "tok123" seg)]
      (is (= :post (:method req)))
      (is (= "https://pds.example.com/xrpc/com.etzhayyim.cohort.gen" (:url req)))
      (is (= "Bearer tok123" (get-in req [:headers "Authorization"])))
      ;; body uses camelCase XRPC keys (pcfL1, role, industry, seniority, locale, k)
      (is (= "tech" (get-in req [:body :pcfL1])))
      (is (= 5 (get-in req [:body :k]))))))

(deftest test-build-list-request
  (testing "GET method with filters in params"
    (let [req (cohort/build-list-request "https://pds.example.com" "tok"
                                          {:pcf-l1 "tech" :role "eng" :limit 50})]
      (is (= :get (:method req)))
      (is (str/includes? (:url req) "com.etzhayyim.cohort.list"))
      (is (= "tech" (get-in req [:params "pcfL1"])))
      (is (= "eng"  (get-in req [:params "role"])))
      (is (= "50"   (get-in req [:params "limit"])))))

  (testing "default limit 100"
    (let [req (cohort/build-list-request "https://pds.example.com" "tok" {})]
      (is (= "100" (get-in req [:params "limit"]))))))

(deftest test-build-fission-request
  (testing "dry-run flag propagated to body"
    (let [req (cohort/build-fission-request "https://pds.example.com" "tok" "coh-123" {:dry-run? true})]
      (is (= :post (:method req)))
      (is (true? (get-in req [:body :dryRun])))
      (is (= "coh-123" (get-in req [:body :id])))))

  (testing "default k=2, dry-run=false"
    (let [req (cohort/build-fission-request "https://pds.example.com" "tok" "x" {})]
      (is (= 2 (get-in req [:body :k])))
      (is (false? (get-in req [:body :dryRun]))))))

(deftest test-build-diff-request
  (testing "from/to params present"
    (let [req (cohort/build-diff-request "https://pds.example.com" "tok"
                                          {:from "2026-06-01" :to "2026-06-21"})]
      (is (= :get (:method req)))
      (is (= "2026-06-01" (get-in req [:params "from"])))
      (is (= "2026-06-21" (get-in req [:params "to"])))))

  (testing "empty opts → no from/to params"
    (let [req (cohort/build-diff-request "https://pds.example.com" "tok" {})]
      (is (empty? (:params req))))))

(deftest test-gen-cohort-dry-run
  (testing "dry-run: returns request shape, does NOT call http-fn"
    (let [{:keys [log http-fn]} (make-fake-http)
          seg    (cohort/build-gen-segment "tech" "eng" "fin" "mid" "ja" 3)
          result (cohort/gen-cohort "https://pds.example.com" "tok" seg
                                     {:dry-run? true :http-fn http-fn})]
      (is (empty? @log) "http-fn must NOT be called in dry-run mode")
      (is (true? (:dry-run result)))
      (is (= :post (get-in result [:request :method]))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; etzhayyim.nono  PURE
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-parse-manifest-data
  (testing "valid data → manifest map"
    (let [data {"nanoid" "n123" "name" "MyWorker"
                "bindings" ["com.x.a" "com.x.b"]
                "skills"   [{"nsid" "com.x.a.run"}]}
          m    (nono/parse-manifest-data data)]
      (is (= "n123"      (:nanoid m)))
      (is (= "MyWorker"  (:name m)))
      (is (= 2           (count (:bindings m))))
      (is (= 1           (count (:skills m))))))

  (testing "keyword keys also work"
    (let [data {:nanoid "k456" :name "Other" :bindings [] :skills []}
          m    (nono/parse-manifest-data data)]
      (is (= "k456" (:nanoid m)))))

  (testing "nil nanoid → returns nil"
    (is (nil? (nono/parse-manifest-data {"name" "NoId"}))))

  (testing "empty string nanoid → returns nil"
    (is (nil? (nono/parse-manifest-data {"nanoid" "" "name" "NoId"}))))

  (testing "defaults: empty bindings and skills"
    (let [m (nono/parse-manifest-data {"nanoid" "x"})]
      (is (= [] (:bindings m)))
      (is (= [] (:skills m))))))

(deftest test-find-manifest-by-nanoid
  (let [manifests [{:nanoid "aaa" :name "A"}
                   {:nanoid "bbb" :name "B"}
                   {:nanoid "ccc" :name "C"}]]

    (testing "found"
      (is (= {:nanoid "bbb" :name "B"}
             (nono/find-manifest-by-nanoid manifests "bbb"))))

    (testing "not found → nil"
      (is (nil? (nono/find-manifest-by-nanoid manifests "zzz"))))

    (testing "empty list → nil"
      (is (nil? (nono/find-manifest-by-nanoid [] "aaa"))))))

(deftest test-build-deploy-reg-body
  (testing "all required JSON-LD fields present"
    (let [data {"@id" "did:web:worker.etzhayyim.com"
                "name" "MyWorker"
                "nanoid" "w1"
                "bindings" ["com.x.y"]
                "primitiveBackend" ["wasm"]
                "skills" [{"nsid" "com.x.y.run"}]}
          body (nono/build-deploy-reg-body data "w1")]
      (is (= "https://etzhayyim.com/ns/nono/v1" (get body "@context")))
      (is (= "did:web:worker.etzhayyim.com"     (get body "@id")))
      (is (= "MyWorker"                          (get body "name")))
      (is (= "w1"                                (get body "nanoid")))
      (is (= "nono"                              (get body "type")))
      (is (= ["com.x.y"]                         (get body "bindings")))
      (is (= ["wasm"]                            (get body "primitiveBackend")))
      (is (= "active"                            (get body "status")))))

  (testing "nanoid arg overrides empty data nanoid"
    (let [body (nono/build-deploy-reg-body {} "fallback-id")]
      (is (= "fallback-id" (get body "nanoid")))))

  (testing "missing fields default to empty collections"
    (let [body (nono/build-deploy-reg-body {"nanoid" "x"} "x")]
      (is (= [] (get body "bindings")))
      (is (= [] (get body "skills")))
      (is (= [] (get body "primitiveBackend"))))))

(deftest test-build-build-command
  ;; Parity with Python build_cmd logic in nono_build():
  ;; 1. pkg.json + scripts.build + pnpm-lock → ["pnpm" "run" "build"]
  ;; 2. pkg.json + scripts.build + no pnpm   → ["npm"  "run" "build"]
  ;; 3. no scripts.build + wrangler.jsonc    → ["npx" "wrangler" "deploy" "--dry-run" ...]
  ;; 4. nothing                              → nil

  (testing "pnpm selected when pnpm-lock.yaml exists"
    (let [pkg {"scripts" {"build" "esbuild src/index.js"}}
          cmd (nono/build-build-command pkg true false)]
      (is (= ["pnpm" "run" "build"] cmd))))

  (testing "npm selected when pnpm-lock absent"
    (let [pkg {"scripts" {"build" "esbuild"}}
          cmd (nono/build-build-command pkg false false)]
      (is (= ["npm" "run" "build"] cmd))))

  (testing "wrangler fallback when no scripts.build"
    (let [pkg {"scripts" {"start" "node index.js"}}
          cmd (nono/build-build-command pkg false true)]
      (is (= ["npx" "wrangler" "deploy" "--dry-run" "--outdir" "dist"] cmd))))

  (testing "wrangler fallback when pkg-data is nil"
    (let [cmd (nono/build-build-command nil false true)]
      (is (= ["npx" "wrangler" "deploy" "--dry-run" "--outdir" "dist"] cmd))))

  (testing "nil when no build source available"
    (is (nil? (nono/build-build-command nil false false)))
    (is (nil? (nono/build-build-command {"scripts" {}} false false)))))

(deftest test-build-deploy-command
  (testing "always returns [npx wrangler deploy]"
    (is (= ["npx" "wrangler" "deploy"] (nono/build-deploy-command)))))

;; ─────────────────────────────────────────────────────────────────────────────
;; etzhayyim.nono  IO request-shaping
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-build-register-manifest-request
  (testing "POST method, correct URL, auth header, body"
    (let [reg-body {"nanoid" "x" "name" "W" "type" "nono"}
          req      (nono/build-register-manifest-request
                    "https://pds.example.com" "tok123" reg-body)]
      (is (= :post (:method req)))
      (is (= "https://pds.example.com/xrpc/com.etzhayyim.actor.registerManifest" (:url req)))
      (is (= "Bearer tok123" (get-in req [:headers "Authorization"])))
      (is (= "application/json" (get-in req [:headers "Content-Type"])))
      (is (= reg-body (:body req))))))

(deftest test-register-skills-dry-run
  (testing "dry-run: request shape returned, http-fn NOT called"
    (let [{:keys [log http-fn]} (make-fake-http)
          data   {"nanoid" "w1" "name" "Worker"}
          result (nono/register-skills "https://pds.example.com" "tok"
                                        data "w1"
                                        {:dry-run? true :http-fn http-fn})]
      (is (empty? @log) "http-fn must NOT be called in dry-run mode")
      (is (true? (:dry-run result)))
      (is (= :post (get-in result [:request :method]))))))

(deftest test-run-build-dry-run
  (testing "dry-run: command shape returned, proc-fn NOT called"
    (let [log      (atom [])
          proc-fn  (fn [m] (swap! log conj m) {:exit-code 0 :stdout "" :stderr ""})
          pkg-data {"scripts" {"build" "esbuild"}}
          result   (nono/run-build "/some/dir" pkg-data false false
                                    {:dry-run? true :proc-fn proc-fn})]
      (is (empty? @log) "proc-fn must NOT be called in dry-run mode")
      (is (true? (:dry-run result)))
      (is (vector? (:command result))))))

(deftest test-run-deploy-dry-run
  (testing "dry-run: command shape returned, proc-fn NOT called"
    (let [log      (atom [])
          proc-fn  (fn [m] (swap! log conj m) {:exit-code 0 :stdout "" :stderr ""})
          result   (nono/run-deploy "/some/dir" {:dry-run? true :proc-fn proc-fn})]
      (is (empty? @log) "proc-fn must NOT be called in dry-run mode")
      (is (true? (:dry-run result)))
      (is (= ["npx" "wrangler" "deploy"] (:command result))))))

(deftest test-load-manifests-injectable-fs
  (testing "load-manifests uses :fs-fn injection (no real fs access)"
    (let [entries [{:path "/ws/w1/nono-manifest.jsonld"
                    :data {"nanoid" "w1" "name" "Worker1" "bindings" [] "skills" []}}
                   {:path "/ws/w2/nono-manifest.jsonld"
                    :data {:nanoid "w2" :name "Worker2" :bindings [] :skills []}}
                   {:path "/ws/bad/nono-manifest.jsonld"
                    :data {"name" "NanoidMissing"}}]  ; no nanoid → filtered
          result  (nono/load-manifests "/workspace"
                                       {:fs-fn (make-fake-fs entries)})]
      (is (= 2 (count result)))
      (is (some #(= "w1" (:nanoid %)) result))
      (is (some #(= "w2" (:nanoid %)) result))
      ;; bad entry (no nanoid) must be filtered out
      (is (not (some #(nil? (:nanoid %)) result))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; etzhayyim.mitama  PURE
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-build-schema-status-stmt
  ;; Parity with Python stmt construction in mitama_schema_status():
  ;;   stmt = "SHOW ALTER TABLE COLUMN FROM graphar"
  ;;   if not all_tables and table.strip():
  ;;     where_clauses.append(f"TableName = '{safe_table}'")
  ;;   if state.strip():
  ;;     where_clauses.append(f"State = '{safe_state}'")

  (testing "base statement with no filters"
    (is (= "SHOW ALTER TABLE COLUMN FROM graphar"
           (mitama/build-schema-status-stmt "" false ""))))

  (testing "table filter only"
    (let [stmt (mitama/build-schema-status-stmt "vertex_actor_manifest" false "")]
      (is (str/includes? stmt "WHERE"))
      (is (str/includes? stmt "TableName = 'vertex_actor_manifest'"))))

  (testing "state filter only"
    (let [stmt (mitama/build-schema-status-stmt "" false "running")]
      (is (str/includes? stmt "WHERE"))
      (is (str/includes? stmt "State = 'RUNNING'"))))

  (testing "both table and state filters"
    (let [stmt (mitama/build-schema-status-stmt "vertex_actor" false "finished")]
      (is (str/includes? stmt "WHERE"))
      (is (str/includes? stmt "TableName = 'vertex_actor'"))
      (is (str/includes? stmt "AND"))
      (is (str/includes? stmt "State = 'FINISHED'"))))

  (testing "all-tables? true → table filter skipped even when table specified"
    (let [stmt (mitama/build-schema-status-stmt "vertex_actor" true "")]
      (is (= "SHOW ALTER TABLE COLUMN FROM graphar" stmt))))

  (testing "state is uppercased"
    (let [stmt (mitama/build-schema-status-stmt "" false "cancelled")]
      (is (str/includes? stmt "State = 'CANCELLED'"))))

  (testing "single-quote in table/state is escaped"
    (let [stmt (mitama/build-schema-status-stmt "it's_table" false "")]
      (is (str/includes? stmt "it''s_table")))))

(deftest test-clamp-timeout-ms
  ;; Parity: max(1000, min(60000, timeout_sec * 1000))
  (testing "below lower bound → 1000"
    (is (= 1000 (mitama/clamp-timeout-ms 0)))
    (is (= 1000 (mitama/clamp-timeout-ms -5))))

  (testing "midrange value → seconds × 1000"
    (is (= 30000 (mitama/clamp-timeout-ms 30))))

  (testing "above upper bound → 60000"
    (is (= 60000 (mitama/clamp-timeout-ms 100)))
    (is (= 60000 (mitama/clamp-timeout-ms 1000)))))

(deftest test-build-set-status-body
  (testing "returns map with id and status"
    (let [body (mitama/build-set-status-body "did:web:actor" "dormant")]
      (is (= "did:web:actor" (:id body)))
      (is (= "dormant" (:status body))))))

(deftest test-build-shinka-payload
  ;; Parity with Python: payload = {}; if model: payload['model'] = model

  (testing "empty model → empty map"
    (is (= {} (mitama/build-shinka-payload "")))
    (is (= {} (mitama/build-shinka-payload nil))))

  (testing "non-empty model → {:model model}"
    (is (= {:model "gemma3:4b"} (mitama/build-shinka-payload "gemma3:4b")))))

;; ─────────────────────────────────────────────────────────────────────────────
;; etzhayyim.mitama  IO request-shaping
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-build-register-request
  (testing "POST with data body and auth header"
    (let [data {"nanoid" "n1" "name" "Actor"}
          req  (mitama/build-register-request "https://pds.example.com" "tok" data)]
      (is (= :post (:method req)))
      (is (= "https://pds.example.com/xrpc/com.etzhayyim.actor.register" (:url req)))
      (is (= "Bearer tok" (get-in req [:headers "Authorization"])))
      (is (= data (:body req))))))

(deftest test-build-list-actors-request
  (testing "GET with limit param"
    (let [req (mitama/build-list-actors-request "https://pds.example.com" "tok" {:limit 50})]
      (is (= :get (:method req)))
      (is (str/includes? (:url req) "listActors"))
      (is (= "50" (get-in req [:params "limit"])))))

  (testing "default limit 100"
    (let [req (mitama/build-list-actors-request "https://pds.example.com" "tok" {})]
      (is (= "100" (get-in req [:params "limit"]))))))

(deftest test-build-inspect-request
  (testing "GET with id param"
    (let [req (mitama/build-inspect-request "https://pds.example.com" "tok" "abc123")]
      (is (= :get (:method req)))
      (is (str/includes? (:url req) "getActor"))
      (is (= "abc123" (get-in req [:params "id"]))))))

(deftest test-build-set-status-request
  (testing "POST with id and status in body"
    (let [req (mitama/build-set-status-request "https://pds.example.com" "tok" "n1" "dormant")]
      (is (= :post (:method req)))
      (is (str/includes? (:url req) "setStatus"))
      (is (= "n1"      (get-in req [:body :id])))
      (is (= "dormant" (get-in req [:body :status]))))))

(deftest test-build-shinka-request
  (testing "POST with empty payload when no model"
    (let [req (mitama/build-shinka-request "https://pds.example.com" "tok" "")]
      (is (= :post (:method req)))
      (is (str/includes? (:url req) "shinka"))
      (is (= {} (:body req)))))

  (testing "POST with model in payload"
    (let [req (mitama/build-shinka-request "https://pds.example.com" "tok" "gemma3:4b")]
      (is (= {:model "gemma3:4b"} (:body req))))))

(deftest test-build-schema-status-request
  (testing "POST with statement and timeoutMs in body"
    (let [req (mitama/build-schema-status-request
               "https://pds.example.com" "tok"
               "vertex_actor_manifest" false "running" 30)]
      (is (= :post (:method req)))
      (is (str/includes? (:url req) "kagami.sql"))
      (is (str/includes? (get-in req [:body :statement]) "TableName"))
      (is (str/includes? (get-in req [:body :statement]) "State = 'RUNNING'"))
      (is (= 30000 (get-in req [:body :timeoutMs]))))))

(deftest test-set-actor-status-dry-run
  (testing "dry-run: request shape returned, http-fn NOT called"
    (let [{:keys [log http-fn]} (make-fake-http)
          result (mitama/set-actor-status "https://pds.example.com" "tok"
                                           "n1" "dormant"
                                           {:dry-run? true :http-fn http-fn})]
      (is (empty? @log) "http-fn must NOT be called in dry-run mode")
      (is (true? (:dry-run result)))
      (is (= :post (get-in result [:request :method]))))))

(deftest test-run-shinka-dry-run
  (testing "dry-run: request shape returned, http-fn NOT called"
    (let [{:keys [log http-fn]} (make-fake-http)
          result (mitama/run-shinka "https://pds.example.com" "tok" ""
                                     {:dry-run? true :http-fn http-fn})]
      (is (empty? @log) "http-fn must NOT be called in dry-run mode")
      (is (true? (:dry-run result)))
      (is (= {} (get-in result [:request :body]))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; etzhayyim.yoroshiku  PURE
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-compute-readiness-checks
  ;; Parity with Python _run_readiness() checks order and text.

  (testing "all passing"
    (let [checks (yoroshiku/compute-readiness-checks
                  {:deps-toml true :claude-md true :apps-dir true :app-count 42 :auth true})]
      (is (= 4 (count checks)))
      (is (every? :ok checks))
      (is (= "deps.toml" (:name (nth checks 0))))
      (is (= "CLAUDE.md" (:name (nth checks 1))))
      (is (= "60-apps"   (:name (nth checks 2))))
      (is (= "authn"     (:name (nth checks 3))))
      ;; detail text parity
      (is (= "deps.toml found" (:detail (nth checks 0))))
      (is (= "CLAUDE.md found" (:detail (nth checks 1))))
      (is (= "42 apps"         (:detail (nth checks 2))))
      (is (= "signed in"       (:detail (nth checks 3))))))

  (testing "all failing"
    (let [checks (yoroshiku/compute-readiness-checks
                  {:deps-toml false :claude-md false :apps-dir false :app-count 0 :auth false})]
      (is (every? #(false? (:ok %)) checks))
      (is (= "deps.toml missing" (:detail (nth checks 0))))
      (is (= "CLAUDE.md missing" (:detail (nth checks 1))))
      (is (= "missing"           (:detail (nth checks 2))))
      (is (= "not signed in"     (:detail (nth checks 3))))))

  (testing "mixed: deps+claude ok but no apps or auth"
    (let [checks (yoroshiku/compute-readiness-checks
                  {:deps-toml true :claude-md true :apps-dir false :app-count 0 :auth false})]
      (is (:ok (nth checks 0)))
      (is (:ok (nth checks 1)))
      (is (false? (:ok (nth checks 2))))
      (is (false? (:ok (nth checks 3))))))

  (testing "missing :app-count defaults to 0"
    (let [checks (yoroshiku/compute-readiness-checks
                  {:deps-toml true :claude-md false :apps-dir true :auth true})]
      (is (= "0 apps" (:detail (nth checks 2)))))))

(deftest test-build-register-request
  (testing "POST to registerWorkspace with workspace in body"
    (let [req (yoroshiku/build-register-request
               "https://pds.example.com" "/path/to/workspace" "tok123")]
      (is (= :post (:method req)))
      (is (= "https://pds.example.com/xrpc/com.etzhayyim.yoroshiku.registerWorkspace"
             (:url req)))
      (is (= "Bearer tok123" (get-in req [:headers "Authorization"])))
      (is (= "application/json" (get-in req [:headers "Content-Type"])))
      (is (= {:workspace "/path/to/workspace"} (:body req))))))

(deftest test-format-check-line
  (testing "[OK  ] format"
    (let [line (yoroshiku/format-check-line {:name "deps.toml" :ok true :detail "found"})]
      (is (str/includes? line "[OK  ]"))
      (is (str/includes? line "deps.toml"))
      (is (str/includes? line "found"))))

  (testing "[WARN] format"
    (let [line (yoroshiku/format-check-line {:name "authn" :ok false :detail "not signed in"})]
      (is (str/includes? line "[WARN]"))
      (is (str/includes? line "not signed in")))))

(deftest test-format-readiness-summary
  (testing "passing/total string"
    (let [checks [{:ok true} {:ok false} {:ok true} {:ok true}]
          s      (yoroshiku/format-readiness-summary checks)]
      (is (str/includes? s "3/4"))
      (is (str/includes? s "よろしく"))))

  (testing "all failing"
    (let [checks [{:ok false} {:ok false}]
          s      (yoroshiku/format-readiness-summary checks)]
      (is (str/includes? s "0/2"))))

  (testing "all passing"
    (let [checks (repeat 4 {:ok true})
          s      (yoroshiku/format-readiness-summary checks)]
      (is (str/includes? s "4/4")))))

;; ─────────────────────────────────────────────────────────────────────────────
;; etzhayyim.yoroshiku  IO request-shaping
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-run-readiness-checks-injectable-fs
  (testing "run-readiness-checks uses injected :fs-fn (no real fs access)"
    (let [fake-fs-fn (fn [_dir]
                       {:deps-toml true
                        :claude-md true
                        :apps-dir  true
                        :app-count 7
                        :auth      false})
          checks     (yoroshiku/run-readiness-checks "/some/workspace"
                                                      {:fs-fn fake-fs-fn})]
      (is (= 4 (count checks)))
      (is (:ok (first checks)))       ; deps-toml
      (is (:ok (second checks)))      ; claude-md
      (is (:ok (nth checks 2)))       ; apps-dir
      (is (false? (:ok (last checks)))) ; auth = false
      (is (= "7 apps" (:detail (nth checks 2)))))))

(deftest test-register-workspace-dry-run
  (testing "dry-run: request shape returned, http-fn NOT called"
    (let [{:keys [log http-fn]} (make-fake-http)
          result (yoroshiku/register-workspace
                  "https://pds.example.com" "tok" "/workspace"
                  {:dry-run? true :http-fn http-fn})]
      (is (empty? @log) "http-fn must NOT be called in dry-run mode")
      (is (true? (:dry-run result)))
      (is (= :post (get-in result [:request :method]))))))

(deftest test-register-workspace-live-fires-post
  (testing "live: POST sent to correct URL with workspace in body"
    (let [{:keys [log http-fn]}
          (make-fake-http [(json/generate-string {"id" "ws-123"})])
          _ (yoroshiku/register-workspace
             "https://pds.example.com" "tok" "/my/workspace"
             {:http-fn http-fn})
          req (first @log)]
      (is (= 1 (count @log)))
      (is (= :post (:method req)))
      (is (str/includes? (:url req) "registerWorkspace"))
      (is (= {:workspace "/my/workspace"} (:body req))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; Zero-mutation dry-run invariant (cross-module)
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-pure-builders-never-call-http-fn
  ;; Calling shape-layer functions never invokes the http-fn.
  (testing "all build-* pure fns produce zero http-fn calls"
    (let [{:keys [log http-fn]} (make-fake-http)
          ;; cohort
          _  (cohort/build-gen-request "https://pds.example.com" "tok"
                                        (cohort/build-gen-segment "a" "b" "c" "d" "e" 1))
          _  (cohort/build-list-request "https://pds.example.com" "tok" {})
          _  (cohort/build-fission-request "https://pds.example.com" "tok" "x" {})
          _  (cohort/build-diff-request "https://pds.example.com" "tok" {})
          ;; nono
          _  (nono/build-register-manifest-request "https://pds.example.com" "tok" {})
          ;; mitama
          _  (mitama/build-register-request "https://pds.example.com" "tok" {})
          _  (mitama/build-list-actors-request "https://pds.example.com" "tok" {})
          _  (mitama/build-inspect-request "https://pds.example.com" "tok" "x")
          _  (mitama/build-set-status-request "https://pds.example.com" "tok" "x" "dormant")
          _  (mitama/build-shinka-request "https://pds.example.com" "tok" "")
          _  (mitama/build-schema-status-request "https://pds.example.com" "tok" "" false "" 30)
          ;; yoroshiku
          _  (yoroshiku/build-register-request "https://pds.example.com" "/ws" "tok")]
      (is (empty? @log)
          "pure request-builder fns must NEVER invoke the http-fn"))))

;; ─── run ──────────────────────────────────────────────────────────────────────

(defn -main [& _args]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-bb-migration-wave8a)]
    (System/exit (if (zero? (+ fail error)) 0 1))))

(when (= *file* (System/getProperty "babashka.file"))
  (-main))
