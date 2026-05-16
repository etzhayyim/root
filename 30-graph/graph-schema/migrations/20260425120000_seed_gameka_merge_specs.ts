import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Seed 3 merge-game specs into vertex_gameka_spec (ADR 2604250900 P2 smoke).
 *
 * These rows give the operator a deterministic input set for the
 * generateGame → playtestGame → publishGame chain *without* having to
 * run proposeGame's LangGraph deliberation first. They cover three
 * distinct sub-genres of "merge" — same-rank-tiles-fuse-into-rank+1 —
 * each pinned to a different kami-engine biome / camera / input combo
 * so the resulting kami-app-{slug} crates are visually distinguishable.
 *
 *   spec-merge-grid-2048   grid swipe (2048-style)            quarry biome
 *   spec-merge-drop-suika  physics drop (Suika-style)         tundra biome
 *   spec-merge-field-triple place-and-cluster (Triple Town)   plains biome
 *
 * Score is set to 0.85 so a downstream re-run of proposeGame in revise
 * mode treats them as healthy avoid-list entries; iteration=0 +
 * lineage_parent='' marks them as autonomous origins (same shape as
 * a real tickStudio-driven proposal).
 *
 * Idempotent — RW PK-upsert semantics make re-runs safe (same
 * vertex_id INSERT overwrites the row in place).
 */

interface MergeSeed {
  specId: string;
  brief: string;
  title: string;
  slug: string;
  genre: string;
  mechanic: Record<string, unknown>;
  scene: Record<string, unknown>;
  budgetUsd: number;
  rationale: string;
}

const SEEDS: MergeSeed[] = [
  // ─── Pattern 1: 2048-style grid swipe ─────────────────────────────
  {
    specId: "spec-merge-grid-2048",
    brief:
      "A relaxing quarry-themed 2048 swipe-merge with stone-slab tiles and Nintendo-pastel polish.",
    title: "Grid Merge — Quarry",
    slug: "grid-merge-quarry",
    genre: "puzzle",
    mechanic: {
      kind: "grid_2048",
      description:
        "4x4 grid puzzle. Swipe to slide all tiles in one direction; same-rank tiles touching merge to rank+1. New rank-1 tile spawns each turn. Lose when the grid is full and no merges remain. Reach rank 11 to win.",
      coreVerb: "swipe-merge",
      board: { kind: "grid", w: 4, h: 4 },
      inputModes: ["swipe", "arrow-keys"],
      progression: { tiers: 11, scaling: "exponential" },
      failState: "deadlock-on-full-grid",
      target: "reach-rank-11",
    },
    scene: {
      description:
        "Quarry biome cathedral interior. Tiles are carved stone slabs floating mid-air on Splatoon-pastel pedestals. Soft volumetric dust, distant rumble of falling rocks. Orbit camera pivots gently while the grid stays centered.",
      biomeHint: "quarry",
      cameraHint: "orbit-fixed",
      palette: "splatoon-pastel-neutral",
      fxBudget: "low",
      ambient: ["dust-motes", "distant-rumble"],
      audioPalette: {
        bgm: "ambient-quarry-low",
        sfx: ["click", "success", "coin", "tick", "select", "loaded"],
        loops: ["wind-soft"],
      },
      socialHooks: { onWin: "share-score", onMilestone: "share-rank" },
    },
    budgetUsd: 80,
    rationale:
      "Seed spec — classic 2048 mechanic on the kami quarry biome. Low fx, single board, cheap to render.",
  },

  // ─── Pattern 2: Suika-style physics drop ──────────────────────────
  {
    specId: "spec-merge-drop-suika",
    brief:
      "Suika-style physics merge in a tundra glass jar — drop snowballs, fuse them, create a glacier.",
    title: "Drop Merge — Tundra",
    slug: "drop-merge-tundra",
    genre: "puzzle",
    mechanic: {
      kind: "drop_suika",
      description:
        "Drop snowballs from a fixed top emitter into a glass container. Snowballs fall under gravity and bounce. Same-tier snowballs in contact merge into the next tier (volume sums, position averages). Lose if the stack overflows the top line. Goal: create the largest possible snowball without overflow.",
      coreVerb: "drop-and-fuse",
      physicsHint: "circle2d-aabb-walls",
      inputModes: ["pointer-x", "arrow-keys"],
      progression: { tiers: 11, scaling: "1.4x-radius-per-tier" },
      failState: "stack-overflow",
      target: "create-max-tier",
    },
    scene: {
      description:
        "Tundra biome. Glass jar suspended above a frozen lake; snowflakes drift past the camera. The jar is the only foreground element; tundra horizon stretches behind it. Static camera, slight parallax from background snowfall.",
      biomeHint: "tundra",
      cameraHint: "static-front",
      palette: "splatoon-pastel-cool",
      fxBudget: "medium",
      ambient: ["snowfall", "wind-howl-soft"],
      audioPalette: {
        bgm: "tundra-wind-soft",
        sfx: ["pop", "whoosh", "success", "loaded", "warning", "coin"],
        loops: ["snowfall"],
      },
      socialHooks: { onWin: "share-score", onMilestone: "share-tier" },
    },
    budgetUsd: 120,
    rationale:
      "Seed spec — Suika-game mechanic, Tundra biome scaffolding. Medium fx for the snowfall + jar refraction; physics2d only.",
  },

  // ─── Pattern 3: Triple Town-style place-and-cluster ──────────────
  {
    specId: "spec-merge-field-triple",
    brief:
      "Triple Town-style place-and-merge on a plains board — grass to castle, golden-hour vibes.",
    title: "Field Merge — Plains",
    slug: "field-merge-plains",
    genre: "puzzle",
    mechanic: {
      kind: "field_triple",
      description:
        "5x5 plains board. Each turn a previewed item is placed on an empty tile chosen by pointer click. When 3+ same-rank items touch in any orthogonal cluster, they auto-merge into a single rank+1 item at the placement spot. Ranks: grass → bush → tree → hut → house → castle. Lose when the board fills and no placement triggers a merge.",
      coreVerb: "place-and-cluster",
      board: { kind: "grid", w: 5, h: 5 },
      inputModes: ["pointer-click"],
      progression: { tiers: 6, scaling: "narrative-rank" },
      failState: "deadlock-on-full-board",
      target: "build-castle",
    },
    scene: {
      description:
        "Plains biome with rolling hills. The 5x5 board floats over a meadow; clouds pass overhead. Day-night cycle is paused at golden hour for warm UI contrast. Orbit camera angles 30 degrees from horizontal, slow auto-rotation.",
      biomeHint: "plains",
      cameraHint: "orbit-30deg-slow",
      palette: "splatoon-pastel-warm",
      fxBudget: "low",
      ambient: ["cloud-shadows", "distant-bird"],
      audioPalette: {
        bgm: "plains-pastoral",
        sfx: ["click", "coin", "success", "loaded", "select", "navigate"],
        loops: ["bird-chirps"],
      },
      socialHooks: { onWin: "share-score", onMilestone: "share-castle" },
    },
    budgetUsd: 100,
    rationale:
      "Seed spec — Triple Town cluster mechanic on the kami plains biome. Low fx, golden-hour palette, satisfies kami-pipelines sky+terrain+water defaults.",
  },
];

const CREATED_AT = "2026-04-25T12:00:00Z";

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of SEEDS) {
    await sql`
      INSERT INTO vertex_gameka_spec (
        vertex_id, owner_did, rkey, repo,
        spec_id, brief, title, slug, genre,
        mechanic_json, scene_json,
        budget_usd, score, rationale,
        iteration, lineage_parent, model_id,
        created_at
      ) VALUES (
        ${`at://did:web:gameka.gftd.ai/ai.gftd.apps.gameka.gameSpec/${s.specId}`},
        ${"did:web:gameka.gftd.ai"},
        ${s.specId},
        ${"did:web:gameka.gftd.ai"},
        ${s.specId},
        ${s.brief},
        ${s.title},
        ${s.slug},
        ${s.genre},
        ${JSON.stringify(s.mechanic)},
        ${JSON.stringify(s.scene)},
        ${s.budgetUsd},
        ${0.85},
        ${s.rationale},
        ${0},
        ${""},
        ${"seed"},
        ${CREATED_AT}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of SEEDS) {
    await sql`
      DELETE FROM vertex_gameka_spec
      WHERE spec_id = ${s.specId}
    `.execute(db);
  }
}
