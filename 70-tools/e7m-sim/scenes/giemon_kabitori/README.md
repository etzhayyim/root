# giemon kabitori (黴取り) — mold-removal probe sim

A clean-room (NVIDIA-free, ADR-2605261800 N1..N9) physics simulation of a
slender cleaning manipulator that removes **existing** mold from confined
surfaces: A/C drain pans + blower housings, building gaps/cavities, and HVAC
ducts. Built on the `kami-genesis` 3-D reduced-coordinate spatial solver
(Featherstone RNEA bias + CRBA mass matrix + LDLᵀ, semi-implicit Euler) and its
rigid contact/collision solver — the same engine that drives the giemon arm.

## Why a probe, not a "nanomachine"

Autonomous mold-eating nano/microrobots are science fiction (no air-borne
propulsion, no autonomy, no energy/recovery). The achievable machine is a
**steerable cleaning probe**: feed it into the gap, press a brush onto the
mold, scrub with friction, extract. This sim validates the robotics of that.

## Topology (6 DOF, mixed prismatic + revolute)

```
base_link  ── fixed to world (host carriage / wrist mount)
 └ j_feed    PRISMATIC +x  — insert the probe into the gap (0 → 300 mm)
    └ j_yaw    REVOLUTE +z  — aim left/right inside the gap
       └ j_pitch  REVOLUTE +y — dip the probe down toward the surface
          └ j_seg1  REVOLUTE +y — flexible segment 1 (continuum approximation)
             └ j_seg2  REVOLUTE +y — flexible segment 2 (continuum approximation)
                └ j_brush REVOLUTE +x — rotary cleaning-brush spin
```

The probe stacks along **+x**; revolute-y joints let the distal segments droop
onto and conform to the target surface. The brush head carries a capsule
**bristle cross** (±y and ±z bars); spinning `j_brush` sweeps those capsule
endpoints horizontally across the surface — the Coulomb-friction **scrub**.

## What is faithfully simulated vs. what is abstracted

| Real thing | Sim representation | Honest gap (deferred) |
|---|---|---|
| Mold surface (pan floor / duct wall / gap face) | the single contact ground plane at `z = ground_z` (`KABITORI_SURFACE_Z = −0.22`) | one plane only; no boxed-in duct walls (contact solver is ground-plane-only) |
| Slender flexible probe | prismatic feed + serial revolute segments | discrete joints, not a true continuum rod |
| Rotary brush | revolute spin + capsule bristle cross | bristles = capsule endpoints, not fibers |
| Scrubbing | Coulomb friction impulses at brush↔surface | mold itself is not an erodible material (no FEM/MPM solver in kami-genesis R1.1) |
| Pressing | solver normal impulse holding the brush on the plane | — |

**Validated**: reach into the gap, contact-force regulation on the target
surface, brush scrub shear, numerical stability (passivity at the contact).
**Not yet**: biofilm erosion, multi-wall duct collision, fluid/spray, self-collision.

## Run

Headless physics validation (the verifiable result — runs anywhere):

```bash
cd 40-engine/kami-engine
cargo test -p kami-app-giemon kabitori
#   kabitori_urdf_parses_mixed_topology      — 6 DOF, 1 prismatic + 5 revolute
#   kabitori_feed_inserts_probe_into_gap      — feed advances the carriage +x
#   kabitori_probe_reaches_and_contacts_surface — brush reaches + scrubs, no tunnelling
#   kabitori_contact_is_stable_once_settled   — no Baumgarte energy pumping
```

WASM render demo (`run_giemon_kabitori_sim_v1`, autonomous feed→dip→scrub):

```bash
# NOTE: build with the rustup toolchain's compiler (Homebrew rust on this host
# lacks the wasm32 std), e.g.:
RUSTC=~/.rustup/toolchains/stable-aarch64-apple-darwin/bin/rustc \
  ~/.rustup/toolchains/stable-aarch64-apple-darwin/bin/cargo \
  build -p kami-app-giemon --target wasm32-unknown-unknown
# then wasm-pack / bundle as with the other giemon entries; HTML calls
#   await init(); run_giemon_kabitori_sim_v1('canvas')
```

## Part ledger → SBOM → kotoba (product / manufacturer / procurement)

Each part is linked to a product name, manufacturer/company, MPN, purl, and a
**procurement type** (`cots` = buy off-the-shelf · `custom-fab` = commission /
fabricate), plus the sim `feature_id` it maps to. The ledger is integrated into
the **kotoba** EAVT store (Datomic-class) and is queryable via the kotoba API.

- **`parts.edn`** — SSoT, Datomic-style EDN ledger (`{:bom/meta … :bom/parts […]}`).
  `:part/sourcing :representative` flags these as R0 design selections, not a
  procurement-verified purchase list.
- **`sbom_gen.py`** — parses `parts.edn` → emits `kabitori.cdx.json` (CycloneDX
  1.5 SBOM) + `kotoba_ingest.json` (a `kg.ingest_batch` body). Run: `python3 sbom_gen.py`.
- **`kabitori.cdx.json`** — committed CycloneDX SBOM (per-part publisher/supplier/purl).

Load into kotoba and query (verified live, 2026-05-31; in-memory, no IPFS):

```bash
KOTOBA_IPFS=off kotoba serve &                          # in-memory EAVT
TOK=$(python3 -c 'import base64,json;b=lambda o:base64.urlsafe_b64encode(json.dumps(o,separators=(",",":")).encode()).rstrip(b"=").decode();print(f"{b({\"alg\":\"HS256\",\"typ\":\"JWT\"})}.{b({\"sub\":\"operator\",\"exp\":9999999999})}.sig")')
curl -s -XPOST localhost:8080/xrpc/com.etzhayyim.apps.kotobase.kg.ingest_batch \
  -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' --data @kotoba_ingest.json
# claims become kg/claim/part/* datoms; query with SPARQL:
kotoba --token "$TOK" sparql 'SELECT * WHERE { ?s <kg/claim/part/procurement> "cots" }'        # → 15
kotoba --token "$TOK" sparql 'SELECT * WHERE { ?s <kg/claim/part/manufacturer> ?m }'           # → 15 companies
kotoba --token "$TOK" sparql 'SELECT * WHERE { ?s <kg/claim/part/simFeature> "link_brush" }'   # CAD↔part join
kotoba --token "$TOK" sparql 'SELECT * WHERE { ?s <kg/claim/part/group> "C-extraction" . ?s <kg/claim/part/manufacturer> ?m }'
```

Verified result: 20 parts (15 cots / 5 custom-fab); manufacturers include
Raspberry Pi Ltd, Sony Semiconductor, TDK InvenSense, Texas Instruments, Maxon,
Makita, Camfil, … Note: the legacy SBOM app (`60-apps/etzhayyim-project-sbom`)
persists to RisingWave; this pilot uses **kotoba** per ADR-2605262130 (no-RisingWave).

## Source

- URDF: `giemon_kabitori.urdf` (this dir)
- Config + colliders + tests: `40-engine/kami-engine/kami-app-giemon/src/lib.rs`
  (`giemon_kabitori_config`, `kabitori_colliders`, `run_giemon_kabitori_sim_v1`)
- Engine: `40-engine/kami-engine/kami-genesis/` (`articulation3d.rs`, `contact.rs`)
