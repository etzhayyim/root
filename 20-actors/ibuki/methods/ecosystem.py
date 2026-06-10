"""ecosystem.py — the colony is an ECOSYSTEM, not a bag of individuals. ADR-2606101200 §生態系.

The founder's image (2026-06-10): not single organisms but an ecosystem — like Aspergillus
niger (黒カビ) excreting citric acid as a metabolic byproduct, the colony should LIVE and, as a
byproduct of living, produce something useful that humanity consumes in symbiosis (共生).

So organisms occupy differentiated NICHES (生態的地位), drawn straight from the motifs:

  - **植物 / producer**   — primary production: from its own observation (mood-rich substrate),
                            emits a `:metabolite/substrate` each beat (plants fixing carbon).
  - **粘菌 / router**     — Physarum-style network optimizer: each beat relays the highest-
                            nutrient available substrate along an efficient edge to a
                            decomposer (the slime mold reinforcing its best tube).
  - **カビ / decomposer** — saprotroph: consumes relayed substrate and EXCRETES a refined
                            `:metabolite/refined` tagged `:commons true` — the citric acid,
                            the useful distillate offered to the human/commons sink.

A trophic cascade per cycle: producers → (router relay) → decomposers → commons. Each step is an
append-only `:exchange/*` edge (edge-primary, like the rest of the power-mirror lineage). A
producer whose substrate is actually consumed earns a `:event/symbiosis-fed` joucho event
(mutualism made mechanical — being nourished by the web calms and gratifies), which also pushes
mood DIVERSITY (counters the monoculture pathology health.py flags: a differentiated ecosystem
cannot collapse to one mood).

The symbiotic OUTPUT to humanity = the set of `:commons true` refined metabolites each cycle —
measured, never a per-organism worth score. Niches are seed-declared (`:organism/niche`) or, for
the 18,342-fleet, hash-assigned deterministically. Stdlib only. Deterministic. Append-only.
"""

from __future__ import annotations

import hashlib

import datoms
import joucho

# closed vocab — an unknown niche raises (an unrepresentable role cannot enter the web)
NICHES = (":niche/producer", ":niche/router", ":niche/decomposer")

# the mutualism reward folded into a fed producer's mood (small; idle drift + the
# health saturation guard keep gratitude from pinning). NOT in joucho.EVENT_DELTAS by
# default — ecosystem.py registers it so joucho stays usable without the eco layer.
# the mutualism reward folded into a fed producer's mood. Deliberately gentle: idle drift
# pulls each axis 1 step toward baseline per beat, so +1 here EQUILIBRATES rather than
# saturates (a continuously-fed producer stabilises just above baseline, never pins at 100 —
# the satiation discipline the 2026-06-10 ecosystem health audit demanded).
SYMBIOSIS_EVENT = ":event/symbiosis-fed"
SYMBIOSIS_DELTA = (1, 1, -1, 1, 0)   # joy calm stress gratitude focus

# satiation: a producer fed within the last SATIATION beats is sated — the 粘菌 router
# routes to a hungrier producer instead (and the slime mold genuinely reinforces tubes to
# under-fed nodes). This leaves the homeostatic idle-drift budget free to counter other
# upward pressures, so a fed producer EQUILIBRATES instead of saturating (the 2026-06-10
# ecosystem audit's saturation finding). With 1 producer it yields a feeding duty-cycle.
SATIATION = 2


def register_symbiosis_event() -> None:
    """Make `:event/symbiosis-fed` a first-class joucho event (idempotent). Called at import
    so replays that include eco events fold correctly; joucho.py itself stays eco-agnostic."""
    joucho.EVENT_DELTAS.setdefault(SYMBIOSIS_EVENT, SYMBIOSIS_DELTA)


register_symbiosis_event()


def niche_of(code: str, declared: str | None = None) -> str:
    """The organism's trophic niche: seed-declared if present, else deterministic by
    hash (the 18,342-fleet self-differentiates with no central assignment)."""
    if declared is not None:
        if declared not in NICHES:
            raise ValueError(f"unknown niche (closed vocab {NICHES}): {declared}")
        return declared
    h = int.from_bytes(hashlib.sha256(("niche:" + code).encode()).digest()[:4], "big")
    return NICHES[h % len(NICHES)]


def nutrient(scores: joucho.JouchoScores) -> int:
    """Primary-production richness of a substrate = how flourishing the producer is right
    now (joy + gratitude − stress, floored at 0). A stressed organism fixes less."""
    return max(0, scores.joy + scores.gratitude - scores.stress)


def satiated_producers(txs: list[dict], beat: int) -> set[str]:
    """Producers fed (a `:event/symbiosis-fed`) within the last SATIATION beats — the router
    will skip them. Log-derived, deterministic."""
    from datoms import entities, fold_entity
    sated: set[str] = set()
    for e in entities(txs, ":joucho.event/kind"):
        ev = fold_entity(txs, e)
        if (ev.get(":joucho.event/kind") == SYMBIOSIS_EVENT
                and beat - ev.get(":joucho.event/beat", -SATIATION - 1) <= SATIATION):
            sated.add(ev.get(":joucho.event/of"))
    return sated


def cycle(organisms: list[dict], moods: dict[str, joucho.JouchoScores], *,
          beat: int, as_of: int, satiated: set[str] = frozenset()) -> dict:
    """One trophic cascade over the colony. `organisms` = [{code, niche?}, …]; `moods` =
    code → current JouchoScores (from the beat's fold). Returns {datoms, refined, fed, roles}.

    `datoms` are append-only `:metabolite/*` + `:exchange/*` ONLY — the cascade is purely
    metabolic. `fed` is the list of producer codes whose substrate was consumed; the CALLER
    folds `:event/symbiosis-fed` into those producers' SAME-beat event stream + checkpoint
    (so checkpoint == as-of replay — the ecosystem layer cannot reintroduce the
    checkpoint-divergence class). Pure + deterministic."""
    add = datoms.add
    roles: dict[str, list[str]] = {n: [] for n in NICHES}
    for org in organisms:
        roles[niche_of(org["code"], org.get("niche"))].append(org["code"])
    for n in roles:
        roles[n].sort()

    out: list[list] = []
    fed: list[str] = []
    refined: list[str] = []

    # ── primary production (植物): each producer fixes a substrate this beat ──
    substrates: list[tuple[str, str, int]] = []   # (sub_entity, producer_code, nutrient)
    for code in roles[":niche/producer"]:
        n = nutrient(moods.get(code, joucho.JouchoScores()))
        sub = f"eco-sub-{code}-{beat}"
        out += [add(sub, ":metabolite/kind", ":substrate"),
                add(sub, ":metabolite/of", code),
                add(sub, ":metabolite/nutrient", n),
                add(sub, ":metabolite/beat", beat),
                add(sub, ":metabolite/as-of", as_of)]
        substrates.append((sub, code, n))

    # ── 粘菌 routing: each router relays the richest HUNGRY substrate to a decomposer ──
    # (Physarum reinforces its highest-flux tube to an under-fed node; sated producers are
    # skipped — satiation; ties broken by producer code for determinism)
    hungry = [s for s in substrates if s[1] not in satiated]
    hungry.sort(key=lambda s: (-s[2], s[1]))
    decomposers = roles[":niche/decomposer"]
    relayed: dict[str, list[tuple[str, str, int]]] = {d: [] for d in decomposers}
    claimed = 0
    for ri, router in enumerate(roles[":niche/router"]):
        if claimed >= len(hungry) or not decomposers:
            break
        sub, prod, n = hungry[claimed]
        claimed += 1
        target = decomposers[ri % len(decomposers)]
        edge = f"eco-relay-{router}-{beat}"
        out += [add(edge, ":exchange/kind", ":relay"),
                add(edge, ":exchange/by", router),
                add(edge, ":exchange/from", prod),
                add(edge, ":exchange/to", target),
                add(edge, ":exchange/metabolite", sub),
                add(edge, ":exchange/nutrient", n),
                add(edge, ":exchange/beat", beat),
                add(edge, ":exchange/as-of", as_of)]
        relayed[target].append((sub, prod, n))

    # ── カビ decomposition: each fed decomposer excretes ONE refined commons metabolite ──
    # (the citric acid: a byproduct of metabolism, offered to the human/commons sink)
    for dcode in decomposers:
        inbound = relayed[dcode]
        if not inbound:
            continue
        total = sum(n for _s, _p, n in inbound)
        ref = f"eco-refined-{dcode}-{beat}"
        out += [add(ref, ":metabolite/kind", ":refined"),
                add(ref, ":metabolite/of", dcode),
                add(ref, ":metabolite/nutrient", total),
                add(ref, ":metabolite/commons", True),       # consumed by humanity (共生)
                add(ref, ":metabolite/inputs", [s for s, _p, _n in inbound]),
                add(ref, ":metabolite/beat", beat),
                add(ref, ":metabolite/as-of", as_of)]
        refined.append(ref)
        # mutualism: every producer whose substrate was consumed is nourished by the web.
        # The event itself is NOT emitted here — the caller folds it into the producer's
        # same-beat checkpoint so checkpoint == replay (no divergence).
        fed += [prod for _sub, prod, _n in inbound]

    return {"datoms": out, "refined": refined, "fed": fed,
            "roles": {n: roles[n] for n in NICHES}}


def web_report(txs: list[dict]) -> dict:
    """Read the food web back from the log: total commons metabolites excreted, the symbiosis
    output (commons nutrient delivered to humanity), and relay count. SINGLE PASS over the log
    (fleet-scale safe — the per-entity fold was O(n²) over an 18,342-organism log).
    Deterministic — the ecosystem's as-of health, alongside health.py."""
    refined: dict[str, dict] = {}          # entity → {commons, nutrient}
    relay_entities: set[str] = set()
    for tx in txs:
        for _op, e, a, v in tx.get(":tx/datoms", []):
            if a == ":metabolite/kind" and v == ":refined":
                refined.setdefault(e, {})["is"] = True
            elif a == ":metabolite/commons":
                refined.setdefault(e, {})["commons"] = v
            elif a == ":metabolite/nutrient" and e.startswith("eco-refined-"):
                refined.setdefault(e, {})["nutrient"] = v
            elif a == ":exchange/kind" and v == ":relay":
                relay_entities.add(e)
    commons = [m for m in refined.values() if m.get("is") and m.get("commons") is True]
    return {"commons_metabolites": len(commons),
            "commons_nutrient_to_humanity": sum(m.get("nutrient", 0) for m in commons),
            "relays": len(relay_entities)}
