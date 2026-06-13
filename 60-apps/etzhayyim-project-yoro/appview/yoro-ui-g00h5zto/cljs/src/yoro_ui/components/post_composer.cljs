(ns yoro-ui.components.post-composer
  "Post compose modal — com.atproto.repo.createRecord (app.bsky.feed.post)."
  (:require [reagent.core :as r]
            [re-frame.core :as rf]
            [yoro-ui.interop.atproto :as at]))

(def ^:private MAX-CHARS 300)

(defn- grapheme-length [^string s]
  (try
    (count (js/Array.from s))
    (catch js/Error _ (.-length s))))

;; ---------------------------------------------------------------------------
;; Events

(rf/reg-event-fx
 :composer/submit
 (fn [{:keys [db]} [_ text]]
   (let [did (get-in db [:auth :session :did] "")]
     {:db (assoc-in db [:composer :posting?] true)
      :atproto/procedure {:nsid "com.atproto.repo.createRecord"
                          :body {:repo did
                                 :collection "app.bsky.feed.post"
                                 :record {:$type "app.bsky.feed.post"
                                          :text text
                                          :createdAt (.toISOString (js/Date.))}}
                          :on-success [:composer/posted]
                          :on-failure [:composer/post-failed]}})))

(rf/reg-event-fx
 :composer/posted
 (fn [{:keys [db]} _]
   {:db (-> db
            (assoc-in [:composer :posting?] false)
            (assoc-in [:composer :open?] false))
    ;; refresh home feed
    :fx [[:dispatch [:feed/fetch]]]}))

(rf/reg-event-db
 :composer/post-failed
 (fn [db [_ err]]
   (-> db
       (assoc-in [:composer :posting?] false)
       (assoc-in [:composer :error]
                 (or (get-in err [:message]) "投稿に失敗しました")))))

(rf/reg-event-db :composer/open  (fn [db _] (assoc-in db [:composer :open?] true)))
(rf/reg-event-db :composer/close (fn [db _] (assoc-in db [:composer :open?] false)))

(rf/reg-sub :composer/open?    (fn [db _] (get-in db [:composer :open?] false)))
(rf/reg-sub :composer/posting? (fn [db _] (get-in db [:composer :posting?] false)))
(rf/reg-sub :composer/error    (fn [db _] (get-in db [:composer :error])))

;; ---------------------------------------------------------------------------
;; Progress ring

(defn- char-ring [remaining ratio]
  (let [r    20
        circ (* 2 js/Math.PI r)
        dash (* circ (- 1 ratio))]
    [:svg {:width 44 :height 44 :viewBox "0 0 44 44"}
     [:circle {:cx 22 :cy 22 :r r
               :fill "none"
               :stroke "#2f3336"
               :stroke-width 3}]
     [:circle {:cx 22 :cy 22 :r r
               :fill "none"
               :stroke (cond
                         (neg? remaining) "#f4212e"
                         (< remaining 20) "#ffd400"
                         :else "#1CB0F6")
               :stroke-width 3
               :stroke-dasharray circ
               :stroke-dashoffset dash
               :stroke-linecap "round"
               :transform "rotate(-90 22 22)"}]
     (when (< remaining 20)
       [:text {:x 22 :y 22
               :text-anchor "middle"
               :dominant-baseline "central"
               :font-size 11
               :fill (if (neg? remaining) "#f4212e" "#e7e9ea")}
        remaining])]))

;; ---------------------------------------------------------------------------
;; Component

(defn post-composer []
  (let [text-ref (r/atom "")]
    (fn []
      (let [open?    @(rf/subscribe [:composer/open?])
            posting? @(rf/subscribe [:composer/posting?])
            error    @(rf/subscribe [:composer/error])
            avatar   @(rf/subscribe [:auth/avatar])
            handle   @(rf/subscribe [:auth/handle])
            len      (grapheme-length @text-ref)
            remaining (- MAX-CHARS len)
            ratio    (/ len MAX-CHARS)
            can-post? (and (> len 0) (<= len MAX-CHARS) (not posting?))
            submit!  (fn []
                       (when can-post?
                         (rf/dispatch [:composer/submit @text-ref])
                         (reset! text-ref "")))]
        (when open?
          [:div {:class    "fixed inset-0 z-50 flex items-end sm:items-center justify-center"
                 :on-click #(when (= (.-target %) (.-currentTarget %))
                              (rf/dispatch [:composer/close]))}

           ;; Backdrop
           [:div {:class "absolute inset-0 bg-black/60 backdrop-blur-sm"}]

           ;; Sheet
           [:div {:class "relative z-10 w-full max-w-[600px] bg-gv2-bg-card rounded-t-2xl sm:rounded-2xl shadow-2xl pb-safe"}

            ;; Top bar
            [:div {:class "flex items-center justify-between px-4 py-3 border-b border-gv2-border"}
             [:button {:class    "text-[15px] text-gv2-text-primary font-medium"
                       :on-click #(rf/dispatch [:composer/close])}
              "キャンセル"]
             [:button {:class    (str "px-4 py-1.5 rounded-xl text-[14px] font-bold transition-opacity "
                                      (if can-post?
                                        "bg-[#1CB0F6] text-white"
                                        "bg-[#1CB0F6]/40 text-white/60 cursor-not-allowed"))
                       :disabled (not can-post?)
                       :on-click submit!}
              (if posting? "投稿中…" "投稿")]]

            ;; Body
            [:div {:class "flex gap-3 px-4 py-4"}

             ;; Avatar
             (if avatar
               [:img {:src avatar :class "w-10 h-10 rounded-full flex-shrink-0 object-cover"}]
               [:div {:class "w-10 h-10 rounded-full bg-[#1CB0F6] flex items-center justify-center flex-shrink-0 text-white text-[14px] font-bold"}
                (when handle (first handle))])

             ;; Textarea
             [:div {:class "flex-1 min-w-0"}
              [:textarea {:class       "w-full bg-transparent text-[17px] text-gv2-text-primary placeholder:text-gv2-text-muted resize-none outline-none min-h-[120px]"
                          :placeholder "いまどうしてる？"
                          :auto-focus  true
                          :value       @text-ref
                          :on-change   #(reset! text-ref (.. % -target -value))
                          :on-key-down #(when (and (.-metaKey %) (= (.-key %) "Enter"))
                                          (submit!))}]

              ;; Error
              (when error
                [:p {:class "text-[12px] text-red-400 mt-1"} error])]]

            ;; Bottom toolbar
            [:div {:class "flex items-center justify-between px-4 py-3 border-t border-gv2-border"}
             [:div {:class "flex items-center gap-2"}

              ;; Globe (everyone) icon placeholder
              [:button {:class "w-9 h-9 flex items-center justify-center rounded-full hover:bg-gv2-bg-base text-gv2-text-muted"}
               [:svg {:width 20 :height 20 :viewBox "0 0 24 24" :fill "none" :stroke "currentColor" :stroke-width 1.75}
                [:circle {:cx 12 :cy 12 :r 10}]
                [:path {:d "M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"}]]]]

             ;; Char counter
             [char-ring remaining ratio]]]])))))
