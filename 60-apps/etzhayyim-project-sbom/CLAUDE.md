# sbom.etzhayyim.com — SBOM + Patch Management

Software Bill of Materials。`etzhayyim build` 時に SBOM 自動生成 → yabai CVE マッチ → 影響 app blast radius → completer 連携。

## Architecture

| 項目 | 値 |
|---|---|
| **Runtime** | Single Worker (`sb0m001x`) |
| **UI** | appview (Protocol Canvas card UI) |
| **Data** | SQL graph — `SbomArtifact`, `SbomComponent`, `VulnMatch`, `PatchPolicy`, `PatchAction` |
| **W Protocol Event Stream** | WRecord kinds: `sbom.sbom_artifact`, `sbom.component`, `sbom.vuln_match`, `sbom.patch_policy`, `sbom.patch_action` |
| **WIT export** | `etzhayyim:sbom/component-registry@1.0.0`, `vuln-match@1.0.0`, `patch-management@1.0.0` |
| **Domain** | `sbom.etzhayyim.com` / `sb0m001x.etzhayyim.com` |

## Graph Relationships

```
SbomArtifact -[:CONTAINS]-> SbomComponent
SbomComponent -[:DEPENDS_ON]-> SbomComponent
VulnMatch -[:AFFECTS]-> SbomComponent
VulnMatch -[:REFERENCES]-> CveEntry (yabai)
PatchAction -[:PATCHES]-> VulnMatch
SbomArtifact -[:BUILT_FOR]-> App (yata)
```

## CVE → App Blast Radius Pipeline

```
[etzhayyim build] → register-sbom (CycloneDX/SPDX) → SbomComponent graph
[ct-monitor] → poll-vuln-feeds → yabai ingest-cve → CveEntry graph
[sbom] → run-vuln-match → CveEntry × SbomComponent → VulnMatch → affected apps
[sbom] → get-blast-radius(cve_id) → all affected apps/components
[sbom] → create-patch-action → propose upgrade → decide → deploy
```

## Patch SLA Defaults

| CVSS Severity | SLA (hours) |
|---|---|
| Critical (≥9.0) | 24 |
| High (≥7.0) | 72 |
| Medium (≥4.0) | 168 |
| Low (<4.0) | 720 |

## SBOM Formats

- **CycloneDX 1.5** (default) — Component inventory + vulnerability references
- **SPDX 3.0** — License compliance + package provenance

## Cross-actor Integration

| Target | Method | Purpose |
|---|---|---|
| yabai.etzhayyim.com | `ingest-cve` / `search-cves` | CVE source for vulnerability matching |
| completer.etzhayyim.com | `evaluate` | Compliance evaluation post-patch |

## Key Files

| File | Purpose |
|---|---|
| `wasm/etzhayyim-wasm-sbom-sb0m001x/src/app.ts` | Single-file business logic |
| `wasm/etzhayyim-wasm-sbom-sb0m001x/kotodama.jsonld` | Runtime config |
| `wit/sbom/package.wit` | Domain WIT (component-registry, vuln-match, patch-management) |
