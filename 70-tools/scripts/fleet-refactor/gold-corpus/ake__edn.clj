;; ported from 20-actors/ake/methods/_edn.py — gold reference (Fable)
;; Minimal EDN reader (subset: [] {} :kw "str" num bool nil).
;; Clojure では clojure.edn が正準なので、薄いラッパとして公開 API を保つ。
;; キーワードは ":ns/name" 文字列のまま保持する (原実装の互換)。
(ns ake.methods.edn
  (:require [clojure.edn :as edn]))

(defn- keywordish->string
  "読み取った EDN の :kw を \":kw\" 文字列へ戻す (原 Python 実装の表現に合わせる)。"
  [x]
  (cond
    (keyword? x) (str x)
    (map? x) (into {} (map (fn [[k v]] [(keywordish->string k)
                                        (keywordish->string v)]))
                   x)
    (vector? x) (mapv keywordish->string x)
    (seq? x) (mapv keywordish->string x)
    :else x))

(defn parse-edn
  "EDN 文字列をパースする。:kw は \":kw\" 文字列として返す。"
  [s]
  (keywordish->string (edn/read-string s)))

(defn load-edn
  "ファイルパスから EDN を読み取る。slurp は I/O 注入想定 (WASM ホストでは差し替え)。"
  [path read-fn]
  (parse-edn (read-fn path)))
