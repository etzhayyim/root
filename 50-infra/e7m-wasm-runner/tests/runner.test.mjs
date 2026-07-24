// Tests for the T2 mesh runner (ADR-2606015200). Runs the committed kanae raw
// core actor end-to-end (resolve-from-file → run → assert), and checks the
// core-vs-component detector. The component (jco) path is exercised against the
// watatsuna componentize-py build (gitignored; rebuild via its build.sh) — see
// ADR-2606014600 where it was verified to run via jco.
//
//   node --experimental-strip-types --test tests/runner.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { resolveAndRun, runBytes, isComponent } from "../runner.mjs";

const DIR = dirname(fileURLToPath(import.meta.url));
const KANAE = join(DIR, "../../../orgs/etzhayyim/com-etzhayyim-kanae/wasm/loader/kanae-core.wasm");

test("runs the kanae core actor → top recipient = Prefectures", async () => {
  const out = await resolveAndRun({ file: KANAE });
  assert.equal(out.actor, "kanae");
  assert.equal(out.top[0].node, "Prefectures");
  assert.equal(out.adjudication, "none");
});

test("isComponent distinguishes core module from component", () => {
  const kanae = new Uint8Array(readFileSync(KANAE));
  assert.equal(isComponent(kanae), false); // core: \0asm 01 00 00 00
  // synthetic component preamble: \0asm 0d 00 01 00
  const comp = Uint8Array.from([0x00, 0x61, 0x73, 0x6d, 0x0d, 0x00, 0x01, 0x00]);
  assert.equal(isComponent(comp), true);
});

test("runBytes runs raw core bytes directly", async () => {
  const out = await runBytes(new Uint8Array(readFileSync(KANAE)));
  assert.equal(out.actor, "kanae");
});
