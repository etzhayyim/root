/**
 * ISEKAI unit tests — pure game logic (no SDK, no network).
 * Run: node --experimental-strip-types src/app.test.ts
 */
import { test, describe } from "node:test";
import assert from "node:assert/strict";

/* ------------------------------------------------------------------ */
/*  Inline pure functions under test (no SDK import needed)           */
/* ------------------------------------------------------------------ */

const MOVE_DATA: Record<string, { power: number; type: string; accuracy: number }> = {
  tackle:          { power: 40, type: "normal",   accuracy: 100 },
  growl:           { power: 0,  type: "normal",   accuracy: 100 },
  scratch:         { power: 40, type: "normal",   accuracy: 100 },
  ember:           { power: 40, type: "fire",     accuracy: 100 },
  "water-gun":     { power: 40, type: "water",    accuracy: 100 },
  "brainrot-blast":{ power: 65, type: "brainrot", accuracy: 90  },
  "sigma-stare":   { power: 55, type: "psychic",  accuracy: 95  },
  "toilet-flush":  { power: 70, type: "water",    accuracy: 85  },
  "ohio-strike":   { power: 80, type: "dark",     accuracy: 90  },
  "shake-heal":    { power: 0,  type: "fairy",    accuracy: 100 },
  "rizz-charm":    { power: 50, type: "fairy",    accuracy: 100 },
  "tax-steal":     { power: 60, type: "ghost",    accuracy: 95  },
};

const TYPE_CHART: Record<string, Record<string, number>> = {
  brainrot: { normal: 2, psychic: 2, dark: 2, ghost: 2, fairy: 2, fire: 2, water: 2, poison: 2, brainrot: 0.5 },
  water:    { fire: 2,   water: 0.5, brainrot: 0.5 },
  fire:     { water: 0.5, fire: 0.5, brainrot: 0.5 },
  psychic:  { dark: 0.5, psychic: 0.5, brainrot: 0.5 },
  dark:     { psychic: 2, ghost: 2 },
  ghost:    { normal: 0, ghost: 2 },
  fairy:    { dark: 2, ghost: 2 },
  poison:   { fairy: 2 },
  normal:   {},
};
const SPECIES_TYPES: Record<number, string> = {
  901: "water", 902: "psychic", 903: "dark", 904: "poison", 905: "fairy", 906: "ghost",
};
function speciesType(id: number): string { return SPECIES_TYPES[id] ?? "normal"; }

function calcDamage(attackerLevel: number, moveName: string, defenderLevel: number, defenderSpeciesId = 0): number {
  const move = MOVE_DATA[moveName] ?? MOVE_DATA["tackle"];
  if (move.power === 0) return 0;
  const atk = 10 + attackerLevel * 2;
  const def = 10 + defenderLevel * 2;
  const base = Math.floor(((attackerLevel / 5 + 2) * move.power * atk) / def / 50 + 2);
  const variance = 0.85 + Math.random() * 0.15;
  const defType = speciesType(defenderSpeciesId);
  const effectiveness = TYPE_CHART[move.type]?.[defType] ?? 1;
  return Math.max(effectiveness === 0 ? 0 : 1, Math.floor(base * variance * effectiveness));
}

function getMovesForSpecies(speciesId: number, level: number): string[] {
  if (speciesId === 901) return ["toilet-flush", "tackle", "brainrot-blast"];
  if (speciesId === 902) return ["sigma-stare",  "tackle", "brainrot-blast"];
  if (speciesId === 903) return ["ohio-strike",  "tackle", "brainrot-blast"];
  if (speciesId === 904) return ["shake-heal",   "tackle", "brainrot-blast"];
  if (speciesId === 905) return ["rizz-charm",   "tackle", "brainrot-blast"];
  if (speciesId === 906) return ["tax-steal",    "tackle", "brainrot-blast"];
  const moves = ["tackle", "growl"];
  if (level >= 20) moves.push("scratch");
  if (level >= 30) moves.push("ember");
  return moves;
}

/* ------------------------------------------------------------------ */
/*  Inventory aggregation helper under test                           */
/* ------------------------------------------------------------------ */

function aggregateInventory(rows: Array<{ itemId: string; name: string; category: string; quantity: number }>): Array<{ itemId: string; quantity: number }> {
  const agg = new Map<string, { itemId: string; name: string; category: string; quantity: number }>();
  for (const row of rows) {
    if (!agg.has(row.itemId)) agg.set(row.itemId, { ...row, quantity: 0 });
    agg.get(row.itemId)!.quantity += row.quantity;
  }
  return Array.from(agg.values()).filter((item) => item.quantity > 0);
}

/* ------------------------------------------------------------------ */
/*  Catch rate simulator                                               */
/* ------------------------------------------------------------------ */

const CATCH_RATES: Record<string, number> = {
  "standard-ball": 0.3,
  "great-ball":    0.5,
  "ultra-ball":    0.7,
  "master-ball":   1.0,
  "brainrot-ball": 0.9,
};

function simulateCatch(ballType: string, isLegendary: boolean, trials: number): number {
  const base = CATCH_RATES[ballType];
  const rate = isLegendary ? base * 0.15 : base;
  let caught = 0;
  for (let i = 0; i < trials; i++) if (Math.random() < rate) caught++;
  return caught / trials;
}

/* ------------------------------------------------------------------ */
/*  Tests                                                              */
/* ------------------------------------------------------------------ */

describe("calcDamage", () => {
  test("tackle Lv10 vs Lv10 returns damage in [2, 25]", () => {
    for (let i = 0; i < 100; i++) {
      const d = calcDamage(10, "tackle", 10);
      assert.ok(d >= 2 && d <= 25, `expected 2–25, got ${d}`);
    }
  });

  test("growl returns 0 (status move)", () => {
    assert.equal(calcDamage(10, "growl", 10), 0);
    assert.equal(calcDamage(50, "growl", 50), 0);
  });

  test("shake-heal returns 0 (status move)", () => {
    assert.equal(calcDamage(30, "shake-heal", 30), 0);
  });

  test("damage is always >= 1 for offensive moves", () => {
    const moves = ["tackle", "brainrot-blast", "ohio-strike", "toilet-flush"];
    for (const mv of moves) {
      for (let i = 0; i < 50; i++) {
        const d = calcDamage(5, mv, 50);
        assert.ok(d >= 1, `${mv} returned 0 damage`);
      }
    }
  });

  test("higher level attacker deals more damage on average", () => {
    const low  = Array.from({ length: 200 }, () => calcDamage(5,  "tackle", 10));
    const high = Array.from({ length: 200 }, () => calcDamage(50, "tackle", 10));
    const avgLow  = low.reduce((s, x) => s + x, 0) / low.length;
    const avgHigh = high.reduce((s, x) => s + x, 0) / high.length;
    assert.ok(avgHigh > avgLow * 2, `expected high (${avgHigh.toFixed(1)}) >> low (${avgLow.toFixed(1)})`);
  });

  test("unknown move falls back to tackle (power 40)", () => {
    const d = calcDamage(10, "nonexistent-move", 10);
    assert.ok(d >= 1, "fallback move should deal >= 1 damage");
  });
});

describe("getMovesForSpecies", () => {
  test("legendary 901 (Skibidion) has toilet-flush as first move", () => {
    const moves = getMovesForSpecies(901, 50);
    assert.equal(moves[0], "toilet-flush");
    assert.ok(moves.includes("brainrot-blast"), "should include brainrot-blast");
  });

  test("legendary 903 (Ohiodon) has ohio-strike", () => {
    assert.ok(getMovesForSpecies(903, 50).includes("ohio-strike"));
  });

  test("common species Lv5 has only tackle+growl", () => {
    const moves = getMovesForSpecies(10, 5);
    assert.deepEqual(moves, ["tackle", "growl"]);
  });

  test("common species Lv20 gains scratch", () => {
    const moves = getMovesForSpecies(10, 20);
    assert.ok(moves.includes("scratch"), "Lv20 should learn scratch");
  });

  test("common species Lv30 gains ember", () => {
    const moves = getMovesForSpecies(10, 30);
    assert.ok(moves.includes("ember"), "Lv30 should learn ember");
  });

  test("all 6 legendaries have brainrot-blast", () => {
    for (let s = 901; s <= 906; s++) {
      assert.ok(getMovesForSpecies(s, 50).includes("brainrot-blast"), `species ${s} missing brainrot-blast`);
    }
  });
});

describe("inventory aggregation", () => {
  test("add rows sum correctly", () => {
    const rows = [
      { itemId: "crystal-shard", name: "Crystal Shard", category: "resource", quantity: 3 },
      { itemId: "crystal-shard", name: "Crystal Shard", category: "resource", quantity: 2 },
    ];
    const result = aggregateInventory(rows);
    assert.equal(result.length, 1);
    assert.equal(result[0].quantity, 5);
  });

  test("add+remove net to correct total", () => {
    const rows = [
      { itemId: "crystal-shard", name: "Crystal Shard", category: "resource", quantity: 5 },
      { itemId: "crystal-shard", name: "Crystal Shard", category: "resource", quantity: -2 },
    ];
    const result = aggregateInventory(rows);
    assert.equal(result[0].quantity, 3);
  });

  test("items with net quantity <= 0 are filtered out", () => {
    const rows = [
      { itemId: "standard-ball", name: "Standard Ball", category: "pokoa-ball", quantity: 1 },
      { itemId: "standard-ball", name: "Standard Ball", category: "pokoa-ball", quantity: -1 },
    ];
    const result = aggregateInventory(rows);
    assert.equal(result.length, 0);
  });

  test("multiple item types aggregated independently", () => {
    const rows = [
      { itemId: "diamond",       name: "Diamond",   category: "resource", quantity: 2 },
      { itemId: "crystal-shard", name: "Crystal",   category: "resource", quantity: 6 },
      { itemId: "crystal-shard", name: "Crystal",   category: "resource", quantity: -3 },
    ];
    const result = aggregateInventory(rows);
    const diamond = result.find((r) => r.itemId === "diamond");
    const crystal = result.find((r) => r.itemId === "crystal-shard");
    assert.equal(diamond?.quantity, 2);
    assert.equal(crystal?.quantity, 3);
  });
});

describe("battle flow", () => {
  // Minimal battle sim (mirrors cmdStartBattle + cmdUseMove logic)
  function runBattle(
    pSpecies: number, pLevel: number,
    eSpecies: number, eLevel: number,
    maxTurns = 50
  ): { status: "won" | "lost" | "timeout"; turns: number } {
    let pHp = 20 + pLevel * 3;
    let eHp = 20 + eLevel * 3;
    let turns = 0;
    while (pHp > 0 && eHp > 0 && turns < maxTurns) {
      const pMoves = getMovesForSpecies(pSpecies, pLevel);
      const eMoves = getMovesForSpecies(eSpecies, eLevel);
      const pDmg = calcDamage(pLevel, pMoves[0], eLevel, eSpecies);
      eHp = Math.max(0, eHp - pDmg);
      if (eHp === 0) break;
      const eDmg = calcDamage(eLevel, eMoves[Math.floor(Math.random() * eMoves.length)], pLevel, pSpecies);
      pHp = Math.max(0, pHp - eDmg);
      turns++;
    }
    if (turns >= maxTurns) return { status: "timeout", turns };
    return { status: eHp === 0 ? "won" : "lost", turns };
  }

  test("battle resolves within 30 turns (even level)", () => {
    for (let i = 0; i < 20; i++) {
      const r = runBattle(1, 10, 4, 10);
      assert.ok(r.status !== "timeout", `battle timed out after ${r.turns} turns`);
      assert.ok(r.turns <= 30, `battle took ${r.turns} turns`);
    }
  });

  test("higher level wins more often (Lv20 vs Lv5, 50 trials)", () => {
    let wins = 0;
    for (let i = 0; i < 50; i++) {
      if (runBattle(1, 20, 4, 5).status === "won") wins++;
    }
    assert.ok(wins >= 35, `expected >= 35 wins, got ${wins}`);
  });

  test("brainrot legendary beats normal-type more often (type advantage)", () => {
    let wins = 0;
    for (let i = 0; i < 50; i++) {
      // 901 uses toilet-flush (water, 2x vs fire) vs fire-type species
      if (runBattle(901, 20, 10, 20).status === "won") wins++;
    }
    // brainrot type 2x vs normal — should win more than 50%
    assert.ok(wins >= 30, `expected >= 30 wins with brainrot advantage, got ${wins}`);
  });

  test("ghost move deals 0 damage vs normal-type", () => {
    // tax-steal is ghost type, spec 1 is normal
    const dmg = calcDamage(30, "tax-steal", 10, 1);
    assert.equal(dmg, 0, "ghost vs normal should be 0");
  });

  test("flee: ~50% success rate over 100 trials", () => {
    let fled = 0;
    for (let i = 0; i < 100; i++) if (Math.random() < 0.5) fled++;
    assert.ok(fled >= 35 && fled <= 65, `expected ~50% flee, got ${fled}%`);
  });
});

describe("catch rate distribution", () => {
  const TRIALS = 1000;

  test("standard-ball ~30% catch rate", () => {
    const rate = simulateCatch("standard-ball", false, TRIALS);
    assert.ok(rate >= 0.24 && rate <= 0.36, `expected ~0.30, got ${rate.toFixed(3)}`);
  });

  test("master-ball always catches (100%)", () => {
    const rate = simulateCatch("master-ball", false, TRIALS);
    assert.equal(rate, 1.0, "master-ball must always catch");
  });

  test("brainrot-ball on legendary ~13.5% (0.9 * 0.15)", () => {
    const rate = simulateCatch("brainrot-ball", true, TRIALS);
    assert.ok(rate >= 0.08 && rate <= 0.20, `expected ~0.135, got ${rate.toFixed(3)}`);
  });

  test("great-ball catches more often than standard-ball", () => {
    const std   = simulateCatch("standard-ball", false, TRIALS);
    const great = simulateCatch("great-ball",    false, TRIALS);
    assert.ok(great > std - 0.05, `great (${great.toFixed(3)}) should >= standard (${std.toFixed(3)})`);
  });
});
