/**
 * business-person actor seed — registers actor profile, app, tools,
 * and initial graph schema into the PDS via XRPC.
 *
 * Usage: npx tsx 60-apps/etzhayyim-project-business-person/seed.ts
 */

const PDS = 'https://atproto.etzhayyim.com';
const NANOID = 'bp3r5n0x';
const ROOT_DID = `did:web:business-person.etzhayyim.com`;
const PROJECT_ID = 'business-person';

// ── Helpers ──

// ADR-0023 P4: use etzhayyim_TOKEN (sk_live_*) Bearer instead of spoofable
// x-kotodama-verified header. Required: `export etzhayyim_TOKEN=$(etzhayyim auth token)`.
const etzhayyim_TOKEN = process.env.etzhayyim_TOKEN;
if (!etzhayyim_TOKEN) {
  throw new Error('etzhayyim_TOKEN env var required — run `export etzhayyim_TOKEN=$(etzhayyim auth token)` first');
}
const INTERNAL_HEADERS = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${etzhayyim_TOKEN}`,
  'x-etzhayyim-org-id': 'anon',
};

async function actorCreate(did: string, displayName: string, description: string): Promise<void> {
  const res = await fetch(`${PDS}/xrpc/com.etzhayyim.actor.create`, {
    method: 'POST',
    headers: INTERNAL_HEADERS,
    body: JSON.stringify({ did, projectId: PROJECT_ID, displayName, description, hasWorker: false }),
  });
  if (!res.ok) console.warn(`actor.create ${did}: ${res.status} ${await res.text()}`);
  else console.log(`✓ Actor: ${did}`);
}

async function registerApp(body: Record<string, unknown>): Promise<void> {
  const res = await fetch(`${PDS}/_internal/register`, {
    method: 'POST',
    headers: INTERNAL_HEADERS,
    body: JSON.stringify(body),
  });
  if (!res.ok) console.warn(`registerApp ${body.nanoid}: ${res.status} ${await res.text()}`);
  else console.log(`✓ RegisterApp: ${body.did}`);
}

async function toolRegister(tool: Record<string, unknown>): Promise<void> {
  const res = await fetch(`${PDS}/xrpc/com.etzhayyim.tool.register`, {
    method: 'POST',
    headers: INTERNAL_HEADERS,
    body: JSON.stringify(tool),
  });
  if (!res.ok) console.warn(`tool.register ${tool.name}: ${res.status}`);
  else console.log(`✓ Tool: ${tool.name}`);
}

async function createRecord(collection: string, record: Record<string, unknown>): Promise<void> {
  const res = await fetch(`${PDS}/xrpc/com.atproto.repo.createRecord`, {
    method: 'POST',
    headers: INTERNAL_HEADERS,
    body: JSON.stringify({ repo: ROOT_DID, collection, record }),
  });
  if (!res.ok) console.warn(`createRecord ${collection}: ${res.status}`);
}

async function socialPost(did: string, text: string): Promise<void> {
  const res = await fetch(`${PDS}/xrpc/com.atproto.repo.createRecord`, {
    method: 'POST',
    headers: INTERNAL_HEADERS,
    body: JSON.stringify({
      repo: did, collection: 'app.bsky.feed.post',
      record: { text, createdAt: new Date().toISOString(), '$type': 'app.bsky.feed.post' },
    }),
  });
  if (!res.ok) console.warn(`post: ${res.status}`);
}

// ══════════════════════════════════════════════════════════════════
// 1. ACTOR DIDs
// ══════════════════════════════════════════════════════════════════

const ACTORS = [
  { did: ROOT_DID, name: 'Business Person', desc: 'Public organizational business person intelligence coordinator' },
  { did: `${ROOT_DID}:registry:edinet`, name: 'EDINET Registry', desc: 'Japan FSA EDINET corporate officer filings' },
  { did: `${ROOT_DID}:registry:gbizinfo`, name: 'gBizINFO Registry', desc: 'Japan gBizINFO corporate registry' },
  { did: `${ROOT_DID}:registry:edgar`, name: 'SEC EDGAR Registry', desc: 'US SEC EDGAR corporate officer filings (DEF 14A, 10-K)' },
  { did: `${ROOT_DID}:role:officer`, name: 'Officer Tracker', desc: 'Corporate officer role tracking and change detection' },
  { did: `${ROOT_DID}:role:board`, name: 'Board Tracker', desc: 'Board membership and director tracking' },
  { did: `${ROOT_DID}:graph:affiliation`, name: 'Affiliation Graph', desc: 'Cross-organization affiliation network analysis' },
];

// ══════════════════════════════════════════════════════════════════
// 2. REGISTRY SOURCES
// ══════════════════════════════════════════════════════════════════

const REGISTRY_SOURCES = [
  { registryType: 'edinet', name: 'EDINET', country: 'jpn', url: 'https://disclosure2.edinet-fsa.go.jp/', description: 'Japan FSA Electronic Disclosure for Investors NETwork. Yuho (annual securities reports) contain officer lists.', filingTypes: 'yuho,kabuho,taisho' },
  { registryType: 'gbizinfo', name: 'gBizINFO', country: 'jpn', url: 'https://info.gbiz.go.jp/', description: 'Japan corporate number + basic corporate info API. Officers from Touki-bo (corporate registry).', filingTypes: 'houjin,yakuin' },
  { registryType: 'edgar', name: 'SEC EDGAR', country: 'usa', url: 'https://www.sec.gov/cgi-bin/browse-edgar', description: 'US SEC Electronic Data Gathering, Analysis, and Retrieval. DEF 14A (proxy), 10-K (annual) contain officer/director lists.', filingTypes: 'DEF14A,10-K,8-K' },
  { registryType: 'companies-house', name: 'Companies House', country: 'gbr', url: 'https://find-and-update.company-information.service.gov.uk/', description: 'UK company registry. Director and secretary appointments.', filingTypes: 'AP01,TM01,CH01' },
  { registryType: 'handelsregister', name: 'Handelsregister', country: 'deu', url: 'https://www.handelsregister.de/', description: 'German commercial register. Geschaeftsfuehrer and Vorstand listings.', filingTypes: 'HRA,HRB' },
];

// ══════════════════════════════════════════════════════════════════
// 3. OFFICER ROLE TYPES
// ══════════════════════════════════════════════════════════════════

const ROLE_TYPES = [
  { code: 'ceo', nameEn: 'Chief Executive Officer', nameJa: '代表取締役社長', level: 'c-suite' },
  { code: 'cfo', nameEn: 'Chief Financial Officer', nameJa: '最高財務責任者', level: 'c-suite' },
  { code: 'cto', nameEn: 'Chief Technology Officer', nameJa: '最高技術責任者', level: 'c-suite' },
  { code: 'coo', nameEn: 'Chief Operating Officer', nameJa: '最高執行責任者', level: 'c-suite' },
  { code: 'ciso', nameEn: 'Chief Information Security Officer', nameJa: '最高情報セキュリティ責任者', level: 'c-suite' },
  { code: 'clo', nameEn: 'Chief Legal Officer', nameJa: '最高法務責任者', level: 'c-suite' },
  { code: 'director', nameEn: 'Director', nameJa: '取締役', level: 'board' },
  { code: 'outside-director', nameEn: 'Outside Director', nameJa: '社外取締役', level: 'board' },
  { code: 'auditor', nameEn: 'Statutory Auditor', nameJa: '監査役', level: 'board' },
  { code: 'outside-auditor', nameEn: 'Outside Statutory Auditor', nameJa: '社外監査役', level: 'board' },
  { code: 'chairman', nameEn: 'Chairman of the Board', nameJa: '取締役会長', level: 'board' },
  { code: 'managing-director', nameEn: 'Managing Director', nameJa: '常務取締役', level: 'executive' },
  { code: 'senior-managing-director', nameEn: 'Senior Managing Director', nameJa: '専務取締役', level: 'executive' },
  { code: 'executive-officer', nameEn: 'Executive Officer', nameJa: '執行役員', level: 'executive' },
  { code: 'registered-agent', nameEn: 'Registered Agent', nameJa: '届出代理人', level: 'statutory' },
  { code: 'company-secretary', nameEn: 'Company Secretary', nameJa: '会社秘書役', level: 'statutory' },
];

// ══════════════════════════════════════════════════════════════════
// TOOLS
// ══════════════════════════════════════════════════════════════════

const TOOLS = [
  { name: 'searchPersons', description: 'Search business persons by name, organization, or role', inputSchema: '{"type":"object","properties":{"query":{"type":"string"},"registryType":{"type":"string"},"roleCode":{"type":"string"},"limit":{"type":"number"}}}' },
  { name: 'getPersonProfile', description: 'Get full profile of a business person with all roles and board memberships', inputSchema: '{"type":"object","properties":{"personId":{"type":"string"}},"required":["personId"]}' },
  { name: 'createPerson', description: 'Register a publicly disclosed business person from official filings', inputSchema: '{"type":"object","properties":{"personId":{"type":"string"},"displayName":{"type":"string"},"source":{"type":"string"},"sourceUrl":{"type":"string"},"registryType":{"type":"string"}},"required":["personId","displayName","source","sourceUrl"]}' },
  { name: 'createOfficerRole', description: 'Register an officer role linking a person to an organization', inputSchema: '{"type":"object","properties":{"personId":{"type":"string"},"registryId":{"type":"string"},"title":{"type":"string"},"since":{"type":"string"},"until":{"type":"string"},"source":{"type":"string"}},"required":["personId","registryId","title","source"]}' },
  { name: 'detectPersonnelChanges', description: 'Detect officer/director changes from recent filings', inputSchema: '{"type":"object","properties":{"registryType":{"type":"string"},"since":{"type":"string"}}}' },
  { name: 'getAffiliationNetwork', description: 'Get cross-organization affiliation network for a person', inputSchema: '{"type":"object","properties":{"personId":{"type":"string"},"depth":{"type":"number"}},"required":["personId"]}' },
];

// ══════════════════════════════════════════════════════════════════
// MAIN
// ══════════════════════════════════════════════════════════════════

async function main(): Promise<void> {
  console.log('=== Business Person Actor Seed ===\n');

  // 1. Actors
  console.log(`── 1. Registering ${ACTORS.length} Actor DIDs ──`);
  for (const a of ACTORS) {
    await actorCreate(a.did, a.name, a.desc);
  }

  // 2. Register App Profile
  console.log('\n── 2. Register App Profile + App ──');
  await registerApp({
    nanoid: NANOID,
    did: ROOT_DID,
    displayName: 'Business Person -- Public Organizational Contact Intelligence',
    description: 'Aggregates publicly disclosed business person information: corporate officers, board members, registered agents, key personnel from EDINET, gBizINFO, SEC EDGAR, and official directories. Public filings only.',
    performerType: 'service',
    contentMode: 'timeline',
    sensitivity: 'public',
    uiType: 'yoro',
    capabilities: [
      'corporate-officer-lookup',
      'board-member-tracking',
      'registered-agent-search',
      'personnel-change-detection',
      'org-chart-graph',
      'cross-org-affiliation',
    ],
    governance: {
      classification: 'public',
      raci: 'responsible',
      complianceFrameworks: ['APPI', 'GDPR-public-interest'],
      deps: [
        { to: 'did:web:business-manager.etzhayyim.com', type: 'data', sourceKind: 'graph', collection: 'com.etzhayyim.apps.businessManager.employee' },
      ],
    },
    icon: '',
    accent: '#2c3e50',
    convoSystemPrompt: 'You are the Business Person agent -- public organizational contact intelligence. You aggregate and search publicly disclosed business person information: corporate officers, board members, registered agents, and key personnel from official registries (EDINET, gBizINFO, SEC EDGAR), press releases, and public directories. You ONLY use publicly available data from official filings and disclosures. Never infer or fabricate private contact information. Respond helpfully in the user\'s language.',
  });

  // 3. Register Tools
  console.log('\n── 3. Register Tools ──');
  for (const t of TOOLS) {
    await toolRegister({ ...t, capabilityWorker: NANOID });
  }

  // 4. Seed Registry Sources
  console.log(`\n── 4. Registry Sources (${REGISTRY_SOURCES.length}) ──`);
  for (const src of REGISTRY_SOURCES) {
    await createRecord('com.etzhayyim.apps.businessPerson.registrySource', {
      ...src,
      ownerDid: ROOT_DID,
    });
  }
  console.log(`  ✓ ${REGISTRY_SOURCES.length} registry sources`);

  // 5. Seed Role Types
  console.log(`\n── 5. Role Types (${ROLE_TYPES.length}) ──`);
  for (const role of ROLE_TYPES) {
    await createRecord('com.etzhayyim.apps.businessPerson.roleType', {
      ...role,
      ownerDid: ROOT_DID,
    });
  }
  console.log(`  ✓ ${ROLE_TYPES.length} role types`);

  // 6. Corporate HP Collection Jobs (1次ソース: 企業公式HP + site.etzhayyim.com JS rendering + Murakumo LLM)
  console.log('\n── 6. Corporate HP Collection Jobs (Primary Source) ──');
  const HP_JOBS = [
    // ── US (S&P 500 top) ── corporate leadership/officer pages
    { id: 'bp-hp-apple', sourceUrl: 'https://www.apple.com/leadership/', format: 'corporateHp', country: 'usa', title: 'Apple Inc.' },
    { id: 'bp-hp-msft', sourceUrl: 'https://www.microsoft.com/en-us/about/leadership', format: 'corporateHp', country: 'usa', title: 'Microsoft' },
    { id: 'bp-hp-alphabet', sourceUrl: 'https://abc.xyz/investor/', format: 'corporateHp', country: 'usa', title: 'Alphabet Inc.' },
    { id: 'bp-hp-amazon', sourceUrl: 'https://www.aboutamazon.com/about-us/leadership-team', format: 'corporateHp', country: 'usa', title: 'Amazon' },
    { id: 'bp-hp-nvidia', sourceUrl: 'https://www.nvidia.com/en-us/about-nvidia/board-of-directors/', format: 'corporateHp', country: 'usa', title: 'NVIDIA' },
    { id: 'bp-hp-meta', sourceUrl: 'https://investor.fb.com/leadership-and-governance/default.aspx', format: 'corporateHp', country: 'usa', title: 'Meta Platforms' },
    { id: 'bp-hp-tesla', sourceUrl: 'https://ir.tesla.com/corporate-governance/board-of-directors', format: 'corporateHp', country: 'usa', title: 'Tesla' },
    { id: 'bp-hp-jpm', sourceUrl: 'https://www.jpmorganchase.com/about/our-leadership', format: 'corporateHp', country: 'usa', title: 'JPMorgan Chase' },
    { id: 'bp-hp-visa', sourceUrl: 'https://usa.visa.com/about-visa/visa-inc/executive-leadership.html', format: 'corporateHp', country: 'usa', title: 'Visa Inc.' },
    { id: 'bp-hp-jnj', sourceUrl: 'https://www.jnj.com/leadership', format: 'corporateHp', country: 'usa', title: 'Johnson & Johnson' },
    // ── UK (FTSE 100) ──
    { id: 'bp-hp-shell', sourceUrl: 'https://www.shell.com/about-us/leadership.html', format: 'corporateHp', country: 'gbr', title: 'Shell plc' },
    { id: 'bp-hp-hsbc', sourceUrl: 'https://www.hsbc.com/who-we-are/leadership', format: 'corporateHp', country: 'gbr', title: 'HSBC' },
    { id: 'bp-hp-bp', sourceUrl: 'https://www.bp.com/en/global/corporate/who-we-are/board-and-executive-management.html', format: 'corporateHp', country: 'gbr', title: 'BP' },
    { id: 'bp-hp-astrazeneca', sourceUrl: 'https://www.astrazeneca.com/our-company/leadership.html', format: 'corporateHp', country: 'gbr', title: 'AstraZeneca' },
    { id: 'bp-hp-unilever', sourceUrl: 'https://www.unilever.com/our-company/our-leadership/', format: 'corporateHp', country: 'gbr', title: 'Unilever' },
    // ── Japan (Nikkei 225 top) ──
    { id: 'bp-hp-toyota', sourceUrl: 'https://global.toyota/en/company/profile/executives/', format: 'corporateHp', country: 'jpn', title: 'Toyota Motor' },
    { id: 'bp-hp-sony', sourceUrl: 'https://www.sony.com/en/SonyInfo/CorporateInfo/officers.html', format: 'corporateHp', country: 'jpn', title: 'Sony Group' },
    { id: 'bp-hp-softbank', sourceUrl: 'https://group.softbank/en/about/officer', format: 'corporateHp', country: 'jpn', title: 'SoftBank Group' },
    { id: 'bp-hp-keyence', sourceUrl: 'https://www.keyence.co.jp/company/outline.jsp', format: 'corporateHp', country: 'jpn', title: 'Keyence' },
    { id: 'bp-hp-fastretailing', sourceUrl: 'https://www.fastretailing.com/eng/about/governance/directors.html', format: 'corporateHp', country: 'jpn', title: 'Fast Retailing' },
    // ── EU (DAX/CAC/AEX top) ──
    { id: 'bp-hp-sap', sourceUrl: 'https://www.sap.com/about/company/executive-board.html', format: 'corporateHp', country: 'deu', title: 'SAP SE' },
    { id: 'bp-hp-siemens', sourceUrl: 'https://www.siemens.com/global/en/company/about/management.html', format: 'corporateHp', country: 'deu', title: 'Siemens' },
    { id: 'bp-hp-lvmh', sourceUrl: 'https://www.lvmh.com/group/about-lvmh/governance/executive-committee/', format: 'corporateHp', country: 'fra', title: 'LVMH' },
    { id: 'bp-hp-nestle', sourceUrl: 'https://www.nestle.com/aboutus/management', format: 'corporateHp', country: 'che', title: 'Nestle' },
    { id: 'bp-hp-asml', sourceUrl: 'https://www.asml.com/en/company/governance/board-of-management', format: 'corporateHp', country: 'nld', title: 'ASML' },
    // ── Asia-Pacific ──
    { id: 'bp-hp-samsung', sourceUrl: 'https://www.samsung.com/global/ir/governance/board-of-directors/', format: 'corporateHp', country: 'kor', title: 'Samsung Electronics' },
    { id: 'bp-hp-tsmc', sourceUrl: 'https://www.tsmc.com/english/aboutTSMC/management_team', format: 'corporateHp', country: 'twn', title: 'TSMC' },
    { id: 'bp-hp-tencent', sourceUrl: 'https://www.tencent.com/en-us/leadership.html', format: 'corporateHp', country: 'chn', title: 'Tencent' },
    { id: 'bp-hp-reliance', sourceUrl: 'https://www.ril.com/about-us/board-of-directors', format: 'corporateHp', country: 'ind', title: 'Reliance Industries' },
    { id: 'bp-hp-bhp', sourceUrl: 'https://www.bhp.com/about/our-company/leadership', format: 'corporateHp', country: 'aus', title: 'BHP Group' },
  ];

  for (const job of HP_JOBS) {
    await createRecord('com.etzhayyim.apps.businessPerson.collectionJob', {
      ...job,
      status: 'pending',
      phase: 1,
      ownerDid: ROOT_DID,
    });
    console.log(`  ✓ HP: ${job.title} (${job.sourceUrl.slice(0, 50)}...)`);
  }
  console.log(`  Total: ${HP_JOBS.length} corporate HP jobs dispatched`);

  // 7. Announcement post
  console.log('\n── 7. Social Post ──');
  await socialPost(ROOT_DID, 'Business Person actor: dispatched 30 corporate HP collection jobs (1次ソース). site.etzhayyim.com JS rendering + Murakumo LLM officer extraction. US/UK/JP/EU/APAC. #etzhayyim #businessPerson');

  // Summary
  const total = ACTORS.length + 1 + TOOLS.length + REGISTRY_SOURCES.length + ROLE_TYPES.length + HP_JOBS.length + 1;
  console.log(`\n=== Done: ${total} records seeded (${HP_JOBS.length} corporate HP jobs dispatched) ===`);
}

main().catch(console.error);
