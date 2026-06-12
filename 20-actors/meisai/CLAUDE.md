# 20-actors/meisai — CLAUDE.md

## Identity

- **Name**: meisai (明細 — the statement itself; the row-level truth of what was spent)
- **DID**: `did:web:etzhayyim.com:actor:meisai`
- **ADR**: ADR-2606122400 (R0, 2026-06-12)
- **Parent ADRs**: ADR-2605262130 + 2605312345 (kotoba Datom log), ADR-2605215000
  (Murakumo-only inference), ADR-2606039200 (karakuri — own-account automation posture)
- **Cross-actor siblings**: karakuri (fetch posture), kaiyaku (recurring-charge consumer),
  organizer (mail-pattern detector), toritate / warifu (boundaries — see README)
- **Status**: R0 — methods + tests landed; first source sumitclub.jp

## Constitutional Discipline (CRITICAL)

meisai is a **member-own personal-data ingestion actor**. The hard rules, in order of how easy
they are to violate by accident:

1. **G3 local-only** — `data/` is gitignored and MUST stay so. Never commit, pin, publish, or
   post a statement, a row, an intake file, or the persisted log. This repo is public; a card
   statement in a commit is unrecoverable. If you add a new data path, add it to `.gitignore`
   in the same change.
2. **G2 credential/PAN unrepresentable** — `ingest.guard` raises on credential-shaped keys and
   PAN-shaped values. Do not weaken the guard; extend the test when you extend the shape.
3. **G1 member-own only** — the only input is a local file the member produced about their own
   account. Do not add a path that takes another person's statement.
4. **G4 read-only at source** — the fetch leg (computer-use-clj `sumitclub_meisai`) carries a
   system prompt that forbids every state-changing control on the card site. If you touch the
   fetch leg, keep that prompt's HARD RULES intact.
5. **G6 Murakumo-only inference** — within etzhayyim, the fetch leg runs on local Ollama
   (gemma 4 QAT default via `jvm_host.clj` `LLM=ollama`). Do NOT wire the Anthropic/Gemini
   adapter paths into anything under this actor (ADR-2605215000).
6. **G7 live leg operator-gated** — meisai's own loop does no network I/O (test-enforced).
   The browser fetch is a step the member runs explicitly, never a cron.

## Architecture

```
member's machine                                 20-actors/meisai/
┌──────────────────────────────┐                 ┌──────────────────────────────┐
│ computer-use-clj             │   statement EDN │ methods/ingest.py  (G2 guard)│
│  sumitclub_meisai.clj        │ ──────────────▶ │ methods/autorun.py (sweep)   │
│  · IComputer macOS host      │  data/intake/   │ methods/kotoba.py  (commit-  │
│  · IVault 1Password/Bitwarden│                 │   DAG, append-only, local)   │
│  · Ollama gemma 4 QAT        │                 │ data/persisted/*.kotoba.edn  │
└──────────────────────────────┘                 └──────────────────────────────┘
       member-principal, read-only                      gitignored, local-only
```

Datom shape: `meisai-stmt:<source>:<YYYY-MM>` entities with `:meisai.stmt/{source,month,
total-jpy,row-count,intake-cid,source-url}`; `meisai-row:<hash16>` entities with
`:meisai.row/{stmt,index,date,merchant,amount-jpy,note}`. All `:db/add`, no retract.

## Build & Test

```bash
./run_tests.sh                      # 2 suites, 21 checks, stdlib only, hermetic
python3 methods/autorun.py --cycles 1   # ingest data/intake/*.edn → local log
```

## R1 triggers (deferred)

lexicon `com.etzhayyim.meisai.statement`; fleet heartbeat registration; kaiyaku handoff
(recurring-merchant detection over `:meisai.row/*` → 縁-ledger worklist); additional sources
(other card portals) in the fetch leg.
