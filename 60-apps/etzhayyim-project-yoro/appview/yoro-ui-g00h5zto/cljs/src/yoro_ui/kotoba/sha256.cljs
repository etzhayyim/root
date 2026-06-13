(ns yoro-ui.kotoba.sha256
  "UTF-8 SHA-256 binding for kotoba.datom/*sha256-hex* on the browser host.

   Uses goog.crypt.Sha256 (synchronous, Closure Library) fed with UTF-8 bytes
   from TextEncoder so multi-byte characters produce the same digest as
   Python's hashlib.sha256(s.encode('utf-8')).hexdigest()."
  (:require [goog.crypt :as crypt]
            ;; Side-effect load: makes goog.crypt.Sha256 constructor available
            goog.crypt.Sha256))

(defn sha256-hex
  "String → lowercase hex SHA-256 digest (UTF-8 bytes, Python-compatible)."
  [^string s]
  (let [sha   (goog.crypt.Sha256.)
        enc   (js/TextEncoder.)
        bytes (js/Array.from (.encode enc s))]
    (.update sha bytes)
    (crypt/byteArrayToHex (.digest sha))))
