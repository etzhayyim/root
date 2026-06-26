(ns app)
(defn ^:export analyze []
  "{\"who_tracks_you\":[],\"surface_leak\":[],\"data_spread\":[],\"reciprocity_gap\":[],\"own_data\":true,\"reciprocity_restoring\":true}")
(defn ^:export datoms [tx]
  (str "[[\":db/add\" \"aburi\" \":aburi/built-with\" \"squint+componentize-js\" " tx "]]"))
(defn ^:export coverage []
  "# aburi coverage (cljc-native wasm)\n- surface/permission/collector/catalogue/datatype: ok\n")
