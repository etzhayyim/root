# aratame 改め

> Authorized GitHub-repo **static-source vulnerability inspection**. Tier-B, R0. ADR-2606024000.
> Read the repo-root `CLAUDE.md` and `20-actors/aratame/CLAUDE.md` first.

The **third leg** of the authorized-security triad:

```
akuma 悪魔     runtime / blackbox diagnosis   (probes running targets)
aratame 改め   static / source diagnosis      (reads source, NO exec, NO write)  ← this actor
tsukuroi 繕い  remediation                    (proposes patches, propose-only)
```

aratame takes an **owner-attested** GitHub repo, clones it **read-only** into an
egress-restricted sandbox, runs OSS **SAST + SCA + secret** scans, triages with a
**Murakumo-only** LLM (`gemma4-26b-a4b`, non-adjudicating), and emits
tsukuroi-compatible `vulnFinding` records. It **never executes the target code**,
**never writes the repo**, and holds **no platform key**. Remediation is
tsukuroi's (propose-only).

## Layout

| Path | What |
|---|---|
| `methods/inspect.py` | **runnable R0 offline demonstrator** (stdlib only) — SAST (Python `ast`) + SCA (purl→CVE) + secret scan |
| `data/sample-repo/` | `:representative` intentionally-weak fixture (the inspected "repo"; weakness patterns only, no exploit) |
| `data/seed-cve-table.kotoba.edn` | bounded `:representative` purl→CVE table (mirrors giemon VulnMatch) |
| `out/inspection-report.md` | aggregate-first, non-adjudicating report + tsukuroi handoff |
| `out/findings.kotoba.edn` | derived findings (`:derived` / `:non-adjudicating`), seeds `com.etzhayyim.aratame.vulnFinding` |
| `CLAUDE.md` · `manifest.jsonld` | actor charter + manifest |

The 8 Pregel cells (`20-actors/magatama/cells/aratame_*/`) and 6 lexicons
(`00-contracts/lexicons/com/etzhayyim/aratame/`) are R0 scaffold (import-time
`RuntimeError`), Council-gated for R1.

## Run

```bash
cd 20-actors/aratame
python3 methods/inspect.py                     # inspects data/sample-repo/ → out/
python3 methods/inspect.py /path/to/repo --out /tmp/o
```

## Honest R0

The SAST rule set is a `:representative` stdlib `ast` stand-in (**not** Semgrep OSS
/ CodeQL); SCA joins a bounded `:representative` CVE seed table (**not** live OSV /
Trivy); secret values are never persisted (sha256 envelope-ref only, G7). The
Murakumo-only LLM triage (`gemma4-26b-a4b`, G10) is **R1-gated** and not invoked —
triage is deterministic here. Live OSS scanners + advisory feeds + private-repo
mandates + the cells are R1/R2 + Council/operator gated. `gemma4-26b-a4b` itself
needs Murakumo fleet registration (fleet serves `gemma4:e4b` today).
