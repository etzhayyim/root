"""analyze.py — 扶持 (fuchi) end-to-end allocation membrane over the :representative seed.

Per ADR-2606052300 (R0 + R1 a/b/c). Runs each seed maintainer through the full pipeline:

    covenant check → sustenance envelope → tenure-weighted allocation (cash≡0)
                   → in-kind rail decomposition → governance gate
                   → [auto | sbt-vote (R1b: real 1 SBT=1 vote + 48h timelock) | council-lv7 | refused]
                   → R1a: provisioning intents to the real producing actors (dry-run, published=false)
                   → R1c: toritate ledgerEntry booking (cash≡0) + kanae-renderable flow graph

and emits an offline scorecard (Markdown) + derived datoms (edn). NO live disbursement /
provisioning / land grant / binding vote — all G10 (Council Lv6+ + operator). Dry-run only.

Stdlib only.
"""

from __future__ import annotations

import pathlib

import book
import couple as couple_mod
import live_gate
import provision as prov
import vote as vote_mod
from _edn import load_edn
from allocate import allocate, cohort_from_seed
from route import (
    gov_route,
    in_kind_coverage,
    rider_hit,
    route_envelope,
    touches_invariant,
)

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_SEED = _ROOT / "data" / "seed-sustenance-graph.kotoba.edn"
_OUT = _ROOT / "methods" / "out"


def _kw(v) -> str:
    return str(v or "").lstrip(":").split("/")[-1].lower()


def _envelopes_for(seed: dict, did: str) -> list[dict]:
    return [e for e in seed.get(":envelope/batch", []) if e.get(":envelope/maintainer") == did]


def _ballots_for(seed: dict, did: str) -> dict:
    for v in seed.get(":gov/ballots", []):
        if v.get(":gov/maintainer") == did:
            return v
    return {}


def run(seed_path: pathlib.Path = _SEED) -> dict:
    seed = load_edn(seed_path)
    records = seed.get(":maintainer/batch", [])
    ceiling = int(seed.get(":graph/stage-ceiling-usd-micros-yr", 30_000_000_000))
    now_h = int(seed.get(":graph/now-hours", 0))

    cohort = cohort_from_seed(records)
    allocs = {a.maintainer_did: a for a in allocate(cohort, ceiling, instrument="sustenance")}
    note_of = {r.get(":maintainer/did"): r.get(":maintainer/note", "") for r in records}
    maintains_of = {r.get(":maintainer/did"): " ".join(r.get(":maintainer/maintains", []) or [])
                    for r in records}

    rows: list[dict] = []
    derived: list[dict] = []
    intents: list[prov.ProvisioningIntent] = []
    ledger: list[book.LedgerEntry] = []
    flows: list[book.FlowEdge] = []
    in_kind_by_actor: dict[str, int] = {}   # R1(d): accepted in-kind imputed per displacing actor
    as_of = 3000
    for r in records:
        as_of += 10
        did = r.get(":maintainer/did")
        cov = _kw(r.get(":maintainer/covenant", ":vowed"))
        env = _envelopes_for(seed, did)

        try:
            rails = route_envelope(env)
        except ValueError as exc:
            rows.append({"did": did, "covenant": cov, "route": ":refused-at-intake",
                         "imputed": "-", "in_kind": "-", "outcome": "refused", "note": str(exc)})
            continue

        imputed_total = sum(rl.imputed_usd_micros_yr for rl in rails)
        coverage = in_kind_coverage(rails)
        ctx = note_of.get(did, "") + " " + maintains_of.get(did, "")
        rider = rider_hit(ctx)
        inv = touches_invariant(ctx)
        route = gov_route(imputed_total, inv, rider)

        outcome = "pending"
        if route == "auto":
            outcome = "accepted"
        elif route == "sbt-vote":
            v = _ballots_for(seed, did)
            ballots = vote_mod.ballots_from_seed(v.get(":gov/votes", []))
            t = vote_mod.tally(ballots, int(v.get(":gov/opened-at-hours", 0)), now_h,
                               timelock_h=int(v.get(":gov/timelock-h", 48)))
            outcome = t["outcome"]
            route = f"sbt-vote {t['yes']}-{t['no']}/{t['timelock_h']}h{'✓' if t['finalizable'] else '…'}"
        elif route == "council-lv7":
            outcome = "pending"
        elif route == "refused":
            outcome = "refused"

        a = allocs.get(did)
        rows.append({
            "did": did, "covenant": cov, "route": ":" + route, "imputed": imputed_total,
            "in_kind": coverage, "share": getattr(a, "share", 0.0),
            "rank": getattr(a, "priority_rank", "-"), "floor": getattr(a, "floor_usd_micros_yr", 0),
            "outcome": outcome, "note": note_of.get(did, ""),
        })

        # R1 a/c — provision + book only for allocations that are accepted or council-pending
        if a is not None and outcome in ("accepted", "pending"):
            # R1(d) — accumulate this maintainer's in-kind imputed onto each actor they maintain
            in_kind_imputed = int(round(imputed_total * coverage))
            for act in (maintains_of.get(did, "").split() or []):
                in_kind_by_actor[act] = in_kind_by_actor.get(act, 0) + in_kind_imputed
            these_intents = prov.provision(rails, a.maintainer_did)
            these_ledger = book.book_toritate(rails, a.maintainer_did, a.maintainer_did)
            these_flows = book.flow_graph(rails, a.maintainer_did, a.maintainer_did)
            intents.extend(these_intents)
            ledger.extend(these_ledger)
            flows.extend(these_flows)
            derived.append({
                ":alloc/maintainer": did, ":alloc/instrument": ":" + a.instrument,
                ":alloc/share": a.share, ":alloc/priority-rank": a.priority_rank,
                ":alloc/floor-usd-micros-yr": a.floor_usd_micros_yr,
                ":alloc/cash-usd-micros": 0, ":alloc/server-held-key": False,
                ":gov/route": ":" + route.split()[0], ":gov/outcome": ":" + outcome,
                ":rail/coverage-in-kind": coverage,
                ":prov/intents": len(these_intents), ":book/entries": len(these_ledger),
                ":wb/as-of": as_of,
            })

    # R1(d) — Displacement-Dividend coupling: per-cohort earmark + G2 gate
    coupling: list[dict] = []
    for ev in couple_mod.events_from_seed(seed.get(":cohort/displacement", [])):
        em = couple_mod.earmark_from_surplus(ev)
        committed = in_kind_by_actor.get(ev.displacing_actor, 0)
        g = couple_mod.coupling_gate(ev, em, committed)
        coupling.append({"earmark": em, "gate": g})

    # R1(live) — show every outward leg's gate REFUSING by default (no operator flag / attestation /
    # Council / member signature in a dry run). This is the deliverable: the live path exists and is
    # refused unless fully gated. `env={}` ⇒ the operator process flag is absent.
    live_status = [live_gate.gate_status(live_gate.LiveGate(leg=leg), env={})
                   for leg in live_gate.LEG_POLICY]

    return {"rows": rows, "derived": derived, "intents": intents, "ledger": ledger,
            "flows": flows, "coupling": coupling, "live_status": live_status}


def _report(res: dict) -> str:
    out = [
        "# 扶持 (fuchi) — maintainer-sustenance allocation dry-run (R0 + R1 a/b/c)\n",
        "The charter-clean INVERSE of an investment fund over the `:representative` seed. "
        "No equity, no ROI, no exit; **cash≡0** everywhere. No live disbursement / provisioning / "
        "land grant / binding vote (G10).\n",
        "## Allocation routing + governance\n",
        "| maintainer | covenant | imputed USD/yr | in-kind | share | rank | floor USD/yr | route | outcome |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in res["rows"]:
        imp = r["imputed"]
        imp_s = f"${imp/1_000_000:,.0f}" if isinstance(imp, int) else imp
        floor = r.get("floor", 0)
        floor_s = f"${floor/1_000_000:,.0f}" if isinstance(floor, int) else floor
        ik = r["in_kind"]
        ik_s = f"{ik*100:.0f}%" if isinstance(ik, float) else ik
        did = r["did"].split(":")[-1]
        out.append(f"| {did} | {r['covenant']} | {imp_s} | {ik_s} | {r.get('share', 0.0)} | "
                   f"{r.get('rank', '-')} | {floor_s} | {r['route']} | {r['outcome']} |")

    out.append("\n## R1(a) provisioning intents → real producing actors (dry-run, published=false)\n")
    out.append("| alloc | rail | provider | kind | imputed USD/yr | member-principal |")
    out.append("|---|---|---|---|---|---|")
    for i in res["intents"]:
        out.append(f"| {i.alloc_id.split(':')[-1]} | {i.rail_kind} | "
                   f"{i.provider_did.split(':')[-1]} | {i.provider_kind} | "
                   f"${i.imputed_usd_micros_yr/1_000_000:,.0f} | {'✓ (warifu 0%)' if i.member_principal else '—'} |")

    out.append("\n## R1(c) toritate ledgerEntry booking (cashStipendUsd ≡ 0)\n")
    out.append("| alloc | category | imputed USD/yr | cash |")
    out.append("|---|---|---|---|")
    for e in res["ledger"]:
        out.append(f"| {e.alloc_id.split(':')[-1]} | {e.category} | "
                   f"${e.imputed_usd_micros_yr/1_000_000:,.0f} | ${e.cash_usd_micros} |")

    out.append("\n## R1(c) kanae-renderable internal sustenance-flow graph\n")
    out.append("| from | to | class | imputed USD/yr | in-kind |")
    out.append("|---|---|---|---|---|")
    for f in res["flows"]:
        out.append(f"| {f.frm.split(':')[-1]} | {f.to.split(':')[-1]} | {f.flow_class} | "
                   f"${f.imputed_usd_micros_yr/1_000_000:,.0f} | {'✓' if f.in_kind else '— (member loan)'} |")

    out.append("\n## R1(d) Displacement-Dividend coupling (G2: no displacement without a funded cohort)\n")
    out.append("| cohort | displacing actor | gross USD/yr | tithe 10% | earmark 90% | funded | committed | admissible |")
    out.append("|---|---|---|---|---|---|---|---|")
    for c in res.get("coupling", []):
        em, g = c["earmark"], c["gate"]
        out.append(f"| {em.cohort_id} | {em.displacing_actor} | "
                   f"${em.gross_usd_micros_yr/1_000_000:,.0f} | ${em.tithe_usd_micros/1_000_000:,.0f} | "
                   f"${em.earmark_usd_micros_yr/1_000_000:,.0f} | {'✓' if em.funded else '—'} | "
                   f"${g['committed']/1_000_000:,.0f} | {'✓ admissible' if g['admissible'] else '✗ REFUSED'} |")

    out.append("\n## R1(live) outward-leg gate (default = REFUSED; G10)\n")
    out.append("Each live leg fires only when its operator flag + attestation + Council level + "
               "member signature are ALL present. In a dry run none are, so every leg is refused.\n")
    out.append("| leg | env flag | min Council | operator flag | attested | ratified | member-signed | admissible |")
    out.append("|---|---|---|---|---|---|---|---|")
    for s in res.get("live_status", []):
        c = s["conditions"]
        def _m(b):
            return "✓" if b else "✗"
        out.append(f"| {s['leg']} | `{s['env_flag']}` | Lv{s['min_council']} | "
                   f"{_m(c['operator_flag'])} | {_m(c['operator_attested'])} | "
                   f"{_m(c['council_ratified'])} | {_m(c['member_signed'])} | "
                   f"{'✓ admissible' if s['admissible'] else '✗ REFUSED'} |")

    out.append("\n## Invariants held\n")
    out.append("- **cash≡0** — every allocation / provisioning intent / ledgerEntry carries 0 cash (N1).")
    out.append("- **no investment vehicle** — instrument ∈ sustenance set; equity/debt/ROI/exit unrepresentable (G1).")
    out.append("- **1 SBT = 1 vote + 48h timelock** — escalated allocations finalize only after the window closes (R1b).")
    out.append("- **in-kind first** — provisioning routed to real producing actors; external fiat only as member-principal warifu 0% (G3).")
    out.append("- **booked, not paid** — toritate cashStipendUsd ≡ 0; no payroll/wage category (R1c).")
    out.append("- **coupled** — a displacement is admissible only against a funded cohort earmark; "
               "10% TitheRouter split exact (R1d).")
    out.append("- **outward-gated** — every live leg (provision/vote/book/couple) REFUSES unless "
               "operator flag + attestation + Council Lv6+/Lv7+ + member signature; default = refused (R1-live).\n")
    return "\n".join(out)


def main() -> int:
    res = run()
    _OUT.mkdir(parents=True, exist_ok=True)
    (_OUT / "allocation-dryrun.md").write_text(_report(res), encoding="utf-8")

    def emit(records: list[dict]) -> str:
        lines = []
        for d in records:
            kvs = []
            for k, v in d.items():
                if isinstance(v, bool):
                    kvs.append(f"{k} {str(v).lower()}")
                elif isinstance(v, str) and not v.startswith(":"):
                    kvs.append(f'{k} "{v}"')
                else:
                    kvs.append(f"{k} {v}")
            lines.append("  {" + " ".join(kvs) + "}")
        return "\n".join(lines)

    (_OUT / "allocations.kotoba.edn").write_text(
        "{:fuchi/derived\n [\n" + emit(res["derived"]) + "\n ]}\n", encoding="utf-8")
    (_OUT / "provisioning-intents.kotoba.edn").write_text(
        "{:fuchi/provisioning\n [\n" + emit([{
            ":prov/alloc": i.alloc_id, ":prov/rail-kind": ":" + i.rail_kind,
            ":prov/provider-did": i.provider_did, ":prov/provider-kind": ":" + i.provider_kind,
            ":prov/imputed-usd-micros-yr": i.imputed_usd_micros_yr,
            ":prov/member-principal": i.member_principal, ":prov/cash-usd-micros": 0,
            ":prov/server-held-key": False, ":prov/published": False,
        } for i in res["intents"]]) + "\n ]}\n", encoding="utf-8")
    (_OUT / "toritate-ledger.kotoba.edn").write_text(
        "{:fuchi/ledger\n [\n" + emit([{
            ":book/alloc": e.alloc_id, ":book/category": ":" + e.category,
            ":book/imputed-usd-micros-yr": e.imputed_usd_micros_yr,
            ":book/cash-usd-micros": 0, ":book/counterparty-did": e.counterparty_did,
        } for e in res["ledger"]]) + "\n ]}\n", encoding="utf-8")
    (_OUT / "kanae-flow.kotoba.edn").write_text(
        "{:fuchi/flow\n [\n" + emit([{
            ":flow/from": f.frm, ":flow/to": f.to, ":flow/class": ":" + f.flow_class,
            ":flow/imputed-usd-micros-yr": f.imputed_usd_micros_yr, ":flow/in-kind": f.in_kind,
        } for f in res["flows"]]) + "\n ]}\n", encoding="utf-8")
    (_OUT / "cohort-earmarks.kotoba.edn").write_text(
        "{:fuchi/coupling\n [\n" + emit([{
            ":earmark/cohort": c["earmark"].cohort_id,
            ":earmark/displacing-actor": c["earmark"].displacing_actor,
            ":earmark/gross-usd-micros-yr": c["earmark"].gross_usd_micros_yr,
            ":earmark/tithe-usd-micros": c["earmark"].tithe_usd_micros,
            ":earmark/earmark-usd-micros-yr": c["earmark"].earmark_usd_micros_yr,
            ":earmark/funded": c["earmark"].funded,
            ":couple/committed-usd-micros-yr": c["gate"]["committed"],
            ":couple/admissible": c["gate"]["admissible"],
        } for c in res["coupling"]]) + "\n ]}\n", encoding="utf-8")
    (_OUT / "live-gate-status.kotoba.edn").write_text(
        "{:fuchi/live-gate\n [\n" + emit([{
            ":gate/leg": ":" + s["leg"], ":gate/env-flag": s["env_flag"],
            ":gate/min-council": s["min_council"],
            ":gate/operator-flag": s["conditions"]["operator_flag"],
            ":gate/operator-attested": s["conditions"]["operator_attested"],
            ":gate/council-ratified": s["conditions"]["council_ratified"],
            ":gate/member-signed": s["conditions"]["member_signed"],
            ":gate/admissible": s["admissible"],
        } for s in res.get("live_status", [])]) + "\n ]}\n", encoding="utf-8")

    print(_report(res))
    print(f"\nwrote allocation-dryrun.md + allocations / provisioning-intents / "
          f"toritate-ledger / kanae-flow / cohort-earmarks / live-gate-status .kotoba.edn → {_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
