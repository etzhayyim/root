# 20-actors/aratame — CLAUDE.md

## Identity

- **Name**: aratame (改め — *to inspect / to examine*, as in 関所改め; the **static-source diagnosis sibling** of `akuma` 悪魔 and the **upstream finding source** for `tsukuroi` 繕い)
- **DID**: `did:web:aratame.etzhayyim.com`
- **nanoid**: `4r4t4m3i`
- **ADR**: ADR-2606024000 (R0 scaffold, 2026-06-02) — SSoT
- **Runtime-diagnosis sibling**: ADR-2605151400 (akuma — runtime / blackbox probing)
- **Remediation sibling / downstream consumer**: ADR-2605291500 (tsukuroi — propose-only patch proposal)
- **Parent ADRs**: ADR-2605192100 (Mission Charter), ADR-2605192200 (Charter Rider), ADR-2605215000 (Murakumo-only), ADR-2605231525 (no platform-held key), ADR-2605262130 (kotoba), ADR-2605181100 (encrypted records), ADR-2605312330 (giemon purl→CVE, reused)
- **Status**: R0 scaffold — 8 cells path-reserved; 6 Lexicon skeletons under `com.etzhayyim.aratame.*`
- **Form**: 任意団体 internal source-inspection substrate (NOT a commercial SAST/SCA SaaS; non-profit only)
- **Inference model**: `gemma4-26b-a4b` (Gemma 4 MoE, ~26B total / ~4B active) — **Murakumo-only** via judah LiteLLM `127.0.0.1:4000` (ADR-2605215000). **New fleet registration required** (fleet serves `gemma4:e4b` today).

## One-line purpose

Take an **owner-attested GitHub repository** → READ-ONLY clone repo@ref into an
egress-restricted sandbox → OSS **SAST + SCA + secret** scan → **Murakumo-only**
LLM triage (`gemma4-26b-a4b`, dedup/severity/false-positive, *non-adjudicating*)
→ emit tsukuroi-compatible `vulnFinding` records + an aggregate `inspectionReport`.
**Read-only & static-only**: aratame **never executes the target code**, **never
writes to the repo**, and holds **no platform master key**. Remediation is
tsukuroi's (propose-only); aratame never patches.

## Three-actor security boundary (CRITICAL)

```
akuma 悪魔     runtime / blackbox diagnosis   (probes running targets, NO write, NO source)
aratame 改め   static / source diagnosis      (reads source, NO execution, NO write)   ← THIS ACTOR
tsukuroi 繕い  remediation                    (proposes patches, propose-only, NO probe, NO scan)
```

Three actors, three egress namespaces, one human at every merge gate. A
compromise of any one cannot trivially become another.

## Capability ceiling (CRITICAL — IMMUTABLE)

1. **READ-ONLY / STATIC-ONLY (G3)** — clones source read-only and runs *static*
   analyzers. NO code execution, NO dynamic analysis / DAST / fuzzing, NO
   write/commit/push to the repo. `codeExecutionCount=0`, `writeToTargetCount=0`.
2. **OSS-TOOLING-ONLY (G5)** — Semgrep OSS / CodeQL OSS terms / OSV-Scanner /
   Trivy / gitleaks / trufflehog OSS. Commercial SAST/SCA SaaS PROHIBITED
   (Charter Rider §2(e)).
3. **NON-ADJUDICATING (G8)** — findings are evidence / an accountability +
   resilience map, NOT a verdict, NOT an exploitation target-list.
   `nonAdjudicating` const `true`.
4. **DEFENSIVE-ONLY / NO EXPLOIT (G9)** — describes a weakness; NO PoC / exploit
   / offensive payload, even as a test fixture (Charter Rider §2(a)).
5. **NO PLATFORM-HELD KEY (G6)** — private-repo read via owner-issued,
   least-privilege, read-only, expiring credential (vault ciphertext) per
   ADR-2605231525. `platformHeldKeyCount=0`.

## InspectionMandate contract

`com.etzhayyim.aratame.inspectionMandate` — `repoUrl`, `ref` (pinned
branch/tag/commit), `publicRepo`, `accessCredentialRef` (ref, not secret;
read-only), `scanTools[]` (closed OSS allowlist), `allowedPaths[]`,
`ownerDid`+`ownerSignature`, `authorityDid`+`authoritySignature`,
`validFrom`/`validUntil`, `legalBasis`, `readOnly` const `true`,
`writeAuthorityHeld` const `false`, `maxReposPerWindow`, `revoked` (one-way).

Valid iff both signatures verify, in window, not revoked, and (for private repos)
`accessCredentialRef` resolves to a live owner-issued read-only token on the same
owner+repo.

## Cells (8; R0 path-reserved under `20-actors/magatama/cells/aratame_*/`)

| Cell | Purpose | Key gate |
|---|---|---|
| `repo_intake` | validate dual-sig mandate; read-only clone repo@ref into egress-restricted sandbox | G3, G4, G6, G11 |
| `sast_scan` | OSS SAST (Semgrep OSS / CodeQL OSS) over source → sastFindings | G3, G5, G9 |
| `sca_scan` | OSS SCA (OSV-Scanner / Trivy) + giemon purl→CVE → dependencyFindings | G3, G5 |
| `secret_scan` | OSS secret detection (gitleaks / trufflehog OSS); encrypted envelope refs only | G3, G7 |
| `triage_synthesis` | Murakumo `gemma4-26b-a4b` dedup/severity/false-positive triage; non-adjudicating | G8, G10 |
| `charter_rider_scan` | §2(a)..(h) scan + offensive/PoC rejection on every emitted text | G1, G9 |
| `finding_emit` | emit tsukuroi-compatible vulnFinding + inspectionReport to kotoba+MST | G2, G13 |
| `silen_aratame_review` | quarterly Council audit; structural zero-counters | G14 |

Each cell is import-time `RuntimeError("aratame R0 scaffold: activate via Council
ADR + R1 ratification")` until R1.

## Lexicons (`com.etzhayyim.aratame.*`)

`inspectionMandate` (`readOnly` const true / `writeAuthorityHeld` const false) ·
`vulnFinding` (`nonAdjudicating` const true / `defensiveContextOnly` const true;
**tsukuroi finding source**) · `dependencyFinding` (purl→CVE, mirrors giemon
`VulnMatch`) · `secretFinding` (`encryptedOnly` const true — envelope ref, never
plaintext) · `inspectionReport` (`executedCode` const false / `nonAdjudicating`
const true) · `silenAratameReview` (zero-counters: `outOfScopeRepoCount`,
`codeExecutionCount`, `plaintextSecretCount`, `vendorInferenceCount`,
`writeToTargetCount` — any nonzero ⇒ cell halt + `chigiri.disputeMediation`).

## Closed loop with akuma + tsukuroi

```
owner-attested GitHub repo (InspectionMandate, dual-sig)
   → aratame.repo_intake        (read-only clone, egress-restricted)
   → aratame.{sast_scan, sca_scan, secret_scan}   (OSS tools)
   → aratame.triage_synthesis   (Murakumo gemma4-26b-a4b; non-adjudicating)
   → aratame.charter_rider_scan → aratame.finding_emit
   → com.etzhayyim.aratame.vulnFinding + inspectionReport
   → [tsukuroi.finding_intake consumes vulnFinding under a RemediationMandate]
   → tsukuroi proposes a defensive patch (PROPOSE-ONLY) → [HUMAN OWNER MERGES]
```

aratame **finds in source**, akuma **finds at runtime**, tsukuroi **mends**.

## Topology (kotoba-native)

- **Edge**: SvelteKit CF Worker proxy `aratame.etzhayyim.com` (edge only)
- **Runtime**: K8s `aratame-langserver`; external surface = magatama MCP facade only
- **Scan**: egress-restricted `aratame-scan` namespace; egress only to the
  owner-attested git source (read), never elsewhere; no code execution
- **Persistence**: kotoba datom (EAVT) + MST `com.etzhayyim.aratame.*`; raw scan
  payloads + detected secrets + read-only credentials ciphertext in
  `vault.etzhayyim.com`
- **Inference**: Murakumo only (ADR-2605215000) — `gemma4-26b-a4b` via judah
  LiteLLM `127.0.0.1:4000`; NO vendor API. **Requires fleet registration** of
  `gemma4-26b-a4b` (LiteLLM route + `ollama create` on a ≥128 GB node) before R1.

## Runnable R0 demonstrator (offline, not gated)

Like its R0 siblings (watatsuna / kabuto), aratame ships a working **offline**
analysis path that runs today — the Council-gated *cells* are separate:

- `methods/inspect.py` (stdlib only) inspects `data/sample-repo/` (a
  `:representative` weak fixture) → `out/inspection-report.md` (aggregate-first,
  non-adjudicating) + `out/findings.kotoba.edn` (`:derived`, seeds `vulnFinding`).
- READ-ONLY / STATIC-ONLY for real: Python is read via `ast.parse`, **never**
  executed (G3). Secret values are never written out — only a sha256
  envelope-ref + redaction (G7).
- **Honest stand-ins**: SAST = `:representative` `ast` rules (NOT Semgrep/CodeQL);
  SCA = bounded `:representative` CVE seed-table join (NOT live OSV/Trivy); triage
  is deterministic — the Murakumo `gemma4-26b-a4b` LLM triage (G10) is R1-gated
  and intentionally not called. Run: `python3 methods/inspect.py`.

## R0 → R3

- **R0** (this commit): charter + scaffold (8 cell paths + 6 Lexicon skeletons +
  reserved LiteLLM `gemma4-26b-a4b` route) **+ the offline `methods/inspect.py`
  demonstrator above**. The cells carry no runtime code (import-time RuntimeError).
- **R1** (Council Lv6+ ≥3 ratify + ≥1 filled seat + `gemma4-26b-a4b` on the
  fleet): 4 core cells (`repo_intake` / `sast_scan` / `sca_scan` /
  `triage_synthesis`) + kotoba datom schema; public repos only; findings internal.
- **R2** (+30-day public objection): + `secret_scan` + `charter_rider_scan` +
  `finding_emit` + first `silenAratameReview`; private repos under a dual-signed
  mandate after a benign public dry run; first handoff into tsukuroi.
- **R3** (+Council Lv7+ for scan_tools allowlist expansion): multi-repo / org-wide
  mandates; federation with toritate + chigiri + kataribe.

## Related Files

- `/90-docs/adr/2606024000-aratame-source-vulnerability-inspection-tier-b-actor-r0.md` — Master ADR (SSoT)
- `/90-docs/adr/2605151400-akuma-authorized-redteam-actor.md` — runtime-diagnosis sibling
- `/90-docs/adr/2605291500-tsukuroi-authorized-remediation-tier-b-actor-r0.md` — remediation sibling / downstream consumer
- `/90-docs/adr/2605312330-giemon-part-graph-sbom-kotoba-fleet-cve-svelte.md` — purl→CVE VulnMatch (reused by sca_scan)
- `/90-docs/adr/2605215000-etzhayyim-inference-murakumo-only-no-runpod.md` — Murakumo-only (gemma4-26b-a4b)
- `/90-docs/adr/2605231525-server-side-signing-capability.md` — no platform-held key
- `/90-docs/adr/2605262130-kotoba-storage-substrate-unification.md` — storage substrate
- `/90-docs/adr/2605181100-encrypted-records.md` — secret envelopes
- `/00-contracts/lexicons/com/etzhayyim/aratame/` — 6 Lexicons
- `/CHARTER-RIDER.md` · `/COUNCIL.md` · `/CLAUDE.md`
