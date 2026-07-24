#!/usr/bin/env node
/**
 * Regression suite for no-danjo-adjudication.mjs (ADR-2605301600 G4 + G8).
 *
 * Run: node --test 70-tools/scripts/lint/no-danjo-adjudication.test.mjs
 *
 * The lint's Check B reads the danjo Lexicon JSON at canonical RELATIVE
 * paths via process.cwd(); these tests therefore spawn the script with
 * `cwd` pointed at a temp tree that contains either a clean or a poisoned
 * fixture, and assert the exit code + message. This pins the two defining
 * guarantees so they cannot silently regress:
 *   - G4: a verdict token in the discrepancyObservation category enum, OR
 *     a missing/false nonAdjudicatingNotice const, MUST fail.
 *   - G8: a commercial gov-intel terminal host/import in danjo code MUST
 *     fail, while a doc that merely enumerates the deny-list MUST pass.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPT = resolve(
  dirname(fileURLToPath(import.meta.url)),
  "no-danjo-adjudication.mjs",
);
const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const LEX_REL = "00-contracts/lexicons/com/etzhayyim/danjo";

function runIn(cwd, args = []) {
  const r = spawnSync("node", [SCRIPT, ...args], { cwd, encoding: "utf8" });
  return { code: r.status, out: (r.stdout || "") + (r.stderr || "") };
}

function makeTree(observationDoc, reportDoc) {
  const root = mkdtempSync(join(tmpdir(), "danjo-lint-"));
  const lexDir = join(root, LEX_REL);
  mkdirSync(lexDir, { recursive: true });
  if (observationDoc)
    writeFileSync(
      join(lexDir, "discrepancyObservation.json"),
      JSON.stringify(observationDoc, null, 2),
    );
  if (reportDoc)
    writeFileSync(
      join(lexDir, "oversightReport.json"),
      JSON.stringify(reportDoc, null, 2),
    );
  return root;
}

const GOOD_OBSERVATION = {
  lexicon: 1,
  id: "com.etzhayyim.danjo.discrepancyObservation",
  defs: {
    main: {
      type: "record",
      record: {
        type: "object",
        properties: {
          category: {
            type: "string",
            knownValues: ["single-bidder-streak", "recipient-concentration"],
          },
          nonAdjudicatingNotice: { type: "boolean", const: true },
        },
      },
    },
  },
};
const GOOD_REPORT = {
  lexicon: 1,
  id: "com.etzhayyim.danjo.oversightReport",
  defs: {
    main: {
      record: { properties: { nonAdjudicatingNotice: { const: true } } },
    },
  },
};

// ── G4 anchor: real repo lexicons must pass the schema audit ─────────
test("clean: real repo lexicons pass with no args (exit 0)", () => {
  const { code } = runIn(REPO_ROOT, []);
  assert.equal(code, 0);
});

test("clean: synthetic good fixture passes (exit 0)", () => {
  const root = makeTree(GOOD_OBSERVATION, GOOD_REPORT);
  try {
    const { code } = runIn(root, []);
    assert.equal(code, 0);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

// ── G4 regression: verdict token in category enum MUST fail ──────────
for (const verdict of ["violation-detected", "criminal-fraud", "有罪-judgment"]) {
  test(`G4: category enum value '${verdict}' fails (exit 1)`, () => {
    const bad = structuredClone(GOOD_OBSERVATION);
    bad.defs.main.record.properties.category.knownValues.push(verdict);
    const root = makeTree(bad, GOOD_REPORT);
    try {
      const { code, out } = runIn(root, []);
      assert.equal(code, 1, "expected non-zero exit");
      assert.match(out, /verdict token/i);
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  });
}

// ── G4 regression: nonAdjudicatingNotice not const:true MUST fail ────
test("G4: nonAdjudicatingNotice missing const:true fails (exit 1)", () => {
  const bad = structuredClone(GOOD_OBSERVATION);
  bad.defs.main.record.properties.nonAdjudicatingNotice = { type: "boolean" };
  const root = makeTree(bad, GOOD_REPORT);
  try {
    const { code, out } = runIn(root, []);
    assert.equal(code, 1);
    assert.match(out, /nonAdjudicatingNotice/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

// ── G8 regression: gov-intel terminal in danjo code MUST fail ────────
test("G8: govwin host + fiscalnote import in danjo code fails (exit 1)", () => {
  const root = mkdtempSync(join(tmpdir(), "danjo-lint-g8-"));
  const codeDir = join(root, "orgs/etzhayyim/com-etzhayyim-danjo");
  mkdirSync(codeDir, { recursive: true });
  const rel = "orgs/etzhayyim/com-etzhayyim-danjo/bad_cell.py";
  writeFileSync(
    join(root, rel),
    'import fiscalnote\nURL = "https://www.govwin.com/api"\n',
  );
  try {
    const { code, out } = runIn(root, [rel]);
    assert.equal(code, 1);
    assert.match(out, /gov-intel|govwin|fiscalnote/i);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

// ── G8 exemption: a DOC enumerating the deny-list MUST pass ──────────
test("G8: README enumerating the deny-list is exempt by extension (exit 0)", () => {
  const root = mkdtempSync(join(tmpdir(), "danjo-lint-doc-"));
  const docDir = join(root, "orgs/etzhayyim/com-etzhayyim-danjo");
  mkdirSync(docDir, { recursive: true });
  // good lexicons so Check B is clean; the doc must not trip Check A
  const lexDir = join(root, LEX_REL);
  mkdirSync(lexDir, { recursive: true });
  writeFileSync(
    join(lexDir, "discrepancyObservation.json"),
    JSON.stringify(GOOD_OBSERVATION),
  );
  const rel = "orgs/etzhayyim/com-etzhayyim-danjo/README.md";
  writeFileSync(
    join(root, rel),
    "# danjo\nProhibited terminals: GovWin IQ / Bloomberg Government / FiscalNote.\n",
  );
  try {
    const { code } = runIn(root, [rel]);
    assert.equal(code, 0);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
