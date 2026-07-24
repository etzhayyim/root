// Tests for ATProto actor registration (ADR-2606232100).
//
// Every resolvable etzhayyim DID — the root entity AND every per-actor /
// sub-DID — must advertise an `#atproto_pds` service so it is a *registered*
// ATProto repo identity (relays/AppView index it; it can host
// app.bsky.feed.post records). Without it, only externally-hosted actors
// (e.g. the high-volume shinshi poster) appear in the feed.
//
// worker.ts pulls in the generated cljs artifact (`../cljs-out/worker_core.js`)
// which is not built in CI test runs, so we stub that single import (it is the
// fetch-delegation seam, unrelated to buildPerActorDidDoc) and bundle the rest.
//
//   node --experimental-strip-types --test scripts/atproto-registration.test.mjs
import { test, before } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import esbuild from "esbuild";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..");
const PDS = "https://pds.etzhayyim.com";

let buildPerActorDidDoc;

before(async () => {
  const hash = createHash("sha1").update(HERE).digest("hex").slice(0, 8);
  const out = join(tmpdir(), `atproto-reg-${hash}.mjs`);
  const stubCljs = {
    name: "stub-cljs",
    setup(b) {
      b.onResolve({ filter: /cljs-out/ }, (a) => ({ path: a.path, namespace: "stub" }));
      b.onLoad({ filter: /.*/, namespace: "stub" }, () => ({
        contents: "export const handle=()=>{};export default {};",
        loader: "js",
      }));
    },
  };
  await esbuild.build({
    stdin: {
      contents: `export { buildPerActorDidDoc } from ${JSON.stringify(join(ROOT, "src/worker.ts"))};`,
      resolveDir: ROOT,
      loader: "ts",
    },
    bundle: true,
    format: "esm",
    platform: "node",
    outfile: out,
    plugins: [stubCljs],
  });
  ({ buildPerActorDidDoc } = await import(`${out}?t=${Date.now()}`));
});

function pdsOf(doc) {
  return (doc.service || []).find((s) => s.type === "AtprotoPersonalDataServer");
}

test("root entity did.json advertises an atproto PDS service", () => {
  const root = JSON.parse(readFileSync(join(ROOT, "did.json"), "utf8"));
  const pds = (root.service || []).find((s) => s.type === "AtprotoPersonalDataServer");
  assert.ok(pds, "root did.json must carry an #atproto_pds service");
  assert.equal(pds.serviceEndpoint, PDS);
  assert.equal(pds.id, "did:web:etzhayyim.com#atproto_pds");
});

test("agent sub-DIDs (namespaced/unispsc) are registered ATProto actors", () => {
  // `c` + 6-12 digits is the unispsc AGENT handle shape (isNamespacedHandle).
  for (const h of ["c12345678", "c987654"]) {
    const doc = buildPerActorDidDoc(h, {});
    const pds = pdsOf(doc);
    assert.ok(pds, `${h}: agent did.json must carry an #atproto_pds service`);
    assert.equal(pds.serviceEndpoint, PDS);
    assert.equal(pds.id, `did:web:etzhayyim.com:actor:${h}#atproto_pds`);
  }
});

test("agent-centric: free-form HUMAN handles (council/member) get NO PDS", () => {
  // Free-form handles are council seats / human members (isKnownHandle Phase α).
  // etzhayyim is agent-only for now — humans are not posting actors, so their
  // DID doc carries the authz resolver but no #atproto_pds.
  for (const h of ["councilseat2", "somemember", "free-form-handle"]) {
    const doc = buildPerActorDidDoc(h, {});
    assert.equal(pdsOf(doc), undefined, `${h}: human handle must NOT carry an #atproto_pds service`);
    const authz = (doc.service || []).find((s) => s.type === "EtzhayyimAuthzResolver");
    assert.ok(authz, `${h}: human handle still resolves (authz service present)`);
  }
});

test("hand-authored infra actors keep their own declared PDS (override preserved)", () => {
  // pinner is an INFRA_ACTOR that already declares its own #atproto_pds — the
  // generator must use the actor's own service[] override, not the default.
  const doc = buildPerActorDidDoc("pinner", {});
  const pds = pdsOf(doc);
  assert.ok(pds, "infra actor must still carry an #atproto_pds service");
  assert.equal(pds.serviceEndpoint, PDS);
});

test("registration declares WHERE the repo lives, not a server-held key (no-server-key)", () => {
  // The default per-actor doc must NOT mint a signing key — writes stay
  // member-signed / self-did:key + CACAO leash (ADR-2606072802).
  const doc = buildPerActorDidDoc("somemember", {});
  assert.deepEqual(doc.verificationMethod, [], "default per-actor vm must stay empty (on-chain-mirrored)");
});
