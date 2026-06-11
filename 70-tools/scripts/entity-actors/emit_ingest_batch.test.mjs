// Tests for the kotoba count-MV ingestion + maintenance reference
// (ADR-2606042330 D4 / actor-count-mv.kotoba.edn). Pure, no kotoba server.
//
//   node --experimental-strip-types --test 70-tools/scripts/entity-actors/emit_ingest_batch.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { build, maintainCount, NS } from "./emit_ingest_batch.mjs";

test("ingest batch materializes one :actor/* datom per mirror, counts match", () => {
  const { entities, counts, total } = build();
  assert.equal(entities.length, total, "one datom per mirror");
  assert.equal(
    Object.values(counts).reduce((a, n) => a + n, 0),
    total,
    "per-namespace counts sum to total",
  );
  assert.ok(total > 8000, `society scale, got ${total}`);
  assert.ok(counts.gov > 7000, `gov ${counts.gov}`);
});

test("every mirror datom is charter-clean (G1 isMirror, G3 never person)", () => {
  const { entities } = build();
  for (const e of entities) {
    const claim = (p) => e.claims.find((c) => c.pred === p)?.value;
    assert.equal(claim("actor/isMirror"), "true", "G1 isMirror");
    assert.ok(
      ["organization", "system"].includes(claim("actor/performerType")),
      "G3 performerType never person",
    );
    assert.ok(NS[claim("actor/namespace")], "namespace is a known entity namespace");
  }
});

test("MV maintain: incremental count == GROUP BY recount (assert stream)", () => {
  const { entities, counts } = build();
  // simulate MvRegistry::maintain over the assert stream
  const deltas = entities.map((e) => ({
    ns: e.claims.find((c) => c.pred === "actor/namespace").value,
    op: +1,
  }));
  const maintained = maintainCount(deltas);
  assert.deepEqual(maintained, counts, "incremental tally == GROUP BY count");
});

test("MV maintain: assert then retract of same datom nets zero (mv.rs semantics)", () => {
  const maintained = maintainCount([
    { ns: "gov", op: +1 },
    { ns: "gov", op: +1 },
    { ns: "gov", op: -1 }, // retract one
    { ns: "corp", op: +1 },
  ]);
  assert.equal(maintained.gov, 1, "two asserts minus one retract = 1");
  assert.equal(maintained.corp, 1);
});
