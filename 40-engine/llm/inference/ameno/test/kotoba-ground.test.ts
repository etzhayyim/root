// Tests for kotoba-grounded conversation (browser gemma4-e4b grounding on the
// published gov-procedures kotoba records). Pure, deterministic, no network
// (fetch is injected). Run:
//   node --experimental-strip-types --test test/kotoba-ground.test.ts
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  tokenize,
  retrieveProcedures,
  buildKotobaContext,
  groundedMessages,
  fetchGovProcedures,
  type KotobaProcedure,
} from "../src/kotoba-ground.ts";

const PROCS: KotobaProcedure[] = [
  {
    id: "proc.pp-jpn-passport",
    title: "Japanese passport application (旅券申請)",
    titleLocal: "旅券申請",
    ownerUnit: "gov.jpn",
    ownerHandle: "gov-jpn",
    jurisdiction: "jpn",
    authority: "都道府県 旅券事務所",
    channel: [":in-person", ":online"],
    requiredDocs: ["戸籍謄本", "写真", "本人確認書類"],
    provenance: "https://www.mofa.go.jp/passport",
    sourcing: "representative",
    verificationStatus: "unverified-seed",
  },
  {
    id: "proc.dl-jpn-driving-licence",
    title: "Driving licence (運転免許 取得・更新)",
    titleLocal: "運転免許 取得・更新",
    ownerUnit: "gov.jpn",
    ownerHandle: "gov-jpn",
    jurisdiction: "jpn",
    authority: "都道府県公安委員会",
    channel: [":in-person"],
    requiredDocs: ["本人確認書類", "写真"],
    legalBasis: "道路交通法",
    provenance: "https://www.npa.go.jp/license",
    sourcing: "representative",
    verificationStatus: "unverified-seed",
  },
  {
    id: "proc.biz-gbr-business",
    title: "Register (incorporate) a limited company",
    ownerUnit: "gov.gbr",
    ownerHandle: "gov-gbr",
    jurisdiction: "gbr",
    authority: "Companies House",
    channel: [":online"],
    requiredDocs: ["company name", "directors"],
    legalBasis: "Companies Act 2006",
    provenance: "https://www.gov.uk/limited-company-formation",
    sourcing: "representative",
    verificationStatus: "unverified-seed",
  },
];

test("tokenize emits words + CJK chars + bigrams", () => {
  const t = tokenize("運転免許 passport");
  assert.ok(t.includes("passport"));
  assert.ok(t.includes("運転"), "CJK bigram 運転 expected");
  assert.ok(t.includes("運"), "single CJK char expected");
});

test("retrieveProcedures: english query matches by title weight", () => {
  const hits = retrieveProcedures("passport japan", PROCS, 5);
  assert.ok(hits.length >= 1);
  assert.equal(hits[0].procedure.id, "proc.pp-jpn-passport");
});

test("retrieveProcedures: CJK query matches the right record", () => {
  const hits = retrieveProcedures("運転免許を取りたい", PROCS, 5);
  assert.ok(hits.length >= 1);
  assert.equal(hits[0].procedure.id, "proc.dl-jpn-driving-licence");
});

test("retrieveProcedures: empty/no-match query returns []", () => {
  assert.deepEqual(retrieveProcedures("", PROCS), []);
  assert.deepEqual(retrieveProcedures("zzzznomatch", PROCS), []);
});

test("retrieveProcedures respects k", () => {
  const hits = retrieveProcedures("company licence passport", PROCS, 1);
  assert.equal(hits.length, 1);
});

test("buildKotobaContext cites provenance + carries the charter constraints", () => {
  const ctx = buildKotobaContext(retrieveProcedures("passport", PROCS, 3));
  assert.match(ctx, /https:\/\/www\.mofa\.go\.jp\/passport/, "must cite source URL");
  assert.match(ctx, /NEVER offer to file/i, "must forbid filing on behalf (toritsugi gate)");
  assert.match(ctx, /unverified-seed/i, "must surface unverified status (G5 honesty)");
  assert.match(ctx, /NOT the government/i, "must carry the mirror disclaimer");
});

test("buildKotobaContext with no hits says so (no invention)", () => {
  const ctx = buildKotobaContext([]);
  assert.match(ctx, /none matched/i);
});

test("groundedMessages returns system+user with the user turn last", () => {
  const msgs = groundedMessages("how do I get a passport in Japan?", PROCS, 3);
  assert.equal(msgs.length, 2);
  assert.equal(msgs[0].role, "system");
  assert.equal(msgs[1].role, "user");
  assert.equal(msgs[1].content, "how do I get a passport in Japan?");
  assert.match(msgs[0].content, /mofa\.go\.jp/);
});

test("fetchGovProcedures parses the index via injected fetch (no real network)", async () => {
  const fakeFetch = (async () =>
    new Response(JSON.stringify({ count: 1, procedures: [PROCS[0]] }), {
      status: 200,
      headers: { "content-type": "application/json" },
    })) as unknown as typeof fetch;
  const got = await fetchGovProcedures("https://etzhayyim.com", fakeFetch);
  assert.equal(got.length, 1);
  assert.equal(got[0].id, "proc.pp-jpn-passport");
});
