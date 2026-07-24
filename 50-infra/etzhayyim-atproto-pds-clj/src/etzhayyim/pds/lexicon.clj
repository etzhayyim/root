(ns etzhayyim.pds.lexicon
  "Opt-in lexicon-shape validation for known collections. A minimal registry of
  required fields + string-typed fields per collection; unknown collections pass
  (the PDS is permissive — this only catches malformed records for the handful of
  well-known app.bsky.* lexicons when PDS_VALIDATE_RECORDS is set)."
  (:require [clojure.string :as str]))

(def lexicons
  {"app.bsky.feed.post"     {:required ["text" "createdAt"]    :string ["text" "createdAt"]}
   "app.bsky.feed.like"     {:required ["subject" "createdAt"] :string ["createdAt"]}
   "app.bsky.feed.repost"   {:required ["subject" "createdAt"] :string ["createdAt"]}
   "app.bsky.graph.follow"  {:required ["subject" "createdAt"] :string ["subject" "createdAt"]}
   "app.bsky.graph.block"   {:required ["subject" "createdAt"] :string ["subject" "createdAt"]}
   "app.bsky.actor.profile" {:required []                      :string ["displayName" "description"]}})

(defn validate
  "Return an error string if `record` violates the known shape for `collection`,
  else nil. Records in unregistered collections always pass."
  [collection record]
  (when-let [spec (get lexicons collection)]
    (let [gv (fn [k] (or (get record k) (get record (keyword k))))
          missing (remove #(some? (gv %)) (:required spec))
          bad-type (for [k (:string spec)
                         :let [v (gv k)]
                         :when (and (some? v) (not (string? v)))]
                     k)]
      (cond
        (seq missing)  (str collection " requires: " (str/join ", " missing))
        (seq bad-type) (str collection " fields must be strings: " (str/join ", " bad-type))))))
