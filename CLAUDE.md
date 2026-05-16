# etzhayyim/root — CLAUDE Index

This monorepo is the **principal-owned half** of the source-control boundary established by ADR 2605152100.

## Status

**Scaffolding only** (2026-05). Content seed (`git filter-repo` from `gftdcojp/ai-gftd-apps-gftdcojp`) is pending. Until seeded, this repo holds:

- `LICENSE` (Apache 2.0)
- `README.md`
- `CLAUDE.md` (this file)
- `deps.toml` (minimal stub; full SSoT remains in vendor monorepo)
- `.gitignore`
- `lefthook.yml` (stub)

## Authoritative SSoT During Scaffolding

Until this monorepo is seeded, defer to the vendor monorepo for full conventions:

- **Repo**: https://github.com/gftdcojp/ai-gftd-apps-gftdcojp
- **Root CLAUDE.md**: project index, all rules / ADR pointers / lexicon / migration policy
- **Root deps.toml**: full SSoT (`[platform.operating_entity]`, `[directory_index.*]`, ADR registry, etc.)
- **ADRs**: `90-docs/adr/` — design decisions, including ADR 2605152100 (this org boundary)

## Identity Reminder

- **Operating entity** (this repo's owner): `etzhayyim` (canonical)
  - Aliases: `amanomibashira` / `天御柱` / `עץ חיים` (Tree of Life) / `etz hayim` / `etzhayim` / `etz chaim` / `エツ・ハイム`
  - Form: 宗教法人 (任意団体 / unincorporated religious voluntary association)
  - Registry: On-chain (blockchain-registered constitution and member roster)
  - DID: `did:web:etzhayyim.com`
  - Domain: https://etzhayyim.com
  - License default: Apache 2.0
- **Vendor**: Gftd Japan株式会社 (corporate number 9007-2846, `did:web:gftd.co.jp`)
- **Boundary rule (CRITICAL)**: Payoff帰属・意思決定権 = etzhayyim only. Vendor risk = SOW / SLA / termination / IP-ownership internalized.

## Planned Layout (post-seed)

Mirrors Shannon-Optimal 8-Layer Architecture (ADR 2604251830):

```
00-contracts/   # open lexicons / bpmn / dmn / Rego policies
10-protocol/    # atproto, xrpc, lexicons-bundle, signal, did-etzhayyim
20-actors/      # magatama actor framework + Pregel-pattern SDK
30-graph/       # open graph schemas + RisingWave migrations
50-infra/       # geth, holochain, ipfs, blockscout, etzhayyim-pds
60-apps/        # open-* (22), public-* (2), atproto, ameno, baien
90-docs/        # open-relevant ADRs
```

## Seed Migration Plan

See ADR 2605152100 §"Seed migration plan (revised — monorepo single-shot)" in the vendor monorepo. Steps 1-5 are done as of 2026-05-15; step 6 (filter-repo content seed) is the next major action.

## Do Not

- Do not copy private business documents (CEO packets, SOW templates, lawfirm legal pages, vault contents, family-office registration). Those belong in the vendor monorepo only.
- Do not introduce `gftd-` prefixed identifiers in newly seeded code. Use `etzhayyim-` or no prefix.
- Do not weaken the Apache 2.0 license default. Religious-corp public-interest activity requires permissive license.

## Future Work

Once seeded:

- Set up lefthook hooks mirrored from vendor monorepo (adr-validate, docs-registry, bpmn-contract-gates)
- Set up GitHub Actions CI (lint / type-check / build / test)
- Set up Dependabot
- Publish `did:web:etzhayyim.com/.well-known/did.json` (Cloudflare Pages or Worker)
