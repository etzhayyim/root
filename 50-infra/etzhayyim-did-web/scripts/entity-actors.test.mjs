// Tests for entity-as-actor mirror registry (ADR-2606042330). Pure, no network.
// Verifies handle membership, charter invariants on the mirror records
// (keyless / person-excluded / mirror-disclaimer), searchActors short-circuit
// logic, and namespace summary counts.
//
//   node --experimental-strip-types --test scripts/entity-actors.test.mjs
// entity-actors.ts + actor-profiles.ts have internal extensionless imports, so
// they are bundled with esbuild before import (same pattern as diddoc-cid.test).
import { test, before } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import esbuild from "esbuild";

const HERE = dirname(fileURLToPath(import.meta.url));
let isEntityHandle,
  isEntityHandleShape,
  entityActorRecord,
  searchEntityActors,
  entityNamespaceSummary,
  ENTITY_TOTAL_COUNT,
  ENTITY_NAMESPACES,
  toDidDoc,
  toGetProfileView;

before(async () => {
  const hash = createHash("sha1").update(HERE).digest("hex").slice(0, 8);
  const out = join(tmpdir(), `entity-actors-${hash}.mjs`);
  const reg = join(HERE, "../src/registry");
  await esbuild.build({
    stdin: {
      contents:
        `export * from ${JSON.stringify(join(reg, "entity-actors.ts"))};\n` +
        `export { toDidDoc, toGetProfileView } from ${JSON.stringify(join(reg, "actor-profiles.ts"))};`,
      resolveDir: reg,
      loader: "ts",
    },
    bundle: true,
    format: "esm",
    platform: "node",
    outfile: out,
  });
  const mod = await import(`${out}?t=${Date.now()}`);
  ({
    isEntityHandle,
    isEntityHandleShape,
    entityActorRecord,
    searchEntityActors,
    entityNamespaceSummary,
    ENTITY_TOTAL_COUNT,
    ENTITY_NAMESPACES,
    toDidDoc,
    toGetProfileView,
  } = mod);
});

test("known entity handles resolve; unknown shapes do not", () => {
  assert.equal(isEntityHandle("corp-tw-tsmc"), true, "TSMC is registered");
  assert.equal(isEntityHandle("craft-vessel-imo9811000"), true, "Ever Given");
  assert.equal(isEntityHandle("cable-jupiter"), true);
  assert.equal(isEntityHandle("corp-zz-does-not-exist"), false);
  assert.equal(isEntityHandle("tsumugi"), false, "named actor, not entity ns");
  assert.equal(isEntityHandle("c70000000"), false, "unispsc shape, not entity");
});

test("entity handle SHAPE gate distinguishes member handles", () => {
  assert.equal(isEntityHandleShape("gov-anything-here"), true);
  assert.equal(isEntityHandleShape("corp-zz-unregistered"), true, "shape only");
  assert.equal(isEntityHandleShape("jun-kawasaki"), false, "no known ns prefix");
  assert.equal(isEntityHandleShape("watari"), false);
});

test("mirror record is charter-clean by construction", () => {
  const rec = entityActorRecord("corp-tw-tsmc");
  assert.ok(rec, "record exists");
  // G5 no-server-key
  assert.deepEqual(rec.vm, [], "verificationMethod empty (no server key)");
  // G3 person-excluded
  assert.notEqual(rec.performerType, "person");
  assert.ok(["organization", "system"].includes(rec.performerType));
  // G1 mirror disclaimer must open the description
  assert.match(rec.description, /^Observational mirror/);
  assert.match(rec.description, /NOT .* itself/);
  assert.match(rec.description, /never a target-list/);
  assert.equal(rec.kind, "entity-mirror");
  assert.equal(rec.did, "did:web:etzhayyim.com:actor:corp-tw-tsmc");
});

test("craft mirror performerType is system, never person (watari G4)", () => {
  const rec = entityActorRecord("craft-vessel-imo9811000");
  assert.equal(rec.performerType, "system");
  assert.match(rec.displayNameEn, /Ever Given/);
});

test("toDidDoc over a mirror record stays keyless", () => {
  const rec = entityActorRecord("cable-jupiter");
  const doc = toDidDoc(rec, {});
  assert.deepEqual(doc.verificationMethod, []);
  assert.equal(doc.id, "did:web:etzhayyim.com:actor:cable-jupiter");
  // service points at the owning KG actor, not a per-entity server
  assert.ok(
    doc.service.some(
      (s) => s.type === "EtzhayyimMirrorSource" && /actor\/watatsuna/.test(s.serviceEndpoint),
    ),
  );
});

test("searchActors short-circuit matches by name and by handle", () => {
  const byName = searchEntityActors("tsmc", 10);
  assert.ok(byName.some((r) => r.handle === "corp-tw-tsmc"));
  const byHandleHere = searchEntityActors("ever given", 10);
  assert.ok(byHandleHere.some((r) => r.handle === "craft-vessel-imo9811000"));
  // respects limit
  assert.ok(searchEntityActors("", 5).length <= 5);
  // getProfile view of a result is well-formed + mirror-labelled
  const view = toGetProfileView(byName[0]);
  assert.match(view.description, /^Observational mirror/);
  assert.equal(view._etzhayyim.kind, "entity-mirror");
});

test("namespace summary counts equal the sum of registries", () => {
  const sum = entityNamespaceSummary();
  assert.equal(sum.length, ENTITY_NAMESPACES.length);
  const total = sum.reduce((a, n) => a + n.count, 0);
  assert.equal(total, ENTITY_TOTAL_COUNT);
  assert.ok(ENTITY_TOTAL_COUNT > 8000, `expected society scale, got ${ENTITY_TOTAL_COUNT}`);
  // gov is the largest namespace
  const gov = sum.find((n) => n.ns === "gov");
  assert.ok(gov.count > 7000, `gov ${gov.count}`);
});
