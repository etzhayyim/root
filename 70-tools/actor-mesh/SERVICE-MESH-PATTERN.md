# Service / concierge mesh pattern (on-http) — 2026-06-24

> Companion to the observatory on-kse pattern. Defines how the **service /
> concierge** actor family is hosted on the KOTOBA Mesh lattice.

## Two actor shapes, two triggers (ADR-2606230001 §4)

| Actor family | Nature | Trigger | mesh.clj entry |
|---|---|---|---|
| Observatory / KG-mirror | passively observes a graph, derives concentration | `:on-kse` (topic `etzhayyim/actor/<a>`) | `run` + `on-kse` |
| Manufacturing (cells) | per-cell process step | `:on-http` `/​<a>/<cell>` | per-cell (blocked — see CELL-DEPLOY-GAPS.md) |
| **Service / concierge** | **responds to a member REQUEST** | **`:on-http` `/<a>`** | **`run` + `on-http`** |

A concierge actor (toritsugi / kurashimori / moushibumi / kadode / kaiyaku /
himotoki …) is **request-driven**, not a passive observer — a member submits a
request and the actor returns **guidance / a draft / a plan**. So it triggers on
HTTP, and its `on-http` handler:

1. records the member's request into the kotoba Datom log, and
2. returns the matching steps from the actor's **coded procedure/target
   registry** (asserted as `(procedure step)` datoms, queried back via Datalog).

## Invariants preserved in the mesh slice

- **Default self-submit / UPL boundary.** The handler returns *guidance/steps*;
  it NEVER submits, represents, or negotiates on the member's behalf (toritsugi /
  kurashimori / moushibumi / chigiri). kadode is a 使者 (relay), never a 代理人.
- **Dry-run / no-server-key for destructive or outward actions.** kaiyaku returns
  a severance *plan* (execution = member-sig + Council); himotoki returns an
  own-data DSAR *draft* (unsent). The mesh component itself performs no outward
  side effect — it asserts/queries datoms only.
- **kotoba-native.** State = kotoba Datom log (`kqe-assert!` / `kqe-query`); the
  full coded registry + document rendering stays in the actor's existing methods.

## Scope of the mesh.clj slice

As with the observatory slices, `mesh.clj` is the kotoba-native *representative*
slice the current kotoba-clj subset expresses (record request → return coded
steps). The actor's real procedure registry, document generation, and
jurisdiction logic remain in its `.cljc`/`.py` methods until the kotoba-clj
compiler gaps (CELL-DEPLOY-GAPS.md) are closed.
