# RisingWave→kotoba Migration Roadmap

**Status**: ADR-2606021730 P9 refactor complete (coverage app). Planning next phases.

**Master timeline**: P0–P3 (schema, resolver, topics, fission-gate) ✅ shipped in tsumugi  
**App-layer timeline**: P9 (coverage app) ✅ complete (2026-06-02)  
**Remaining**: P10+ (other apps) — priority TBD

---

## Migration Categories

### Category A: Latent-Entity Path (ADR-2606021730)

Apps querying `vertex_latent_entity`, `edge_entity_evidence`, `vertex_lda_*`:

- ✅ **coverage** (P9 done, 2026-06-02)
- [ ] *others TBD by grep scan*

### Category B: World Coverage & Domain Data

Apps querying `mv_world_coverage_live`, `vertex_domain_rank`, etc.:

- [ ] `yoro` (maps app — may need coverage metrics)
- [ ] `jp-fiscal` (government coverage)
- [ ] Others (TBD)

### Category C: Organization & Supply Chain

Apps querying `vertex_org`, `edge_org_supply`:

- [ ] `kabuto` (public-company supply chain, tsumugi sibling)
- [ ] Other org/corp entities (TBD)

### Category D: General Actor/Collection Queries

Apps querying `vertex_actor`, `vertex_post`, `vertex_profile`:

- **Assessment**: Most are framework-level (magatama-host-sdk). Mass refactor needed.
- **Scope**: 50+ apps found. Potential for parallel batch refactor.

### Category E: Legacy etzhayyim Projects

Mostly seeded from old etzhayyim project. Most are NOT priority for etzhayyim charter refactoring.

- `yatabase`, `ongakuka`, `kyber-*`, `open-*` — **Assessment: Archive-pending**
- `manimani` — **Assessment: Constitutional audit needed**

---

## Priority Assessment (Next 30 Days)

### P10 (High priority — validation + consumer refactors)

**Verified 2026-06-02**: tsumugi (latent-entity) + kabuto (org/supply-chain) both output kotoba-native `.edn`.
- tsumugi: `:latent/* :topic/* :spirit.bond/*` (ADR-2606011800)
- kabuto: `:company/* :supply.edge/* :company.process/*` (ADR-2606022000)

**Remaining work**: Find apps that CONSUME these (latent-entity reports, supply-chain viz, etc.) and refactor
their RW queries to kotoba adapters (similar to P9 pattern).

- **Scope**: latent-entity consumer apps (coverage ✅ done) + supply-chain consumers (TBD) + analysis/viz
- **Effort**: 2–3 apps × 60 min each = ~2–3 hours (reduced due to already-native producers)
- **Gate**: G2 (edge-primary), G6 (Murakumo-only), G14 (verified kotoba)
- **Target**: End of Phase 2 (post-Council testnet, 2026-07-15 est)

### P11 (Medium priority — framework cleanup)

- **Scope**: magatama-host-sdk + 50+ inherited apps (batch refactor)
- **Effort**: Architecture review + codegen tool (~8 hours)
- **Gate**: Framework-level (no G-gates)
- **Target**: Phase 2.5 (post-Phase 2 full LDA)

### P12 (Low priority — archive)

- **Scope**: Legacy etzhayyim projects (yatabase, ongakuka, etc.)
- **Action**: Constitutional audit → archive or rebuild
- **Target**: Post-mainnet (Phase 3+)

---

## Honest Assessment

- **Covered**: Latent-entity path (P9 ✅)
- **Partially covered**: World coverage metrics (fixture mode)
- **Not covered**: Org/supply-chain (tsumugi/kabuto pending)
- **Not covered**: Framework-level actor/collection queries (50+ apps)

Estimated **total RW→kotoba work**: 15–20 hours across P10–P12.

Current momentum: 1 hour/iteration (P9 in 3 iterations). Sustainable pace: 10 min/day = 5 hours/week.

**Realistic mainnet readiness**: Phase 2.5 (post-testnet, 2026-07-15 est.)
