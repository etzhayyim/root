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

test("mirror is a registered ATProto actor (can post AS the mirror, keyless) — ADR-2606232100", () => {
  const rec = entityActorRecord("corp-tw-tsmc");
  const pds = rec.service.find((s) => s.type === "AtprotoPersonalDataServer");
  assert.ok(pds, "mirror must carry an #atproto_pds so it can post its observations");
  assert.equal(pds.serviceEndpoint, "https://pds.etzhayyim.com");
  assert.equal(pds.id, "did:web:etzhayyim.com:actor:corp-tw-tsmc#atproto_pds");
  // still keyless (no-server-key) and still a non-impersonating mirror source.
  assert.deepEqual(rec.vm, [], "mirror stays keyless even though it can post");
  assert.ok(
    rec.service.some((s) => s.type === "EtzhayyimMirrorSource"),
    "mirror-source service preserved",
  );
  assert.match(rec.description, /^Observational mirror/);
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
  assert.ok(byName.records.some((r) => r.handle === "corp-tw-tsmc"));
  const byHandleHere = searchEntityActors("ever given", 10);
  assert.ok(byHandleHere.records.some((r) => r.handle === "craft-vessel-imo9811000"));
  // respects limit
  assert.ok(searchEntityActors("", 5).records.length <= 5);
  // getProfile view of a result is well-formed + mirror-labelled
  const view = toGetProfileView(byName.records[0]);
  assert.match(view.description, /^Observational mirror/);
  assert.equal(view._etzhayyim.kind, "entity-mirror");
});

test("offset cursor pages through the full corpus without overlap or loss", () => {
  // browse (no query): total === ENTITY_TOTAL_COUNT
  const p0 = searchEntityActors("", 50, 0);
  assert.equal(p0.total, ENTITY_TOTAL_COUNT);
  assert.equal(p0.records.length, 50);
  assert.equal(p0.nextOffset, 50);
  const p1 = searchEntityActors("", 50, p0.nextOffset);
  assert.equal(p1.records.length, 50);
  // no overlap between consecutive pages
  const h0 = new Set(p0.records.map((r) => r.handle));
  assert.ok(p1.records.every((r) => !h0.has(r.handle)), "pages disjoint");
  // last page: nextOffset null, records < limit
  const last = searchEntityActors("", 50, ENTITY_TOTAL_COUNT - 10);
  assert.equal(last.records.length, 10);
  assert.equal(last.nextOffset, null);
});

test("query total is the full match count (not the page size)", () => {
  const p = searchEntityActors("tokyo", 3, 0);
  assert.ok(p.total >= p.records.length, "total counts all matches");
  assert.ok(p.records.length <= 3, "page respects limit");
  // walking the cursor collects exactly `total` records
  let seen = 0;
  let off = 0;
  for (let guard = 0; guard < 1000; guard++) {
    const pg = searchEntityActors("tokyo", 3, off);
    seen += pg.records.length;
    if (pg.nextOffset === null) break;
    off = pg.nextOffset;
  }
  assert.equal(seen, p.total, "cursor walk yields every match once");
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
