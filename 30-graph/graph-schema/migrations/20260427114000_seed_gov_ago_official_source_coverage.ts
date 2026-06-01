import type { Kysely } from "kysely";
import { sql } from "kysely";

const ownerDid = "did:web:ago-state.etzhayyim.com";
const actorDid = ownerDid;
const actorPath = "country:ago";
const actorName = "Angolan Government";
const createdAt = "2026-04-27T11:40:00Z";

const sources = [
  {
    rkey: "ago-ministro-8c8c8b4d31-11400000",
    title: "Governo - Ministros",
    url: "https://governo.gov.ao/ministro",
    pageBlob: "official-sources/ago/governo/ago-ministro/page.html",
    screenshotBlob: "official-sources/ago/governo/ago-ministro/gyotaku.png",
    screenshotSize: 0,
  },
  {
    rkey: "ago-governador-e495bf67e7-11400000",
    title: "Governo - Governadores Provinciais",
    url: "https://governo.gov.ao/governador",
    pageBlob: "official-sources/ago/governo/ago-governador/page.html",
    screenshotBlob: "official-sources/ago/governo/ago-governador/gyotaku.png",
    screenshotSize: 0,
  },
  {
    rkey: "ago-provincias-36779ddfea-11400000",
    title: "Angola - Províncias",
    url: "https://governo.gov.ao/angola/provincias",
    pageBlob: "official-sources/ago/governo/ago-provincias/page.html",
    screenshotBlob: "official-sources/ago/governo/ago-provincias/gyotaku.png",
    screenshotSize: 0,
  },
];

function vertexId(rkey: string): string {
  return `at://${ownerDid}/app.etzhayyim.gov.source/${rkey}`;
}

function props(source: (typeof sources)[number]): string {
  return JSON.stringify({
    countryCode: "AGO",
    officialPublisher: "Angolan Government",
    evidence: {
      page: {
        rkey: source.rkey,
        vertexId: `at://${ownerDid}/app.etzhayyim.apps.site.page/${source.rkey}`,
        b2Blob: source.pageBlob,
      },
      wet: {
        pageRkey: source.rkey,
        vertexId: `at://${ownerDid}/app.etzhayyim.apps.site.wetChunk/${source.rkey}`,
      },
      wat: {
        rkey: source.rkey,
        vertexId: `at://${ownerDid}/app.etzhayyim.apps.site.wat/${source.rkey}`,
      },
      screenshot: {
        rkey: source.rkey,
        vertexId: `at://${ownerDid}/app.etzhayyim.apps.site.screenshot/${source.rkey}`,
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
        ${actorDid}, 'app.etzhayyim.gov.source', 'active', ${actorDid}, ${actorPath},
        ${actorName}, 'official-government-page', ${source.url}, 'html',
        'gov-ago-official-seed', 'pending-page-wet-wat-gyotaku',
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
