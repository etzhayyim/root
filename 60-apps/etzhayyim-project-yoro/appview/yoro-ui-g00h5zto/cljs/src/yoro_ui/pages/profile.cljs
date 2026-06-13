(ns yoro-ui.pages.profile
  "Profile page — port of svelte routes/profile/[handle]/+page.svelte."
  (:require [reagent.core :as r]
            [re-frame.core :as rf]
            [yoro-ui.interop.atproto :as at]
            [yoro-ui.router :as router]
            [yoro-ui.components.post-card :refer [post-card post-skeleton avatar]]))

;; ---------------------------------------------------------------------------
;; Data loading helpers

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
                                       {:uri        (:uri post)
                                        :cid        (:cid post)
                                        :author     (:author post)
                                        :record     (:record post)
                                        :like-count   (get post :likeCount 0)
                                        :repost-count (get post :repostCount 0)
                                        :reply-count  (get post :replyCount 0)
                                        :indexed-at  (:indexedAt post)}))
                                   items)]
                   (swap! state-atom assoc :posts posts :posts-loading? false))))
        (.catch (fn [_]
                  (swap! state-atom assoc :posts-loading? false))))))

;; ---------------------------------------------------------------------------
;; Sub-components

(defn- stat-chip [label value path]
  [:button {:class "flex flex-col items-center hover:opacity-80"
            :on-click (when path #(router/navigate! path))}
   [:span {:class "text-[17px] font-black text-gv2-text-primary"} (str value)]
   [:span {:class "text-[11px] text-gv2-text-muted"} label]])

;; Form-2 component: follows/DM buttons with local optimistic follow state
(defn- profile-action-buttons [profile-init]
  (let [my-did    (rf/subscribe [:auth/did])
        my-handle (rf/subscribe [:auth/handle])
        signed-in? (rf/subscribe [:auth/signed-in?])
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
           ;; Follow / unfollow toggle
           [:button
            {:class    (str "px-4 py-1.5 rounded-xl text-[13px] font-bold transition-colors "
                            (if @following-uri
                              "border border-gv2-border text-gv2-text-primary hover:border-red-400 hover:text-red-500"
                              "bg-[#1CB0F6] text-white hover:opacity-90"))
             :on-click (fn []
                         (if @following-uri
                           ;; Unfollow: delete the follow record
                           (let [prev @following-uri
                                 rkey (last (clojure.string/split prev #"/"))]
                             (reset! following-uri nil) ; optimistic
                             (-> (at/at-procedure "com.atproto.repo.deleteRecord"
                                                  {:collection "app.bsky.graph.follow" :rkey rkey})
                                 (.catch (fn [_] (reset! following-uri prev)))))
                           ;; Follow: create record
                           (-> (at/at-procedure "com.atproto.repo.createRecord"
                                               {:collection "app.bsky.graph.follow"
                                                :record     {:$type     "app.bsky.graph.follow"
                                                             :subject   (:did profile)
                                                             :createdAt (.toISOString (js/Date.))}})
                               (.then (fn [r] (reset! following-uri (:uri r))))
                               (.catch (fn [_])))))}
            (if @following-uri "フォロー中" "フォロー")]
           ;; DM button
           [:button
            {:class    "px-3 py-1.5 rounded-xl border border-gv2-border text-[13px] font-bold text-gv2-text-primary hover:bg-gv2-bg-card"
             :on-click #(router/navigate! "/convo")}
            "DM"]])))))

(defn- profile-header [{:keys [banner avatar-url display-name handle] :as banner-props} profile]
  [:div
   ;; Banner image / gradient
   (if banner
     [:img {:src banner :alt "" :class "w-full h-28 object-cover"}]
     [:div {:class "w-full h-28 bg-gradient-to-r from-[#1CB0F6]/20 to-[#58CC02]/20"}])
   ;; Avatar + action row
   [:div {:class "px-4 -mt-10 flex items-end justify-between"}
    [avatar {:src avatar-url :display-name display-name :size 72}]
    ;; Action buttons rendered separately so they carry their own local state
    (when profile
      [profile-action-buttons profile])]])

;; ---------------------------------------------------------------------------
;; Page component

(defn profile-page [{:keys [handle]}]
  (let [state       (r/atom {:loading? false :error nil :profile nil
                              :posts [] :posts-loading? false})
        prev-handle (r/atom nil)]
    (r/create-class
     {:display-name "profile-page"

      :component-did-mount
      (fn [_]
        (reset! prev-handle handle)
        (load-profile! handle state))

      :component-did-update
      (fn [_]
        (when (not= handle @prev-handle)
          (reset! prev-handle handle)
          (reset! state {:loading? false :error nil :profile nil
                         :posts [] :posts-loading? false})
          (load-profile! handle state)))

      :reagent-render
      (fn [{:keys [handle]}]
        (let [{:keys [loading? error profile posts posts-loading?]} @state]

          ;; Load author feed once we have the DID
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

              ;; Name + handle
              [:div {:class "px-4 mt-3"}
               [:h1 {:class "text-[20px] font-black text-gv2-text-primary"}
                (or (:displayName profile) (:handle profile))]
               [:p {:class "text-[13px] text-gv2-text-muted"}
                (str "@" (:handle profile))]
               (when-let [desc (:description profile)]
                 [:p {:class "text-[13px] text-gv2-text-primary mt-2 leading-relaxed"}
                  desc])]

              ;; Stats row
              [:div {:class "px-4 mt-3 flex gap-6 border-b border-gv2-border pb-3"}
               [stat-chip "投稿" (get profile :postsCount 0) nil]
               [stat-chip "フォロー" (get profile :followsCount 0)
                (str "/profile/" handle "/follows")]
               [stat-chip "フォロワー" (get profile :followersCount 0)
                (str "/profile/" handle "/followers")]]

              ;; Posts tab header
              [:div {:class "border-b border-gv2-border px-4 py-2"}
               [:span {:class "text-[13px] font-bold text-[#1CB0F6] border-b-2 border-[#1CB0F6] pb-2"}
                "投稿"]]

              ;; Author feed
              (cond
                posts-loading?
                [:div (for [i (range 4)] ^{:key i} [post-skeleton])]

                (empty? posts)
                [:div {:class "py-10 text-center text-[13px] text-gv2-text-muted"}
                 "投稿がありません"]

                :else
                [:div (for [p posts]
                        ^{:key (:uri p)} [post-card p])])]

             :else nil)]))})))
