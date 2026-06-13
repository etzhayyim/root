(ns yoro-ui.pages.profile
  "Profile page — port of svelte routes/profile/[handle]/+page.svelte."
  (:require [reagent.core :as r]
            [re-frame.core :as rf]
            [yoro-ui.interop.atproto :as at]
            [yoro-ui.router :as router]
            [yoro-ui.components.post-card :refer [post-card post-skeleton avatar]]))

;; ---------------------------------------------------------------------------
;; Local state atom

(defonce profile-cache (atom {}))

(defn- load-profile! [handle-or-did state-atom]
  (when (and (seq handle-or-did) (not (:loading? @state-atom)))
    (swap! state-atom assoc :loading? true :error nil)
    (let [cached (get @profile-cache handle-or-did)]
      (if cached
        (reset! state-atom {:profile cached :loading? false :posts [] :posts-loading? true})
        (-> (at/at-query "app.bsky.actor.getProfile" {:actor handle-or-did})
            (.then (fn [resp]
                     (swap! profile-cache assoc handle-or-did resp)
                     (swap! state-atom assoc :profile resp :loading? false)))
            (.catch (fn [e]
                      (swap! state-atom assoc :error (str e) :loading? false))))))))

(defn- load-author-feed! [did state-atom]
  (when did
    (swap! state-atom assoc :posts-loading? true)
    (-> (at/at-query "app.bsky.feed.getAuthorFeed"
                     {:actor did :limit 20 :filter "posts_no_replies"})
        (.then (fn [resp]
                 (let [items (or (:feed resp) [])
                       posts (mapv (fn [item]
                                     (let [post (:post item)]
                                       {:uri (:uri post)
                                        :cid (:cid post)
                                        :author (:author post)
                                        :record (:record post)
                                        :like-count (:likeCount post 0)
                                        :repost-count (:repostCount post 0)
                                        :reply-count (:replyCount post 0)
                                        :indexed-at (:indexedAt post)}))
                                   items)]
                   (swap! state-atom assoc :posts posts :posts-loading? false))))
        (.catch (fn [_]
                  (swap! state-atom assoc :posts-loading? false))))))

;; ---------------------------------------------------------------------------
;; Sub-components

(defn- stat-chip [label value]
  [:div {:class "flex flex-col items-center"}
   [:span {:class "text-[17px] font-black text-gv2-text-primary"} (str value)]
   [:span {:class "text-[11px] text-gv2-text-muted"} label]])

(defn- profile-banner [{:keys [banner avatar-url display-name handle]}]
  [:div
   ;; Banner
   (if banner
     [:img {:src banner :alt "" :class "w-full h-28 object-cover"}]
     [:div {:class "w-full h-28 bg-gradient-to-r from-[#1CB0F6]/20 to-[#58CC02]/20"}])
   ;; Avatar row
   [:div {:class "px-4 -mt-10 flex items-end justify-between"}
    [avatar {:src avatar-url :display-name display-name :size 72}]
    [:button {:class "px-4 py-1.5 rounded-xl border border-gv2-border text-[13px] font-bold text-gv2-text-primary hover:bg-gv2-bg-card"}
     "フォロー"]]])

(defn profile-page [{:keys [handle]}]
  (let [state (r/atom {:loading? false :error nil :profile nil
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

          ;; Load author feed once we have the profile DID
          (when (and profile (not posts-loading?) (empty? posts))
            (load-author-feed! (or (:did profile) handle) state))

          [:div {:class "flex flex-col pb-20"}

           (cond
             loading?
             [:div {:class "px-4 py-8 text-center text-gv2-text-muted"} "読み込み中…"]

             error
             [:div {:class "px-4 py-8 text-center"}
              [:p {:class "text-gv2-text-muted"} error]
              [:button {:class "mt-3 px-4 py-2 rounded-xl bg-[#1CB0F6] text-white text-[13px] font-bold"
                        :on-click #(load-profile! handle state)}
               "再試行"]]

             profile
             [:div
              [profile-banner {:banner (:banner profile)
                               :avatar-url (:avatar profile)
                               :display-name (:displayName profile)
                               :handle (:handle profile)}]

              ;; Name + handle
              [:div {:class "px-4 mt-3"}
               [:h1 {:class "text-[20px] font-black text-gv2-text-primary"}
                (or (:displayName profile) (:handle profile))]
               [:p {:class "text-[13px] text-gv2-text-muted"}
                (str "@" (:handle profile))]
               (when-let [desc (:description profile)]
                 [:p {:class "text-[13px] text-gv2-text-primary mt-2 leading-relaxed"}
                  desc])]

              ;; Stats
              [:div {:class "px-4 mt-3 flex gap-5 border-b border-gv2-border pb-3"}
               [stat-chip "投稿" (or (:postsCount profile) 0)]
               [stat-chip "フォロー" (or (:followsCount profile) 0)]
               [stat-chip "フォロワー" (or (:followersCount profile) 0)]]

              ;; Posts tab
              [:div {:class "border-b border-gv2-border px-4 py-2"}
               [:span {:class "text-[13px] font-bold text-[#1CB0F6] border-b-2 border-[#1CB0F6] pb-2"}
                "投稿"]]

              ;; Author feed
              (cond
                posts-loading?
                (for [i (range 4)] ^{:key i} [post-skeleton])

                (empty? posts)
                [:div {:class "py-10 text-center text-[13px] text-gv2-text-muted"}
                 "投稿がありません"]

                :else
                (for [p posts]
                  ^{:key (:uri p)} [post-card p]))]

             :else nil)]))})))
