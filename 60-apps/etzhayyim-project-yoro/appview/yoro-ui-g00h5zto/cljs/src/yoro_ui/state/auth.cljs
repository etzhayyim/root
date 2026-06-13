(ns yoro-ui.state.auth
  "Auth state — reads the CACAO session from localStorage (no XRPC on bootstrap).
   Session probe rule: never fire com.atproto.server.getSession on unauthenticated
   bootstrap (CLAUDE.md §CRITICAL: Session probe)."
  (:require [re-frame.core :as rf]
            [yoro-ui.interop.atproto :as at]))

(def session-key "yoro-cacao-session")   ; localStorage key written by kotoba auth
(def did-key "yoro-active-did")

;; ---------------------------------------------------------------------------
;; Helpers — read-only localStorage probes

(defn- ls-get [k]
  (when (exists? js/localStorage)
    (try (.getItem js/localStorage k) (catch js/Error _ nil))))

(defn- parse-session [raw]
  (when raw
    (try (js->clj (js/JSON.parse raw) :keywordize-keys true)
         (catch js/Error _ nil))))

(defn read-local-session
  "Read the CACAO session from localStorage without firing any XRPC."
  []
  (or (parse-session (ls-get session-key))
      ;; Fallback: look for the standard AT Protocol accessJwt session shape
      (parse-session (ls-get "atproto-session"))
      nil))

;; ---------------------------------------------------------------------------
;; re-frame subs

(rf/reg-sub
 :auth/session
 (fn [db _]
   (get-in db [:auth :session])))

(rf/reg-sub
 :auth/signed-in?
 (fn [db _]
   (boolean (get-in db [:auth :session :did]))))

(rf/reg-sub
 :auth/did
 (fn [db _]
   (get-in db [:auth :session :did])))

(rf/reg-sub
 :auth/display-name
 (fn [db _]
   (or (get-in db [:auth :session :displayName])
       (get-in db [:auth :session :handle])
       "ゲスト")))

(rf/reg-sub
 :auth/handle
 (fn [db _]
   (get-in db [:auth :session :handle])))

(rf/reg-sub
 :auth/avatar
 (fn [db _]
   (get-in db [:auth :session :avatar])))

;; ---------------------------------------------------------------------------
;; re-frame events

(rf/reg-event-fx
 :auth/bootstrap
 (fn [{:keys [db]} _]
   (let [session (read-local-session)]
     (if session
       {:db (assoc-in db [:auth :session] session)
        :fx [[:dispatch [:auth/wire-atproto-client session]]]}
       {:db (assoc-in db [:auth :session] nil)}))))

(rf/reg-event-fx
 :auth/wire-atproto-client
 (fn [_ [_ session]]
   (at/set-session! session)
   {}))

(rf/reg-event-fx
 :auth/set-session
 (fn [{:keys [db]} [_ session]]
   (at/set-session! session)
   {:db (assoc-in db [:auth :session] session)}))

(rf/reg-event-fx
 :auth/sign-out
 (fn [{:keys [db]} _]
   (when (exists? js/localStorage)
     (try
       (.removeItem js/localStorage session-key)
       (.removeItem js/localStorage "atproto-session")
       (catch js/Error _)))
   (at/set-session! nil)
   {:db (assoc-in db [:auth :session] nil)}))

;; ---------------------------------------------------------------------------
;; Convenience fn for imperative use

(defn signed-in? []
  (boolean (:did (read-local-session))))
