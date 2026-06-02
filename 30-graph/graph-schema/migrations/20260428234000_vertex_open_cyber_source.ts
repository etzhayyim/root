import type { Kysely } from "kysely";
import { sql } from "kysely";

const createdAt = "2026-04-28T23:40:00Z";
const ownerDid = "did:web:open-cyber-vuln.etzhayyim.com:ops";

type SourceSeed = {
  sourceId: string;
  displayName: string;
  baseUrl: string;
  cadenceIso8601: string;
  authStrategy: string;
  secretRef: string | null;
  license: string;
  initCursor: string | null;
};

const seeds: SourceSeed[] = [
  {
    sourceId: "nvd",
    displayName: "NVD CVE 2.0 API",
    baseUrl: "https://services.nvd.nist.gov/rest/json/cves/2.0",
    cadenceIso8601: "R/PT6H",
    authStrategy: "none",
    secretRef: null,
    license: "public-domain",
    initCursor: "2024-01-01T00:00:00.000",
  },
  {
    sourceId: "cisa-kev",
    displayName: "CISA Known Exploited Vulnerabilities",
    baseUrl: "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
    cadenceIso8601: "R/PT12H",
    authStrategy: "none",
    secretRef: null,
    license: "public-domain",
    initCursor: null,
  },
  {
    sourceId: "ghsa",
    displayName: "GitHub Security Advisories (GHSA)",
    baseUrl: "https://api.github.com/advisories",
    cadenceIso8601: "R/PT12H",
    authStrategy: "none",
    secretRef: null,
    license: "cc-by-4.0",
    initCursor: "2024-01-01T00:00:00Z",
  },
  {
    sourceId: "mitre-attack",
    displayName: "MITRE ATT&CK TAXII 2.1",
    baseUrl: "https://cti-taxii.mitre.org/stix/collections/95ecc380-afe9-11e4-9b6c-751b66dd541e/objects/",
    cadenceIso8601: "R/PT24H",
    authStrategy: "none",
    secretRef: null,
    license: "cc-by-4.0",
    initCursor: null,
  },
  {
    sourceId: "cisa-alerts",
    displayName: "CISA US-CERT Alerts Atom Feed",
    baseUrl: "https://www.cisa.gov/uscert/ncas/alerts.xml",
    cadenceIso8601: "R/PT6H",
    authStrategy: "none",
    secretRef: null,
    license: "public-domain",
    initCursor: null,
  },
];

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_cyber_source (
      vertex_id         varchar PRIMARY KEY,
      _seq              bigint,
      created_date      date,
      sensitivity_ord   int,
      owner_did         varchar,
      source_id         varchar NOT NULL,
      display_name      varchar NOT NULL,
      base_url          varchar NOT NULL,
      cadence_iso8601   varchar NOT NULL,
      auth_strategy     varchar NOT NULL,
      secret_ref        varchar,
      license           varchar,
      last_cursor       varchar,
      last_fetched_at   varchar,
      status            varchar NOT NULL,
      created_at        varchar,
      org_id            varchar,
      user_id           varchar,
      actor_id          varchar
    )
  `.execute(db);

  for (const s of seeds) {
    const vertexId = `at://did:web:open-cyber-vuln.etzhayyim.com/com.etzhayyim.apps.openCyberVuln.source/${s.sourceId}`;
    await sql`
      INSERT INTO vertex_open_cyber_source
        (vertex_id, sensitivity_ord, owner_did, source_id, display_name, base_url, cadence_iso8601, auth_strategy, secret_ref, license, last_cursor, last_fetched_at, status, created_at, org_id, user_id, actor_id)
      SELECT ${vertexId}, 1, ${ownerDid}, ${s.sourceId}, ${s.displayName}, ${s.baseUrl}, ${s.cadenceIso8601}, ${s.authStrategy}, ${s.secretRef}, ${s.license}, ${s.initCursor}, null, 'active', ${createdAt}, ${ownerDid}, ${ownerDid}, 'sys.bpmn.seed.open-cyber'
      WHERE NOT EXISTS (SELECT 1 FROM vertex_open_cyber_source WHERE source_id = ${s.sourceId})
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_open_cyber_source`.execute(db);
}
