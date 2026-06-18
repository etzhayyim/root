(ns yoro-ui.state.auth
  "Auth state — reads the WebAuthn passkey session from sessionStorage (no XRPC on bootstrap).
   Session probe rule: never fire com.atproto.server.getSession on unauthenticated
   bootstrap (CLAUDE.md §CRITICAL: Session probe).
   Key contract (passkey.ts / same-origin-auth.ts):
     sessionStorage 'etzhayyim-auth-session' — live session (cleared on tab close)
     localStorage   'etzhayyim-auth-did'     — DID for display-before-session bootstrap"
  (:require [re-frame.core :as rf]
            [yoro-ui.interop.atproto :as at]))

;; Session lives in sessionStorage (charter: ADR-2606061800 same-origin passkey)
(def session-key "etzhayyim-auth-session")  ; sessionStorage
(def did-key     "etzhayyim-auth-did")       ; localStorage

;; ---------------------------------------------------------------------------
;; Helpers — read-only storage probes

(defn- ss-get [k]
  (when (exists? js/sessionStorage)
    (try (.getItem js/sessionStorage k) (catch js/Error _ nil))))

(defn- ls-get [k]
  (when (exists? js/localStorage)
    (try (.getItem js/localStorage k) (catch js/Error _ nil))))

(defn- parse-session [raw]
  (when raw
    (try (js->clj (js/JSON.parse raw) :keywordize-keys true)
         (catch js/Error _ nil))))

(defn read-local-session
  "Read the passkey session from sessionStorage without firing any XRPC.
   Falls back to localStorage legacy key for backward compat during migration."
  []
  (or (parse-session (ss-get session-key))           ; ← sessionStorage primary
      ;; Legacy fallbacks (removed after all clients have migrated)
      (parse-session (ls-get "yoro-cacao-session"))
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
   ;; Clear sessionStorage primary
   (when (exists? js/sessionStorage)
     (try (.removeItem js/sessionStorage session-key) (catch js/Error _)))
   ;; Clear legacy localStorage keys
   (when (exists? js/localStorage)
     (try
       (.removeItem js/localStorage "yoro-cacao-session")
       (.removeItem js/localStorage "atproto-session")
       (catch js/Error _)))
   (at/set-session! nil)
   {:db (assoc-in db [:auth :session] nil)}))

;; ---------------------------------------------------------------------------
;; Convenience fn for imperative use

(defn signed-in? []
  (boolean (:did (read-local-session))))
