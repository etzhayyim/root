(ns yoro-ui.pages.post-thread
  "Post thread detail page — fetches via public.api.bsky.app getPostThread."
  (:require [reagent.core :as r]
            [re-frame.core :as rf]
            [yoro-ui.interop.atproto :as at]
            [yoro-ui.components.post-card :refer [post-card post-skeleton]]))

(defonce thread-cache (r/atom {}))

(defn- fetch-thread! [handle rkey cache-key]
  (let [uri (str "at://" handle "/app.bsky.feed.post/" rkey)]
    (swap! thread-cache assoc cache-key {:loading? true :thread nil :error nil})
    (-> (at/at-public-query "app.bsky.feed.getPostThread"
                            {:uri uri :depth 6 :parentHeight 10})
        (.then (fn [resp]
                 (swap! thread-cache assoc cache-key
                        {:loading? false
                         :thread (:thread resp)
                         :error nil})))
        (.catch (fn [e]
                  (swap! thread-cache assoc cache-key
                         {:loading? false
                          :thread nil
                          :error (str e)}))))))

(defn- post-view->card-props [post]
  {:uri          (:uri post)
   :cid          (:cid post)
   :author       (:author post)
   :record       (:record post)
   :like-count   (:likeCount post 0)
   :repost-count (:repostCount post 0)
   :reply-count  (:replyCount post 0)
   :indexed-at   (:indexedAt post)})

(defn- reply-list [replies depth]
  (when (seq replies)
    [:div {:class "ml-3"}
     (for [[i reply] (map-indexed vector (take 10 replies))]
       (when (map? (:post reply))
         ^{:key (or (get-in reply [:post :uri]) i)}
         [:div
          [post-card (post-view->card-props (:post reply))]
          [reply-list (:replies reply) (inc depth)]]))]))

(defn- thread-node [{:keys [post replies parent]}]
  (when (map? post)
    [:div
     ;; Parent context above root (dimmed)
     (when (and parent (map? (:post parent)))
       [:div {:class "opacity-60 border-l-2 border-gv2-border/40 ml-4"}
        [post-card (post-view->card-props (:post parent))]])
     ;; Root post
     [post-card (post-view->card-props post)]
     ;; Replies
     [reply-list replies 0]]))

(defn post-thread-page [{:keys [handle rkey]}]
  (r/create-class
   {:display-name "post-thread-page"

    :component-did-mount
    (fn [_]
      (let [k (str handle "/" rkey)]
        (when-not (get @thread-cache k)
          (fetch-thread! handle rkey k))))

    :component-did-update
    (fn [this [_ prev-props]]
      (when (or (not= (:handle prev-props) handle)
                (not= (:rkey prev-props) rkey))
        (fetch-thread! handle rkey (str handle "/" rkey))))

    :reagent-render
    (fn [{:keys [handle rkey]}]
      (let [k     (str handle "/" rkey)
            state (get @thread-cache k {:loading? true})]
        [:div {:class "flex flex-col"}

         ;; Header
         [:div {:class "px-4 py-3 border-b border-gv2-border sticky top-0 z-10 bg-gv2-bg-base flex items-center gap-3"}
          [:button {:class    "text-gv2-text-muted text-[20px] leading-none"
                    :on-click #(rf/dispatch [:nav/back])}
           "←"]
          [:h2 {:class "text-[17px] font-bold text-gv2-text-primary"} "投稿"]]

         (cond
           (:loading? state)
           [:div {:class "divide-y divide-gv2-border/40"}
            (for [i (range 3)] ^{:key i} [post-skeleton])]

           (:error state)
           [:div {:class "flex flex-col items-center justify-center py-20 text-center px-6"}
            [:div {:class "text-4xl mb-4"} "⚠️"]
            [:p {:class "text-[14px] text-gv2-text-muted mb-4"} "投稿を読み込めませんでした"]
            [:button {:class    "px-4 py-2 rounded-xl bg-[#1CB0F6] text-white text-[13px] font-bold"
                      :on-click #(fetch-thread! handle rkey k)}
             "再試行"]]

           (:thread state)
           [thread-node (:thread state)]

           :else
           [:div {:class "py-20 text-center text-gv2-text-muted"} "投稿が見つかりません"])]))}))
