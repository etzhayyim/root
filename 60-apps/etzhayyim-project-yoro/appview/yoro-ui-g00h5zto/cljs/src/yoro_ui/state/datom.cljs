(ns yoro-ui.state.datom
  "re-frame integration for the browser-local kotoba Datom log.

   fx :kotoba/transact  — append EAVT datoms to the local log
   cofx :kotoba/log     — inject current log into coeffects
   sub  :kotoba/head-cid — reactive head CID
   event :kotoba/init   — bind sha256 seam + verify chain on startup"
  (:require [re-frame.core :as rf]
            [kotoba.datom :as d]
            [yoro-ui.kotoba.core :as kotoba]))

;; ---------------------------------------------------------------------------
;; Bootstrap event

(rf/reg-event-fx
 :kotoba/init
 (fn [{:keys [db]} _]
   (let [{:keys [ok length broken-at]} (kotoba/init!)]
     (if ok
       {:db (assoc-in db [:kotoba :status] {:ok true :length length})}
       {:db (assoc-in db [:kotoba :status] {:ok false :broken-at broken-at})
        :fx [[:dispatch [:kotoba/chain-broken broken-at]]]}))))

(rf/reg-event-db
 :kotoba/chain-broken
 (fn [db [_ broken-at]]
   (js/console.error "kotoba: local chain broken at tx" broken-at)
   (assoc-in db [:kotoba :chain-broken] broken-at)))

;; ---------------------------------------------------------------------------
;; Effect: append datoms to the local log

(rf/reg-fx
 :kotoba/transact
 (fn [{:keys [datoms actor as-of]}]
   (when (seq datoms)
     (kotoba/transact! datoms {:actor (or actor "yoro-browser") :as-of as-of}))))

;; ---------------------------------------------------------------------------
;; Coeffect: inject the current log

(rf/reg-cofx
 :kotoba/log
 (fn [coeffects _]
   (assoc coeffects :kotoba-log (kotoba/read-log))))

;; ---------------------------------------------------------------------------
;; Subscriptions

(rf/reg-sub
 :kotoba/head-cid
 (fn [db _]
   (get-in db [:kotoba :head-cid] (kotoba/head-cid))))

(rf/reg-sub
 :kotoba/status
 (fn [db _]
   (get-in db [:kotoba :status])))

;; ---------------------------------------------------------------------------
;; Helpers — build datoms from common yoro events

(defn feed-view-datoms
  "Datoms recording that the user viewed a feed post."
  [uri did]
  [(d/add uri ":view/by" did)
   (d/add uri ":view/at" (.toISOString (js/Date.)))])

(defn like-datoms
  "Datoms for a like action."
  [uri did]
  [(d/add uri ":like/by" did)
   (d/add uri ":like/at" (.toISOString (js/Date.)))])

(defn search-datoms
  "Datoms recording a search query."
  [query did]
  [(d/add (str "search/" (js/Date.now)) ":search/query" query)
   (d/add (str "search/" (js/Date.now)) ":search/by" did)
   (d/add (str "search/" (js/Date.now)) ":search/at" (.toISOString (js/Date.)))])
