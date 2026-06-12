(ns yoro-ui.state.inference-consent
  "Port of svelte/src/lib/components/inference-consent-state.svelte.ts —
   module-singleton consent gate re-expressed as re-frame state.

   Consent flow:
   1. Caller awaits (request-consent!).
   2. If localStorage 'yoro-inference-tos-accepted' = 'accepted', resolves immediately.
   3. Otherwise the InferenceConsent modal becomes visible.
   4. On accept: localStorage set, promise resolves true.
   5. On decline: promise never resolves (caller simply does nothing)."
  (:require [re-frame.core :as rf]))

(def storage-key "yoro-inference-tos-accepted")
(def llm-enabled-key "yoro-local-llm-enabled")

;; pending promise-resolve callback (module singleton, like _onAccept)
(defonce on-accept (atom nil))

(rf/reg-sub
 :inference-consent/visible?
 (fn [db _]
   (get-in db [:inference-consent :visible?] false)))

(rf/reg-event-db
 :inference-consent/show
 (fn [db _]
   (assoc-in db [:inference-consent :visible?] true)))

(rf/reg-event-db
 :inference-consent/accept
 (fn [db _]
   (when (exists? js/window)
     (try (.setItem js/localStorage storage-key "accepted") (catch js/Error _)))
   (when-let [cb @on-accept]
     (reset! on-accept nil)
     (cb))
   (assoc-in db [:inference-consent :visible?] false)))

(rf/reg-event-db
 :inference-consent/decline
 (fn [db _]
   (reset! on-accept nil)
   (assoc-in db [:inference-consent :visible?] false)))

(defn has-consent? []
  (if-not (exists? js/window)
    false
    (= "accepted"
       (try (.getItem js/localStorage storage-key) (catch js/Error _ nil)))))

(defn revoke-consent!
  "Revoke inference consent and disable LLM auto-load."
  []
  (when (exists? js/window)
    (try
      (.removeItem js/localStorage storage-key)
      (.removeItem js/localStorage llm-enabled-key)
      (catch js/Error _))))

(defn request-consent!
  "Returns a js/Promise resolving true on accept; never resolves on decline."
  []
  (if (has-consent?)
    (js/Promise.resolve true)
    (js/Promise.
     (fn [resolve _reject]
       (reset! on-accept #(resolve true))
       (rf/dispatch [:inference-consent/show])))))
