;; etzhayyim.test-deploy — deploy pure-helper invariants (cljc port).
;; Run: bb test:deploy
;; Covers the pure cfg/validation helpers (wrangler/subprocess/env legs deferred):
;; app-id · ui-type · actor-handle · extract-wit-imports ·
;; validate-no-cors · validate-no-pds-hardcode · validate-governance-import.
(ns etzhayyim.test-deploy
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.deploy :as dep]))

(deftest app-id-and-ui-type
  (testing "app-id = nanoid, else name, else empty"
    (is (= "n1" (dep/app-id {"nanoid" "n1" "name" "foo"})))
    (is (= "foo" (dep/app-id {"name" "foo"})))
    (is (= "" (dep/app-id {}))))
  (testing "ui-type defaults to 'appview'"
    (is (= "iframe" (dep/ui-type {"uiType" "iframe"})))
    (is (= "appview" (dep/ui-type {})))))

(deftest actor-handle-derivation
  (testing "profile.handle wins"
    (is (= "myhandle" (dep/actor-handle {"profile" {"handle" "  myhandle  "}} "ignored"))))
  (testing "derives <slug> from etzhayyim-wasm-<slug>-<nanoid> dir name"
    (is (= "cargo" (dep/actor-handle {} "etzhayyim-wasm-cargo-a1b2c3d4"))))
  (testing "no handle / no match → empty string"
    (is (= "" (dep/actor-handle {} "some-other-dir")))
    (is (= "" (dep/actor-handle {} nil)))))

(deftest extract-wit-imports-parsing
  (is (= ["foo:bar/iface" "baz:qux"]
         (dep/extract-wit-imports "import foo:bar/iface;\nimport baz:qux;\ninterface x {}")))
  (is (= [] (dep/extract-wit-imports "")))
  (is (= [] (dep/extract-wit-imports "no imports here"))))

(deftest validate-no-cors-guard
  (testing "passes on clean content"
    (is (nil? (dep/validate-no-cors "const x = 1;" "f.ts"))))
  (testing "throws on a CORS header literal"
    (is (thrown? clojure.lang.ExceptionInfo
                 (dep/validate-no-cors "headers['Access-Control-Allow-Origin'] = '*'" "f.ts")))))

(deftest validate-no-pds-hardcode-guard
  (testing "passes on clean content"
    (is (nil? (dep/validate-no-pds-hardcode "appId: myId" "f.ts"))))
  (testing "throws on a hardcoded 'pds' appId"
    (is (thrown? clojure.lang.ExceptionInfo
                 (dep/validate-no-pds-hardcode "const c = { appId: \"pds\" }" "f.ts")))))

(deftest validate-governance-import-guard
  (testing "passes when the governance import/include is present"
    (is (nil? (dep/validate-governance-import
               "import kotodama:agent/governance@1.0.0;\nworld w {}" "world.wit")))
    (is (nil? (dep/validate-governance-import
               "include kotodama:runtime/kotodama-component@1.0.0;" "world.wit")))
    (is (nil? (dep/validate-governance-import "" "world.wit"))))   ;; blank → skipped
  (testing "throws when neither is present"
    (is (thrown? clojure.lang.ExceptionInfo
                 (dep/validate-governance-import "world w { import other:x; }" "world.wit")))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-deploy)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
