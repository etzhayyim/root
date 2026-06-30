(ns did-web.shell
  "Shared HTML shell for etzhayyim.com public pages — the CLJS mirror of
  src/shell.ts renderShell. Single source of truth for the header/nav/footer
  envelope + the same-origin /_shell/shell.css link. Page builders pass the
  <main> inner HTML; this wraps it in a full document so every page shares one
  layout, one nav, one footer, one stylesheet (style-src 'self', no inline
  <style>, no third-party CDN). .cljc so babashka can test it.
  ADR: etzhayyim-did-web UIUX unification."
  (:require [clojure.string :as str]))

(def ^:private nav
  [["/organism" "organism"]
   ["/system-dynamics" "system dynamics"]
   ["/actors" "actors"]
   ["/gov" "gov atlas"]
   ["/donate" "donate"]
   ["/.well-known/did.json" "DID"]])

(defn- esc [s]
  (-> (str s)
      (str/replace "&" "&amp;")
      (str/replace "<" "&lt;")
      (str/replace ">" "&gt;")
      (str/replace "\"" "&quot;")))

(defn- nav-html [active]
  (str/join
   (map (fn [[href label]]
          (str "<a href=\"" (esc href) "\""
               (when (= href active) " aria-current=\"page\"")
               ">" (esc label) "</a>"))
        nav)))

(def ^:private default-footer
  (str "Machine roots: <a href=\"/.well-known/did.json\">/.well-known/did.json</a> "
       "· <a href=\"/.well-known/actors.json\">/.well-known/actors.json</a> "
       "· <a href=\"/.well-known/donation.json\">/.well-known/donation.json</a>. "
       "No ads, no trackers, no cookies."))

(defn page-html
  "Full HTML document envelope with shared header/nav/footer + /_shell/shell.css.
  Opts map:
    :title         required
    :lang          default \"en\"
    :description   optional <meta description>
    :active        nav href that is current (aria-current=page)
    :main          <main> inner HTML (required)
    :wrap-class    extra class on .wrap
    :extra-css     seq of additional same-origin css hrefs
    :script-src    same-origin script src (deferred to end of body)
    :script-type   default \"text/javascript\"
    :footer-html   page-specific footer inner (replaces default)"
  [{:keys [title lang description active main wrap-class extra-css
           script-src script-type footer-html]
    :or {lang "en" script-type "text/javascript"}}]
  (let [css (str/join
             (map (fn [h] (str "<link rel=\"stylesheet\" href=\"" (esc h) "\">"))
                  (cons "/_shell/shell.css" (or extra-css []))))
        script (when script-src
                 (str "<script type=\"" (esc script-type) "\" src=\""
                      (esc script-src) "\"></script>"))
        footer (or footer-html default-footer)]
    (str "<!DOCTYPE html><html lang=\"" (esc lang) "\"><head>"
         "<meta charset=\"utf-8\">"
         "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
         "<title>" (esc title) "</title>"
         (when description
           (str "<meta name=\"description\" content=\"" (esc description) "\">"))
         css
         "</head><body>"
         "<div class=\"wrap" (when wrap-class (str " " (esc wrap-class))) "\">"
         "<header class=\"site-hd\">"
         "<a class=\"brand\" href=\"/\">etzhayyim</a>"
         "<nav class=\"site-nav\" aria-label=\"Primary\">"
         (nav-html active)
         "</nav></header>"
         "<main class=\"site-main\">"
         main
         "</main>"
         "<footer class=\"site-ft\">" footer "</footer>"
         "</div>"
         script
         "</body></html>")))
