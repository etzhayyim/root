;; test_bb_migration_dns_sync.clj — parity + request-shaping tests for dns_sync.cljc
;;
;; Run with:
;;   bb 70-tools/src/etzhayyim/test_bb_migration_dns_sync.clj
;;
;; from repo root.  classpath 70-tools/src is in bb.edn :paths so no -cp needed.
;;
;; Test coverage:
;;   PURE parity (no network):
;;     - parse-identifier-tables
;;     - build-desired-records
;;     - diff-records
;;     - emit-routing-map-ts
;;     - emit-yoro-mirror-ts
;;     - find-services-range
;;     - patch-wrangler-bindings
;;
;;   IO request-shaping (injectable fake http-fn, no network):
;;     - build-apply-request (create / update / delete / keep)
;;     - cf-get request shape (URL / method / auth header)
;;     - resolve-zone request shape
;;     - list-managed-records pagination request shapes
;;     - apply-one dispatches correct method/url/body per action
;;     - dry-run path (sync-dns :apply? false) builds correct request shapes
;;       without network calls
;;
;;   HONEST NOTE:
;;     Live behavioral parity (whether CF actually accepts the requests and
;;     returns the expected data shapes) requires a live CF token + zone and
;;     CANNOT be verified offline. The request-shaping tests demonstrate that
;;     dns_sync.cljc builds the SAME URLs / headers / body structures as
;;     dns_sync.py (verified by manual cross-comparison in comments below).

(ns etzhayyim.test-bb-migration-dns-sync
  (:require [clojure.test       :refer [deftest is testing run-tests]]
            [clojure.string     :as str]
            [cheshire.core      :as json]
            [etzhayyim.dns-sync :as dns]))

;; ─── helpers ──────────────────────────────────────────────────────────────────

(defn- make-fake-http
  "Returns a fake http-fn + a call-log atom.
   The fake records every call and returns the given fixed-responses in order
   (cycling if more calls than responses).  Each response is {:status :body-str}."
  ([] (make-fake-http []))
  ([fixed-responses]
   (let [log      (atom [])
         resp-idx (atom 0)]
     {:log   log
      :http-fn
      (fn [req]
        (swap! log conj req)
        (if (seq fixed-responses)
          (let [r (nth fixed-responses (mod @resp-idx (count fixed-responses)))]
            (swap! resp-idx inc)
            (if (string? r) {:status 200 :body r} r))
          {:status 200 :body "{}"}))
      })))

(def ^:private sample-actors
  [{:name "alice" :domain "alice.etzhayyim.com" :nanoid "abc123" :did "did:web:alice.etzhayyim.com" :handles []}
   {:name "bob"   :domain "bob.etzhayyim.com"   :nanoid "def456" :did "did:web:bob.etzhayyim.com"   :handles []}
   {:name "carol" :domain "carol.other.com"      :nanoid ""       :did "did:web:carol.other.com"     :handles []}])

(def ^:private sample-legacies
  [{:actor "alice-old" :nanoid "abc123" :handle "alice.etzhayyim.com" :did ""}
   {:actor "bob-old"   :nanoid "def456" :handle "bob.etzhayyim.com"   :did ""}])

;; ─── PURE: parse-identifier-tables ───────────────────────────────────────────

(deftest test-parse-identifier-tables
  (testing "extracts actors and legacies from data map"
    (let [data {"mitama_actors" [{"name" "alice" "domain" "alice.etzhayyim.com"
                                  "nanoid" "abc" "did" "did:web:alice.etzhayyim.com"
                                  "handles" ["alice.etzhayyim.com"]}
                                 {"name" "" "domain" "ignored.etzhayyim.com"}]  ; no name → skipped
                "legacy_nanoids" [{"actor" "old" "nanoid" "xyz" "handle" "old.etzhayyim.com" "did" ""}
                                  {"actor" "" "nanoid" "skip"}]}  ; no actor → skipped
              result (dns/parse-identifier-tables data)]
      (is (= 1 (count (:actors result))))
      (is (= "alice" (:name (first (:actors result)))))
      (is (= "did:web:alice.etzhayyim.com" (:did (first (:actors result)))))
      (is (= ["alice.etzhayyim.com"] (:handles (first (:actors result)))))
      (is (= 1 (count (:legacies result))))
      (is (= "old" (:actor (first (:legacies result)))))
      (is (= "xyz" (:nanoid (first (:legacies result)))))))

  (testing "empty tables return empty vectors"
    (let [{:keys [actors legacies]} (dns/parse-identifier-tables {})]
      (is (empty? actors))
      (is (empty? legacies)))))

;; ─── PURE: build-desired-records ─────────────────────────────────────────────

(deftest test-build-desired-records
  (testing "produces TXT records for in-zone actors with DID"
    (let [recs (dns/build-desired-records sample-actors [] true false "etzhayyim.com")]
      ;; alice and bob are in zone; carol is .other.com → excluded
      (is (= 2 (count recs)))
      (is (every? #(= "TXT" (:type %)) recs))
      (is (= "_atproto.alice.etzhayyim.com" (:name (first recs))))
      (is (= "\"did=did:web:alice.etzhayyim.com\"" (:content (first recs))))
      (is (= 3600 (:ttl (first recs))))
      (is (= false (:proxied (first recs))))
      (is (= "etzhayyim:adr-0013:atproto-verify" (:comment (first recs))))))

  (testing "produces CNAME records for in-zone legacies"
    (let [recs (dns/build-desired-records [] sample-legacies false true "etzhayyim.com")]
      (is (= 2 (count recs)))
      (is (every? #(= "CNAME" (:type %)) recs))
      (is (= "abc123.etzhayyim.com" (:name (first recs))))
      (is (= "alice.etzhayyim.com" (:content (first recs))))
      (is (= true (:proxied (first recs))))))

  (testing "sorts output by name then type"
    (let [recs (dns/build-desired-records sample-actors sample-legacies true true "etzhayyim.com")]
      (let [names (map :name recs)]
        (is (= names (sort names))))))

  (testing "excludes actors with no DID when include-txt? = true"
    (let [no-did-actor {:name "x" :domain "x.etzhayyim.com" :did "" :handles [] :nanoid ""}
          recs (dns/build-desired-records [no-did-actor] [] true false "etzhayyim.com")]
      (is (empty? recs)))))

;; ─── PURE: diff-records ───────────────────────────────────────────────────────

(deftest test-diff-records
  (let [d1 {:name "_atproto.alice.etzhayyim.com" :type "TXT"
             :content "\"did=did:web:alice\"" :ttl 3600 :proxied false
             :comment "etzhayyim:adr-0013:atproto-verify"}
        d2 {:name "_atproto.bob.etzhayyim.com" :type "TXT"
             :content "\"did=did:web:bob\"" :ttl 3600 :proxied false
             :comment "etzhayyim:adr-0013:atproto-verify"}]

    (testing "keep when content and comment match"
      (let [e1 {:name "_atproto.alice.etzhayyim.com" :type "TXT"
                :content "\"did=did:web:alice\"" :comment "etzhayyim:adr-0013:atproto-verify"
                :id "e1-id"}
            plan (dns/diff-records [d1] [e1])]
        (is (= 1 (count plan)))
        (is (= :keep (:action (first plan))))))

    (testing "update when content differs"
      (let [e1-stale {:name "_atproto.alice.etzhayyim.com" :type "TXT"
                      :content "\"did=did:web:alice-OLD\"" :comment "etzhayyim:adr-0013:atproto-verify"
                      :id "e1-id"}
            plan (dns/diff-records [d1] [e1-stale])]
        (is (= 1 (count plan)))
        (is (= :update (:action (first plan))))
        (is (= "e1-id" (:id (:record (first plan)))))))

    (testing "create when record is new"
      (let [plan (dns/diff-records [d1 d2] [])]
        (is (= 2 (count plan)))
        (is (every? #(= :create (:action %)) plan))))

    (testing "delete when existing record not in desired"
      (let [orphan {:name "_atproto.orphan.etzhayyim.com" :type "TXT"
                    :content "\"did=orphan\"" :comment "etzhayyim:adr-0013:atproto-verify"
                    :id "orphan-id"}
            plan (dns/diff-records [] [orphan])]
        (is (= 1 (count plan)))
        (is (= :delete (:action (first plan))))
        (is (str/includes? (:reason (first plan)) "orphan"))))

    (testing "mixed plan"
      (let [e1 {:name "_atproto.alice.etzhayyim.com" :type "TXT"
                :content "\"did=did:web:alice\"" :comment "etzhayyim:adr-0013:atproto-verify"
                :id "id1"}
            orphan {:name "_atproto.removed.etzhayyim.com" :type "TXT"
                    :content "x" :comment "etzhayyim:adr-0013:atproto-verify" :id "id2"}
            plan (dns/diff-records [d1 d2] [e1 orphan])
            by-action (group-by :action plan)]
        (is (= 1 (count (:keep by-action))))
        (is (= 1 (count (:create by-action))))
        (is (= 1 (count (:delete by-action))))))))

;; ─── PURE: emit-routing-map-ts ───────────────────────────────────────────────

(deftest test-emit-routing-map-ts
  (testing "generates valid TS with sorted entries"
    (let [legacies [{:nanoid "zzz" :handle "z.etzhayyim.com"}
                    {:nanoid "aaa" :handle "a.etzhayyim.com"}]
          ts       (dns/emit-routing-map-ts legacies)]
      (is (str/includes? ts "export const LEGACY_NANOID_MAP"))
      (is (str/includes? ts "\"aaa\": \"a.etzhayyim.com\""))
      (is (str/includes? ts "\"zzz\": \"z.etzhayyim.com\""))
      (is (str/includes? ts "PHASE4_DEPRECATE_AT"))
      ;; aaa must come before zzz (sorted)
      (is (< (.indexOf ts "\"aaa\"") (.indexOf ts "\"zzz\""))))))

;; ─── PURE: emit-yoro-mirror-ts ───────────────────────────────────────────────

(deftest test-emit-yoro-mirror-ts
  (testing "generates yoro-mirror TS with resolveLegacyHandle function"
    (let [legacies [{:nanoid "abc" :handle "alice.etzhayyim.com"}]
          ts       (dns/emit-yoro-mirror-ts legacies)]
      (is (str/includes? ts "MIRROR OF"))
      (is (str/includes? ts "resolveLegacyHandle"))
      (is (str/includes? ts "\"abc\": \"alice.etzhayyim.com\""))
      ;; yoro mirror uses trailing semicolons
      (is (str/includes? ts "};"))))

  (testing "routing-map and yoro-mirror differ in footer"
    (let [legacies [{:nanoid "x" :handle "x.etzhayyim.com"}]
          ts-gw   (dns/emit-routing-map-ts legacies)
          ts-yoro (dns/emit-yoro-mirror-ts legacies)]
      (is (str/ends-with? ts-gw "export const PHASE4_DEPRECATE_AT = new Date('2026-10-01T00:00:00Z')\n"))
      (is (str/ends-with? ts-yoro "}\n")))))

;; ─── PURE: find-services-range ───────────────────────────────────────────────

(deftest test-find-services-range
  (testing "finds simple services block"
    (let [src (str "{\n  \"name\": \"test\",\n  \"services\": [\n    {\"binding\": \"A\"}\n  ]\n}")
          [ks ke] (dns/find-services-range src)]
      (is (int? ks))
      (is (int? ke))
      (is (= "\"services\"" (subs src ks (+ ks 10))))
      (is (= \] (.charAt src (dec ke))))))

  (testing "returns nil when no services key"
    (is (nil? (dns/find-services-range "{\"name\": \"test\"}"))))

  (testing "handles nested brackets and strings containing brackets"
    (let [src "{ \"services\": [ {\"x\": \"[fake]\"}, {\"y\": \"v\"} ] }"
          rng (dns/find-services-range src)]
      (is (some? rng))
      (let [[_ ke] rng]
        (is (= \] (.charAt src (dec ke))))))))

;; ─── PURE: patch-wrangler-bindings ───────────────────────────────────────────

(deftest test-patch-wrangler-bindings
  (testing "patches existing services block"
    (let [src    "{\n  \"name\": \"gw\",\n  \"services\": [\n    {\"binding\": \"OLD\"}\n  ]\n}"
          actors [{:name "alice" :domain "alice.etzhayyim.com" :handles [] :did "" :nanoid ""}]
          [patched cnt] (dns/patch-wrangler-bindings src actors)]
      (is (str/includes? patched "WORKER_ALICE"))
      (is (str/includes? patched "etzhayyim-actor-alice"))
      (is (str/includes? patched "PDS_WORKER"))
      (is (str/includes? patched "PLC_DIRECTORY"))
      (is (= 3 cnt))  ; 2 fixed + 1 actor
      (is (not (str/includes? patched "OLD")))))

  (testing "inserts services block when none exists"
    (let [src    "{\"name\": \"gw\"}"
          actors []
          [patched cnt] (dns/patch-wrangler-bindings src actors)]
      (is (str/includes? patched "PDS_WORKER"))
      (is (= 2 cnt))))

  (testing "actor with no handle is skipped"
    (let [src    "{ \"services\": [] }"
          actors [{:name "no-handle" :domain "" :handles [] :did "" :nanoid ""}]
          [patched cnt] (dns/patch-wrangler-bindings src actors)]
      (is (= 2 cnt))  ; only the 2 fixed entries
      (is (not (str/includes? patched "no-handle")))))

  (testing "binding name uppercases and replaces hyphens"
    (let [src    "{ \"services\": [] }"
          actors [{:name "my-actor" :domain "my-actor.etzhayyim.com" :handles [] :did "" :nanoid ""}]
          [patched _] (dns/patch-wrangler-bindings src actors)]
      (is (str/includes? patched "WORKER_MY_ACTOR")))))

;; ─── IO REQUEST-SHAPING: build-apply-request ─────────────────────────────────

(deftest test-build-apply-request
  ;; Parity note: Python _apply_one() uses:
  ;;   create: httpx.post(base, json=rec, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
  ;;   update: httpx.patch(f"{base}/{rec['id']}", json=rec, headers=...)
  ;;   delete: httpx.delete(f"{base}/{rec['id']}", headers=...)
  ;; dns_sync.cljc build-apply-request must produce equivalent structure.

  (let [zone-id "zone123"
        token   "test-token"
        base    (str "https://api.cloudflare.com/client/v4/zones/" zone-id "/dns_records")]

    (testing "create → POST to base URL with full record body"
      (let [rec  {:type "TXT" :name "_atproto.alice.etzhayyim.com"
                  :content "\"did=alice\"" :ttl 3600 :proxied false
                  :comment "etzhayyim:adr-0013:atproto-verify"}
            item {:action :create :record rec}
            req  (dns/build-apply-request zone-id token item)]
        (is (= :post (:method req)))
        (is (= base (:url req)))
        (is (= (str "Bearer " token) (get-in req [:headers "Authorization"])))
        (is (= rec (:body req)))))

    (testing "update → PATCH to base/id with record including :id"
      (let [rec  {:type "TXT" :name "_atproto.alice.etzhayyim.com"
                  :content "\"did=alice-new\"" :ttl 3600 :proxied false
                  :comment "etzhayyim:adr-0013:atproto-verify"
                  :id "record-id-456"}
            item {:action :update :record rec}
            req  (dns/build-apply-request zone-id token item)]
        (is (= :patch (:method req)))
        (is (= (str base "/record-id-456") (:url req)))
        (is (= (str "Bearer " token) (get-in req [:headers "Authorization"])))
        (is (= rec (:body req)))))

    (testing "delete → DELETE to base/id, no body"
      (let [rec  {:type "TXT" :name "_atproto.old.etzhayyim.com"
                  :content "x" :id "del-id-789"}
            item {:action :delete :record rec :existing rec}
            req  (dns/build-apply-request zone-id token item)]
        (is (= :delete (:method req)))
        (is (= (str base "/del-id-789") (:url req)))
        (is (= (str "Bearer " token) (get-in req [:headers "Authorization"])))
        (is (nil? (:body req)))))

    (testing "keep → nil (no request)"
      (let [rec  {:type "TXT" :name "x" :content "x"}
            item {:action :keep :record rec :existing rec}]
        (is (nil? (dns/build-apply-request zone-id token item)))))))

;; ─── IO REQUEST-SHAPING: cf-get (injectable) ─────────────────────────────────

(deftest test-cf-get-request-shape
  ;; Parity note: Python _cf_get(token, url) → httpx.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
  (testing "cf-get shapes the GET request correctly"
    (let [{:keys [log http-fn]} (make-fake-http
                                 [(json/generate-string {:success true :result [{:id "z1"}]})])
          url   "https://api.cloudflare.com/client/v4/zones?name=etzhayyim.com"
          token "my-token"
          _     (dns/cf-get token url {:http-fn http-fn})
          req   (first @log)]
      (is (= :get (:method req)))
      (is (= url (:url req)))
      (is (= "Bearer my-token" (get-in req [:headers "Authorization"])))
      (is (nil? (:body req))))))

;; ─── IO REQUEST-SHAPING: resolve-zone ────────────────────────────────────────

(deftest test-resolve-zone-request-shape
  ;; Parity note: Python _resolve_zone(token, zone_name):
  ;;   url = f"https://api.cloudflare.com/client/v4/zones?name={urllib.parse.quote(zone_name)}"
  (testing "resolve-zone fires GET to zones?name=<zone>"
    (let [{:keys [log http-fn]} (make-fake-http
                                 [(json/generate-string {:success true :result [{:id "zone-abc"}]})])
          zone-id (dns/resolve-zone "tok" "etzhayyim.com" {:http-fn http-fn})
          req     (first @log)]
      (is (= :get (:method req)))
      (is (str/includes? (:url req) "/zones?name="))
      (is (str/includes? (:url req) "etzhayyim"))
      (is (= "zone-abc" zone-id))))

  (testing "resolve-zone throws when success=false"
    (let [{:keys [http-fn]} (make-fake-http
                             [(json/generate-string {:success false :result [] :errors ["not found"]})])]
      (is (thrown? Exception (dns/resolve-zone "tok" "unknown.com" {:http-fn http-fn}))))))

;; ─── IO REQUEST-SHAPING: list-managed-records pagination ─────────────────────

(deftest test-list-managed-records-pagination
  ;; Parity note: Python _list_managed_records paginates with
  ;;   url = f".../{zone_id}/dns_records?per_page=1000&page={page}"
  (testing "list-managed-records paginates correctly"
    (let [page1 (json/generate-string
                 {:result      [{:name "_atproto.a.etzhayyim.com" :type "TXT"
                                 :comment "etzhayyim:adr-0013:atproto-verify"}
                                {:name "other.example.com" :type "A"
                                 :comment "manual-record"}]
                  :result_info {:page 1 :total_pages 2}})
          page2 (json/generate-string
                 {:result      [{:name "_atproto.b.etzhayyim.com" :type "TXT"
                                 :comment "etzhayyim:adr-0013:atproto-verify"}]
                  :result_info {:page 2 :total_pages 2}})
          {:keys [log http-fn]} (make-fake-http [page1 page2])
          recs  (dns/list-managed-records "tok" "zone-id" {:http-fn http-fn})]
      ;; only the etzhayyim-managed records (not the manual one)
      (is (= 2 (count recs)))
      (is (every? #(str/starts-with? (:comment %) "etzhayyim:") recs))
      ;; two API calls made
      (is (= 2 (count @log)))
      ;; first call is page=1, second is page=2
      (is (str/includes? (:url (first @log)) "page=1"))
      (is (str/includes? (:url (second @log)) "page=2"))
      ;; both use per_page=1000 (matches Python's per_page=1000)
      (is (every? #(str/includes? (:url %) "per_page=1000") @log))))

  (testing "list-managed-records stops at single page"
    (let [single (json/generate-string
                  {:result      [{:name "_atproto.x.etzhayyim.com" :type "TXT"
                                  :comment "etzhayyim:adr-0013:atproto-verify"}]
                   :result_info {:page 1 :total_pages 1}})
          {:keys [log http-fn]} (make-fake-http [single])
          recs (dns/list-managed-records "tok" "zone-id" {:http-fn http-fn})]
      (is (= 1 (count recs)))
      (is (= 1 (count @log))))))

;; ─── IO REQUEST-SHAPING: apply-one dispatches ────────────────────────────────

(deftest test-apply-one-dispatches
  (testing "apply-one dispatches create with POST + body"
    (let [{:keys [log http-fn]} (make-fake-http [{:status 200 :body "{}"}])
          rec   {:type "TXT" :name "_atproto.x.etzhayyim.com"
                 :content "\"did=x\"" :ttl 3600 :proxied false
                 :comment "etzhayyim:adr-0013:atproto-verify"}
          item  {:action :create :record rec}]
      (dns/apply-one "tok" "zone-id" item {:http-fn http-fn})
      (is (= 1 (count @log)))
      (is (= :post (:method (first @log))))
      (is (= rec (:body (first @log))))))

  (testing "apply-one raises on HTTP 4xx"
    (let [{:keys [http-fn]} (make-fake-http [{:status 400 :body "{\"errors\":[\"bad\"]}"}])
          rec  {:type "TXT" :name "x" :content "y" :id "id1"}
          item {:action :update :record rec}]
      (is (thrown? Exception (dns/apply-one "tok" "zone-id" item {:http-fn http-fn})))))

  (testing "apply-one skip keep items (no HTTP call)"
    (let [{:keys [log http-fn]} (make-fake-http)
          rec  {:type "TXT" :name "x" :content "y"}
          item {:action :keep :record rec :existing rec}]
      (dns/apply-one "tok" "zone-id" item {:http-fn http-fn})
      (is (empty? @log)))))

;; ─── IO: dry-run (no network) ────────────────────────────────────────────────

(deftest test-dry-run-no-network
  (testing "dry-run calls no http-fn and returns plan structure"
    ;; In dry-run mode, sync-dns must NOT call the http-fn (it needs a token
    ;; to call CF, and dry-run should skip CF entirely when :no-cf? true).
    ;; With :no-cf? true the token is never read either.
    (let [{:keys [log http-fn]} (make-fake-http)
          result (dns/sync-dns sample-actors sample-legacies
                               {:zone-name "etzhayyim.com"
                                :include-txt?    true
                                :include-nanoid? true
                                :no-cf?    true
                                :apply?    false
                                :http-fn   http-fn})]
      (is (= :offline (:mode result)))
      (is (empty? @log) "offline mode must make zero HTTP calls")
      (is (seq (:desired result)))))

  (testing "dry-run with CF mode builds plan but makes no mutation calls"
    ;; The dry-run path in CF mode calls resolve-zone + list-managed-records
    ;; (both reads) but NOT apply-one (write). We verify the exact count.
    (let [zone-resp (json/generate-string {:success true :result [{:id "zone-abc"}]})
          recs-resp (json/generate-string {:result [] :result_info {:page 1 :total_pages 1}})
          {:keys [log http-fn]} (make-fake-http [zone-resp recs-resp])
          ;; Temporarily override token resolution for the test by passing
          ;; actors/legacies that have a zone match, then override resolve-cf-token
          ;; indirectly via the with-redefs mechanism.
          _ (with-redefs [etzhayyim.dns-sync/resolve-cf-token
                          (fn [] {:token "fake-token" :source "test"})]
              (dns/sync-dns sample-actors sample-legacies
                            {:zone-name "etzhayyim.com"
                             :include-txt?    true
                             :include-nanoid? true
                             :no-cf?    false
                             :apply?    false  ; <— DRY RUN
                             :http-fn   http-fn}))]
      ;; exactly 2 read calls (resolve-zone + list-managed-records page 1)
      ;; ZERO write calls (dry-run → no POST/PATCH/DELETE)
      (is (= 2 (count @log)))
      (is (every? #(= :get (:method %)) @log)))))

;; ─── run ──────────────────────────────────────────────────────────────────────

(defn -main [& _args]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-bb-migration-dns-sync)]
    (System/exit (if (zero? (+ fail error)) 0 1))))

(when (= *file* (System/getProperty "babashka.file"))
  (-main))
