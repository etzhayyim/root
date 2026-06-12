(ns yoro-ui.state.history
  (:require [re-frame.core :as rf]
            [yoro-ui.interop.atproto :as at]))

(def dedup-window-ms (* 60 60 1000))
(def collection "com.etzhayyim.apps.yoro.browsingHistory")

(rf/reg-sub
  :history/entries
  (fn [db _]
    (get-in db [:history :entries] [])))

(rf/reg-sub
  :history/is-loaded?
  (fn [db _]
    (get-in db [:history :is-loaded?] false)))

(rf/reg-sub
  :history/is-loading?
  (fn [db _]
    (get-in db [:history :is-loading?] false)))

(rf/reg-event-db
  :history/set-loading
  (fn [db [_ loading?]]
    (assoc-in db [:history :is-loading?] loading?)))

(rf/reg-event-db
  :history/set-entries
  (fn [db [_ entries]]
    (-> db
        (assoc-in [:history :entries] entries)
        (assoc-in [:history :is-loaded?] true)
        (assoc-in [:history :is-loading?] false))))

(rf/reg-event-fx
  :history/record-visit
  (fn [{:keys [db]} [_ {:keys [path] :as entry}]]
    (let [now (.now js/Date)
          recent-paths (get-in db [:history :recent-paths] {})
          last-visit (get recent-paths path)]
      (if (and last-visit (< (- now last-visit) dedup-window-ms))
        {} ; Deduplicate
        (let [visited-at (.toISOString (js/Date. now))
              new-entry (assoc entry :visitedAt visited-at)
              entries (get-in db [:history :entries] [])
              filtered-entries (remove #(= (:path %) path) entries)
              new-entries (take 200 (cons new-entry filtered-entries))]
          {:db (-> db
                   (assoc-in [:history :entries] new-entries)
                   (assoc-in [:history :recent-paths path] now))
           ;; Dispatch interop event to write to PDS
           :dispatch [:history/write-to-pds "com.etzhayyim.apps.yoro.browsingHistory" new-entry]})))))

(rf/reg-event-fx
  :history/write-to-pds
  (fn [_ [_ coll record]]
    ;; Fire-and-forget createRecord. Signed-out → no XRPC (401-noise rule),
    ;; entry stays local-only (parity with svelte history.svelte.ts).
    (if (at/get-session)
      {:atproto/procedure {:nsid "com.atproto.repo.createRecord"
                           :body {:collection coll :record record}
                           :on-failure [:history/pds-noop]}}
      {})))

(rf/reg-event-db
  :history/pds-noop
  (fn [db _] db))

(rf/reg-event-fx
  :history/load
  (fn [{:keys [db]} _]
    (if (get-in db [:history :is-loading?])
      {}
      {:db (assoc-in db [:history :is-loading?] true)
       ;; Dispatch interop event to list records
       :dispatch [:history/load-from-pds]})))

(rf/reg-event-fx
  :history/load-from-pds
  (fn [_ _]
    ;; Graph query (BrowsingHistory nodes, newest first) when signed in;
    ;; signed-out → empty (local-only), no XRPC fired.
    (if-let [did (:did (at/get-session))]
      {:atproto/procedure
       {:nsid "com.etzhayyim.kagami.graph.query"
        :body {:statement (str "MATCH (h:BrowsingHistory) WHERE h.repo = $did "
                               "RETURN h ORDER BY h.created_at DESC LIMIT 200")
               :parameters {:did did}}
        :on-success [:history/load-success]
        :on-failure [:history/load-failure]}}
      {:dispatch [:history/set-entries []]})))

(rf/reg-event-fx
  :history/load-success
  (fn [_ [_ resp]]
    (let [rows (or (:rows resp) (:results resp) [])
          entries (mapv (fn [row]
                          (let [h (or (:h row) row)]
                            {:path (:path h)
                             :title (:title h)
                             :history_type (:history_type h)
                             :avatar (:avatar h)
                             :handle (:handle h)
                             :visitedAt (:created_at h)
                             :rkey (:rkey h)}))
                        rows)]
      {:dispatch [:history/set-entries entries]})))

(rf/reg-event-fx
  :history/load-failure
  (fn [_ _]
    ;; fail-open: degrade to local-only
    {:dispatch [:history/set-entries []]}))

(rf/reg-event-fx
  :history/remove-entry
  (fn [{:keys [db]} [_ path]]
    (let [entries (get-in db [:history :entries] [])
          entry-to-remove (first (filter #(= (:path %) path) entries))
          new-entries (remove #(= (:path %) path) entries)]
      (merge
       {:db (assoc-in db [:history :entries] new-entries)}
       (when-let [rkey (:rkey entry-to-remove)]
         {:dispatch [:history/delete-from-pds rkey]})))))

(rf/reg-event-fx
  :history/delete-from-pds
  (fn [_ [_ rkey]]
    (if (at/get-session)
      {:atproto/procedure {:nsid "com.atproto.repo.deleteRecord"
                           :body {:collection collection :rkey rkey}
                           :on-failure [:history/pds-noop]}}
      {})))

(rf/reg-event-fx
  :history/clear
  (fn [{:keys [db]} _]
    (let [entries (get-in db [:history :entries] [])
          to-delete (filter :rkey entries)]
      {:db (-> db
               (assoc-in [:history :entries] [])
               (assoc-in [:history :recent-paths] {}))
       :dispatch [:history/clear-pds-records (map :rkey to-delete)]})))

(rf/reg-event-fx
  :history/clear-pds-records
  (fn [_ [_ rkeys]]
    {:fx (mapv (fn [rkey] [:dispatch [:history/delete-from-pds rkey]])
               (filter some? rkeys))}))
