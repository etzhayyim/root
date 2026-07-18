(ns danjo.methods.ingest-status
  "ingest_status.cljc — 弾正 (danjo) R1 procurement/budget ingest status (HONEST W3 stubs).
  ADR-2605301600 + ADR-2607180900.

  Two of the three R1 ingest cells — procurement_graph (政府調達) and budget_ledger (予算書) —
  depend on W3 fetchers (jp_chotatsu / jp_yosan) that do NOT yet exist (ADR-2605263900 W1
  landed jp_kokkai_kaigiroku only). Rather than fabricate procurement/budget datoms (which
  would violate G8 non-fabrication AND G5 source-provenance), these cells return an explicit
  :awaiting-w3-fetcher status and persist NOTHING. The cell is live-shaped (fleet-deployable)
  but data-inert until the W3 fetcher + IPFS-pinned corpus land.

  This is the honest R1 posture: the ingest trio is structurally complete and ratified, the
  diet axis runs on real fixture data, and the procurement/budget axes declare their W3
  dependency in-band instead of papering over it. These are PURE observability status fns
  (no I/O, no data emission, no fabrication surface) so they carry NO R1 gate themselves —
  the live-activation gate lives on the data-persisting paths (diet_beat.beat + mesh observe),
  where refusing-until-ratified actually matters. Pure + stdlib only."
  (:require [clojure.string :as str]))

(defn procurement-status
  "R1 procurement_graph cell status. jp_chotatsu (政府調達情報ポータル) fetcher is W3 work
  (ADR-2605263900); until it + the IPFS-pinned procurementRecord corpus land, this cell
  appends nothing. Returns a status map; never touches any log (G8)."
  []
  {:cell "DanjoProcurementGraph" :appended false :datoms 0
   :reason :awaiting-w3-fetcher :w3 "jp_chotatsu"
   :gates {:G3 :passive-only :G8 :no-fabrication}
   :server-held-key false})

(defn budget-status
  "R1 budget_ledger cell status. jp_yosan (予算書) fetcher is W3 work; only a representative
  seed (data/gov-fiscal-seed.jp.json, marked :representative) exists, not a live-pinned
  budgetRecord corpus. This cell appends nothing until W3. Returns a status map (G8)."
  []
  {:cell "DanjoBudgetLedger" :appended false :datoms 0
   :reason :awaiting-w3-fetcher :w3 "jp_yosan"
   :seed "data/gov-fiscal-seed.jp.json (representative — not live-pinned)"
   :gates {:G3 :passive-only :G8 :no-fabrication}
   :server-held-key false})
