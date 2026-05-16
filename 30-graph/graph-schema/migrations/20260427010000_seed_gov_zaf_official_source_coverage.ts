import type { Kysely } from "kysely";
import { sql } from "kysely";

const ownerDid = "did:web:zaf-state.gftd.ai";
const actorDid = ownerDid;
const actorPath = "country:zaf";
const actorName = "South African Government";
const createdAt = "2026-04-27T01:00:00Z";

const sources = [
  {
    rkey: "zaf-national-departments-9cfc7bff4a-10304550",
    title: "National departments | South African Government",
    url: "https://www.gov.za/about-government/government-system/national-departments",
    pageBlob: "official-sources/zaf/govza/zaf-national-departments/page.html",
    screenshotBlob: "official-sources/zaf/govza/zaf-national-departments/gyotaku.png",
    screenshotSize: 388467,
  },
  {
    rkey: "zaf-provinces-2aa86b5df1-10305612",
    title: "Provinces | South African Government",
    url: "https://www.gov.za/provinces",
    pageBlob: "official-sources/zaf/govza/zaf-provinces/page.html",
    screenshotBlob: "official-sources/zaf/govza/zaf-provinces/gyotaku.png",
    screenshotSize: 493001,
  },
  {
    rkey: "zaf-provincial-government-6eeae56a66-10306648",
    title: "Provincial government | South African Government",
    url: "https://www.gov.za/links/provincial-government",
    pageBlob: "official-sources/zaf/govza/zaf-provincial-government/page.html",
    screenshotBlob: "official-sources/zaf/govza/zaf-provincial-government/gyotaku.png",
    screenshotSize: 549036,
  },
];

function vertexId(rkey: string): string {
  return `at://${ownerDid}/ai.gftd.gov.source/${rkey}`;
}

function props(source: (typeof sources)[number]): string {
  return JSON.stringify({
    countryCode: "ZAF",
    officialPublisher: "South African Government",
    evidence: {
      page: {
        rkey: source.rkey,
        vertexId: `at://${ownerDid}/ai.gftd.apps.site.page/${source.rkey}`,
        b2Blob: source.pageBlob,
      },
      wet: {
        pageRkey: source.rkey,
        vertexId: `at://${ownerDid}/ai.gftd.apps.site.wetChunk/${source.rkey}`,
      },
      wat: {
        rkey: source.rkey,
        vertexId: `at://${ownerDid}/ai.gftd.apps.site.wat/${source.rkey}`,
      },
      screenshot: {
        rkey: source.rkey,
        vertexId: `at://${ownerDid}/ai.gftd.apps.site.screenshot/${source.rkey}`,
        b2Blob: source.screenshotBlob,
        format: "png",
        fileSize: source.screenshotSize,
      },
    },
  });
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const source of sources) {
    await sql`
      INSERT INTO vertex_gov_source (
        vertex_id, owner_did, rkey, repo, did, collection, status,
        "actorDid", "actorPath", "actorName", "sourceType", "sourceUrl", format,
        "discoveryMethod", "coverageStage", "lastSeenAt", props
      )
      SELECT
        ${vertexId(source.rkey)}, ${ownerDid}, ${source.rkey}, ${ownerDid},
        ${actorDid}, 'ai.gftd.gov.source', 'active', ${actorDid}, ${actorPath},
        ${actorName}, 'official-government-page', ${source.url}, 'html',
        'gov-za-official-seed', 'page-wet-wat-gyotaku-ingested',
        ${createdAt}, ${props(source)}
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_gov_source WHERE vertex_id = ${vertexId(source.rkey)}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const source of sources) {
    await sql`DELETE FROM vertex_gov_source WHERE vertex_id = ${vertexId(source.rkey)}`.execute(db);
  }
}
