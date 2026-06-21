(ns etzhayyim.explorer.coverage7-test
  "Coverage for the window-coupled data plane (data-base / url) and the live
   sync-base resolution — exercised under a synthetic `globalThis.window`, so no
   jsdom is needed."
  (:require [cljs.test :refer-macros [deftest is testing]]
            [goog.object :as gobj]
            [etzhayyim.explorer.data :as data]
            [etzhayyim.explorer.live :as live]))

(defn- set-window! [o] (gobj/set js/globalThis "window" o))

(deftest data-base-same-origin
  (testing "no override → same-origin ("") and url is the path verbatim"
    (set-window! #js {})
    (is (= "" (data/data-base)))
    (is (= "/organism/vitals.kotoba.edn" (data/url "/organism/vitals.kotoba.edn")))))

(deftest data-base-window-override
  (testing "window.__DATA_BASE__ overrides the origin and prefixes url"
    (set-window! #js {:__DATA_BASE__ "https://etzhayyim.com"})
    (is (= "https://etzhayyim.com" (data/data-base)))
    (is (= "https://etzhayyim.com/kotoba/blocks/bafy"
           (data/url "/kotoba/blocks/bafy")))))

(deftest data-constants
  (is (= "yoro-social-v1" data/default-genesis)))

(deftest live-sync-base-resolution
  (testing "sync-base uses window.__SYNC_BASE__ when set, else falls back to data-base"
    (set-window! #js {:__SYNC_BASE__ "http://localhost:8720"})
    (is (= "http://localhost:8720" (live/sync-base)))
    (set-window! #js {:__DATA_BASE__ "https://etzhayyim.com"})   ; no __SYNC_BASE__
    (is (= "https://etzhayyim.com" (live/sync-base)))
    (set-window! #js {})
    (is (= "" (live/sync-base)))))
