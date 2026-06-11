#!/usr/bin/env python3
"""mimamori 見守り — covenant bond lifecycle + schema validator + EAVT emit.

mishmeret ha-adam (ADR-2606112300). The degeneration path 五人組→隣組→Stasi→
social-credit is made UNREPRESENTABLE here, not merely prohibited:

  G1  care-route targets outside {kokoro, wakai, iyashi} raise (no denunciation rail)
  G2  any :mishmeret.person/* attr or score/risk token raises (no score-of-soul)
  G3  no active bond without the kept's explicit consent; decline/exit unconditional
  G4  bonds are visible to BOTH parties by construction (no hidden keeping)
  G5  queries are own-DID-only; no all-persons view (NEVER-a-throne, ADR-2606112200 D3)
  G6  heartbeats are content-free (the act only)
  G7  R0 accepts SYNTHETIC fictional DIDs only

Pure stdlib — runnable inside the mimamori kotoba pywasm actor (componentize-py).
Deterministic: tx = event cycle (no wall clock).
Usage:
    python3 bond.py [seed.json] [--out OUTDIR]
"""
from __future__ import annotations
import json
import pathlib
import sys

# ── schema (the whole representable surface) ────────────────────────────────
ATTR_WHITELIST = {
    ":mishmeret.bond/keeper", ":mishmeret.bond/kept", ":mishmeret.bond/state",
    ":mishmeret.bond/cycle", ":mishmeret.bond/ceremony",
    ":mishmeret.keep/bond", ":mishmeret.keep/act", ":mishmeret.keep/cycle",
    ":mishmeret.route/bond", ":mishmeret.route/to", ":mishmeret.route/consent",
    ":mishmeret.route/cycle",
    ":mishmeret.relay/bond", ":mishmeret.relay/from", ":mishmeret.relay/to",
    ":mishmeret.relay/cycle",
}
FORBIDDEN_ATTR_PREFIXES = (":mishmeret.person/",)          # G2: no person nodes at all
FORBIDDEN_TOKENS = ("score", "risk", "isolation", "danger", "rating")  # G2
CARE_WHITELIST = {":kokoro", ":wakai", ":iyashi"}           # G1: the ONLY route targets
STATES = {":offered", ":active", ":declined", ":exited", ":handed-off"}
SYNTHETIC_MARK = ":fictional:"                              # G7 (R0)


class GateViolation(Exception):
    """A mishmeret gate would be violated — the operation is unrepresentable."""


def validate_attr(attr: str) -> str:
    for p in FORBIDDEN_ATTR_PREFIXES:
        if attr.startswith(p):
            raise GateViolation(f"G2: person-node attribute unrepresentable: {attr}")
    low = attr.lower()
    for t in FORBIDDEN_TOKENS:
        if t in low:
            raise GateViolation(f"G2: score-of-soul token unrepresentable: {attr}")
    if attr not in ATTR_WHITELIST:
        raise GateViolation(f"schema: unknown attr {attr} (whitelist-only)")
    return attr


def validate_did(did: str) -> str:
    if SYNTHETIC_MARK not in did:
        raise GateViolation(f"G7: R0 accepts SYNTHETIC fictional DIDs only: {did}")
    return did


class Mishmeret:
    """Append-only bond engine. One instance = one replayed log."""

    def __init__(self):
        self.datoms: list[tuple] = []   # (e, a, v, tx, op) — op is always :add
        self.cycle = 0
        self._state: dict[str, str] = {}     # bond-id -> state
        self._keeper: dict[str, str] = {}    # bond-id -> current keeper
        self._kept: dict[str, str] = {}      # bond-id -> kept
        self._declined_at: dict[str, int] = {}  # bond-id -> cycle (cooldown)

    # ── internals ──────────────────────────────────────────────────────────
    def _add(self, e: str, a: str, v, tx: int):
        validate_attr(a)
        self.datoms.append((e, a, v, tx, ":add"))

    @staticmethod
    def _bid(keeper: str, kept: str) -> str:
        return f"bond.{keeper}.{kept}"

    def _tick(self) -> int:
        self.cycle += 1
        return self.cycle

    # ── lifecycle ──────────────────────────────────────────────────────────
    REOFFER_COOLDOWN = 3  # cycles (anti-pestering, G3)

    def offer(self, keeper: str, kept: str) -> str:
        validate_did(keeper), validate_did(kept)
        bid = self._bid(keeper, kept)
        if bid in self._declined_at and self.cycle - self._declined_at[bid] < self.REOFFER_COOLDOWN:
            raise GateViolation("G3: re-offer cooldown — a declined offer rests")
        tx = self._tick()
        self._state[bid] = ":offered"
        self._keeper[bid], self._kept[bid] = keeper, kept
        self._add(bid, ":mishmeret.bond/keeper", keeper, tx)
        self._add(bid, ":mishmeret.bond/kept", kept, tx)
        self._add(bid, ":mishmeret.bond/state", ":offered", tx)
        self._add(bid, ":mishmeret.bond/cycle", tx, tx)
        return bid

    def consent(self, keeper: str, kept: str) -> str:
        bid = self._bid(keeper, kept)
        if self._state.get(bid) != ":offered":
            raise GateViolation("G3: consent requires a standing offer")
        tx = self._tick()
        self._state[bid] = ":active"
        self._add(bid, ":mishmeret.bond/state", ":active", tx)
        return bid

    def decline(self, keeper: str, kept: str):
        bid = self._bid(keeper, kept)
        if self._state.get(bid) != ":offered":
            raise GateViolation("G3: decline targets a standing offer")
        tx = self._tick()
        self._state[bid] = ":declined"
        self._declined_at[bid] = tx
        self._add(bid, ":mishmeret.bond/state", ":declined", tx)

    def exit_bond(self, keeper: str, kept: str):
        """Unilateral, unconditional, penalty-free (G3). Appends — never erases."""
        bid = self._bid(keeper, kept)
        if self._state.get(bid) != ":active":
            raise GateViolation("G3: exit targets an active bond")
        tx = self._tick()
        self._state[bid] = ":exited"
        self._add(bid, ":mishmeret.bond/state", ":exited", tx)

    def heartbeat(self, keeper: str, kept: str):
        """Content-free (G6): the ACT only. No message, no observation, no note."""
        bid = self._bid(keeper, kept)
        if self._state.get(bid) != ":active":
            raise GateViolation("G3: keeping requires an active, consented bond")
        tx = self._tick()
        kid = f"keep.{bid}.{tx}"
        self._add(kid, ":mishmeret.keep/bond", bid, tx)
        self._add(kid, ":mishmeret.keep/act", ":reached-out", tx)
        self._add(kid, ":mishmeret.keep/cycle", tx, tx)

    def route_care(self, keeper: str, kept: str, to: str, kept_consents: bool):
        """G1: care actors ONLY. G3: the kept consents to THIS routing, each time."""
        if to not in CARE_WHITELIST:
            raise GateViolation(f"G1: route target unrepresentable: {to} "
                                f"(care whitelist = {sorted(CARE_WHITELIST)})")
        if not kept_consents:
            raise GateViolation("G3: care routing requires the kept's consent, each time")
        bid = self._bid(keeper, kept)
        if self._state.get(bid) != ":active":
            raise GateViolation("G3: routing requires an active bond")
        tx = self._tick()
        rid = f"route.{bid}.{tx}"
        self._add(rid, ":mishmeret.route/bond", bid, tx)
        self._add(rid, ":mishmeret.route/to", to, tx)
        self._add(rid, ":mishmeret.route/consent", True, tx)
        self._add(rid, ":mishmeret.route/cycle", tx, tx)

    def handoff(self, keeper: str, kept: str, to_keeper: str) -> str:
        """Relay 継ぎ (G5): finite keepers in succession — no sleepless center."""
        validate_did(to_keeper)
        bid = self._bid(keeper, kept)
        if self._state.get(bid) != ":active":
            raise GateViolation("G3: handoff targets an active bond")
        tx = self._tick()
        self._state[bid] = ":handed-off"
        self._add(bid, ":mishmeret.bond/state", ":handed-off", tx)
        rid = f"relay.{bid}.{tx}"
        self._add(rid, ":mishmeret.relay/bond", bid, tx)
        self._add(rid, ":mishmeret.relay/from", keeper, tx)
        self._add(rid, ":mishmeret.relay/to", to_keeper, tx)
        self._add(rid, ":mishmeret.relay/cycle", tx, tx)
        # the new bond is offered + consented as part of the relay covenant
        nbid = self.offer(to_keeper, kept)
        self.consent(to_keeper, kept)
        return nbid

    # ── queries (G4 + G5: own-DID-only; both parties see) ──────────────────
    def bonds_of(self, did: str) -> list[dict]:
        """Every bond in which `did` is a PARTY (keeper or kept) — and no other.
        G4: the kept always sees who keeps them. G5: there is no all-persons view."""
        out = []
        for bid, st in self._state.items():
            if self._keeper[bid] == did or self._kept[bid] == did:
                out.append({"bond": bid, "keeper": self._keeper[bid],
                            "kept": self._kept[bid], "state": st})
        return sorted(out, key=lambda b: b["bond"])

    # ── EAVT emit ───────────────────────────────────────────────────────────
    def emit(self) -> str:
        L = [";; mimamori 見守り — GENERATED kotoba Datom log (ADR-2606112300). DO NOT hand-edit.",
             ";; Canonical EAVT (ADR-2605312345). [e a v tx op] — append-only, op :add only.",
             ";; bond-edge-only: there are NO :mishmeret.person/* datoms (G2, by construction).",
             "["]
        for (e, a, v, tx, op) in self.datoms:
            vv = "true" if v is True else ("false" if v is False else
                 (v if isinstance(v, str) and v.startswith(":") else
                  (str(v) if isinstance(v, int) else '"' + str(v) + '"')))
            ee = e if e.startswith(":") else '"' + e + '"'
            L.append(f"[{ee} {a} {vv} {tx} {op}]")
        L.append("]")
        return "\n".join(L) + "\n"


# ── seed replay ─────────────────────────────────────────────────────────────
def load_seed(path: pathlib.Path) -> dict:
    seed = json.loads(path.read_text(encoding="utf-8"))
    if not seed.get("synthetic"):
        raise GateViolation("G7: R0 seed must declare synthetic:true")
    for did in seed["roster"]:
        validate_did(did)
    return seed


def replay(seed: dict) -> "Mishmeret":
    m = Mishmeret()
    for ev in seed["events"]:
        op = ev["op"]
        if op == "offer":
            m.offer(ev["keeper"], ev["kept"])
        elif op == "consent":
            m.consent(ev["keeper"], ev["kept"])
        elif op == "decline":
            m.decline(ev["keeper"], ev["kept"])
        elif op == "exit":
            m.exit_bond(ev["keeper"], ev["kept"])
        elif op == "heartbeat":
            m.heartbeat(ev["keeper"], ev["kept"])
        elif op == "route":
            m.route_care(ev["keeper"], ev["kept"], ev["to"], ev.get("consent", False))
        elif op == "handoff":
            m.handoff(ev["keeper"], ev["kept"], ev["to_keeper"])
        else:
            raise GateViolation(f"unknown op {op}")
    return m


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed_path = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-mimamori-bonds.json"
    outdir = pathlib.Path(argv[argv.index("--out") + 1]) if "--out" in argv else here / "out"
    outdir.mkdir(parents=True, exist_ok=True)
    m = replay(load_seed(seed_path))
    out = outdir / "mimamori-datoms.kotoba.edn"
    out.write_text(m.emit(), encoding="utf-8")
    print(f"mimamori datom log → {out} ({len(m.datoms)} datoms, {len(m._state)} bonds)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
