#!/usr/bin/env python3
"""itonami 営み — R3 SCADA/OT scan-cycle ingest adapter (ADR-2606082300).

Closes the gap (3) "SCADA/OT operating-data → operations-optimization loop". Folds a
kotoba-os plc-host-runner Datom stream (ADR-2606031600: scan-cycle = Datom transaction) into
itonami :tick/* observations, which analyze.py / optimize.py / inspect.py then consume — i.e.
OT field data → operations intelligence, end to end, on the canonical Datom log.

  parse_scan_datoms  — read a recorded stream of raw [e a v tx op] scan datoms
  fold_to_ticks      — EAVT fold to reconstruct scan-report entities, then aggregate reports
                       sharing (:scan/station, :scan/t) into one interval tick. Energy Wh→kWh.
                       Tick state = MOST-SEVERE report state (:down > :idle > :run) — a stop is
                       NEVER hidden by averaging (charter-honest availability).
  to_tick_edn        — render ticks back as a :tick/* EDN seed (round-trips into analyze.load)

CONSTITUTIONAL (read before any change):
  G6 — OFFLINE REPLAY ONLY. This adapter reads a RECORDED Datom stream. A LIVE OT socket
    (Modbus/OPC-UA/EtherCAT via kotoba-os device worlds) requires Council + operator DID;
    `ingest_live()` is a gated stub that refuses by construction.
  G1 — ingest is read-only. itonami NEVER writes back to the PLC / OT bus (no-server-key).
  G2 — scan datoms are STATION/PLC scale. There is no per-worker scan field; a stream carrying
    :worker/:person/:operator is rejected (anti-labor-surveillance, Wellbecoming §1.13).

Pure stdlib (no numpy). Usage:
    python3 ingest.py [stream.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, pathlib
from collections import defaultdict
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import read_edn  # noqa: E402

_STATE_SEVERITY = {":run": 0, ":idle": 1, ":down": 2}
_FORBIDDEN_ATTR_PREFIXES = (":worker", ":person", ":operator", ":face", ":biometric")


def parse_scan_datoms(text: str) -> list:
    """Return the list of [e a v tx op] scan datoms from a recorded kotoba-os stream."""
    forms = read_edn(text)
    datoms = []
    for f in forms:
        if isinstance(f, list) and len(f) == 5 and isinstance(f[1], str) and f[1].startswith(":scan/"):
            datoms.append(f)
    return datoms


def _guard_no_person(datoms: list) -> None:
    for e, a, v, tx, op in datoms:
        for bad in _FORBIDDEN_ATTR_PREFIXES:
            if isinstance(a, str) and a.startswith(bad):
                raise ValueError(f"G2 violation: scan stream carries a person/worker attr {a!r}")


def fold_to_ticks(datoms: list) -> list:
    """EAVT-fold raw scan datoms into per-(station,t) interval ticks."""
    _guard_no_person(datoms)
    # 1) EAVT fold: entity -> {attr: value}, last write (by tx order) wins; :retract removes
    ordered = sorted(datoms, key=lambda d: d[3])  # by tx
    ent = defaultdict(dict)
    for e, a, v, tx, op in ordered:
        if op == ":retract":
            ent[e].pop(a, None)
        else:
            ent[e][a] = v

    # 2) aggregate reconstructed report entities by (station, t)
    agg = defaultdict(lambda: dict(good=0, scrap=0, energy_wh=0.0, dt_s=0.0, states=[]))
    for e, m in ent.items():
        st, t = m.get(":scan/station"), m.get(":scan/t")
        if st is None or t is None:
            continue
        g = agg[(st, t)]
        g["good"] += int(m.get(":scan/good", 0) or 0)
        g["scrap"] += int(m.get(":scan/scrap", 0) or 0)
        g["energy_wh"] += float(m.get(":scan/energy-wh", 0) or 0)
        g["dt_s"] += float(m.get(":scan/dt-s", 0) or 0)
        g["states"].append(m.get(":scan/state", ":run"))

    # 3) build ticks (state = most-severe report state; energy Wh→kWh; cycles = good + scrap)
    ticks = []
    for (st, t), g in sorted(agg.items(), key=lambda kv: (str(kv[0][0]), kv[0][1])):
        state = max(g["states"], key=lambda s: _STATE_SEVERITY.get(s, 0))
        good, scrap = int(g["good"]), int(g["scrap"])
        ticks.append({
            ":tick/station": st, ":tick/t": t, ":tick/state": state,
            ":tick/cycles": good + scrap, ":tick/good": good, ":tick/scrap": scrap,
            ":tick/kwh": g["energy_wh"] / 1000.0,
            ":tick/interval-s": g["dt_s"],
        })
    return ticks


def _fmt(v) -> str:
    if isinstance(v, str):
        return v if v.startswith(":") else f'"{v}"'
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


_TICK_KEYS = [":tick/station", ":tick/t", ":tick/state", ":tick/cycles",
              ":tick/good", ":tick/scrap", ":tick/kwh", ":tick/interval-s"]


def to_tick_edn(ticks: list) -> str:
    """Render ticks as a :tick/* EDN seed (round-trips into analyze.load)."""
    L = [";; itonami — GENERATED :tick/* observations folded from a kotoba-os scan-cycle stream.",
         ";; Source: offline Datom replay (G6). DO NOT hand-edit.", "["]
    for tk in ticks:
        pairs = " ".join(f"{k} {_fmt(tk[k])}" for k in _TICK_KEYS if k in tk)
        L.append("{" + pairs + "}")
    L.append("]")
    return "\n".join(L) + "\n"


def ingest_live(*_a, **_k):
    """LIVE OT ingest — gated by construction (G6). Refuses without a Council/operator grant."""
    raise NotImplementedError(
        "G6: live OT ingest (Modbus/OPC-UA/EtherCAT via kotoba-os device worlds) requires "
        "Council + operator DID. itonami R3 supports OFFLINE replay of a recorded scan-cycle "
        "Datom stream only; there is no live socket and no PLC write-back (no-server-key).")


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    stream = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-scancycle-stream.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)

    datoms = parse_scan_datoms(stream.read_text(encoding="utf-8"))
    ticks = fold_to_ticks(datoms)
    out = outdir / "ingested-ticks.kotoba.edn"
    out.write_text(to_tick_edn(ticks), encoding="utf-8")
    stations = sorted({tk[":tick/station"] for tk in ticks})
    print(f"itonami R3: {len(datoms)} scan datoms → {len(ticks)} ticks "
          f"across {len(stations)} stations → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
