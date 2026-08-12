;; etzhayyim.test-yoroshiku — yoroshiku readiness pure invariants (cljc port).
;; Run via the aggregate: bb test:helpers
;; Covers the pure readiness/format/request helpers (fs + HTTP legs deferred):
;; compute-readiness-checks · build-register-request · format-check-line ·
;; format-readiness-summary · the `register` CLI leg's PDS resolution.
(ns etzhayyim.test-yoroshiku
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [cheshire.core  :as json]
            [etzhayyim.auth :as auth]
            [etzhayyim.yoroshiku :as y]))

(deftest readiness-checks-from-signals
  (testing "all-present → 4 OK checks in canonical order"
    (let [cs (y/compute-readiness-checks
              {:deps-toml true :claude-md true :apps-dir true :app-count 5 :auth true})]
      (is (= ["deps.toml" "CLAUDE.md" "60-apps" "authn"] (mapv :name cs)))
      (is (every? :ok cs))
      (is (= "5 apps" (:detail (nth cs 2))))      ;; 60-apps detail shows count
      (is (= "signed in" (:detail (nth cs 3))))))
  (testing "empty signals → all WARN, app-count defaults to 0"
    (let [cs (y/compute-readiness-checks {})]
      (is (every? (complement :ok) cs))
      (is (= "deps.toml missing" (:detail (first cs))))
      (is (= "missing" (:detail (nth cs 2))))
      (is (= "not signed in" (:detail (nth cs 3)))))))

(deftest register-request-shape
  (let [r (y/build-register-request "https://pds.example" "/ws/path" "tok")]
    (is (= :post (:method r)))
    (is (= "https://pds.example/xrpc/com.etzhayyim.yoroshiku.registerWorkspace" (:url r)))
    (is (= "Bearer tok" (get-in r [:headers "Authorization"])))
    (is (= {:workspace "/ws/path"} (:body r)))))

(deftest format-check-line-display
  (is (= "  [OK  ] deps.toml  found" (y/format-check-line {:name "deps.toml" :ok true :detail "found"})))
  (is (= "  [WARN] authn  not signed in"
         (y/format-check-line {:name "authn" :ok false :detail "not signed in"}))))

(deftest readiness-summary-line
  (is (= "yoroshiku (よろしく): 2/3 checks passing"
         (y/format-readiness-summary [{:ok true} {:ok false} {:ok true}])))
  (is (= "yoroshiku (よろしく): 0/0 checks passing" (y/format-readiness-summary []))))

;; ── `register` CLI leg: which PDS gets contacted ─────────────────────────────
;;
;; `register` is the one subcommand that transmits a credential: it sends
;; `Authorization: Bearer $E7M_TOKEN` to whatever host it resolved. So the host
;; must always be one somebody chose — either passed as `--pds`, or the
;; workspace-wide constant `etzhayyim.auth/default-pds`. It must never be a name
;; the CLI invented for itself.
;;
;; The CLI used to fall back to a literal "https://pds.local". `.local` is the
;; mDNS/Bonjour namespace (RFC 6762), so that name is claimable by any host on
;; the same link — `yoroshiku register --execute` on a shared network would hand
;; the bearer token to whoever answered first.
;;
;; These read the dry-run request shape, so nothing is sent.

(defn- register-url
  "Resolve the URL `yoroshiku register` would POST to, via the dry-run leg."
  [& argv]
  (-> (with-out-str (apply y/-main "register" "--json" argv))
      (json/parse-string true)
      (get-in [:request :url])))

(deftest register-never-invents-a-pds-host
  (testing "no --pds → the workspace's chosen default PDS, not an invented name"
    (let [url (register-url "--workspace-dir" "/ws")]
      (is (= (str auth/default-pds "/xrpc/com.etzhayyim.yoroshiku.registerWorkspace")
             url))
      ;; The specific regression: an mDNS-squattable host reached by default.
      (is (not (str/includes? url "pds.local"))
          "register must not default to a .local (mDNS) host")))

  ;; POSITIVE CONTROL — passes both before and after the fix. An explicitly
  ;; supplied --pds was always honoured; if this ever fails, the breakage is in
  ;; flag parsing or URL building, not in the default-host change above.
  (testing "explicit --pds is honoured"
    (is (= "https://pds.example/xrpc/com.etzhayyim.yoroshiku.registerWorkspace"
           (register-url "--pds" "https://pds.example" "--workspace-dir" "/ws"))))

  (testing "explicit --pds is trailing-slash normalized"
    (is (= "https://pds.example/xrpc/com.etzhayyim.yoroshiku.registerWorkspace"
           (register-url "--pds" "https://pds.example///" "--workspace-dir" "/ws"))))

  (testing "blank --pds falls back to the default rather than building a bare path"
    (is (= (str auth/default-pds "/xrpc/com.etzhayyim.yoroshiku.registerWorkspace")
           (register-url "--pds" "  " "--workspace-dir" "/ws")))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-yoroshiku)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
