(ns yoro-ui.pages.profile
  "Profile page — AT Protocol actors + etzhayyim actors (kotoba datom pull)."
  (:require [reagent.core :as r]
            [re-frame.core :as rf]
            [clojure.string :as str]
            [cljs.reader :as reader]
            [yoro-ui.interop.atproto :as at]
            [yoro-ui.kotoba.actor :as kactor]
            [yoro-ui.router :as router]
            [yoro-ui.components.post-card :refer [post-card post-skeleton avatar]]))

;; ===========================================================================
;; AT Protocol profile helpers (shared)
;; ===========================================================================

(defonce profile-cache (atom {}))

(defn- load-profile! [handle-or-did state-atom]
  (when (and (seq handle-or-did) (not (:loading? @state-atom)))
    (swap! state-atom assoc :loading? true :error nil)
    (let [cached (get @profile-cache handle-or-did)]
      (if cached
        (reset! state-atom {:profile cached :loading? false :posts [] :posts-loading? true})
        (-> (at/at-public-query "app.bsky.actor.getProfile" {:actor handle-or-did})
            (.then (fn [resp]
                     (swap! profile-cache assoc handle-or-did resp)
                     (swap! state-atom assoc :profile resp :loading? false)))
            (.catch (fn [e]
                      (swap! state-atom assoc :error (str e) :loading? false))))))))

(defn- load-author-feed! [did state-atom]
  (when did
    (swap! state-atom assoc :posts-loading? true)
    (-> (at/at-public-query "app.bsky.feed.getAuthorFeed"
                            {:actor did :limit 20 :filter "posts_no_replies"})
        (.then (fn [resp]
                 (let [items (or (:feed resp) [])
                       posts (mapv (fn [item]
                                     (let [post (:post item)]
                                       {:uri          (:uri post)
                                        :cid          (:cid post)
                                        :author       (:author post)
                                        :record       (:record post)
                                        :like-count   (get post :likeCount 0)
                                        :repost-count (get post :repostCount 0)
                                        :reply-count  (get post :replyCount 0)
                                        :indexed-at   (:indexedAt post)}))
                                   items)]
                   (swap! state-atom assoc :posts posts :posts-loading? false))))
        (.catch (fn [_]
                  (swap! state-atom assoc :posts-loading? false))))))

;; ===========================================================================
;; Shared sub-components
;; ===========================================================================

(defn- stat-chip [label value path]
  [:button {:class    "flex flex-col items-center hover:opacity-80"
            :on-click (when path #(router/navigate! path))}
   [:span {:class "text-[17px] font-black text-gv2-text-primary"} (str value)]
   [:span {:class "text-[11px] text-gv2-text-muted"} label]])

(defn- profile-action-buttons [profile-init]
  (let [my-did        (rf/subscribe [:auth/did])
        my-handle     (rf/subscribe [:auth/handle])
        signed-in?    (rf/subscribe [:auth/signed-in?])
        following-uri (r/atom (get-in profile-init [:viewer :following]))]
    (fn [profile]
      (let [is-own? (or (= (:did profile) @my-did)
                        (and @my-handle (= (:handle profile) @my-handle)))]
        (cond
          is-own?
          [:button {:class    "px-4 py-1.5 rounded-xl border border-gv2-border text-[13px] font-bold text-gv2-text-primary hover:bg-gv2-bg-card"
                    :on-click #(router/navigate! "/settings")}
           "プロフィール編集"]

          (not @signed-in?)
          [:button {:class    "px-4 py-1.5 rounded-xl bg-[#1CB0F6] text-white text-[13px] font-bold hover:opacity-90"
                    :on-click #(rf/dispatch [:auth-modal/open])}
           "フォロー"]

          :else
          [:div {:class "flex gap-2"}
           [:button
            {:class    (str "px-4 py-1.5 rounded-xl text-[13px] font-bold transition-colors "
                            (if @following-uri
                              "border border-gv2-border text-gv2-text-primary hover:border-red-400 hover:text-red-500"
                              "bg-[#1CB0F6] text-white hover:opacity-90"))
             :on-click (fn []
                         (if @following-uri
                           (let [prev @following-uri
                                 rkey (last (str/split prev #"/"))]
                             (reset! following-uri nil)
                             (-> (at/at-procedure "com.atproto.repo.deleteRecord"
                                                  {:collection "app.bsky.graph.follow" :rkey rkey})
                                 (.catch (fn [_] (reset! following-uri prev)))))
                           (-> (at/at-procedure "com.atproto.repo.createRecord"
                                                {:collection "app.bsky.graph.follow"
                                                 :record     {:$type     "app.bsky.graph.follow"
                                                              :subject   (:did profile)
                                                              :createdAt (.toISOString (js/Date.))}})
                               (.then (fn [r] (reset! following-uri (:uri r))))
                               (.catch (fn [_])))))}
            (if @following-uri "フォロー中" "フォロー")]
           [:button
            {:class    "px-3 py-1.5 rounded-xl border border-gv2-border text-[13px] font-bold text-gv2-text-primary hover:bg-gv2-bg-card"
             :on-click #(router/navigate! "/convo")}
            "DM"]])))))

(defn- profile-header [{:keys [banner avatar-url display-name handle]} profile]
  [:div
   (if (seq banner)
     [:img {:src banner :alt "" :class "w-full h-28 object-cover"}]
     [:div {:class "w-full h-28 bg-gradient-to-r from-[#1CB0F6]/20 to-[#58CC02]/20"}])
   [:div {:class "px-4 -mt-10 flex items-end justify-between"}
    [avatar {:src avatar-url :display-name display-name :size 72}]
    (when profile [profile-action-buttons profile])]])

;; ===========================================================================
;; etzhayyim actor profile sub-components
;; ===========================================================================

(defn- adr-chip [adr]
  [:span {:class "text-[9px] px-1.5 py-0.5 rounded bg-gv2-bg-base border border-gv2-border text-gv2-text-muted font-mono"}
   (str "ADR-" adr)])

(defn- ez-tab-bar [active-tab on-select]
  [:div {:class "flex border-b border-gv2-border"}
   (for [[tab label] [[:posts "投稿"] [:related "関連 Actor"]]]
     ^{:key tab}
     [:button
      {:class    (str "flex-1 py-2.5 text-[13px] font-bold transition-colors "
                      (if (= tab active-tab)
                        "text-[#1CB0F6] border-b-2 border-[#1CB0F6]"
                        "text-gv2-text-muted hover:text-gv2-text-primary"))
       :on-click #(on-select tab)}
      label])])

(defn- actor-chip [actor]
  (let [handle (:handle actor "")
        sn     (str/replace handle #"\.etzhayyim\.com$" "")
        glyph  (:glyph actor "")
        name   (:displayName actor sn)]
    [:button
     {:class    "flex items-center gap-2 px-3 py-2 rounded-xl bg-gv2-bg-card border border-gv2-border hover:border-[#1CB0F6]/50 transition-colors text-left w-full"
      :on-click #(router/navigate! (str "/profile/" handle))}
     [:div {:class "w-[32px] h-[32px] rounded-full bg-gv2-bg-base border border-gv2-border flex items-center justify-center flex-shrink-0"}
      (if (seq glyph)
        [:span {:class "text-[15px]"} glyph]
        [:span {:class "text-[12px] text-gv2-text-muted"} "⬡"])]
     [:div {:class "min-w-0"}
      [:p {:class "text-[12px] font-bold text-gv2-text-primary line-clamp-1"} name]
      [:p {:class "text-[10px] text-gv2-text-muted font-mono"} sn]]]))

(defn- ez-related-tab [shortname actors-all]
  (let [{:keys [follows feeds siblings group]} (kactor/actor-related shortname actors-all)]
    [:div {:class "px-4 py-3 flex flex-col gap-4 pb-20"}

     ;; Group badge
     (when group
       [:div {:class "flex items-center gap-2"}
        [:span {:class "text-[10px] font-bold text-gv2-text-muted uppercase tracking-widest"} "Lineage group"]
        [:span {:class "text-[10px] px-2 py-0.5 rounded-full bg-[#1CB0F6]/10 text-[#1CB0F6] font-mono border border-[#1CB0F6]/20"}
         group]])

     ;; Depends-on
     (when (seq follows)
       [:div
        [:p {:class "text-[11px] font-bold text-gv2-text-muted mb-2"} "⬆ 依存 (ingests from)"]
        [:div {:class "flex flex-col gap-2"}
         (for [a follows] ^{:key (:handle a)} [actor-chip a])]])

     ;; Feeds-into
     (when (seq feeds)
       [:div
        [:p {:class "text-[11px] font-bold text-gv2-text-muted mb-2"} "⬇ 出力先 (feeds into)"]
        [:div {:class "flex flex-col gap-2"}
         (for [a feeds] ^{:key (:handle a)} [actor-chip a])]])

     ;; Siblings
     (when (seq siblings)
       [:div
        [:p {:class "text-[11px] font-bold text-gv2-text-muted mb-2"} "⇄ 同系統 (siblings)"]
        [:div {:class "flex flex-col gap-2"}
         (for [a siblings] ^{:key (:handle a)} [actor-chip a])]])

     (when (not (or (seq follows) (seq feeds) (seq siblings)))
       [:div {:class "py-8 text-center"}
        [:p {:class "text-[13px] text-gv2-text-muted"} "依存関係データなし"]])

     [:p {:class "text-[10px] text-gv2-text-muted font-mono mt-2"}
      "依存グラフは ADR lineage descriptions から静的生成"]]))

(defn- ez-posts-tab [posts posts-loading?]
  (cond
    posts-loading?
    [:div (for [i (range 3)] ^{:key i} [post-skeleton])]

    (empty? posts)
    [:div {:class "py-12 text-center"}
     [:p {:class "text-[13px] text-gv2-text-muted"} "投稿がありません"]
     [:p {:class "text-[11px] text-gv2-text-muted mt-1 font-mono"} "AT Protocol feed empty"]]

    :else
    [:div (for [p posts] ^{:key (:uri p)} [post-card p])]))

;; ===========================================================================
;; etzhayyim actor profile page (kotoba datom pull + tabs)
;; ===========================================================================

(defn- ez-profile-page [handle]
  (let [tab-state   (r/atom :posts)
        posts-state (r/atom {:posts [] :posts-loading? false})
        shortname   (kactor/handle->shortname handle)
        actor-did   (str "did:web:etzhayyim.com:actor:" shortname)]
    (r/create-class
     {:display-name "ez-profile-page"

      :component-did-mount
      (fn [_]
        (rf/dispatch [:ez-actor/load-profile handle])
        (rf/dispatch [:etzhayyim/load-actors])
        ;; Best-effort AT Protocol feed (most etzhayyim actors have postsCount 0)
        (load-author-feed! actor-did posts-state))

      :reagent-render
      (fn [_]
        (let [loading?   @(rf/subscribe [:ez-actor/profile-loading? handle])
              error      @(rf/subscribe [:ez-actor/profile-error handle])
              entity     @(rf/subscribe [:ez-actor/profile handle])
              actors-all @(rf/subscribe [:etzhayyim/actors-all])
              active-tab @tab-state
              {:keys [posts posts-loading?]} @posts-state]

          [:div {:class "flex flex-col"}

           ;; ── Banner ────────────────────────────────────────────────────────
           (let [glyph (get entity ":actor/glyph" "")]
             [:div {:class "w-full h-28 bg-gradient-to-br from-[#1CB0F6]/20 via-[#1CB0F6]/5 to-[#58CC02]/10 flex items-center justify-center"}
              (when (seq glyph)
                [:span {:class "text-[64px] opacity-20 select-none"} glyph])])

           ;; ── Glyph avatar + datom badge ────────────────────────────────────
           (let [glyph (get entity ":actor/glyph" "")]
             [:div {:class "px-4 -mt-10 flex items-end justify-between"}
              [:div {:class "w-[72px] h-[72px] rounded-full bg-gv2-bg-card border-2 border-gv2-border flex items-center justify-center"}
               (if (seq glyph)
                 [:span {:class "text-[32px]"} glyph]
                 [:span {:class "text-[24px] text-gv2-text-muted"} "⬡"])]
              [:span {:class "text-[9px] px-2 py-1 rounded-full bg-[#1CB0F6]/10 text-[#1CB0F6] font-mono border border-[#1CB0F6]/20"}
               "kotoba datom"]])

           (cond
             loading?
             [:div {:class "px-4 py-8 text-center text-gv2-text-muted"} "読み込み中…"]

             error
             [:div {:class "px-4 py-6 text-center"}
              [:p {:class "text-gv2-text-muted text-[13px]"} error]
              [:button {:class    "mt-3 px-4 py-2 rounded-xl bg-[#1CB0F6] text-white text-[13px] font-bold"
                        :on-click #(rf/dispatch [:ez-actor/load-profile handle])}
               "再試行"]]

             entity
             (let [display-name (get entity ":actor/displayName" handle)
                   description  (get entity ":actor/description" "")
                   tier         (get entity ":etzhayyim/tier" "")
                   status       (get entity ":etzhayyim/status" "")
                   primary-lex  (get entity ":etzhayyim/primaryLexicon" "")
                   adr-str      (get entity ":etzhayyim/adr" "")
                   adrs         (try (reader/read-string adr-str) (catch js/Error _ []))]
               [:<>
                ;; Name + handle
                [:div {:class "px-4 mt-3"}
                 [:h1 {:class "text-[20px] font-black text-gv2-text-primary leading-snug"}
                  display-name]
                 [:p {:class "text-[13px] text-gv2-text-muted mt-0.5"} (str "@" handle)]]

                ;; Description
                (when (seq description)
                  [:div {:class "px-4 mt-2"}
                   [:p {:class "text-[13px] text-gv2-text-primary leading-relaxed line-clamp-3"}
                    description]])

                ;; Metadata
                [:div {:class "px-4 mt-3 flex flex-col gap-2"}
                 (when (or (seq tier) (seq status))
                   [:div {:class "flex gap-2 items-center flex-wrap"}
                    (when (seq tier)
                      [:span {:class "text-[11px] px-2 py-1 rounded-lg bg-[#1CB0F6]/10 text-[#1CB0F6] font-bold border border-[#1CB0F6]/20"}
                       (str "Tier-" tier)])
                    (when (seq status)
                      [:span {:class "text-[11px] px-2 py-1 rounded-lg bg-gv2-bg-card border border-gv2-border text-gv2-text-muted font-mono"}
                       status])])

                 (when (seq primary-lex)
                   [:div {:class "p-3 rounded-xl bg-gv2-bg-card border border-gv2-border"}
                    [:div {:class "text-[10px] font-bold text-gv2-text-muted uppercase tracking-widest mb-1"}
                     "Primary Lexicon"]
                    [:code {:class "text-[11px] text-[#1CB0F6] font-mono break-all"}
                     primary-lex]])

                 (when (seq adrs)
                   [:div {:class "p-3 rounded-xl bg-gv2-bg-card border border-gv2-border"}
                    [:div {:class "text-[10px] font-bold text-gv2-text-muted uppercase tracking-widest mb-2"}
                     "ADR References"]
                    [:div {:class "flex gap-1 flex-wrap"}
                     (for [adr adrs] ^{:key adr} [adr-chip adr])]])]

                ;; Tab bar
                [ez-tab-bar active-tab #(reset! tab-state %)]

                ;; Tab content
                (case active-tab
                  :posts   [ez-posts-tab posts posts-loading?]
                  :related [ez-related-tab shortname actors-all])])

             :else
             [:div {:class "px-4 py-8 text-center text-gv2-text-muted"} "読み込み中…"])]))})))

;; ===========================================================================
;; AT Protocol profile page
;; ===========================================================================

(defn- at-profile-page [{:keys [handle]}]
  (let [state       (r/atom {:loading? false :error nil :profile nil
                              :posts [] :posts-loading? false})
        prev-handle (r/atom nil)]
    (r/create-class
     {:display-name "at-profile-page"

      :component-did-mount
      (fn [_]
        (reset! prev-handle handle)
        (load-profile! handle state))

      :component-did-update
      (fn [this]
        (let [new-handle (-> this .-props .-argv (nth 1) :handle)]
          (when (not= new-handle @prev-handle)
            (reset! prev-handle new-handle)
            (reset! state {:loading? false :error nil :profile nil
                           :posts [] :posts-loading? false})
            (load-profile! new-handle state))))

      :reagent-render
      (fn [{:keys [handle]}]
        (let [{:keys [loading? error profile posts posts-loading?]} @state]

          (when (and profile (not posts-loading?) (empty? posts))
            (load-author-feed! (or (:did profile) handle) state))

          [:div {:class "flex flex-col pb-20"}

           (cond
             loading?
             [:div {:class "px-4 py-8 text-center text-gv2-text-muted"} "読み込み中…"]

             error
             [:div {:class "px-4 py-8 text-center"}
              [:p {:class "text-gv2-text-muted"} error]
              [:button {:class    "mt-3 px-4 py-2 rounded-xl bg-[#1CB0F6] text-white text-[13px] font-bold"
                        :on-click #(load-profile! handle state)}
               "再試行"]]

             profile
             [:div
              [profile-header {:banner       (:banner profile)
                               :avatar-url   (:avatar profile)
                               :display-name (:displayName profile)
                               :handle       (:handle profile)}
               profile]

              [:div {:class "px-4 mt-3"}
               [:h1 {:class "text-[20px] font-black text-gv2-text-primary"}
                (or (:displayName profile) (:handle profile))]
               [:p {:class "text-[13px] text-gv2-text-muted"}
                (str "@" (:handle profile))]
               (when-let [desc (:description profile)]
                 [:p {:class "text-[13px] text-gv2-text-primary mt-2 leading-relaxed"}
                  desc])]

              [:div {:class "px-4 mt-3 flex gap-6 border-b border-gv2-border pb-3"}
               [stat-chip "投稿" (get profile :postsCount 0) nil]
               [stat-chip "フォロー" (get profile :followsCount 0)
                (str "/profile/" handle "/follows")]
               [stat-chip "フォロワー" (get profile :followersCount 0)
                (str "/profile/" handle "/followers")]]

              [:div {:class "border-b border-gv2-border px-4 py-2"}
               [:span {:class "text-[13px] font-bold text-[#1CB0F6] border-b-2 border-[#1CB0F6] pb-2"}
                "投稿"]]

              (cond
                posts-loading?
                [:div (for [i (range 4)] ^{:key i} [post-skeleton])]

                (empty? posts)
                [:div {:class "py-10 text-center text-[13px] text-gv2-text-muted"}
                 "投稿がありません"]

                :else
                [:div (for [p posts] ^{:key (:uri p)} [post-card p])])]

             :else nil)]))})))

;; ===========================================================================
;; Dispatcher
;; ===========================================================================

(defn profile-page [{:keys [handle]}]
  (if (kactor/etzhayyim? handle)
    [ez-profile-page handle]
    [at-profile-page {:handle handle}]))
