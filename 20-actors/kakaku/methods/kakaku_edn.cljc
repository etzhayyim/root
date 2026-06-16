(ns kakaku.methods.kakaku-edn
  "kakaku 価格 — shared minimal EDN reader + seed classifier (stdlib only).
  1:1 Clojure port of `methods/kakaku_edn.py` (ADR-2605091200).

  Subset: vectors [], maps {}, :keyword, \"string\", number, bool, nil.
  Keywords are kept as \":ns/name\" strings (not Clojure keywords) to mirror Python."
  (:require [clojure.string :as str]))

;; ── minimal EDN reader (subset) ─────────────────────────────────────────────
(def ^:private tok-re
  ;; _TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')
  #"[\s,]+|;[^\n]*|(\[|\]|\{|\}|\"(?:\\.|[^\"\\])*\"|[^\s,\[\]{}]+)")

(defn- tokens [s]
  (let [m (re-matcher tok-re s)]
    ((fn step []
       (lazy-seq
        (when (.find m)
          (let [t (.group m 1)]
            (if (nil? t)
              (step)
              (cons t (step))))))))))

(defn- atom-of [t]
  (cond
    (str/starts-with? t "\"")
    (-> (subs t 1 (dec (count t)))
        (str/replace "\\\"" "\"")
        (str/replace "\\\\" "\\"))
    (= t "true") true
    (= t "false") false
    (= t "nil") nil
    (str/starts-with? t ":") t
    :else
    (let [as-long (try (Long/parseLong t) (catch #?(:clj Exception :cljs :default) _ ::nan))]
      (if (not= as-long ::nan)
        as-long
        (let [as-dbl (try (Double/parseDouble t) (catch #?(:clj Exception :cljs :default) _ ::nan))]
          (if (not= as-dbl ::nan) as-dbl t))))))

(def ^:private end-marker ::end)

(defn- parse-step [toks i]
  (let [t (nth toks i)
        i (inc i)]
    (cond
      (= t "[")
      (loop [i i, out []]
        (let [[x i] (parse-step toks i)]
          (if (= x end-marker)
            [out i]
            (recur i (conj out x)))))

      (= t "{")
      (loop [i i, out {}]
        (let [[k i] (parse-step toks i)]
          (if (= k end-marker)
            [out i]
            (let [[v i] (parse-step toks i)]
              (recur i (assoc out k v))))))

      (or (= t "]") (= t "}"))
      [end-marker i]

      :else
      [(atom-of t) i])))

(defn read-edn-str
  "Parse the first top-level form from EDN text (matches load_edn → _parse(_tokens(text)))."
  [text]
  (let [toks (vec (tokens text))]
    (first (parse-step toks 0))))

(defn load-edn
  "Read + parse an EDN file. File I/O only at this edge."
  [path]
  (read-edn-str (slurp (str path))))

;; ── helpers / classifier ────────────────────────────────────────────────────

(defn _kw
  "Strip a leading ':' from an EDN keyword value (':in-stock' → 'in-stock')."
  [v]
  (if (and (string? v) (str/starts-with? v ":"))
    (subs v 1)
    v))

(defn classify
  "Split the flat seed vector into products, merchants, offers, price-history,
  normalizing the agent-facing field names. Keyword values (availability, region,
  status) are stripped of their leading ':'.

  Returns a Clojure map:
    {:products {<id> {...}} :merchants {<id> {...}} :offers [...] :ph [...]}"
  [rows]
  (let [products (transient {})
        merchants (transient {})
        offers (transient [])
        ph (transient [])]
    (doseq [r rows]
      (when (map? r)
        (cond
          (contains? r ":product/id")
          (let [id (get r ":product/id")]
            (assoc! products id
                    {:productId id
                     :name (get r ":product/name")
                     :brand (get r ":product/brand")
                     :jan (get r ":product/jan")
                     :category (get r ":product/category")}))

          (contains? r ":merchant/id")
          (let [id (get r ":merchant/id")]
            (assoc! merchants id
                    {:merchantId id
                     :name (get r ":merchant/name")
                     :region (_kw (get r ":merchant/region"))
                     :reputationScore (get r ":merchant/reputation-score")
                     :status (_kw (get r ":merchant/status"))}))

          (contains? r ":offer/id")
          (let [id (get r ":offer/id")
                mid (first (str/split id #":"))]
            (conj! offers
                   {:offerId id
                    :merchantId mid
                    :price (get r ":offer/price" 0)
                    :shippingFee (get r ":offer/shipping-fee" 0)
                    :totalPrice (get r ":offer/total-price" 0)
                    :availability (_kw (get r ":offer/availability" "unknown"))
                    :deliveryEtaDays (get r ":offer/delivery-eta-days" 14)
                    :productUrl (get r ":offer/product-url")}))

          (contains? r ":ph/total-price")
          (conj! ph
                 {:totalPrice (get r ":ph/total-price")
                  :availability (_kw (get r ":ph/availability" "unknown"))
                  :observedAt (get r ":ph/observed-at")}))))
    {:products (persistent! products)
     :merchants (persistent! merchants)
     :offers (vec (persistent! offers))
     :ph (vec (persistent! ph))}))
