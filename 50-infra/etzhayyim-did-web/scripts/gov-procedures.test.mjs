// Tests for the compiled gov-procedures registry served by the apex Worker
// (ADR-2606021600 / 2606042330): public administrative procedures published
// FINELY BY ADMINISTRATIVE UNIT (grouped under the owning gov entity-actor
// handle). Pure, no network. Verifies counts, owner→handle grouping, the
// mirror/honesty invariants (all :representative / :unverified-seed), and that
// every owner handle resolves as a real gov entity-actor.
//
//   node --experimental-strip-types --test scripts/gov-procedures.test.mjs
import { test, before } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import esbuild from "esbuild";

const HERE = dirname(fileURLToPath(import.meta.url));
let GP, ENT;

before(async () => {
  const hash = createHash("sha1").update(HERE).digest("hex").slice(0, 8);
  const out = join(tmpdir(), `gov-procedures-${hash}.mjs`);
  const reg = join(HERE, "../src/registry");
  await esbuild.build({
    stdin: {
      contents:
        `export * as GP from ${JSON.stringify(join(reg, "gov-procedures.gen.ts"))};\n` +
        `export * as ENT from ${JSON.stringify(join(reg, "entity-actors.ts"))};`,
      resolveDir: reg,
      loader: "ts",
    },
    bundle: true,
    format: "esm",
    platform: "node",
    outfile: out,
  });
  const mod = await import(`${out}?t=${Date.now()}`);
  GP = mod.GP;
  ENT = mod.ENT;
});

test("registry is non-empty and counts are self-consistent", () => {
  assert.ok(GP.GOV_PROCEDURES_TOTAL > 0, "must have procedures");
  assert.equal(GP.GOV_PROCEDURE_LIST.length, GP.GOV_PROCEDURES_TOTAL);
  assert.equal(GP.GOV_PROCEDURES_BY_OWNER.size, GP.GOV_PROCEDURES_OWNER_COUNT);
  const distinctJuris = new Set(GP.GOV_PROCEDURE_LIST.map((p) => p.jurisdiction).filter(Boolean));
  assert.equal(distinctJuris.size, GP.GOV_PROCEDURES_JURISDICTION_COUNT);
});

test("by-owner grouping is consistent with the flat list", () => {
  let counted = 0;
  for (const [handle, procs] of GP.GOV_PROCEDURES_BY_OWNER) {
    counted += procs.length;
    for (const p of procs) {
      assert.equal(p.ownerHandle, handle, `${p.id} grouped under wrong handle`);
    }
  }
  assert.equal(counted, GP.GOV_PROCEDURES_TOTAL, "grouped count must equal total");
});

test("every owner handle is a gov entity-actor handle (no dangling/impersonation)", () => {
  for (const handle of GP.GOV_PROCEDURES_BY_OWNER.keys()) {
    assert.match(handle, /^gov-[a-z0-9-]*$|^gov$/, `${handle} not a gov handle`);
    assert.ok(
      ENT.isEntityHandle(handle),
      `owner handle '${handle}' does not resolve as a registered gov entity-actor`,
    );
  }
});

test("G5 honesty — every procedure is :representative / :unverified-seed", () => {
  for (const p of GP.GOV_PROCEDURE_LIST) {
    assert.equal(
      p.verificationStatus,
      "unverified-seed",
      `${p.id} must ship verification-status unverified-seed (G5; never authoritative coverage)`,
    );
    assert.equal(p.sourcing, "representative", `${p.id} must ship sourcing representative`);
  }
});

test("every procedure carries id, title, owner, jurisdiction and a https provenance", () => {
  for (const p of GP.GOV_PROCEDURE_LIST) {
    assert.ok(p.id && p.title && p.ownerUnit && p.ownerHandle, `${p.id}: missing core field`);
    assert.ok(p.jurisdiction, `${p.id}: missing jurisdiction`);
    if (p.provenance) {
      assert.ok(p.provenance.startsWith("https://"), `${p.id}: provenance must be https`);
    }
  }
});

test("toritsugi-ref present on projected rows (delivery↔structure link)", () => {
  // Most rows link back to the citizen-facing toritsugi procedure; at least the
  // overwhelming majority must (JP hand-authored + all auto-projected rows do).
  const withRef = GP.GOV_PROCEDURE_LIST.filter((p) => p.toritsugiRef).length;
  assert.ok(
    withRef >= GP.GOV_PROCEDURES_TOTAL * 0.9,
    `expected >=90% of procedures to carry a toritsugi-ref; got ${withRef}/${GP.GOV_PROCEDURES_TOTAL}`,
  );
});
