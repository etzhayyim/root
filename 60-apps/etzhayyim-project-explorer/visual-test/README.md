# visual-test — visual react loop (computer-use-clj + Ollama gemma)

A visual feedback test loop for the etzhayyim explorer SPA (ADR-2606201610),
built on **[computer-use-clj](https://github.com/com-junkawasaki/computer-use-clj)**.

Per explorer route it:

1. **navigates** the browser (AppleScript: activate + load the route),
2. **screenshots** via computer-use-clj's `IComputer` host capability
   (`computeruse.computer` / `computeruse.macos`; a display-targeted host is
   included for multi-monitor boxes),
3. **judges** the screenshot with a local **Ollama gemma-4 vision** model — "does
   this screen actually show the Organism / Explorer / Nodes view?",
4. **reacts**: on a failed/inconclusive verdict it reloads, settles longer, and
   re-judges (up to `:max-react`) — a real visual feedback loop, not a one-shot
   assert,
5. **records** every verdict on a **kotoba Datom log** via the canonical
   `kotoba.datom` codec (content-addressed + chain-verifiable — the SAME codec the
   `/explorer` view verifies in the browser).

## What it caught

On its first real run it reported the **Organism** view as `FAIL — "DATA
UNAVAILABLE"`, reacted (reloaded, re-judged, still failing → a true positive).
Root cause: `data/fetch-edn` bound `cljs.reader/*default-data-reader-fn*` to a
bare fn, but cljs expects an **atom** there — so every `.kotoba.edn` fetch threw
`No protocol method IDeref.-deref`. Fixed in `src/.../data.cljs`; re-running the
loop now reports **3/3 PASS**.

## Run

Prereqs: macOS, `clojure`, a running Ollama with a vision model
(`hf.co/unsloth/gemma-4-E4B-it-qat-GGUF:UD-Q4_K_XL` by default), the explorer dev
server up (`npm run dev` → :8710), and Screen-Recording permission for the
terminal.

```sh
# offline self-test (mock computer + stub judge — no desktop/Ollama needed):
clojure -M:smoke

# real run (screenshots the live browser, gemma judges):
clojure -M:run
#   VISUAL_DISPLAY=2   capture a specific monitor (the SPA's display)
#   VISUAL_BROWSER="Google Chrome"   which browser AppleScript drives
#   OLLAMA_URL / OLLAMA_MODEL        override the vision endpoint/model
#   VISUAL_LOG=/path/results.kotoba.edn   where to append the result log
```

Output: a per-route PASS/FAIL trace (with what the model saw), an `N/3` summary,
and a kotoba Datom log path with its verified head CID. Exit code is non-zero if
any check fails (CI-friendly).

## Layout

```
visual-test/
├── deps.edn                         # computer-use-clj/src + kotoba codec on :paths (no git deps)
└── src/etzhayyim/explorer/visual/
    ├── vision.clj                   # Ollama vision judge (java.net.http; image → {:pass :saw})
    └── react_loop.clj               # the loop + IComputer hosts + kotoba.datom result log
```

The loop's capabilities (`:navigate` / `:capture` / `:judge`) are injected, so the
same loop runs against the real desktop+Ollama or offline stubs (`--smoke`).
