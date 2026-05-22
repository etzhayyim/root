# `_observations/council/` — Council nomination observation log

Per `README.md § As Artificial Organism Ecosystem` Axis 1 Autopoiesis, this directory is the autopoietic surface for Council Seat 2-5 self-nominations during the 2026-05-20 → 2026-06-19 RFP window (and any future Council RFP).

## Why this directory exists

Before cycle 05 of the active-inference loop, a Council nomination arrived only as a PR — a human had to notice it, parse the diff, and run eligibility checks by eye. That is not autopoiesis; that is human polling.

This directory is populated automatically by `.github/workflows/council-nomination-watch.yml`. Every PR that touches `COUNCIL.md` or `COUNCIL-BOOTSTRAP-RFP.md` triggers:

1. A structural-eligibility check (`70-tools/scripts/council/check-nomination.sh`)
2. A PR comment with the findings
3. An observation file appended to this directory: `YYMMDDHHMM-pr-NNNN.md`

The organism notices its own nominations. The founder is freed from polling.

## File schema

Each `YYMMDDHHMM-pr-NNNN.md` contains:

- Timestamp + PR number + author + URL
- Output of the structural-eligibility check (seat / name / DID format / wallet format)

## What this is NOT

- This is **not** a vote tally. Council votes are ≥3-of-N multisig on-chain attestations; they do not occur in this log.
- This is **not** substantive eligibility review. Adherent SBT possession, Charter affirmation, and Rider §2(a)-(h) clearance are human Council review per `COUNCIL-BOOTSTRAP-RFP.md`.
- This is **not** a public objection mechanism. Public objections during the RFP window are filed as their own PRs against `COUNCIL.md`; the workflow logs them but does not adjudicate.

## RFP window

- **Open:** 2026-05-20
- **Close:** 2026-06-19
- **Days remaining as of cycle 05:** 28

After 2026-06-19, the founder selects from un-objected candidates and confirms via signed commit. The workflow continues to run for any future RFP window without modification.

## References

- [`COUNCIL.md`](../../COUNCIL.md) — Bootstrap Council roster
- [`COUNCIL-BOOTSTRAP-RFP.md`](../../COUNCIL-BOOTSTRAP-RFP.md) — RFP-period candidacy declarations
- [`90-docs/adr/2605192300-etzhayyim-bootstrap-council-five.md`](../../90-docs/adr/2605192300-etzhayyim-bootstrap-council-five.md) — Constitutional mechanics
- [`.github/workflows/council-nomination-watch.yml`](../../.github/workflows/council-nomination-watch.yml) — Detector workflow
- [`70-tools/scripts/council/check-nomination.sh`](../../70-tools/scripts/council/check-nomination.sh) — Structural check script
