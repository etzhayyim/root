#!/usr/bin/env node
/**
 * Regression suite for transparency-floor-and-gate.mjs (ADR-2605310100 §4 + §5).
 *
 * Run: node --test 70-tools/scripts/lint/transparency-floor-and-gate.test.mjs
 *
 * Checks A + B read the transparency Lexicon JSON at canonical RELATIVE
 * paths via process.cwd(); these tests spawn the script with `cwd` pointed
 * at a temp tree holding either a clean or a poisoned fixture. Check C is
 * exercised by passing a temp code file as an arg. Pins the defining
 * guarantees so they cannot silently regress:
 *   - §5: a ratificationStatus const other than "proposed-unratified", OR a
 *     missing one, MUST fail; and code that flips it without a
 *     councilRatificationCid MUST fail.
 *   - §4: secretsRedacted/ingressConsentBasis/failClosed floor anchors MUST fail
 *     when removed or changed.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPT = resolve(
  dirname(fileURLToPath(import.meta.url)),
  "transparency-floor-and-gate.mjs",
);
const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const LEX_REL = "00-contracts/lexicons/com/etzhayyim/transparency";

function runIn(cwd, args = []) {
  const r = spawnSync("node", [SCRIPT, ...args], { cwd, encoding: "utf8" });
  return { code: r.status, out: (r.stdout || "") + (r.stderr || "") };
}

const PROPOSED = "proposed-unratified";

function lex(id, extraProps = {}) {
  return {
    lexicon: 1,
    id,
    defs: {
      main: {
        type: "record",
        key: "tid",
        record: {
          type: "object",
          properties: {
            ratificationStatus: { type: "string", const: PROPOSED },
            ...extraProps,
          },
        },
      },
    },
  };
}

function goodTree(overrides = {}) {
  const root = mkdtempSync(join(tmpdir(), "transparency-lint-"));
  const lexDir = join(root, LEX_REL);
  mkdirSync(lexDir, { recursive: true });
  const files = {
    "ingressDisclosureNotice.json": lex(
      "com.etzhayyim.transparency.ingressDisclosureNotice",
    ),
    "accessLogPublication.json": lex(
      "com.etzhayyim.transparency.accessLogPublication",
      {
        secretsRedacted: { type: "boolean", const: true },
        ingressConsentBasis: { type: "string", const: "ingress-act" },
      },
    ),
    "covenantTransparencyAttestation.json": lex(
      "com.etzhayyim.transparency.covenantTransparencyAttestation",
    ),
    "redactionMethodNote.json": lex(
      "com.etzhayyim.transparency.redactionMethodNote",
      { failClosed: { type: "boolean", const: true } },
    ),
    ...overrides,
  };
  for (const [name, doc] of Object.entries(files)) {
    writeFileSync(join(lexDir, name), JSON.stringify(doc, null, 2));
  }
  return root;
}

// ── Check A + B: the real repo passes ────────────────────────────────
test("real repo transparency lexicons pass (exit 0)", () => {
  const { code } = runIn(REPO_ROOT);
  assert.equal(code, 0);
});

test("clean fixture tree passes (exit 0)", () => {
  const { code } = runIn(goodTree());
  assert.equal(code, 0);
});

// ── Check A: §5 ratification gate ────────────────────────────────────
test("ratificationStatus const != proposed-unratified fails (§5)", () => {
  const poisoned = lex("com.etzhayyim.transparency.ingressDisclosureNotice");
  poisoned.defs.main.record.properties.ratificationStatus.const = "ratified";
  const { code, out } = runIn(
    goodTree({ "ingressDisclosureNotice.json": poisoned }),
  );
  assert.equal(code, 1);
  assert.match(out, /ratificationStatus/);
});

test("missing ratificationStatus fails (§5)", () => {
  const poisoned = {
    lexicon: 1,
    id: "com.etzhayyim.transparency.covenantTransparencyAttestation",
    defs: { main: { type: "record", record: { type: "object", properties: {} } } },
  };
  const { code } = runIn(
    goodTree({ "covenantTransparencyAttestation.json": poisoned }),
  );
  assert.equal(code, 1);
});

// ── Check B: §4 floor ────────────────────────────────────────────────
test("secretsRedacted const false fails (§4)", () => {
  const poisoned = lex("com.etzhayyim.transparency.accessLogPublication", {
    secretsRedacted: { type: "boolean", const: false },
    ingressConsentBasis: { type: "string", const: "ingress-act" },
  });
  const { code, out } = runIn(
    goodTree({ "accessLogPublication.json": poisoned }),
  );
  assert.equal(code, 1);
  assert.match(out, /secretsRedacted/);
});

test("ingressConsentBasis wrong const fails (§3/§4)", () => {
  const poisoned = lex("com.etzhayyim.transparency.accessLogPublication", {
    secretsRedacted: { type: "boolean", const: true },
    ingressConsentBasis: { type: "string", const: "membership" },
  });
  const { code, out } = runIn(
    goodTree({ "accessLogPublication.json": poisoned }),
  );
  assert.equal(code, 1);
  assert.match(out, /ingressConsentBasis/);
});

test("failClosed missing on redactionMethodNote fails (§4)", () => {
  const poisoned = lex("com.etzhayyim.transparency.redactionMethodNote");
  const { code, out } = runIn(
    goodTree({ "redactionMethodNote.json": poisoned }),
  );
  assert.equal(code, 1);
  assert.match(out, /failClosed/);
});

// ── Check C: premature execution in code ─────────────────────────────
test("transparency code flipping ratification without council proof fails (§5)", () => {
  const root = goodTree();
  const codeDir = join(root, "40-engine/kotoba/src");
  mkdirSync(codeDir, { recursive: true });
  const rel = "40-engine/kotoba/src/transparency_publish.rs";
  writeFileSync(
    join(root, rel),
    'let ratification_status = "ratified";\n',
  );
  const { code, out } = runIn(root, [rel]);
  assert.equal(code, 1);
  assert.match(out, /councilRatificationCid/);
});

test("transparency code with councilRatificationCid passes (§5)", () => {
  const root = goodTree();
  const codeDir = join(root, "40-engine/kotoba/src");
  mkdirSync(codeDir, { recursive: true });
  const rel = "40-engine/kotoba/src/transparency_publish.rs";
  writeFileSync(
    join(root, rel),
    'let council_ratification_cid = "..."; // councilRatificationCid present\n' +
      'let ratification_status = "ratified";\n',
  );
  const { code } = runIn(root, [rel]);
  assert.equal(code, 0);
});
