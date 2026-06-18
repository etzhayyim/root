(ns did-web.router-test
  "Babashka-runnable unit tests for the PURE Worker routing decision. These run
  under bb (run_tests.sh) on the exact .cljc that shadow-cljs compiles into the
  deployed Worker — so the route ownership table is verified without a browser
  or a wrangler deploy."
  (:require [clojure.test :refer [deftest is testing]]
            [did-web.router :as router]))

(defn- r [method path] (:route (router/route {:method method :path path})))

(deftest local-json-and-html-routes-owned
  (testing "the local content/identity surface is owned by the cljs core"
    (is (= :did-json            (r "GET" "/.well-known/did.json")))
    (is (= :donation-json       (r "GET" "/.well-known/donation.json")))
    (is (= :donate-html         (r "GET" "/donate")))
    (is (= :actors-json         (r "GET" "/.well-known/actors.json")))
    (is (= :actors-html         (r "GET" "/actors")))
    (is (= :gov-units-json      (r "GET" "/.well-known/gov-units.json")))
    (is (= :gov-procedures-json (r "GET" "/.well-known/gov-procedures.json")))
    (is (= :organism-html       (r "GET" "/organism")))))

(deftest actor-routes-extract-handle
  (testing "per-actor routes resolve + extract the raw handle segment"
    (is (= {:route :actor-did :handle "tsumugi"}
           (router/route {:method "GET" :path "/actor/tsumugi/did.json"})))
    (is (= {:route :actor-profile :handle "ooyake"}
           (router/route {:method "GET" :path "/actor/ooyake/profile.json"})))
    (is (= {:route :actor-procedures :handle "gov-jp-somu"}
           (router/route {:method "GET" :path "/actor/gov-jp-somu/procedures.json"})))
    (testing "a nested/extra segment is NOT an actor route"
      (is (= :fallback (r "GET" "/actor/x/y/did.json")))
      (is (= :fallback (r "GET" "/actor//did.json"))))))

(deftest gov-html-stays-on-fallback-this-batch
  (testing "/gov (inline HTML) is intentionally still the TS fallback"
    (is (= :fallback (r "GET" "/gov")))))

(deftest ipfs-route-owned
  (testing "the trustless /ipfs/<cid> gateway is owned by the cljs core"
    (is (= {:route :ipfs :cid "bafkreialpha"}
           (router/route {:method "GET" :path "/ipfs/bafkreialpha"})))
    (is (router/method-allowed? :ipfs "HEAD"))
    (is (not (router/method-allowed? :ipfs "POST")))
    (testing "a slash inside the cid segment is not an ipfs route"
      (is (= :fallback (r "GET" "/ipfs/ab/cd"))))))

(deftest io-plumbing-falls-back
  (testing "heavy I/O routes still on the legacy TS handler (next batches)"
    (doseq [p ["/"
               "/kotoba/blocks/bafkreibeta"
               "/kotoba/stats"
               "/xrpc/app.bsky.feed.getTimeline"
               "/xrpc/com.etzhayyim.apps.kotoba.block.put"
               "/some/spa/route"]]
      (is (= :fallback (r "GET" p)) (str p " should fall through to TS")))))

(deftest method-policy
  (testing "owned content routes are GET/HEAD-only; others unconstrained here"
    (is (router/method-allowed? :did-json "GET"))
    (is (router/method-allowed? :did-json "HEAD"))
    (is (not (router/method-allowed? :did-json "POST")))
    (is (not (router/method-allowed? :actor-did "DELETE")))
    (is (router/method-allowed? :fallback "POST"))
    (is (router/method-allowed? :fallback "GET"))))

(deftest trailing-slash-normalized
  (testing "a trailing slash on a static content route does not change ownership"
    (is (= :donate-html (r "GET" "/donate/")))
    (is (= :actors-html (r "GET" "/actors/")))
    (is (= :organism-html (r "GET" "/organism/")))
    (is (= :fallback (r "GET" "/")))))
