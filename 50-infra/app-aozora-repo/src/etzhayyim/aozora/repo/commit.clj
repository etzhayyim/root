(ns etzhayyim.aozora.repo.commit
  "AT Protocol v3 repo commit — unsigned object + **no-server-key** signing seam.

  The commit references the MST data root (mst/data-root!) and is the repo head
  (`[<did> :repo/head <commit-cid>]`). Signing is an INJECTED `sign-fn` fed by the
  member/operator Ed25519 key (Keychain/1Password) — this namespace never holds a
  key (ADR-2605231525; mirrors etzhayyim.kotoba-rad). The signature covers the
  dag-cbor of the *unsigned* commit; the signed commit's CID is the head."
  (:require [etzhayyim.aozora.repo.cid :as cid]
            [etzhayyim.aozora.repo.dag-cbor :as dc]
            [etzhayyim.aozora.repo.blockstore :as bs]))

(defn unsigned-commit
  "The unsigned AT-Proto v3 commit map for `did` with MST `data-cid`, revision
  `rev`, optional previous commit `prev` (nil for the first)."
  [{:keys [did data-cid rev prev]}]
  {"did" did
   "version" 3
   "data" (dc/cid-link data-cid)
   "rev" rev
   "prev" (when prev (dc/cid-link prev))})

(defn sign-commit
  "Sign `unsigned` (the map from `unsigned-commit`) with `sign-fn`
  (`^bytes unsigned-dag-cbor -> ^bytes ed25519-sig`). Returns
  {:cid :bytes :commit}. Without `sign-fn` the commit is UNSIGNED (`sig` absent) —
  fine for dev / dry-run, refused for federation (caller checks `:signed?`)."
  ([unsigned] (sign-commit unsigned nil))
  ([unsigned sign-fn]
   (let [unsigned-bytes (dc/encode unsigned)
         signed (cond-> unsigned sign-fn (assoc "sig" (sign-fn unsigned-bytes)))
         {:keys [cid bytes]} (cid/block signed)]
     {:cid cid :bytes bytes :commit signed :signed? (boolean sign-fn)})))

(defn commit!
  "Build, (optionally) sign, store the commit block, and advance the repo head on
  the kotoba blockstore. Returns {:cid :rev :signed?}."
  [store {:keys [did data-cid rev prev sign-fn]}]
  (let [u (unsigned-commit {:did did :data-cid data-cid :rev rev :prev prev})
        {:keys [cid bytes signed?]} (sign-commit u sign-fn)]
    (bs/put-block store cid bytes)
    (bs/set-head! store did cid)
    (bs/assert-datoms store [[did :repo/rev rev]])
    {:cid cid :rev rev :signed? signed?}))
