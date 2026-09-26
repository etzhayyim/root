(ns did-web.kotoba-test
  (:require [cljs.test :refer [deftest is]]
            [did-web.kotoba :as kotoba]))

(defn- bytes->vec [b] (vec (js/Array.from b)))

(deftest base32-decode-valid
  (is (= [98] (bytes->vec (kotoba/base32-decode "mi")))
      "sanity: a valid base32 string still decodes"))

(deftest base32-decode-rejects-invalid-characters
  ;; A character outside the b32 alphabet used to be silently SKIPPED
  ;; instead of rejected. root-multibase (the caller in verify-root-sig)
  ;; is untrusted, attacker-controlled HTTP request body: since a
  ;; corrupted string with extraneous junk characters spliced in could
  ;; decode to the SAME bytes as the original, an attacker could pair a
  ;; corrupted root string with a signature that's still valid for the
  ;; (unchanged) decoded bytes, while store-check-advance stores the
  ;; corrupted STRING (not the original) as the new manifest root.
  (doseq [bad ["mi!" "mi*" "mi1" "mi0" "mi8" "mi9"]]
    (is (thrown? js/Error (kotoba/base32-decode bad))
        (str "must reject invalid base32 character: " bad))))
