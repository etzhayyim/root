;; etzhayyim.app-sdk.test-ids — shared SDK identifier-module invariants (bb/clj side).
;; The same .cljc compiles under squint for the app/edge side (ADR-2606251200 §Decision 4).
(ns etzhayyim.app-sdk.test-ids
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.app-sdk.ids :as ids]))

(deftest rkey-validity
  (testing "valid record keys"
    (is (ids/valid-rkey? "self"))
    (is (ids/valid-rkey? "3jzfcijpj2z2a"))
    (is (ids/valid-rkey? "a.b_c~d:e-f")))
  (testing "rejects empty, reserved dots, bad chars, >512"
    (is (not (ids/valid-rkey? "")))
    (is (not (ids/valid-rkey? ".")))
    (is (not (ids/valid-rkey? "..")))
    (is (not (ids/valid-rkey? "has space")))
    (is (not (ids/valid-rkey? "slash/here")))
    (is (not (ids/valid-rkey? (apply str (repeat 513 "a")))))
    (is (not (ids/valid-rkey? nil)))))

(deftest tid-shape
  (testing "13-char sortable base32 = TID-shaped"
    (is (ids/tid-rkey? "3jzfcijpj2z2a"))
    (is (ids/tid-rkey? "2222222222222")))
  (testing "wrong length / charset / type → not a TID"
    (is (not (ids/tid-rkey? "self")))            ;; too short
    (is (not (ids/tid-rkey? "3jzfcijpj2z2ab")))  ;; 14 chars
    (is (not (ids/tid-rkey? "0000000000000")))   ;; 0/1/8/9 not in alphabet
    (is (not (ids/tid-rkey? nil)))))

(deftest nsid-split
  (is (= "profile" (ids/nsid-name "com.etzhayyim.apps.cargo.profile")))
  (is (= "com.etzhayyim.apps.cargo" (ids/nsid-authority "com.etzhayyim.apps.cargo.profile")))
  (is (= "post" (ids/nsid-name "app.bsky.feed.post")))
  (is (= "app.bsky.feed" (ids/nsid-authority "app.bsky.feed.post")))
  (testing "no dot / non-string → nil"
    (is (nil? (ids/nsid-name "nodots")))
    (is (nil? (ids/nsid-authority "nodots")))
    (is (nil? (ids/nsid-name nil)))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.app-sdk.test-ids)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
