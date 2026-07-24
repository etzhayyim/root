#!/usr/bin/env node
/**
 * Regression suite for no-kanae-adjudication.mjs (ADR-2605302300 G4+G7+G8+G15).
 *
 * Run: node --test 70-tools/scripts/lint/no-kanae-adjudication.test.mjs
 *
 * The lint's Checks A + B read the kanae Lexicon JSON at canonical RELATIVE
 * paths via process.cwd(); these tests spawn the script with `cwd` pointed
 * at a temp tree holding either a clean or a poisoned fixture, and assert
 * the exit code + message. This pins the defining guarantees so they cannot
 * silently regress:
 *   - G4: a verdict token in the fundFlowEdge flowClass enum, OR a
 *     missing/false flowNarrative nonAdjudicatingNotice const, MUST fail.
 *   - G7: a missing murakumoInferenceAttestation requirement, OR an
 *     inferenceSubstrate not pinned to const "murakumo", MUST fail.
 *   - G8: a commercial gov-intel terminal host/import in kanae code MUST
 *     fail; a doc that merely enumerates the deny-list MUST pass.
 *   - G15: an ad / analytics SDK token in kanae render code MUST fail.
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
  "no-kanae-adjudication.mjs",
);
const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const LEX_REL = "orgs/etzhayyim/com-etzhayyim-kanae/wire/lexicons";

function runIn(cwd, args = []) {
  const r = spawnSync("node", [SCRIPT, ...args], { cwd, encoding: "utf8" });
  return { code: r.status, out: (r.stdout || "") + (r.stderr || "") };
}

function makeTree(edgeDoc, narrativeDoc) {
  const root = mkdtempSync(join(tmpdir(), "kanae-lint-"));
  const lexDir = join(root, LEX_REL);
  mkdirSync(lexDir, { recursive: true });
  if (edgeDoc)
    writeFileSync(
      join(lexDir, "fundFlowEdge.json"),
      JSON.stringify(edgeDoc, null, 2),
    );
  if (narrativeDoc)
    writeFileSync(
      join(lexDir, "flowNarrative.json"),
      JSON.stringify(narrativeDoc, null, 2),
    );
  return root;
}

const GOOD_EDGE = {
  lexicon: 1,
  id: "com.etzhayyim.kanae.fundFlowEdge",
  defs: {
    main: {
      type: "record",
      record: {
        type: "object",
        properties: {
          flowClass: {
            type: "string",
            knownValues: ["appropriation", "outlay", "intergovernmental-transfer"],
          },
        },
      },
    },
  },
};
const GOOD_NARRATIVE = {
  lexicon: 1,
  id: "com.etzhayyim.kanae.flowNarrative",
  defs: {
    main: {
      type: "record",
      record: {
        type: "object",
        required: ["nonAdjudicatingNotice", "murakumoInferenceAttestation"],
        properties: {
          nonAdjudicatingNotice: { type: "boolean", const: true },
          murakumoInferenceAttestation: { type: "ref", ref: "#murakumoAttestation" },
        },
      },
    },
    murakumoAttestation: {
      type: "object",
      properties: { inferenceSubstrate: { type: "string", const: "murakumo" } },
    },
  },
};

// ── clean ────────────────────────────────────────────────────────────
test("clean: real repo lexicons pass with no args (exit 0)", () => {
  const { code } = runIn(REPO_ROOT, []);
  assert.equal(code, 0);
});

test("clean: synthetic good fixture passes (exit 0)", () => {
  const root = makeTree(GOOD_EDGE, GOOD_NARRATIVE);
  try {
    assert.equal(runIn(root, []).code, 0);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

// ── G4: verdict token in flowClass enum MUST fail ────────────────────
for (const verdict of ["violation-flow", "criminal-fraud", "有罪-transfer"]) {
  test(`G4: flowClass value '${verdict}' fails (exit 1)`, () => {
    const bad = structuredClone(GOOD_EDGE);
    bad.defs.main.record.properties.flowClass.knownValues.push(verdict);
    const root = makeTree(bad, GOOD_NARRATIVE);
    try {
      const { code, out } = runIn(root, []);
      assert.equal(code, 1, "expected non-zero exit");
      assert.match(out, /verdict token/i);
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  });
}

// ── G4: nonAdjudicatingNotice not const:true MUST fail ───────────────
test("G4: nonAdjudicatingNotice missing const:true fails (exit 1)", () => {
  const bad = structuredClone(GOOD_NARRATIVE);
  bad.defs.main.record.properties.nonAdjudicatingNotice = { type: "boolean" };
  const root = makeTree(GOOD_EDGE, bad);
  try {
    const { code, out } = runIn(root, []);
    assert.equal(code, 1);
    assert.match(out, /nonAdjudicatingNotice/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

// ── G7: missing murakumoInferenceAttestation requirement MUST fail ───
test("G7: murakumoInferenceAttestation not required fails (exit 1)", () => {
  const bad = structuredClone(GOOD_NARRATIVE);
  bad.defs.main.record.required = ["nonAdjudicatingNotice"];
  const root = makeTree(GOOD_EDGE, bad);
  try {
    const { code, out } = runIn(root, []);
    assert.equal(code, 1);
    assert.match(out, /murakumoInferenceAttestation/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

// ── G7: inferenceSubstrate not const "murakumo" MUST fail ────────────
test("G7: inferenceSubstrate not const murakumo fails (exit 1)", () => {
  const bad = structuredClone(GOOD_NARRATIVE);
  bad.defs.murakumoAttestation.properties.inferenceSubstrate = {
    type: "string",
    const: "openai",
  };
  const root = makeTree(GOOD_EDGE, bad);
  try {
    const { code, out } = runIn(root, []);
    assert.equal(code, 1);
    assert.match(out, /inferenceSubstrate|murakumo/i);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

// ── G8: gov-intel terminal in kanae code MUST fail ───────────────────
test("G8: govwin host + fiscalnote import in kanae code fails (exit 1)", () => {
  const root = mkdtempSync(join(tmpdir(), "kanae-lint-g8-"));
  // good lexicons so Checks A+B are clean
  const lexDir = join(root, LEX_REL);
  mkdirSync(lexDir, { recursive: true });
  writeFileSync(join(lexDir, "fundFlowEdge.json"), JSON.stringify(GOOD_EDGE));
  writeFileSync(join(lexDir, "flowNarrative.json"), JSON.stringify(GOOD_NARRATIVE));
  const codeDir = join(root, "orgs/etzhayyim/com-etzhayyim-kanae");
  mkdirSync(codeDir, { recursive: true });
  const rel = "orgs/etzhayyim/com-etzhayyim-kanae/bad_cell.py";
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

// ── G15: ad / analytics SDK token in kanae render code MUST fail ─────
test("G15: ga4/gtag token in kanae render code fails (exit 1)", () => {
  const root = mkdtempSync(join(tmpdir(), "kanae-lint-g15-"));
  const lexDir = join(root, LEX_REL);
  mkdirSync(lexDir, { recursive: true });
  writeFileSync(join(lexDir, "fundFlowEdge.json"), JSON.stringify(GOOD_EDGE));
  writeFileSync(join(lexDir, "flowNarrative.json"), JSON.stringify(GOOD_NARRATIVE));
  const codeDir = join(root, "orgs/etzhayyim/com-etzhayyim-kanae");
  mkdirSync(codeDir, { recursive: true });
  const rel = "orgs/etzhayyim/com-etzhayyim-kanae/viz.js";
  writeFileSync(join(root, rel), 'gtag("config", "GA4-XXXX");\n');
  try {
    const { code, out } = runIn(root, [rel]);
    assert.equal(code, 1);
    assert.match(out, /ad \/ analytics|gtag|ga4/i);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

// ── G8/G15 exemption: a DOC enumerating the deny-lists MUST pass ─────
test("G8: README enumerating the deny-list is exempt by extension (exit 0)", () => {
  const root = mkdtempSync(join(tmpdir(), "kanae-lint-doc-"));
  const lexDir = join(root, LEX_REL);
  mkdirSync(lexDir, { recursive: true });
  writeFileSync(join(lexDir, "fundFlowEdge.json"), JSON.stringify(GOOD_EDGE));
  writeFileSync(join(lexDir, "flowNarrative.json"), JSON.stringify(GOOD_NARRATIVE));
  const docDir = join(root, "orgs/etzhayyim/com-etzhayyim-kanae");
  mkdirSync(docDir, { recursive: true });
  const rel = "orgs/etzhayyim/com-etzhayyim-kanae/README.md";
  writeFileSync(
    join(root, rel),
    "# kanae\nProhibited: GovWin IQ / Bloomberg Government / FiscalNote; no GA4 / Meta Pixel.\n",
  );
  try {
    assert.equal(runIn(root, [rel]).code, 0);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
