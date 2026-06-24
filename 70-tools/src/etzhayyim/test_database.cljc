;; etzhayyim.test-database — database pure-helper invariants (cljc port).
;; Run: bb test:database
;; Covers the pure helpers (XRPC/subprocess/env legs are IO-deferred):
;; redact-url · validate-migrator-args! · build-git-root-command ·
;; build-kysely-migrate-command · build-xrpc-get-request · build-xrpc-post-request.
(ns etzhayyim.test-database
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.database :as db]))

(deftest redact-url-strips-password
  (testing "password is replaced with *** for postgres/postgresql URLs"
    (is (= "postgres://root:***@127.0.0.1:14566/dev"
           (db/redact-url "postgres://root:secret@127.0.0.1:14566/dev")))
    (is (= "postgresql://u:***@h/db" (db/redact-url "postgresql://u:p@h/db"))))
  (testing "passwordless URLs and empty/nil are returned unchanged"
    (is (= "postgres://root@127.0.0.1/dev" (db/redact-url "postgres://root@127.0.0.1/dev")))
    (is (= "" (db/redact-url "")))
    (is (nil? (db/redact-url nil)))))

(deftest validate-migrator-args
  (testing "a valid subcommand returns nil (no throw)"
    (is (nil? (db/validate-migrator-args! ["latest"])))
    (is (nil? (db/validate-migrator-args! ["to" "00010"]))))
  (testing "empty args throw"
    (is (thrown? clojure.lang.ExceptionInfo (db/validate-migrator-args! []))))
  (testing "an unknown subcommand throws"
    (is (thrown? clojure.lang.ExceptionInfo (db/validate-migrator-args! ["bogus"])))))

(deftest argv-command-builders
  (testing "git-root command is a fixed argv vector"
    (is (= ["git" "rev-parse" "--show-toplevel"] (db/build-git-root-command))))
  (testing "kysely migrate command builds injection-safe argv + DATABASE_URL env"
    (is (= {:argv ["node" "--loader=ts-node/esm" "/schema/scripts/migrate.ts" "latest"]
            :env  {"DATABASE_URL" "postgres://x"}}
           (db/build-kysely-migrate-command "/schema" "postgres://x" ["latest"])))))

(deftest xrpc-request-shaping
  (testing "GET strips a trailing slash and attaches bearer auth"
    (is (= {:method  :get
            :url     "https://pds.example/xrpc/com.atproto.repo.listRecords"
            :headers {"Authorization" "Bearer tok" "Content-Type" "application/json"}}
           (db/build-xrpc-get-request "https://pds.example/" "tok"
                                      "com.atproto.repo.listRecords"))))
  (testing "POST adds the body"
    (let [r (db/build-xrpc-post-request "https://pds.example" "tok" "com.x" {"k" 1})]
      (is (= :post (:method r)))
      (is (= "https://pds.example/xrpc/com.x" (:url r)))
      (is (= {"k" 1} (:body r))))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-database)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
