import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * domain.etzhayyim.com Phase 1 seed (ADR-0036 + ADR-0056 + ADR-2604282300).
 *
 * Seeds:
 *   • 4 TLD catalog rows (.law / .lawyer / .legal / .attorney)
 *   • 7 registrar catalog rows (cloudflare / namecheap / godaddy /
 *     eurodns / dynadot / join-law / squarespace)
 *   • 4 legal regulator rows (JFBA / ABA / SRA-EnglandWales / IBA)
 *   • 6 eligibility advice rows (.law × {JP-bengoshi / JP-gaikokuho-jimu-bengoshi /
 *     UK-solicitor / US-bar} + .lawyer × open + .legal × open)
 *   • 14 registrar↔TLD support edges (which registrar handles which TLD)
 *   • 2 TLD↔regulator accept edges (.law accepts JFBA + ABA)
 *
 * BPMN actors (3):
 *   domain_eligibility_check   ai.gftd.apps.domain.eligibilityCheck
 *   domain_register_assist     ai.gftd.apps.domain.registerAssist
 *   domain_refresh_tld_catalog (timer R/P30D, autonomous, Phase 1 stub)
 *
 * Lexicon bindings (2 XRPC entries; 4 query lexicons are schema-doc only).
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };
type B = { vertexId: string; nsid: string; bpmnProcessId: string; ownerDid: string; resultTimeoutMs: number };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-07T23:00:00Z";
const ownerDid = "did:web:domain.etzhayyim.com";
const actorTag = "sys.bpmn.seed.domain";

// ── Catalog rows ─────────────────────────────────────────────────────

type TldRow = {
  tld: string;
  operator: string;
  restricted: boolean;
  verificationRequired: boolean;
  summary: string;
  policyUrl: string | null;
  typicalUses: string;
  notes: string | null;
};

const tldSeeds: TldRow[] = [
  {
    tld: ".law",
    operator: "GoDaddy Registry (Registry Services, LLC)",
    restricted: true,
    verificationRequired: true,
    summary:
      "Restricted to legal professionals (lawyers / barristers / solicitors / law firms / law schools / courts / legal regulators) appropriately licensed by a recognized accredited body or authorized government authority. Independent verification agent may request supporting documentation; failure to remain eligible is grounds for cancellation without refund.",
    policyUrl:
      "https://domains.registry.godaddy/policiespdf/LAW-POL-001-Eligibility_Policy-1.0.pdf",
    typicalUses: "law-firm primary domain, individual lawyer brand, bar-association portal",
    notes:
      "Policy §1.1 uses jurisdiction-neutral language (no approved-regulator allow-list); JP bengoshi via JFBA, UK solicitor via SRA, US lawyer via state bar all qualify. Continuing-eligibility rule §1.1: contact registrar within 14 days if license lapses.",
  },
  {
    tld: ".lawyer",
    operator: "Identity Digital (formerly Donuts/Afilias)",
    restricted: false,
    verificationRequired: false,
    summary:
      "Open generic TLD — no occupational eligibility requirement. Anyone may register. Trademark / UDRP rights protections apply but no licensing-of-law check.",
    policyUrl: "https://www.identity.digital/policies",
    typicalUses: "lawyer marketing site, legal-tech product brand, podcast",
    notes:
      "Despite the suggestive name, registry policy is open. Use case is closer to .com than to .law.",
  },
  {
    tld: ".legal",
    operator: "Identity Digital",
    restricted: false,
    verificationRequired: false,
    summary:
      "Open generic TLD — no occupational eligibility requirement. Anyone may register.",
    policyUrl: "https://www.identity.digital/policies",
    typicalUses: "law-firm marketing, legal information site, citizens-advice service",
    notes: "Companion to .lawyer; same operator and policy regime.",
  },
  {
    tld: ".attorney",
    operator: "Identity Digital",
    restricted: false,
    verificationRequired: false,
    summary:
      "Open generic TLD — no occupational eligibility requirement. Anyone may register.",
    policyUrl: "https://www.identity.digital/policies",
    typicalUses: "US-style attorney marketing site",
    notes: "Companion to .lawyer/.legal; same operator and policy regime.",
  },
];

type RegistrarRow = {
  slug: string;
  name: string;
  homepage: string;
  jpFriendly: boolean;
  notes: string;
};

const registrarSeeds: RegistrarRow[] = [
  {
    slug: "cloudflare",
    name: "Cloudflare Registrar",
    homepage: "https://domains.cloudflare.com/",
    jpFriendly: true,
    notes:
      "Wholesale-priced, ~400 TLDs supported. Does NOT currently support .law (verified TLD). Open-policy .lawyer/.legal/.attorney also not on the supported list as of 2026-05. NS / DNS / proxy can still front a domain registered elsewhere.",
  },
  {
    slug: "namecheap",
    name: "Namecheap",
    homepage: "https://www.namecheap.com/domains/registration/gtld/law/",
    jpFriendly: true,
    notes:
      "Handles .law verification flow (requests bar admission documentation when needed). Standard registrar for .lawyer/.legal/.attorney. JP customers supported.",
  },
  {
    slug: "godaddy",
    name: "GoDaddy",
    homepage: "https://www.godaddy.com/tlds/law-domain",
    jpFriendly: true,
    notes:
      "Owns the .law registry (Registry Services LLC) and is the default reseller. JP localization available.",
  },
  {
    slug: "eurodns",
    name: "EuroDNS",
    homepage: "https://www.eurodns.com/domain-extensions/law-domain-registration",
    jpFriendly: true,
    notes: "EU-based; carries .law and the open-policy legal TLDs. Useful for EU registrant compliance.",
  },
  {
    slug: "dynadot",
    name: "Dynadot",
    homepage: "https://www.dynadot.com/domain/law",
    jpFriendly: true,
    notes: "Carries .law plus open-policy legal TLDs.",
  },
  {
    slug: "join-law",
    name: "Join.Law",
    homepage: "https://www.join.law/",
    jpFriendly: false,
    notes:
      "Specialty .law-only registrar with bar-verification workflow built into the signup. Geared toward US/UK bar admissions; JP credential acceptance requires direct conversation.",
  },
  {
    slug: "squarespace",
    name: "Squarespace Domains (formerly Google Domains)",
    homepage: "https://domains.squarespace.com/",
    jpFriendly: true,
    notes: "Generalist registrar; carries .lawyer/.legal/.attorney but not .law verified TLD.",
  },
];

type RegulatorRow = {
  slug: string;
  name: string;
  jurisdiction: string;
  kind: string;
  publicRegisterUrl: string | null;
  notes: string;
};

const regulatorSeeds: RegulatorRow[] = [
  {
    slug: "jfba",
    name: "Japan Federation of Bar Associations (日本弁護士連合会 / 日弁連)",
    jurisdiction: "JP",
    kind: "national-bar",
    publicRegisterUrl: "https://www.nichibenren.or.jp/library/ja/member/search/",
    notes:
      "Sole supreme legal regulator in Japan under 弁護士法. Registers bengoshi (弁護士), Gaikokuho-Jimu-Bengoshi (外国法事務弁護士 / GJB), legal-professional corporations (弁護士法人), and supervises local bar associations. Independent of government supervision.",
  },
  {
    slug: "aba-state-bars",
    name: "US State Bar Associations (admitted via state supreme courts; ABA accreditation)",
    jurisdiction: "US",
    kind: "state-bar-network",
    publicRegisterUrl: null,
    notes:
      "US lawyer licensure is per-state. Each state bar is the Legal Regulator. ABA itself accredits law schools but does not license lawyers.",
  },
  {
    slug: "sra-england-wales",
    name: "Solicitors Regulation Authority (SRA, England & Wales)",
    jurisdiction: "GB-EAW",
    kind: "national-bar",
    publicRegisterUrl: "https://www.sra.org.uk/consumers/register/",
    notes: "Statutory regulator of solicitors in England & Wales.",
  },
  {
    slug: "iba",
    name: "International Bar Association (IBA)",
    jurisdiction: "INTL",
    kind: "international-association",
    publicRegisterUrl: null,
    notes:
      "Not a Legal Regulator in the .law policy sense, but referenced by some registrars as a corroborating source for cross-border verification.",
  },
];

type EligibilityAdvice = {
  slug: string;
  tld: string;
  jurisdiction: string;
  regulatorSlug: string | null;
  actorKind: string;
  eligible: boolean;
  basis: string;
  policyExcerpt: string;
  sourceUrl: string;
  effectiveAt: string;
};

const adviceSeeds: EligibilityAdvice[] = [
  {
    slug: "law-jp-bengoshi",
    tld: ".law",
    jurisdiction: "JP",
    regulatorSlug: "jfba",
    actorKind: "individual-lawyer",
    eligible: true,
    basis:
      "JFBA は弁護士法に基づく recognized accredited body であり、日本の bengoshi は currently-licensed practitioner として JFBA 弁護士検索 (公開 registry) で identifiable。policy §1.1 の要件 (recognized accredited body or authorized government authority) を満たす。",
    policyExcerpt:
      "Registration of domain names in the TLD is restricted to legal professionals (e.g., lawyers, barristers, solicitors, law firms, and other practitioners of law) appropriately licensed to practice law by a recognized accredited body or authorized government authority.",
    sourceUrl:
      "https://domains.registry.godaddy/policiespdf/LAW-POL-001-Eligibility_Policy-1.0.pdf",
    effectiveAt: "2022-01-01",
  },
  {
    slug: "law-jp-gaikokuho-jimu-bengoshi",
    tld: ".law",
    jurisdiction: "JP",
    regulatorSlug: "jfba",
    actorKind: "registered-foreign-lawyer",
    eligible: true,
    basis:
      "Gaikokuho-Jimu-Bengoshi (外国法事務弁護士 / GJB) は法務大臣承認 + JFBA special member registration で確立される recognized status。policy §1.1 の other practitioners of law に該当。",
    policyExcerpt:
      "(法的根拠) Foreign Lawyers Act §3-§7 + JFBA 入会手続。承認後は JFBA special member として公開登録される。",
    sourceUrl: "https://www.toben.or.jp/english/f-lawyer/flra.html",
    effectiveAt: "2022-01-01",
  },
  {
    slug: "law-jp-bengoshi-houjin",
    tld: ".law",
    jurisdiction: "JP",
    regulatorSlug: "jfba",
    actorKind: "law-firm",
    eligible: true,
    basis:
      "弁護士法人 (legal-professional corporation) は弁護士法 §30 以降に基づき JFBA registration が要求される。policy §1.1 列挙の law firm に直接該当。",
    policyExcerpt:
      "Eligible categories include law firms — partnerships or entities formed by qualified lawyers.",
    sourceUrl:
      "https://domains.registry.godaddy/policiespdf/LAW-POL-001-Eligibility_Policy-1.0.pdf",
    effectiveAt: "2022-01-01",
  },
  {
    slug: "law-uk-solicitor",
    tld: ".law",
    jurisdiction: "GB-EAW",
    regulatorSlug: "sra-england-wales",
    actorKind: "individual-lawyer",
    eligible: true,
    basis:
      "SRA は statutory Legal Regulator。Solicitor は SRA roll で identifiable。",
    policyExcerpt:
      "Registration of domain names in the TLD is restricted to legal professionals appropriately licensed to practice law by a recognized accredited body or authorized government authority.",
    sourceUrl: "https://www.sra.org.uk/consumers/register/",
    effectiveAt: "2022-01-01",
  },
  {
    slug: "law-us-bar",
    tld: ".law",
    jurisdiction: "US",
    regulatorSlug: "aba-state-bars",
    actorKind: "individual-lawyer",
    eligible: true,
    basis:
      "Each US state bar is the Legal Regulator. Active member status is required; inactive / non-practicing is excluded per §1.1.",
    policyExcerpt:
      "A lawyer with inactive or non-practicing status who is not authorized to provide regulated legal services under the rules of their Legal Regulator is not eligible.",
    sourceUrl:
      "https://domains.registry.godaddy/policiespdf/LAW-POL-001-Eligibility_Policy-1.0.pdf",
    effectiveAt: "2022-01-01",
  },
  {
    slug: "law-non-practicing-corp",
    tld: ".law",
    jurisdiction: "JP",
    regulatorSlug: null,
    actorKind: "non-legal-corporation",
    eligible: false,
    basis:
      "Gftd Japan株式会社 のような非弁護士法人は §1.1 の eligible categories に該当しない。提携弁護士または弁護士法人名義での登録 or .lawyer/.legal への切り替えが代替路。",
    policyExcerpt:
      "Registration of domain names in the TLD is restricted to legal professionals (e.g., lawyers, barristers, solicitors, law firms, and other practitioners of law) appropriately licensed to practice law by a recognized accredited body or authorized government authority.",
    sourceUrl:
      "https://domains.registry.godaddy/policiespdf/LAW-POL-001-Eligibility_Policy-1.0.pdf",
    effectiveAt: "2022-01-01",
  },
  {
    slug: "lawyer-jp-open",
    tld: ".lawyer",
    jurisdiction: "JP",
    regulatorSlug: null,
    actorKind: "any",
    eligible: true,
    basis:
      ".lawyer は Identity Digital の open generic TLD。occupational requirement なし。誰でも登録可。",
    policyExcerpt: "No occupational eligibility requirement.",
    sourceUrl: "https://www.identity.digital/policies",
    effectiveAt: "2014-04-01",
  },
  {
    slug: "legal-jp-open",
    tld: ".legal",
    jurisdiction: "JP",
    regulatorSlug: null,
    actorKind: "any",
    eligible: true,
    basis:
      ".legal は Identity Digital の open generic TLD。occupational requirement なし。",
    policyExcerpt: "No occupational eligibility requirement.",
    sourceUrl: "https://www.identity.digital/policies",
    effectiveAt: "2014-04-01",
  },
];

type SupportEdge = {
  registrarSlug: string;
  tld: string;
  handlesVerification: boolean;
  notes: string | null;
};

const supportEdges: SupportEdge[] = [
  // .law — only registrars that carry the verified TLD
  { registrarSlug: "namecheap",  tld: ".law", handlesVerification: true,  notes: "Handles registry verification flow." },
  { registrarSlug: "godaddy",    tld: ".law", handlesVerification: true,  notes: "Default reseller (operator-aligned)." },
  { registrarSlug: "eurodns",    tld: ".law", handlesVerification: true,  notes: null },
  { registrarSlug: "dynadot",    tld: ".law", handlesVerification: true,  notes: null },
  { registrarSlug: "join-law",   tld: ".law", handlesVerification: true,  notes: "Specialty .law registrar." },

  // .lawyer
  { registrarSlug: "namecheap",   tld: ".lawyer", handlesVerification: false, notes: null },
  { registrarSlug: "godaddy",     tld: ".lawyer", handlesVerification: false, notes: null },
  { registrarSlug: "eurodns",     tld: ".lawyer", handlesVerification: false, notes: null },
  { registrarSlug: "dynadot",     tld: ".lawyer", handlesVerification: false, notes: null },
  { registrarSlug: "squarespace", tld: ".lawyer", handlesVerification: false, notes: null },

  // .legal
  { registrarSlug: "namecheap",   tld: ".legal", handlesVerification: false, notes: null },
  { registrarSlug: "godaddy",     tld: ".legal", handlesVerification: false, notes: null },
  { registrarSlug: "eurodns",     tld: ".legal", handlesVerification: false, notes: null },
  { registrarSlug: "squarespace", tld: ".legal", handlesVerification: false, notes: null },

  // .attorney
  { registrarSlug: "namecheap",   tld: ".attorney", handlesVerification: false, notes: null },
  { registrarSlug: "godaddy",     tld: ".attorney", handlesVerification: false, notes: null },
];

type AcceptEdge = { tld: string; regulatorSlug: string; basis: string };

const acceptEdges: AcceptEdge[] = [
  {
    tld: ".law",
    regulatorSlug: "jfba",
    basis:
      "Policy §1.1 jurisdiction-neutral 'recognized accredited body' wording covers JFBA (弁護士法に基づく自治団体).",
  },
  {
    tld: ".law",
    regulatorSlug: "aba-state-bars",
    basis:
      "Policy §1.1 covers US state bars (each is an authorized government authority via state supreme court).",
  },
  {
    tld: ".law",
    regulatorSlug: "sra-england-wales",
    basis: "Policy §1.1 covers SRA as statutory Legal Regulator.",
  },
];

// ── BPMN process defs + lexicon bindings ────────────────────────────

const processSeeds: P[] = [
  {
    vertexId:
      "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/domain-eligibility-check-v1",
    bpmnProcessId: "domain_eligibility_check",
    sourcePath: "00-contracts/bpmn/ai/gftd/domain/eligibilityCheck.bpmn",
    ownerDid,
  },
  {
    vertexId:
      "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/domain-register-assist-v1",
    bpmnProcessId: "domain_register_assist",
    sourcePath: "00-contracts/bpmn/ai/gftd/domain/registerAssist.bpmn",
    ownerDid,
  },
  {
    vertexId:
      "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/domain-refresh-tld-catalog-v1",
    bpmnProcessId: "domain_refresh_tld_catalog",
    sourcePath: "00-contracts/bpmn/ai/gftd/domain/refreshTldCatalog.bpmn",
    ownerDid,
  },
];

const bindingSeeds: B[] = [
  {
    vertexId:
      "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/domain-eligibilityCheck-v1",
    nsid: "ai.gftd.apps.domain.eligibilityCheck",
    bpmnProcessId: "domain_eligibility_check",
    ownerDid,
    resultTimeoutMs: 30_000,
  },
  {
    vertexId:
      "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/domain-registerAssist-v1",
    nsid: "ai.gftd.apps.domain.registerAssist",
    bpmnProcessId: "domain_register_assist",
    ownerDid,
    resultTimeoutMs: 30_000,
  },
];

// ── Insert helpers ──────────────────────────────────────────────────

async function insertTld(db: Kysely<unknown>, t: TldRow): Promise<void> {
  const vid = `at://${ownerDid}/ai.gftd.apps.domain.tld/${t.tld.replace(/^\./, "")}`;
  await sql`
    INSERT INTO vertex_domain_tld (vertex_id, owner_did, sensitivity_ord, tld, operator, restricted, eligibility_summary, eligibility_policy_url, verification_required, typical_uses, notes, status, created_at, org_id, user_id, actor_id)
    SELECT ${vid}, ${ownerDid}, 0, ${t.tld}, ${t.operator}, CAST(${t.restricted} AS boolean), ${t.summary}, ${t.policyUrl}, CAST(${t.verificationRequired} AS boolean), ${t.typicalUses}, ${t.notes}, 'active', ${createdAt}, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_tld WHERE vertex_id = ${vid})
  `.execute(db);
}

async function insertRegistrar(db: Kysely<unknown>, r: RegistrarRow): Promise<void> {
  const vid = `at://${ownerDid}/ai.gftd.apps.domain.registrar/${r.slug}`;
  await sql`
    INSERT INTO vertex_domain_registrar (vertex_id, owner_did, sensitivity_ord, registrar_slug, name, homepage_url, iana_id, jp_friendly, notes, status, created_at, org_id, user_id, actor_id)
    SELECT ${vid}, ${ownerDid}, 0, ${r.slug}, ${r.name}, ${r.homepage}, NULL, CAST(${r.jpFriendly} AS boolean), ${r.notes}, 'active', ${createdAt}, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_registrar WHERE vertex_id = ${vid})
  `.execute(db);
}

async function insertRegulator(db: Kysely<unknown>, r: RegulatorRow): Promise<void> {
  const vid = `at://${ownerDid}/ai.gftd.apps.domain.legalRegulator/${r.slug}`;
  await sql`
    INSERT INTO vertex_domain_legal_regulator (vertex_id, owner_did, sensitivity_ord, regulator_slug, name, jurisdiction, kind, public_register_url, notes, status, created_at, org_id, user_id, actor_id)
    SELECT ${vid}, ${ownerDid}, 0, ${r.slug}, ${r.name}, ${r.jurisdiction}, ${r.kind}, ${r.publicRegisterUrl}, ${r.notes}, 'active', ${createdAt}, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_legal_regulator WHERE vertex_id = ${vid})
  `.execute(db);
}

async function insertAdvice(db: Kysely<unknown>, a: EligibilityAdvice): Promise<void> {
  const vid = `at://${ownerDid}/ai.gftd.apps.domain.eligibilityAdvice/${a.slug}`;
  await sql`
    INSERT INTO vertex_domain_eligibility_advice (vertex_id, owner_did, sensitivity_ord, tld, jurisdiction, regulator_slug, actor_kind, eligible, basis, policy_excerpt, source_url, effective_at, status, created_at, org_id, user_id, actor_id)
    SELECT ${vid}, ${ownerDid}, 0, ${a.tld}, ${a.jurisdiction}, ${a.regulatorSlug}, ${a.actorKind}, CAST(${a.eligible} AS boolean), ${a.basis}, ${a.policyExcerpt}, ${a.sourceUrl}, ${a.effectiveAt}, 'active', ${createdAt}, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_eligibility_advice WHERE vertex_id = ${vid})
  `.execute(db);
}

async function insertSupportEdge(db: Kysely<unknown>, e: SupportEdge): Promise<void> {
  const tldKey = e.tld.replace(/^\./, "");
  const eid = `edge:domain:supports:${e.registrarSlug}:${tldKey}`;
  const src = `at://${ownerDid}/ai.gftd.apps.domain.registrar/${e.registrarSlug}`;
  const dst = `at://${ownerDid}/ai.gftd.apps.domain.tld/${tldKey}`;
  await sql`
    INSERT INTO edge_domain_registrar_supports_tld (edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, registrar_slug, tld, verified_at, handles_verification, notes, created_at, org_id, user_id, actor_id)
    SELECT ${eid}, ${ownerDid}, 0, ${src}, ${dst}, ${e.registrarSlug}, ${e.tld}, ${createdAt}, CAST(${e.handlesVerification} AS boolean), ${e.notes}, ${createdAt}, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM edge_domain_registrar_supports_tld WHERE edge_id = ${eid})
  `.execute(db);
}

async function insertAcceptEdge(db: Kysely<unknown>, e: AcceptEdge): Promise<void> {
  const tldKey = e.tld.replace(/^\./, "");
  const eid = `edge:domain:accepts:${tldKey}:${e.regulatorSlug}`;
  const src = `at://${ownerDid}/ai.gftd.apps.domain.tld/${tldKey}`;
  const dst = `at://${ownerDid}/ai.gftd.apps.domain.legalRegulator/${e.regulatorSlug}`;
  await sql`
    INSERT INTO edge_domain_tld_accepts_regulator (edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, tld, regulator_slug, basis, created_at, org_id, user_id, actor_id)
    SELECT ${eid}, ${ownerDid}, 0, ${src}, ${dst}, ${e.tld}, ${e.regulatorSlug}, ${e.basis}, ${createdAt}, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM edge_domain_tld_accepts_regulator WHERE edge_id = ${eid})
  `.execute(db);
}

async function insertProcessDef(db: Kysely<unknown>, s: P): Promise<void> {
  const xml = readContract(s.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${s.vertexId}, ${s.ownerDid}, ${s.bpmnProcessId}, 1, ${xml}, CAST(${size} AS integer), ${s.sourcePath}, 'active', ${createdAt}, 1, ${s.ownerDid}, ${s.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId})
  `.execute(db);
}

async function insertBinding(db: Kysely<unknown>, s: B): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${s.vertexId}, ${s.ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1, CAST(${s.resultTimeoutMs} AS integer), 'active', ${createdAt}, 1, ${s.ownerDid}, ${s.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.vertexId})
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const t of tldSeeds) await insertTld(db, t);
  for (const r of registrarSeeds) await insertRegistrar(db, r);
  for (const r of regulatorSeeds) await insertRegulator(db, r);
  for (const a of adviceSeeds) await insertAdvice(db, a);
  for (const e of supportEdges) await insertSupportEdge(db, e);
  for (const e of acceptEdges) await insertAcceptEdge(db, e);
  for (const s of processSeeds) await insertProcessDef(db, s);
  for (const s of bindingSeeds) await insertBinding(db, s);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of bindingSeeds)
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.vertexId}`.execute(db);
  for (const s of processSeeds)
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId}`.execute(db);
  await sql`DELETE FROM edge_domain_tld_accepts_regulator WHERE owner_did = ${ownerDid}`.execute(db);
  await sql`DELETE FROM edge_domain_registrar_supports_tld WHERE owner_did = ${ownerDid}`.execute(db);
  await sql`DELETE FROM vertex_domain_eligibility_advice WHERE owner_did = ${ownerDid}`.execute(db);
  await sql`DELETE FROM vertex_domain_legal_regulator WHERE owner_did = ${ownerDid}`.execute(db);
  await sql`DELETE FROM vertex_domain_registrar WHERE owner_did = ${ownerDid}`.execute(db);
  await sql`DELETE FROM vertex_domain_tld WHERE owner_did = ${ownerDid}`.execute(db);
}
