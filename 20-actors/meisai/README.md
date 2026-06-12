# meisai 明細

**Member card-statement (利用明細) ingestion into the local kotoba Datom log.** Tier-B actor ·
R0 · ADR-2606122400 · `did:web:etzhayyim.com:actor:meisai`.

A member fetches their OWN card statement with a read-only computer-use agent run on their OWN
machine — [`com-junkawasaki/computer-use-clj`](https://github.com/com-junkawasaki/computer-use-clj)
`examples/sumitclub_meisai.clj` (karakuri 絡繰 T2 posture: ToS-permitted automation of the
member's own account; credentials vault-injected via `type_secret`; inference on **local Ollama
gemma 4 QAT**, Murakumo-conformant per ADR-2605215000). The agent writes a statement EDN file
locally; **meisai ingests that file** into append-only `:meisai.stmt/*` + `:meisai.row/*` EAVT
datoms on a content-addressed local kotoba Datom log.

First source: **sumitclub.jp** (SuMi TRUST CLUB). The intake shape is source-agnostic — any card
portal the fetch leg learns to read lands through the same ingest.

## What is structural, not advisory

- **G2 — credentials and card numbers are unrepresentable.** `ingest.guard` RAISES on
  credential-shaped keys (`password`/`secret`/`otp`/`cvv`/`pin`/`token`) and PAN-shaped values
  (13–19-digit runs) anywhere in an intake. Test-enforced.
- **G3 — personal data never leaves the machine.** `data/` (intake + persisted log) is
  gitignored; the loop persists locally and publishes/pins/posts nothing.
- **G5 — provenance + dedup.** Every statement tx carries the intake file's content CID;
  re-running the loop over the same intakes appends nothing; `verify_chain` detects tamper.

## Run

```bash
# 1. fetch (member-run, on the member's machine — see computer-use-clj README):
#    SUMITCLUB_OUT=20-actors/meisai/data/intake/2026-05.edn \
#      clojure -M:dev:examples -e "(require 'sumitclub-meisai) (sumitclub-meisai/-main)"

# 2. ingest (no network, no credentials):
python3 methods/autorun.py --cycles 1

# tests (standalone, stdlib only):
./run_tests.sh
```

## Boundaries

| Sibling | Relation |
|---|---|
| karakuri 絡繰 | the fetch leg is karakuri-shaped (T2 own-account automation); meisai is the ingestion side |
| kaiyaku 解約 | statement rows = ground truth for recurring-charge ties (feeds the 縁-ledger worklist) |
| organizer | detects ご利用明細 *mail* patterns; meisai holds the statement *table* |
| toritate 執帳 | corp's OWN on-chain books — a MEMBER's personal card is not that; never conflate |
| warifu 割符 | the corp's own card rails; meisai only reads external bank-issued cards |

## R0 honesty

Methods + 21 green tests; live fetch verified end-to-end against local gemma 4 QAT (mock-host
loop) on 2026-06-12. No lexicon, no fleet cell, no Pregel registration yet — R1 work, gated as
usual. Aggregate/derived views (monthly totals → kaiyaku handoff) are future waves.
