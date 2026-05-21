# yorishiro_arxiv

Pregel cell for the **arxiv** yorishiro (kami: `arxiv.org`).

Per **ADR-2605211900** (yorishiro external-actor bridge) +
**ADR-2605202200** (magatama cell.py runtime contract).

Generator: `@etzhayyim/yorishiro` v0.1.0
Transport: `openapi-v3`
Base URL : `http://export.arxiv.org/api`
Charter purposes: `grant`

## Ops

| Op | HTTP | Summary |
|---|---|---|
| `searchPapers` | `GET` `/query` | Search arXiv papers |

## Lexicon SSoT

`00-contracts/lexicons/ai/etzhayyim/yorishiro/arxiv/searchPapers.json`

## MCP exposure

`20-actors/magatama/mcp/yorishiro-arxiv-mcp/` (stdio + Streamable HTTP)

## Regenerate

```bash
yorishiro regen arxiv
```

Hand edits to `cell.py` are overwritten on regen — extend the kami
OpenAPI spec at `00-contracts/openapi/kami/arxiv.openapi.json` instead.
