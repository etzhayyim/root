(ns media-gamers.games
  "media-gamers seed catalog + pure scoring/prompt helpers — clj twin of the
  SEED_GAMES / GUIDE_TYPES / TARGET_LANGS / _compute_quality / _build_prompt /
  mood-map constants shared by guide_generator.py + autopilot.py.

  Pure + bb/cljs-safe (no I/O). Kept in one ns so the two graph twins share one
  source of truth, exactly as the two python files duplicated them verbatim."
  (:require [clojure.string :as str]))

(def seed-games
  [{:slug "elden-ring" :name "Elden Ring" :genre "action-rpg" :releaseYear 2022 :developer "fromsoftware" :publisher "bandai-namco" :platforms ["PS5" "Xbox Series X" "PC"]}
   {:slug "zelda-totk" :name "The Legend of Zelda: Tears of the Kingdom" :genre "action-adventure" :releaseYear 2023 :developer "nintendo" :publisher "nintendo" :platforms ["Switch"]}
   {:slug "monster-hunter-wilds" :name "Monster Hunter Wilds" :genre "action-rpg" :releaseYear 2025 :developer "capcom" :publisher "capcom" :platforms ["PS5" "Xbox Series X" "PC"]}
   {:slug "black-myth-wukong" :name "Black Myth: Wukong" :genre "action-rpg" :releaseYear 2024 :developer "game-science" :publisher "game-science" :platforms ["PS5" "PC"]}
   {:slug "pokoa-world" :name "Pokoa World" :genre "creature-rpg" :releaseYear 2026 :developer "etzhayyim-studio" :publisher "etzhayyim" :platforms ["PC" "Mobile"]}
   {:slug "metaphor-refantazio" :name "Metaphor: ReFantazio" :genre "jrpg" :releaseYear 2024 :developer "atlus" :publisher "atlus" :platforms ["PS5" "PS4" "PC"]}
   {:slug "ff7-rebirth" :name "Final Fantasy VII Rebirth" :genre "jrpg" :releaseYear 2024 :developer "square-enix" :publisher "square-enix" :platforms ["PS5" "PC"]}
   {:slug "stellar-blade" :name "Stellar Blade" :genre "action-rpg" :releaseYear 2024 :developer "shift-up" :publisher "sony" :platforms ["PS5" "PC"]}
   {:slug "dq3-hd2d" :name "Dragon Quest III HD-2D Remake" :genre "jrpg" :releaseYear 2024 :developer "square-enix" :publisher "square-enix" :platforms ["Switch" "PS5" "Xbox" "PC"]}
   {:slug "gta-vi" :name "Grand Theft Auto VI" :genre "open-world" :releaseYear 2025 :developer "rockstar" :publisher "take-two" :platforms ["PS5" "Xbox Series X"]}
   {:slug "pokemon-legends-z-a" :name "Pokémon Legends: Z-A" :genre "creature-rpg" :releaseYear 2025 :developer "game-freak" :publisher "the-pokemon-company" :platforms ["Switch" "Switch 2"]}])

(def seed-games-by-slug
  (into {} (map (juxt :slug identity)) seed-games))

(def guide-types ["boss-guide" "weapon-guide" "beginner-guide" "tier-list"])
(def target-langs ["ja" "zh" "es" "ar" "hi" "ko"])
(def quality-threshold 70)

;; Joucho mood → game slugs mapping (autopilot)
(def mood->games
  {"focused"    ["elden-ring" "black-myth-wukong"]
   "calm"       ["elden-ring" "black-myth-wukong"]
   "joyful"     ["zelda-totk" "pokoa-world" "dq3-hd2d"]
   "grateful"   ["zelda-totk" "pokoa-world" "dq3-hd2d"]
   "reflective" ["monster-hunter-wilds" "metaphor-refantazio"]})

(def moods ["focused" "calm" "joyful" "grateful" "reflective"])

(def heading-re #"(?m)(^|\n)#{1,3}\s+")
(def numlist-re #"\n\d+\.")

(defn compute-quality
  "Port of `_compute_quality`: length 0.45 + heading 0.30 + checklist 0.25, ×100,
  rounded to 1 decimal."
  [body]
  (let [body (str body)
        length-score (min 1.0 (/ (count body) 4000.0))
        heading-score (if (re-find heading-re body) 1.0 0.4)
        checklist-score (if (or (str/includes? body "-") (re-find numlist-re body)) 1.0 0.5)
        raw (* (+ (* length-score 0.45) (* heading-score 0.30) (* checklist-score 0.25)) 100)]
    (/ (Math/round (* raw 10.0)) 10.0)))

(defn title-case [s]
  (->> (str/split (str s) #"\s+")
       (map (fn [w] (if (seq w) (str (str/upper-case (subs w 0 1)) (subs w 1)) w)))
       (str/join " ")))

(defn build-prompt
  "Port of `_build_prompt` → [system user]."
  [game-name game-genre game-year guide-type]
  (let [system (str "You are an expert gaming guide writer. "
                    "Write detailed, well-structured guides with headings (##), bullet points, and numbered lists. "
                    "Target length: 800-1200 words. Language: English.")
        guide-label (title-case (str/replace (str guide-type) "-" " "))
        user (str "Write a comprehensive " guide-label " for " game-name
                  " (" game-genre ", " game-year "). "
                  "Include: introduction, key strategies, tips and tricks, common mistakes to avoid. "
                  "Format with markdown headings and bullet points. Start with a title on the first line.")]
    [system user]))

(defn split-title-body
  "Port of the `lines[0]`/`lines[1:]` title+body split used in _node_generate."
  [raw game-name guide-type]
  (let [raw (str/trim (str raw))
        lines (str/split-lines raw)
        title (if (seq lines)
                (str/trim (str/replace (first lines) #"^#+" ""))
                (str game-name " " guide-type))]
    (if (> (count lines) 1)
      [title (str/trim (str/join "\n" (rest lines)))]
      [title raw])))
