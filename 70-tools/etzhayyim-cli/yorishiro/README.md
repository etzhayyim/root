# @etzhayyim/yorishiro

依代 (yorishiro) generator — wrap an external app or webservice into an
etzhayyim **3-layer actor** (Lexicon SSoT + magatama Pregel cell + MCP
server) so that an agent can drive it through the substrate.

Per **ADR-2605211900**. Phase 1 ships the generator skeleton + OpenAPI v3
input mode + the first reference yorishiro (arxiv).

> **依代** (yorishiro) は kami が宿る vessel。外部 software = kami、
> 生成された 3-layer artifact = vessel。`unispsc-isic-mcp`
> (ADR-2605180900 Phase 8) を hand-written reference impl とし、本
> generator はその pattern の量産機。

## What it emits (3-layer, all-or-nothing)

For a yorishiro named `<name>` with N operations, the generator writes:

```
00-contracts/
└── lexicons/ai/etzhayyim/yorishiro/<name>/
    ├── <op1>.json        # Lexicon (atproto schema 1, query|procedure)
    ├── <op2>.json
    └── ...

20-actors/magatama/cells/yorishiro_<name>/
    ├── cell.py           # Pregel cell.py (ADR-2605202200 runtime contract)
    └── README.md

20-actors/magatama/mcp/yorishiro-<name>-mcp/
    ├── package.json
    ├── tsconfig.json
    ├── README.md
    └── src/
        ├── index.ts
        ├── cli.ts        # stdio entry (Claude Desktop / Codex CLI)
        ├── server.ts     # MCP Server factory (stdio + Streamable HTTP)
        └── tools.ts      # zod schemas + handler dispatch

skills/etzhayyim-yorishiro-<name>/
    └── SKILL.md
```

The L1 Lexicon JSONs carry four required extension fields (D2 in
ADR-2605211900):

| Field | Purpose |
|---|---|
| `x-yorishiro-external: true` | flags any op that crosses the substrate boundary |
| `x-yorishiro-kami: "<id>"` | the kami being inhabited (FQDN / package / binary) |
| `x-yorishiro-transport: "openapi-v3" \| "source-repo" \| "browser-only" \| "binary-cli"` | input source mode the generator used |
| `x-charter-purpose: [...]` | ADR-2605192115 purposes. **`subscription` / `purchase` / `tip` are rejected at pre-commit by `no-external-purchase-purpose`** |

## CLI

```bash
# Phase 1: OpenAPI v3 mode
yorishiro create <name> \
  --from openapi-v3 \
  --source <url-or-path-to-openapi-spec> \
  --kami <fqdn>           \
  --purpose <csv>          # e.g. grant,kisha,donation

# regenerate from the same kami source (after kami API changes)
yorishiro regen <name>

# list all yorishiri in the repo
yorishiro list

# Charter compliance audit: scan every yorishiro lexicon for invalid
#   x-charter-purpose values + missing x-yorishiro-external flag.
yorishiro audit
```

## Input source modes

| Mode | Status | Inputs |
|---|---|---|
| `openapi-v3` | **Phase 1 ✓** | OpenAPI 3.x JSON/YAML at a URL or local path |
| `source-repo` | Phase 2 ⏳ | git URL or local repo path (CLI-Anything style AST analysis) |
| `browser-only` | Phase 3 ⏳ | base URL + a Playwright/UI flow script + mcp__claude-in-chrome |
| `binary-cli` | Phase 2 ⏳ | local binary with `--help` introspection |

## Reference yorishiri (shipped)

| Name | Kami | Mode | Purposes | Ops |
|---|---|---|---|---|
| `arxiv` | `arxiv.org` | `openapi-v3` | `grant` | `searchPapers` |

The arXiv kami OpenAPI spec lives at
`00-contracts/openapi/kami/arxiv.openapi.json` (hand-authored because
arXiv does not publish OpenAPI). To regenerate the arXiv yorishiro:

```bash
cd 70-tools/etzhayyim-cli/yorishiro
pnpm yorishiro create arxiv \
  --from openapi-v3 \
  --source ../../../00-contracts/openapi/kami/arxiv.openapi.json \
  --kami arxiv.org \
  --purpose grant
```

## Charter compliance

The generator refuses to emit a yorishiro whose `--purpose` list contains
any of: `subscription`, `purchase`, `tip`. This mirrors
ADR-2605192115 §4 (Charter Rider v2.0): external write-side ops must
carry only non-profit purposes. The same constraint is enforced at
pre-commit by the `no-external-purchase-purpose` lefthook hook so a
hand-written lexicon cannot smuggle a forbidden value past the
generator.

## Hard rules (constitutional, NOT amendable)

Per ADR-2605211900 §Constitutional invariants:

- A yorishiro **must not** wrap an ad-tech kami (GA4 ads / Meta Pixel
  / AdSense / affiliate network) — see Charter Rider §2(a).
- A yorishiro **must not** wrap a covert force / closed-source military
  kami — see ADR-2605192100 §1.12 (Transparent Religious Force only).
- A yorishiro **must not** wrap an eschatological / apocalyptic kami
  (Revelation-derived, end-times prediction APIs) — see
  ADR-2605192100 §1.15 (non-eschatological).
- A yorishiro `x-charter-purpose` **must not** include `subscription`,
  `purchase`, or `tip` for external write-side ops — see ADR-2605192115
  §4. The internal SBT↔SBT carveout is **not** the concern of
  yorishiro; internal carveout apps stay as ordinary magatama actors.

## See also

- ADR-2605211900 (full architecture, this generator's authoritative spec)
- ADR-2605202200 (magatama cell.py runtime contract — what L2 must export)
- ADR-2605180900 (LangGraph Pregel + MCP bridge, hand-written reference impl)
- `20-actors/magatama/mcp/unispsc-isic-mcp/` (the first hand-written 3-layer)
- HKUDS/CLI-Anything (external inspiration, output-layer translated to etzhayyim)
