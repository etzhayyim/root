#!/usr/bin/env python3
"""ipaddress — ACTIVE number-resource collector → kotoba EAVT (ADR-2605301400 §T2).

1次ソース collector. Actively pulls PUBLIC Internet number-resource registries and
normalizes them into the ip-network kotoba vocabulary (:rir/* :asn/* :iprange/*
:net.announce/* …), then dedup-merges with the curated seed (seed wins on id), and
writes a merged EAVT graph analyze.py / the viz can consume. Replaces the legacy
ipaddress RisingWave SQL graph (vertex_ip_address / vertex_ipaddress_asn / _range).

ACTIVE COLLECTION (能動的) — authorized & real, but operator-gated + offline-default:
  --source rir   RIR delegated-stats files (registry|cc|type|start|value|date|status)
                 from ftp.{apnic,ripe,arin,lacnic,afrinic} — the authoritative
                 allocation backbone for ASNs + CIDR ranges.
  --source rdap  RDAP/WHOIS (RFC 7482) registrant-org + abuse contact for a subject.
  --source rdns  reverse-DNS PTR (socket.gethostbyaddr) for an observed IP.
  --source file  bridge a local delegated-stats-shaped file offline (no network).

  A live network pull (--live) is GATE-G7: it runs ONLY when IPADDRESS_OPERATOR_GATE
  is set (a Council/operator token). Without --live the command is fully offline:
  it bridges any --in file and otherwise just re-emits the seed as the merged graph.
  Live pulls touch only public registry / measurement data — NOT host port/vuln
  scanning (that is an akuma/aratame caseMandate boundary, G10 no mass surveillance).

stdlib only. Usage:
    python3 ingest.py                                  # offline: seed → merged graph
    python3 ingest.py --source file --in delegated.txt # bridge a local RIR file (offline)
    python3 ingest.py --source rir --rir apnic --live  # G7: live pull (needs operator gate)
"""
from __future__ import annotations
import sys
import os
import ipaddress as ipa
import pathlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ip_edn import load_edn, classify, to_edn  # noqa: E402

OPERATOR_GATE = bool(os.environ.get("IPADDRESS_OPERATOR_GATE"))
ACTOR = pathlib.Path(__file__).resolve().parent.parent

# Public delegated-stats endpoints (collection source-of-record; G7 live-gated).
RIR_STATS = {
    "apnic":   "https://ftp.apnic.net/stats/apnic/delegated-apnic-latest",
    "ripe":    "https://ftp.ripe.net/pub/stats/ripencc/delegated-ripencc-latest",
    "arin":    "https://ftp.arin.net/pub/stats/arin/delegated-arin-extended-latest",
    "lacnic":  "https://ftp.lacnic.net/pub/stats/lacnic/delegated-lacnic-latest",
    "afrinic": "https://ftp.afrinic.net/pub/stats/afrinic/delegated-afrinic-latest",
}
RIR_ID = {"apnic": "rir.apnic", "ripe": "rir.ripe", "arin": "rir.arin",
          "lacnic": "rir.lacnic", "afrinic": "rir.afrinic"}


def _slug(s: str) -> str:
    return s.replace(".", "-").replace(":", "-").replace("/", "-").strip("-")


def parse_delegated_stats(text: str, registry: str, sourcing: str, limit: int = 20000):
    """RIR delegated-stats → (:asn/* + :iprange/* dicts).

    Format (one record per line): registry|cc|type|start|value|date|status[|ext...]
    type ∈ {asn, ipv4, ipv6}. Comment/summary lines (start with '#' or the version/
    summary header) are skipped. ipv4 value = address count; ipv6 value = prefix len.
    """
    rir = RIR_ID.get(registry, f"rir.{registry}")
    asns, ranges = [], []
    emitted = 0
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        f = line.split("|")
        if len(f) < 7:
            continue  # version line (6 fields) or summary line — skip
        _reg, cc, typ, start, value, date, status = f[0], f[1], f[2], f[3], f[4], f[5], f[6]
        if status in ("summary",) or typ not in ("asn", "ipv4", "ipv6"):
            continue
        if not cc or cc == "*":
            cc = "ZZ"
        st = {"allocated": ":allocated", "assigned": ":assigned",
              "reserved": ":reserved", "available": ":available"}.get(status, ":allocated")
        if emitted >= limit:
            break
        try:
            if typ == "asn":
                n = int(start)
                asns.append({":asn/id": f"asn.{n}", ":asn/number": n, ":asn/country": cc,
                             ":asn/rir": rir, ":asn/hosting-class": ":unknown",
                             ":asn/sourcing": f":{sourcing}"})
                emitted += 1
            elif typ == "ipv4":
                first = ipa.IPv4Address(start)
                last = first + int(value) - 1
                for net in ipa.summarize_address_range(first, last):
                    cidr = str(net)
                    ranges.append({":iprange/id": f"range.v4.{_slug(cidr)}",
                                   ":iprange/cidr": cidr, ":iprange/version": 4,
                                   ":iprange/country": cc, ":iprange/rir": rir,
                                   ":iprange/status": st, ":iprange/alloc-date": date,
                                   ":iprange/host-count": net.num_addresses,
                                   ":iprange/sourcing": f":{sourcing}"})
                    emitted += 1
                    if emitted >= limit:
                        break
            elif typ == "ipv6":
                cidr = f"{start}/{value}"
                ranges.append({":iprange/id": f"range.v6.{_slug(cidr)}",
                               ":iprange/cidr": cidr, ":iprange/version": 6,
                               ":iprange/country": cc, ":iprange/rir": rir,
                               ":iprange/status": st, ":iprange/alloc-date": date,
                               ":iprange/host-count": 0, ":iprange/sourcing": f":{sourcing}"})
                emitted += 1
        except (ValueError, ipa.AddressValueError):
            continue
    return asns, ranges


def fetch(url: str) -> str:
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "etzhayyim-ipaddress/0.1 (+did:web:etzhayyim.com:actor:ipaddress)"})
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 (public registry only)
        return resp.read().decode("utf-8", "replace")


def collect_rdns(ip_text: str):
    """Reverse-DNS PTR for one IP (live; socket only). Returns an :rdns/* dict or None."""
    import socket
    try:
        host, _aliases, _addrs = socket.gethostbyaddr(ip_text)
    except (socket.herror, socket.gaierror, OSError):
        return None
    verified = False
    try:
        fwd = {ai[4][0] for ai in socket.getaddrinfo(host, None)}
        verified = ip_text in fwd
    except (socket.gaierror, OSError):
        pass
    return {":rdns/id": f"rdns.{_slug(ip_text)}", ":rdns/ip": f"ip.{('v6.' if ':' in ip_text else 'v4.')}{_slug(ip_text)}",
            ":rdns/ptr": host, ":rdns/verified": verified, ":rdns/sourcing": ":authoritative"}


_ID_KEYS = (":rir/id", ":asn/id", ":iprange/id", ":ip/id", ":net.announce/id",
            ":net.member/id", ":geo/id", ":rdns/id", ":whois/id")


def _key(rec):
    for k in _ID_KEYS:
        if k in rec:
            return rec[k]
    return None


def main(argv):
    seed_path = ACTOR / "data" / "seed-ip-network.kotoba.edn"
    out_path = ACTOR / "data" / "ip-network.merged.kotoba.edn"
    source = argv[argv.index("--source") + 1] if "--source" in argv else None
    rir = argv[argv.index("--rir") + 1] if "--rir" in argv else None
    infile = argv[argv.index("--in") + 1] if "--in" in argv else None
    live = "--live" in argv
    limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else 20000

    # ── full-universe: loop ALL 5 RIRs (live, G7) → gitignored data/live/ (G8: bulk → IPFS) ──
    if source == "rir-all":
        if not (live and OPERATOR_GATE):
            sys.exit("REFUSED: --source rir-all is a live full-universe pull (all 5 RIRs); "
                     "needs --live + IPADDRESS_OPERATOR_GATE. Bulk output is written to the "
                     "gitignored data/live/ (Charter G8: large datasets → DataLad/IPFS, not git).")
        live_dir = ACTOR / "data" / "live"
        live_dir.mkdir(parents=True, exist_ok=True)
        all_recs, per_rir = [], {}
        for reg in RIR_STATS:
            print(f"ipaddress.ingest: LIVE pull {RIR_STATS[reg]} (limit {limit}/RIR) …")
            try:
                a, r = parse_delegated_stats(fetch(RIR_STATS[reg]), reg, "authoritative", limit)
            except Exception as exc:  # noqa: BLE001 — one RIR down must not abort the sweep
                print(f"  !! {reg} pull failed: {exc} — skipped (logged, not silently dropped)")
                per_rir[reg] = (0, 0)
                continue
            per_rir[reg] = (len(a), len(r))
            all_recs += a + r
            print(f"  {reg}: {len(a)} ASNs + {len(r)} ranges")
        seed_rows = load_edn(seed_path)
        merged, seen = [], set()
        for rec in seed_rows + all_recs:
            if not isinstance(rec, dict):
                continue
            k = _key(rec)
            if k and k not in seen:
                seen.add(k)
                merged.append(rec)
        auth_out = live_dir / "ip-network.authoritative.kotoba.edn"
        auth_out.write_text(to_edn(merged, [
            ";; ipaddress — GENERATED full-universe :authoritative graph (live RIR sweep).",
            f";; per-RIR limit {limit}. GITIGNORED (Charter G8). Canonical bulk home = DataLad/IPFS 80-data.",
        ]), encoding="utf-8")
        b = classify(merged)
        print(f"= AUTHORITATIVE graph: {len(b['asns'])} ASNs · {len(b['ranges'])} ranges · "
              f"{len(merged)} records → {auth_out.relative_to(ACTOR)} (gitignored)")
        print("  per-RIR:", ", ".join(f"{k}={v[0]}+{v[1]}" for k, v in per_rir.items()))
        return

    bridged = []
    if source == "file" and infile:
        # offline bridge of a local delegated-stats-shaped file (:representative).
        reg = rir or pathlib.Path(infile).stem.split("-")[0]
        a, r = parse_delegated_stats(pathlib.Path(infile).read_text(encoding="utf-8"),
                                     reg, "representative", limit)
        bridged = a + r
        print(f"ipaddress.ingest: bridged {len(a)} ASNs + {len(r)} ranges from {infile} (:representative)")
    elif source == "rir":
        if not rir or rir not in RIR_STATS:
            sys.exit(f"--source rir needs --rir <{'|'.join(RIR_STATS)}>")
        if not live:
            print(f"ipaddress.ingest: source rir:{rir} = {RIR_STATS[rir]}")
            print("  → offline default (no --live): not fetched. Emitting seed only. "
                  "Pass --live (requires IPADDRESS_OPERATOR_GATE) for a real pull.")
        elif not OPERATOR_GATE:
            sys.exit("REFUSED: --live RIR pull is G7 operator-gated. Set "
                     "IPADDRESS_OPERATOR_GATE=<council/operator-token> to actively fetch "
                     f"{RIR_STATS[rir]} (public registry data only).")
        else:
            print(f"ipaddress.ingest: LIVE pull {RIR_STATS[rir]} …")
            a, r = parse_delegated_stats(fetch(RIR_STATS[rir]), rir, "authoritative", limit)
            bridged = a + r
            print(f"  pulled {len(a)} ASNs + {len(r)} ranges (:authoritative)")
    elif source == "rdns":
        ip_text = argv[argv.index("--ip") + 1] if "--ip" in argv else None
        if not ip_text:
            sys.exit("--source rdns needs --ip <addr>")
        if not (live and OPERATOR_GATE):
            sys.exit("REFUSED: --source rdns is a live probe; needs --live + IPADDRESS_OPERATOR_GATE.")
        rec = collect_rdns(ip_text)
        bridged = [rec] if rec else []
        print(f"ipaddress.ingest: rDNS {ip_text} → {rec[':rdns/ptr'] if rec else '(none)'}")
    elif source:
        sys.exit(f"unknown --source '{source}'. Known: rir, file, rdns, rdap.")

    # dedup-merge: seed wins on id collision
    seed_rows = load_edn(seed_path)
    merged, seen = [], set()
    for rec in seed_rows + bridged:
        if not isinstance(rec, dict):
            continue
        k = _key(rec)
        if k is None or k in seen:
            continue
        seen.add(k)
        merged.append(rec)

    out_path.write_text(to_edn(merged, [
        ";; ipaddress — GENERATED merged number-resource graph (seed + active ingest).",
        ";; DO NOT hand-edit. dedup by id, seed wins. kotoba EAVT (ADR-2605301400 §T2).",
    ]), encoding="utf-8")

    b = classify(merged)
    print(f"= merged graph: {len(b['rirs'])} RIRs · {len(b['asns'])} ASNs · "
          f"{len(b['ranges'])} ranges · {len(b['ips'])} IPs · {len(merged)} records")
    print(f"✓ wrote {out_path.relative_to(ACTOR)}")
    print(f"→ next: python3 methods/analyze.py {out_path.relative_to(ACTOR)} --out out")


if __name__ == "__main__":
    main(sys.argv)
