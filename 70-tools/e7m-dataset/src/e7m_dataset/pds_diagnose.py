"""PDS resolver operator-side diagnostic CLI.

Mirror of `vision_pii_diagnose.py` for the PDS-side concerns
(`e7m_dataset.pds.resolve_datasetpin` + `parse_at_uri`).

Usage:

  # 1. Validate env + PDS reachability (HTTP HEAD; no auth):
  python3 -m e7m_dataset.pds_diagnose check
  # → reports ETZ_E7M_PDS_URL + reachability
  # → exit 0 = ready, 1 = unreachable, 2 = missing dep

  # 2. Parse an at-uri to (repo, collection, rkey):
  python3 -m e7m_dataset.pds_diagnose parse \
      at://did:web:dataset-pinner.etzhayyim.com/com.etzhayyim.substrate.datasetPin/3kpqab
  # → prints components; exit 0 = valid, 2 = malformed

  # 3. Resolve an at-uri against the configured PDS:
  python3 -m e7m_dataset.pds_diagnose resolve <at-uri>
  # → real GET com.atproto.repo.getRecord; prints CID
  # → exit 0 = found, 1 = not found / wrong collection, 2 = dep / parse error

Reduces operator-side debugging — before running assemble-usd-scene
with real datasetPin AT URIs (instead of `<rkey-placeholder>`), run
`check` + `parse` to validate the URI shape and PDS reachability.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Optional


def _check_dep(name: str) -> tuple[bool, str]:
    try:
        mod = __import__(name)
    except ImportError as exc:
        return False, str(exc)
    return True, str(getattr(mod, "__version__", "unknown"))


def _cmd_check(args: argparse.Namespace) -> int:
    """Validate PDS setup: httpx installed + env URL set + reachable."""
    report: dict = {
        "deps": {},
        "env": {},
        "reachable": None,
    }
    critical_missing = False

    for dep in ("httpx",):
        ok, info = _check_dep(dep)
        report["deps"][dep] = {"available": ok,
                                "version": info if ok else None,
                                "error": None if ok else info}
        if not ok:
            critical_missing = True

    pds_url = os.environ.get("ETZ_E7M_PDS_URL")
    report["env"]["ETZ_E7M_PDS_URL"] = pds_url or "(unset; defaults to https://pds.etzhayyim.com)"
    report["env"]["ETZ_E7M_PDS_DID"] = os.environ.get("ETZ_E7M_PDS_DID")
    has_session = os.environ.get("ETZ_E7M_PDS_SESSION")
    has_auth = os.environ.get("ETZ_E7M_PDS_AUTH")
    report["env"]["ETZ_E7M_PDS_SESSION"] = "(set)" if has_session else "(unset)"
    report["env"]["ETZ_E7M_PDS_AUTH"] = "(set)" if has_auth else "(unset)"

    if not critical_missing and not args.skip_network:
        from .pds import DEFAULT_PDS
        base = (pds_url or DEFAULT_PDS).rstrip("/")
        try:
            import httpx   # type: ignore
            with httpx.Client(timeout=args.timeout, follow_redirects=True) as c:
                # HEAD against the well-known XRPC root path; describes the
                # auth+health surface. /.well-known/atproto-did or
                # /xrpc/_health typically returns 200 or 404 (still proves
                # the server is up).
                resp = c.head(f"{base}/xrpc/")
                report["reachable"] = {
                    "url": f"{base}/xrpc/",
                    "status_code": resp.status_code,
                    "ok": resp.status_code < 500,
                }
        except Exception as exc:   # noqa: BLE001
            report["reachable"] = {
                "url": f"{base}/xrpc/",
                "error": str(exc),
                "ok": False,
            }

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        _print_human(report)

    if critical_missing:
        return 2
    if not args.skip_network and (report["reachable"] is None
                                   or not report["reachable"].get("ok")):
        return 1
    return 0


def _print_human(report: dict) -> None:
    print("PDS resolver setup check\n")
    print("Deps:")
    for dep, info in report["deps"].items():
        mark = "✓" if info["available"] else "✘"
        ver = info["version"] or info["error"]
        print(f"  {mark} {dep}: {ver}")
    print("Environment:")
    for k, v in report["env"].items():
        print(f"  - {k}: {v}")
    r = report["reachable"]
    if r is None:
        print("\nReachability: (skipped)")
    elif r.get("ok"):
        print(f"\nReachability: ✓ {r['url']} → HTTP {r['status_code']}")
    elif "error" in r:
        print(f"\nReachability: ✘ {r['url']} → {r['error']}")
    else:
        print(f"\nReachability: ✘ {r['url']} → HTTP {r['status_code']}")


def _cmd_parse(args: argparse.Namespace) -> int:
    from .pds import parse_at_uri, PdsError
    try:
        repo, collection, rkey = parse_at_uri(args.at_uri)
    except PdsError as exc:
        print(f"parse: {exc}", file=sys.stderr)
        return 2

    payload = {"repo": repo, "collection": collection, "rkey": rkey}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"repo:       {repo}")
        print(f"collection: {collection}")
        print(f"rkey:       {rkey}")
        if collection != "com.etzhayyim.substrate.datasetPin":
            print(f"  ⚠ collection differs from expected "
                  f"`com.etzhayyim.substrate.datasetPin`")
    return 0


def _cmd_resolve(args: argparse.Namespace) -> int:
    from .pds import resolve_datasetpin, PdsError
    try:
        record = resolve_datasetpin(args.at_uri, timeout_sec=args.timeout)
    except PdsError as exc:
        print(f"resolve: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(record, indent=2, default=str))
    else:
        print(f"cid:        {record.get('cid')}")
        print(f"name:       {record.get('name')}")
        print(f"revision:   {record.get('revision')}")
        print(f"size:       {record.get('sizeBytes')}")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="PDS resolver operator-side diagnostic CLI."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="Validate env + httpx + PDS reachability")
    p_check.add_argument("--json", action="store_true")
    p_check.add_argument("--timeout", type=float, default=5.0)
    p_check.add_argument("--skip-network", action="store_true",
                          help="Skip the HTTP HEAD reachability probe")
    p_check.set_defaults(func=_cmd_check)

    p_parse = sub.add_parser("parse", help="Parse an at:// URI into (repo, collection, rkey)")
    p_parse.add_argument("at_uri")
    p_parse.add_argument("--json", action="store_true")
    p_parse.set_defaults(func=_cmd_parse)

    p_resolve = sub.add_parser("resolve",
                                help="Resolve an at:// URI to the datasetPin record's CID")
    p_resolve.add_argument("at_uri")
    p_resolve.add_argument("--json", action="store_true")
    p_resolve.add_argument("--timeout", type=float, default=30.0)
    p_resolve.set_defaults(func=_cmd_resolve)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
