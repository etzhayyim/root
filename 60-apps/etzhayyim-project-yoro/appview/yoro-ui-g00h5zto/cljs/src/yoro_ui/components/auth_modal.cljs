(ns yoro-ui.components.auth-modal
  "Sign-in modal — createSession → localStorage, no getSession probe."
  (:require [reagent.core :as r]
            [re-frame.core :as rf]
            [yoro-ui.interop.atproto :as at]))

;; ---------------------------------------------------------------------------
;; Sign-in event (createSession)

(rf/reg-event-fx
 :auth/sign-in
 (fn [{:keys [db]} [_ {:keys [identifier password]}]]
   {:db (-> db
            (assoc-in [:auth-modal :loading?] true)
            (assoc-in [:auth-modal :error] nil))
    :atproto/procedure {:nsid "com.atproto.server.createSession"
                        :body {:identifier identifier :password password}
                        :on-success [:auth/sign-in-ok]
                        :on-failure [:auth/sign-in-fail]}}))

(rf/reg-event-fx
 :auth/sign-in-ok
 (fn [{:keys [db]} [_ session]]
   (let [key "atproto-session"]
     (try
       (.setItem js/localStorage key (pr-str session))
       (catch js/Error _ nil))
     {:db (-> db
              (assoc-in [:auth-modal :loading?] false)
              (assoc-in [:auth-modal :open?] false))
      :fx [[:dispatch [:auth/set-session session]]]})))

(rf/reg-event-db
 :auth/sign-in-fail
 (fn [db [_ err]]
   (-> db
       (assoc-in [:auth-modal :loading?] false)
       (assoc-in [:auth-modal :error]
                 (or (get-in err [:message])
                     (get-in err [:error])
                     "ログインに失敗しました")))))

(rf/reg-event-db
 :auth-modal/open
 (fn [db _]
   (assoc-in db [:auth-modal :open?] true)))

(rf/reg-event-db
 :auth-modal/close
 (fn [db _]
   (-> db
       (assoc-in [:auth-modal :open?] false)
       (assoc-in [:auth-modal :error] nil))))

(rf/reg-sub :auth-modal/open?   (fn [db _] (get-in db [:auth-modal :open?] false)))
(rf/reg-sub :auth-modal/loading? (fn [db _] (get-in db [:auth-modal :loading?] false)))
(rf/reg-sub :auth-modal/error   (fn [db _] (get-in db [:auth-modal :error])))

;; ---------------------------------------------------------------------------
;; Component

(defn auth-modal []
  (let [id-ref  (r/atom "")
        pw-ref  (r/atom "")
        submit! (fn []
                  (when (and (seq @id-ref) (seq @pw-ref))
                    (rf/dispatch [:auth/sign-in {:identifier @id-ref :password @pw-ref}])))]
    (fn []
      (let [open?    @(rf/subscribe [:auth-modal/open?])
            loading? @(rf/subscribe [:auth-modal/loading?])
            error    @(rf/subscribe [:auth-modal/error])]
        (when open?
          [:div {:class    "fixed inset-0 z-50 flex items-center justify-center"
                 :on-click #(when (= (.-target %) (.-currentTarget %))
                              (rf/dispatch [:auth-modal/close]))}

           ;; Backdrop
           [:div {:class "absolute inset-0 bg-black/50 backdrop-blur-sm"}]

           ;; Card
           [:div {:class "relative z-10 w-[340px] bg-gv2-bg-card rounded-2xl shadow-2xl p-6 mx-4"}

            ;; Close button
            [:button {:class    "absolute top-3 right-3 w-8 h-8 flex items-center justify-center rounded-full hover:bg-gv2-bg-base text-gv2-text-muted"
                      :on-click #(rf/dispatch [:auth-modal/close])}
             "✕"]

            ;; Logo / title
            [:div {:class "text-center mb-6"}
             [:div {:class "text-4xl mb-2"} "🌿"]
             [:h2 {:class "text-[18px] font-bold text-gv2-text-primary"} "yoro へようこそ"]
             [:p {:class "text-[12px] text-gv2-text-muted mt-1"} "Bluesky アカウントでログイン"]]

            ;; Error banner
            (when error
              [:div {:class "mb-4 px-3 py-2 bg-red-500/10 border border-red-400/30 rounded-xl"}
               [:p {:class "text-[12px] text-red-400"} error]])

            ;; Fields
            [:div {:class "space-y-3 mb-4"}
             [:input {:type         "text"
                      :placeholder  "ハンドル or メールアドレス"
                      :class        "w-full px-3 py-2.5 bg-gv2-bg-base rounded-xl text-[14px] text-gv2-text-primary placeholder:text-gv2-text-muted outline-none border border-gv2-border focus:border-[#1CB0F6]"
                      :auto-focus   true
                      :value        @id-ref
                      :on-change    #(reset! id-ref (.. % -target -value))
                      :on-key-down  #(when (= (.-key %) "Tab") nil)}]
             [:input {:type         "password"
                      :placeholder  "パスワード"
                      :class        "w-full px-3 py-2.5 bg-gv2-bg-base rounded-xl text-[14px] text-gv2-text-primary placeholder:text-gv2-text-muted outline-none border border-gv2-border focus:border-[#1CB0F6]"
                      :value        @pw-ref
                      :on-change    #(reset! pw-ref (.. % -target -value))
                      :on-key-down  #(when (= (.-key %) "Enter") (submit!))}]]

            ;; Submit
            [:button {:class    (str "w-full py-2.5 rounded-xl text-[14px] font-bold transition-opacity "
                                     (if loading?
                                       "bg-[#1CB0F6]/50 text-white cursor-not-allowed"
                                       "bg-[#1CB0F6] text-white hover:bg-[#1CB0F6]/90"))
                      :disabled loading?
                      :on-click submit!}
             (if loading? "ログイン中…" "ログイン")]

            ;; Bsky link
            [:p {:class "text-center text-[11px] text-gv2-text-muted mt-4"}
             "アカウントをお持ちでない方は "
             [:a {:href "https://bsky.app" :target "_blank" :rel "noopener"
                  :class "text-[#1CB0F6] underline"}
              "Bluesky"]
             " で作成できます"]]])))))
