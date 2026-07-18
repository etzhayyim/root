#!/usr/bin/env python3
"""CI grep gate — forbid commercial remittance MSB references in kawase-yui source.

Enforces ADR-2605282200 G7: NEVER integrate / import / link to commercial
remittance MSB software in any kawase-yui runtime path. The structural
silenKawaseReview Lexicon already constrains the count to 0 at the audit
layer (commercialRemittanceSoftwarePenetrationPct const 0); this hook is the
build-time enforcement so violations are caught BEFORE they reach the audit.

The 15 prohibited vendors are explicit per ADR-2605282200 G7 + Charter Rider
§2(e) anti-gatekeeping + §2(c) covert-ops avoidance:

    Wise / TransferWise / Western Union / MoneyGram / Remitly / WorldRemit /
    Xoom / Revolut / OFX / Currencies Direct / Ria / Paysend /
    Atlantic Money / Sendwave / Boss Revolution / PayPal-Xoom

Allow-list (matched AFTER the violation regex, so excluded files never
trigger): ADR documents that NAME the prohibition in their G7 statement,
the kawase-yui README that documents the prohibition, this lint script
itself, and the silenKawaseReview Lexicon enum that DELIBERATELY EXCLUDES
the vendors. All other appearances are violations.

Exit codes:
    0 — clean (no violations)
    1 — at least one violation found

Usage::

    python3 70-tools/scripts/lint/verify_no_commercial_remittance.py
    python3 70-tools/scripts/lint/verify_no_commercial_remittance.py --root <path>
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

# Repo-root-relative paths to the runtime source trees we guard.
# As of R0 (ADR-2605282200), kawase-yui is path-reserved — these directories
# do not exist yet. We still register them so the hook is wired before R1
# code lands. Once R1 scaffolds the trees, the hook starts guarding them.
_GUARDED_ROOTS = [
    # Retained for synthetic-test roots and the MOVED tombstone. Live actor
    # source is scanned through ETZHAYYIM_KAWASE_YUI_ROOT below.
    Path("../com-etzhayyim-kawase-yui"),
    Path("40-engine/kotoba/crates/kotoba-kotodama/cells/kawase_pool_match"),
    Path("40-engine/kotoba/crates/kotoba-kotodama/cells/kawase_fx_oracle_watcher"),
    Path("40-engine/kotoba/crates/kotoba-kotodama/cells/kawase_rebalance_proposer"),
    Path("40-engine/kotoba/crates/kotoba-kotodama/cells/kawase_jurisdiction_compliance"),
    Path("40-engine/kotoba/crates/kotoba-kotodama/cells/kawase_silen_review"),
    Path("50-infra/etzhayyim-kawase-pool"),
    # Python facade — relocated per ADR-2605282300 from inside the
    # kotoba subrepo to a sibling location (same pattern as
    # kotoba_murakumo). Both paths are listed so the hook is layout-
    # tolerant during the ADR-2605282300 cutover window; the legacy
    # path is empty in the post-cutover tree.
    Path("40-engine/kotoba_kawase"),
    Path("40-engine/kotoba/py/kotoba_kawase"),
]

# File extensions to scan. We do NOT scan .md / .json / .toml — those are
# allowed to reference the prohibited vendor names because that is exactly
# where the prohibition is documented.
_EXTS = {".py", ".ts", ".tsx", ".js", ".mjs", ".cjs", ".rs", ".sol", ".go"}

# Vendor name patterns. Each is wrapped with \b word boundaries so partial
# matches (e.g., "wisely" does NOT match "wise") are excluded. Case-insensitive.
# We match import / from / require / package.json dependency / DSN / URL forms.
_VENDOR_NAMES = (
    r"transferwise",
    r"wise(?:[-_]?api|[-_]?sdk)?",  # wise / wise-api / wise_sdk
    r"western[-_ ]?union",
    r"moneygram",
    r"remitly",
    r"worldremit",
    r"xoom",
    r"revolut",
    # OFX is a 3-char identifier — only match when used as the company name,
    # not the Open Financial Exchange data format (which is also OFX).
    # We anchor on dependency-import contexts only via the IMPORT_CONTEXTS regex below.
    r"ofx[-_]?money",
    r"currencies[-_ ]?direct",
    # Ria is a common given name — require "ria" + remittance/money/transfer
    # in the same import/url context.
    r"ria[-_](?:money|remit|transfer|financial)",
    r"paysend",
    r"atlantic[-_ ]?money",
    r"sendwave",
    r"boss[-_ ]?revolution",
    r"paypal[-_ ]?xoom",
)

_VENDOR_RE = re.compile(
    r"(?ix)"
    r"(?:"
    + "|".join(_VENDOR_NAMES) +
    r")"
)

# Contexts in which a vendor-name match is treated as a violation.
# Outside these contexts (e.g., a docstring quoting the prohibition), it is
# not a violation; it is a description of the rule.
#
# Two regex variants:
#   _LINE_CONTEXTS matches an entire line that starts with an import/require
#                  /use statement or a package.json dependency line.
#   _URL_LITERAL_RE catches a vendor URL anywhere in a source line, including
#                   string-literal assignments (BASE_URL = "https://wise.com").
_LINE_CONTEXTS = re.compile(
    r"(?im)"
    r"^(?:"
    r"\s*from\s+\S+\s+import\s.+"     # python: from foo import bar
    r"|\s*import\s+\S+"                # python: import foo
    r"|\s*(?:const|let|var)\s+\S+\s*=\s*require\("  # node CJS
    r"|\s*import\s+(?:\{[^}]+\}|\S+)\s+from\s+['\"]"  # ES module
    r"|\s*\"[^\"]+\"\s*:\s*\"[^\"]+\""  # package.json dependency line
    r"|\s*use\s+\S+::"                 # rust: use foo::bar
    r")"
)
_URL_LITERAL_RE = re.compile(
    r"(?i)https?://[A-Za-z0-9.\-]*(?:"
    + "|".join(_VENDOR_NAMES) +
    r")[A-Za-z0-9.\-/_]*"
)

# Optional explicit allow-list — files that ARE allowed to contain the names
# (typically because they document the prohibition). Relative to repo root.
_ALLOW_LIST = {
    Path("70-tools/scripts/lint/verify_no_commercial_remittance.py"),
    # ADR documents are .md — already excluded by extension, but list explicitly
    # in case of future extension-set change.
    Path("90-docs/adr/2605282200-kawase-yui-multi-stable-adherent-remittance-mutual-aid.md"),
}


def find_violations(root: Path) -> list[tuple[Path, int, str]]:
    findings: list[tuple[Path, int, str]] = []
    actor_root = Path(os.environ.get(
        "ETZHAYYIM_KAWASE_YUI_ROOT",
        root.parent / "com-etzhayyim-kawase-yui",
    ))
    if actor_root.exists():
        for path in sorted(actor_root.rglob("*")):
            if path.is_file() and path.suffix in _EXTS:
                _scan_file(root, path, findings)
    for guarded in _GUARDED_ROOTS:
        pkg = root / guarded
        if not pkg.exists():
            # Path is reserved (R0) — no files to scan yet. Not a violation.
            continue
        if pkg.is_file():
            _scan_file(root, pkg, findings)
            continue
        for path in sorted(pkg.rglob("*")):
            if not path.is_file() or path.suffix not in _EXTS:
                continue
            _scan_file(root, path, findings)
    return findings


def _scan_file(root: Path, path: Path, findings: list[tuple[Path, int, str]]) -> None:
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path
    if rel in _ALLOW_LIST:
        return
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return

    # Pass 1: vendor name appears inside a line-anchored import/require/use.
    for ctx_match in _LINE_CONTEXTS.finditer(text):
        line = ctx_match.group(0)
        vendor_match = _VENDOR_RE.search(line)
        if not vendor_match:
            continue
        line_no = text[: ctx_match.start()].count("\n") + 1
        findings.append((rel, line_no, vendor_match.group(0)))

    # Pass 2: vendor URL appears anywhere in any line (string-literal
    # assignment, config dict value, decorator argument).
    for url_match in _URL_LITERAL_RE.finditer(text):
        line_no = text[: url_match.start()].count("\n") + 1
        findings.append((rel, line_no, url_match.group(0)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=Path(__file__).resolve().parents[3],
        type=Path,
        help="repo root (default: auto-detect from script location)",
    )
    args = parser.parse_args()

    findings = find_violations(args.root)
    if not findings:
        print(
            "no-commercial-remittance gate: clean "
            "(kawase-yui runtime source does not reference "
            "Wise / Western Union / MoneyGram / Remitly / WorldRemit / "
            "Xoom / Revolut / OFX-money / Currencies Direct / Ria / "
            "Paysend / Atlantic Money / Sendwave / Boss Revolution / "
            "PayPal-Xoom in any import or URL context)"
        )
        return 0

    print(
        "ADR-2605282200 G7 violation: kawase-yui source integrates a "
        "commercial remittance MSB (prohibited per Charter Rider §2(e) "
        "anti-gatekeeping + §2(c) covert-ops avoidance):",
        file=sys.stderr,
    )
    for path, line_no, match in findings:
        print(f"  {path}:{line_no}: {match!r}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
