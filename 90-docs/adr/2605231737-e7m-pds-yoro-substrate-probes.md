---
id: adr-2605231737-e7m-pds-yoro-substrate-probes
title: "ADR-2605231737: e7m PDS / yoro substrate probes — operator + MCP surface for timeline-class debugging"
status: active
doc_type: adr
topic: e7m-operator-surface
authoritative: true
last_verified: 2026-05-23
priority: 4.5
axis: substrate
weight: 0.55
priority_note: "Closes the 'how does the operator (or an agent) debug yoro timeline-class failures through a sanctioned surface' gap."
authoritative_for:
  - 70-tools/e7m PDS / yoro probe commands
  - e7m-mcp tool surface for substrate introspection
  - timeline incident 2026-05-23 RCA + remediation record
depends_on:
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605211000
related:
  - adr-2605222330-etzhayyim-com-substrate-violation-transition-window
  - adr-2605211000
supersedes: []
superseded_by: []
---

# ADR-2605231737: e7m PDS / yoro substrate probes — operator + MCP surface for timeline-class debugging

**Status**: active
**Date**: 2026-05-23
**Deciders**: Jun Kawasaki + Claude Opus 4.7

## Context

The yoro frontend at `https://etzhayyim.com/` failed to load its timeline. The debugging session that diagnosed and remediated it consisted of:

1. Browser network capture (etzhayyim.com `/xrpc/app.bsky.feed.getDiscoverFeed` → **HTTP 405**)
2. Reading the deployed JS bundle to confirm the minified `atQuery` was emitting `POST` for every NSID
3. Cross-referencing the source (`60-apps/etzhayyim-project-yoro/.../atproto-agent.ts`) — already fixed to `GET`, but the deployed bundle pre-dated that fix
4. Probing the rw-free adapter chain (`etzhayyim-did-web` worker → `yoro-xrpc-adapter` service binding → `rw-free.collectFeed`)
5. Probing both PDS surfaces (`atproto.etzhayyim.com` vs `pds.etzhayyim.com`) for `did:web:yoro.etzhayyim.com` existence

All of this happened as ad-hoc `curl` + `grep` + `wrangler deploy`. There is no sanctioned operator surface for any of it.

Per ADR-2605192100 §1.6 (substrate boundary) and ADR-2605172000, every PDS / XRPC touchpoint should route through the e7m CLI or e7m-mcp server so audit hooks can be added in exactly one place. Today's incident was solved with bare curl because that surface didn't exist for yoro-class probes.

## Decision

Add a `pds` + `yoro` command family to `70-tools/e7m` (the Python operator CLI + MCP server), mirroring the manual flow used in the 2026-05-23 incident.

### Read-only surface (CLI + MCP)

| Command | XRPC | Why this is the canonical operator path |
|---|---|---|
| `e7m pds describe-server [--host <alias\|url>]` | `com.atproto.server.describeServer` | First call when an unfamiliar PDS is in play. Surfaces `inviteCodeRequired`, `availableUserDomains`, authorization servers. |
| `e7m pds list-repos [--host <h>] [--limit N] [--cursor C]` | `com.atproto.sync.listRepos` | Confirms which DIDs the PDS knows. Today's incident exposed that `pds.etzhayyim.com` is empty (`{repos:[]}`) while `atproto.etzhayyim.com` holds the `did:web:*.etzhayyim.com` corpus. |
| `e7m pds describe-repo <did> [--host <h>]` | `com.atproto.repo.describeRepo` | Yes/no answer for "does this DID actually have a repo on this PDS?". Sets `exists=true` only when the PDS returns a real DID (defends against the empty-shell response some custom PDS implementations send). |
| `e7m pds resolve-handle <handle> [--host <h>]` | `com.atproto.identity.resolveHandle` | Handle → DID. |
| `e7m pds xrpc <nsid> [--method GET\|POST] [--host <h>] [--params JSON] [--body JSON] [--bearer JWT] [--allow-write]` | any NSID | Generic escape hatch. POSTs to non-read NSIDs require `--allow-write` so an operator cannot accidentally mutate state. NSID prefix safelist matches the substrate surface (`com.atproto.*` read, `app.bsky.*`, `com.etzhayyim.yoro.*`). |
| `e7m yoro probe` | composite | Replays today's diagnostic in one call: apex HTML + bundle entrypoint + `atQuery` GET-vs-POST check + three feed endpoints. Idempotent. Use this *first* when the timeline is reported failing. |

### Write surface (CLI-only, NOT exposed via MCP)

| Command | XRPC | Why CLI-only |
|---|---|---|
| `e7m pds create-account --host <h> --handle <h> [--did <did>] [--invite <code>] [--email <e>] [--password <p>]` | `com.atproto.server.createAccount` | Mutates the substrate. Mirrors the `prune_approve` carve-out in `mcp_server.py` — only the operator may seed an account, through the local CLI with their explicit credentials. Agents may *propose* via chat; they may not invoke. |

### Host aliases

```
atproto = https://atproto.etzhayyim.com   (live PDS that yoro frontend currently uses)
pds     = https://pds.etzhayyim.com       (xrpc-adapter ACTOR_DID backend; currently empty)
yoro    = https://yoro.etzhayyim.com      (yoro static + xrpc routes)
apex    = https://etzhayyim.com           (did-web proxy → yoro)
```

Anything else accepted as a full URL so the same machinery serves staging / smoke targets.

### Implementation layout

```
70-tools/e7m/src/e7m/
├── pds.py             ← new: HTTP layer (httpx, already a dep) + safelist + probe composite
├── commands.py        ← thin wrappers re-exporting pds.* under the SoT layer
├── __main__.py        ← `e7m pds <action>` + `e7m yoro probe` subcommands
└── mcp_server.py      ← 6 new TOOLS + DISPATCH entries (write excluded)
```

`commands.py` stays the single funnel both surfaces (CLI + MCP) route through — keeps audit injection in exactly one place per the original e7m design contract.

## Consequences

### Positive

- **Today's incident reproducible in one call.** `e7m yoro probe` returns the exact 5-tuple (apex proxy headers / entry bundle / atQuery method / 3 feed endpoint statuses) that took ~20 manual curl/grep round-trips to diagnose. The recurrence cost is ~200ms.
- **Substrate boundary upheld.** `pds.etzhayyim.com` introspection no longer needs bare curl — it routes through the sanctioned operator surface so audit hooks (future) land in one spot.
- **Agent debugging cap restored.** The MCP server now exposes the same probes to other Claude sessions, which previously had no path to investigate yoro failures without violating ADR-2605192100 §1.6.
- **Write asymmetry preserved.** `create-account` is in the CLI but deliberately not in MCP — mirrors `prune_approve`. Substrate mutation stays operator-attributed.

### Negative / accepted

- `httpx` is now a required runtime dep (it already was — only formalized).
- The `_SAFE_NSID_PREFIXES` allowlist is curated. Adding new write-class NSIDs requires touching `pds.py` (intentional — write surface should be hard to grow accidentally).
- `e7m pds xrpc` is a powerful escape hatch. Operators must consciously add `--allow-write` for non-safelisted POSTs. We accept this in exchange for not needing one wrapper per NSID.

### Migration / install

`70-tools/e7m` is editable-installed in the local `.venv` (uv-managed); the new commands are live without rebuild. Wheel build verified: `uv build --wheel -o /tmp/e7m-dist` produces `e7m-0.1.0-py3-none-any.whl` (29 KiB) for any non-editable host. CLI + MCP smoke pass:

```bash
e7m --json pds describe-server --host pds       # → invite_code_required=true visible
e7m --json yoro probe                           # → 5 checks, ok=true after today's fixes
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | e7m-mcp \
  → 22 tools (16 baseline + 6 new)
```

## Timeline incident record (2026-05-23)

Captured here so future agents see the through-line from problem → tool. The 3 root causes and 3 remediations:

| # | Root cause | Remediation | Status |
|---|---|---|---|
| 1 | Deployed yoro-ui bundle's minified `atQuery` emitted `POST` for every XRPC (source already fixed) | Surgical 1-byte patch on `static/assets/index-KYx0b32R.js`: `Rf("POST",t,a,void 0,o)` → `Rf("GET",t,void 0,a,o)`; `wrangler deploy magatama-yoro` (Version `a054ad4d-f5d7-4803-8a0d-7cac4a727685`) | ✅ live |
| 2 | `rw-free.collectFeed` 500'd with `Could not find repo: did:web:yoro.etzhayyim.com` because the configured `pds.etzhayyim.com` has no repo for that DID | `try/catch` on the substrate read; `Could not find repo` / `RepoNotFound` → empty feed instead of 500; `wrangler deploy yoro-xrpc-adapter` (Version `a60f975d-a578-429e-bc26-3a42de1aa7fe`) | ✅ live |
| 3 | No sanctioned operator surface for any of the above probes | This ADR — `e7m pds *` + `e7m yoro probe` + 6 new MCP tools | ✅ this commit |

The downstream seed step (`did:web:yoro.etzhayyim.com` repo creation on `pds.etzhayyim.com`) is now a one-liner:

```bash
e7m pds create-account \
  --host pds \
  --handle yoro.etzhayyim.com \
  --did did:web:yoro.etzhayyim.com \
  --invite <CODE>
```

Blocked on the operator obtaining the invite code (not in repo, not knowable to an agent), which is the correct boundary.

## Alternatives Considered

- **Per-NSID wrappers.** Rejected: would need ~30 wrappers to cover the surface that today's incident touched, vs one `e7m pds xrpc` with a curated safelist. Adding wrappers later is cheap; removing the generic call after the fact is not.
- **Generic `e7m pds` exposed via MCP for writes too.** Rejected: mirrors the explicit `prune_approve` decision in `mcp_server.py` — mutations stay operator-attributed. Agents can propose by drafting the CLI command in chat.
- **Adding the surface to the Go `e7m-cli` (70-tools/e7m-cli/, binary at /opt/homebrew/bin/e7m) instead.** Rejected: the Go CLI's surface is build/deploy/actor for magatama components; the Python `e7m` is explicitly the "operator + MCP server — the only sanctioned external surface for the religious-corp organism" (per `pyproject.toml`). Probing the substrate fits there.
- **Patch the bundle in-place forever.** Rejected — the 1-byte patch is a stopgap; the long-term fix is the SvelteKit migration completing and the build pipeline emitting the corrected bundle. Recording the patch here so a future rebuild does not silently regress.

## References

- ADR-2605172000 (substrate boundary — no direct atproto/IPFS/L2 client imports from app code)
- ADR-2605192100 (mission charter §1.6 substrate; §1.3 decision attribution)
- ADR-2605211000 (worker xrpc-adapter deploy runbook)
- ADR-2605222330 (etzhayyim.com substrate-violation transition window — the broader runtime substrate context this incident lives inside)
- `70-tools/e7m/src/e7m/pds.py` — implementation
- `60-apps/etzhayyim-project-yoro/rw-free/src/feed.ts` — `collectFeed` resilience patch
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/static/assets/index-KYx0b32R.js` — atQuery POST→GET in-place patch
