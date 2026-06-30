(ns did-web.shell-test
  "Babashka-runnable tests for the shared HTML shell. Verifies the canonical
  envelope (header/nav/footer + /_shell/shell.css) that every public page is
  unified on, and that it never emits the Tailwind CDN. Runs under bb on the
  exact .cljc that shadow-cljs compiles. ADR: did-web UIUX unification."
  (:require [clojure.test :refer [deftest is testing]]
            [did-web.shell :as shell]))

(defn- page [opts] (shell/page-html (merge {:title "T" :main "<p>x</p>"} opts)))

(deftest shell-emits-canonical-envelope
  (testing "every page links the same-origin shared stylesheet"
    (is (re-find #"<link rel=\"stylesheet\" href=\"/_shell/shell\.css\">" (page {}))))
  (testing "every page has the shared header + primary nav"
    (is (re-find #"<header class=\"site-hd\">" (page {})))
    (is (re-find #"<nav class=\"site-nav\" aria-label=\"Primary\">" (page {}))))
  (testing "all seven nav links are present on every page"
    (let [html (page {})]
      (doseq [href ["/organism" "/system-dynamics" "/actors" "/murakumo" "/gov" "/donate"
                    "/.well-known/did.json"]]
        (is (re-find (re-pattern (str "href=\"" href "\"")) html)
            (str href " missing from nav")))))
  (testing "the brand links home"
    (is (re-find #"<a class=\"brand\" href=\"/\">etzhayyim</a>" (page {}))))
  (testing "active nav item gets aria-current=page"
    (let [html (page {:active "/donate"})]
      (is (re-find #"<a href=\"/donate\" aria-current=\"page\">donate</a>" html))
      (is (not (re-find #"<a href=\"/organism\" aria-current" html)))))
  (testing "the shared footer is present"
    (is (re-find #"<footer class=\"site-ft\">" (page {}))))
  (testing "a page script is wired as same-origin (deferred to end of body)"
    (is (re-find #"<script[^>]*src=\"/_shell/home-feed\.js\"></script>" (page {:script-src "/_shell/home-feed.js"})))))

(deftest shell-never-uses-tailwind-cdn
  (testing "the unified shell must not emit the Tailwind CDN (style-src 'self')"
    (is (not (re-find #"cdn\.tailwindcss\.com" (page {}))))
    (is (not (re-find #"cdn\.tailwindcss\.com"
                      (page {:active "/system-dynamics" :script-src "/_shell/x.js"}))))))

(deftest shell-never-emits-inline-style
  (testing "no inline <style> — styles come only from /_shell/shell.css"
    (is (not (re-find #"<style" (page {}))))))
