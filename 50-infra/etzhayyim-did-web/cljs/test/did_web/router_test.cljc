(ns did-web.router-test
  "Babashka-runnable unit tests for the PURE Worker routing decision. These run
  under bb (run_tests.sh) on the exact .cljc that shadow-cljs compiles into the
  deployed Worker — so the route ownership table is verified without a browser
  or a wrangler deploy."
  (:require [clojure.test :refer [deftest is testing]]
            [did-web.router :as router]))

(deftest did-json-owned
  (testing "the entity DID document route is owned by the cljs core"
    (is (= :did-json (:route (router/route {:method "GET"
                                            :path "/.well-known/did.json"}))))
    (is (router/owned? {:method "GET" :path "/.well-known/did.json"}))
    (testing "method does not change ownership (405 is decided in the handler)"
      (is (= :did-json (:route (router/route {:method "POST"
                                              :path "/.well-known/did.json"})))))))

(deftest unowned-routes-fall-back
  (testing "routes the cljs core does not own resolve to :fallback (legacy TS)"
    (doseq [p ["/"
               "/donate"
               "/.well-known/donation.json"
               "/actors"
               "/actor/tsumugi/did.json"
               "/xrpc/app.bsky.feed.getTimeline"
               "/ipfs/bafkreialpha"
               "/kotoba/stats"]]
      (is (= :fallback (:route (router/route {:method "GET" :path p})))
          (str p " should fall through to the TS handler")))))

(deftest trailing-slash-normalized
  (testing "a trailing slash does not change the route (root stays root)"
    (is (= :fallback (:route (router/route {:method "GET" :path "/"}))))
    ;; once /donate is owned this will flip; for now it stays fallback either way
    (is (= (:route (router/route {:method "GET" :path "/donate"}))
           (:route (router/route {:method "GET" :path "/donate/"}))))))
