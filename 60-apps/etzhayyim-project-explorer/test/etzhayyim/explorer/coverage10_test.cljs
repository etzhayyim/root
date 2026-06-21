(ns etzhayyim.explorer.coverage10-test
  "Coverage for the data plane's fetch I/O wrappers — the last genuinely
   untested logic. A stubbed `globalThis.fetch` returns Response-like objects so
   fetch-text/json/edn/block-bytes + the non-ok error path are exercised without
   real network."
  (:require [cljs.test :refer-macros [deftest is testing async]]
            [goog.object :as gobj]
            [etzhayyim.explorer.data :as data]))

(defn- stub-fetch!
  "Install a fake fetch that resolves a Response-like object."
  [{:keys [ok status text buf] :or {ok true status 200}}]
  (gobj/set js/globalThis "window" #js {})                 ; same-origin data-base
  (gobj/set js/globalThis "fetch"
            (fn [_url _opts]
              (js/Promise.resolve
               #js {:ok ok :status status :url "stub"
                    :text (fn [] (js/Promise.resolve text))
                    :arrayBuffer (fn [] (js/Promise.resolve buf))}))))

(deftest fetch-text-ok
  (stub-fetch! {:text "hello"})
  (async done
    (-> (data/fetch-text "/x")
        (.then (fn [t] (is (= "hello" t)) (done)))
        (.catch (fn [e] (is false (str e)) (done))))))

(deftest fetch-json-parses
  (stub-fetch! {:text "{\"a\":1,\"b\":[2,3]}"})
  (async done
    (-> (data/fetch-json "/x")
        (.then (fn [m] (is (= {:a 1 :b [2 3]} m)) (done)))
        (.catch (fn [e] (is false (str e)) (done))))))

(deftest fetch-edn-parses-and-degrades-tags
  (stub-fetch! {:text "{:k [1 2] :tagged #some/tag 9}"})
  (async done
    (-> (data/fetch-edn "/x")
        (.then (fn [m]
                 (is (= [1 2] (:k m)))
                 (is (= 9 (:tagged m)))            ; unknown tag degrades to its value
                 (done)))
        (.catch (fn [e] (is false (str e)) (done))))))

(deftest fetch-non-ok-rejects
  (stub-fetch! {:ok false :status 404 :text ""})
  (async done
    (-> (data/fetch-text "/missing")
        (.then (fn [_] (is false "should have rejected") (done)))
        (.catch (fn [e] (is (some? e)) (done))))))

(deftest block-bytes-returns-uint8
  (stub-fetch! {:buf (.-buffer (js/Uint8Array. #js [1 2 3 4]))})
  (async done
    (-> (data/block-bytes "bafyblock")
        (.then (fn [u8]
                 (is (instance? js/Uint8Array u8))
                 (is (= 4 (.-length u8)))
                 (done)))
        (.catch (fn [e] (is false (str e)) (done))))))

(deftest root-pointer-fetches-genesis
  (stub-fetch! {:text "{\"genesis\":\"yoro-social-v1\",\"head\":{\"seq\":7}}"})
  (async done
    (-> (data/root-pointer)
        (.then (fn [m]
                 (is (= "yoro-social-v1" (:genesis m)))
                 (is (= 7 (get-in m [:head :seq])))
                 (done)))
        (.catch (fn [e] (is false (str e)) (done))))))
