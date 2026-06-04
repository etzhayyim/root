import { Kysely, sql } from 'kysely';

/**
 * Migration 20260427210000 — icon column + yoro /apps registry backfill
 *
 * 1. ADD COLUMN icon VARCHAR to vertex_app
 * 2. INSERT 74 platform app entries from apps.ts into vertex_app
 *    owner_did = did:web:yoro.etzhayyim.com so listApps can scope by owner
 *
 * RisingWave PK implicit upsert: same vertex_id re-INSERT = overwrite.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await db.executeQuery(
    sql`ALTER TABLE "vertex_app" ADD COLUMN IF NOT EXISTS "icon" VARCHAR`.compile(db)
  );

  // Helper to build a canonical vertex_id for a yoro app registration
  const vid = (id: string) =>
    `at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/${id}`;

  type Row = {
    vertex_id: string;
    handle: string;
    display_name: string;
    description: string;
    icon: string;
    classification: string;
    embed_url: string;
    app_did: string;
    status: string;
    performer_type: string;
    sensitivity: string;
    sensitivity_ord: number;
    owner_did: string;
    collection: string;
    repo: string;
  };

  const svc = 'service';
  const sys = 'system';
  const org = 'organization';
  const OWNER = 'did:web:yoro.etzhayyim.com';
  const COL = 'com.etzhayyim.apps.yoro.appRegistry';
  const base = {
    status: 'active',
    sensitivity: 'public',
    sensitivity_ord: 0,
    owner_did: OWNER,
    collection: COL,
    repo: OWNER,
  };

  function row(
    id: string,
    shortName: string,
    icon: string,
    category: 'Services' | 'Systems' | 'Orgs',
    href: string,
    appName: string,
    description: string,
  ): Row {
    const performerType = category === 'Orgs' ? org : category === 'Systems' ? sys : svc;
    return {
      ...base,
      vertex_id: vid(id),
      handle: id,
      display_name: shortName,
      description,
      icon,
      classification: category,
      embed_url: href,
      app_did: `did:web:${appName}`,
      performer_type: performerType,
    };
  }

  const rows: Row[] = [
    // ── Orgs ──
    row('etzhayyim', 'etzhayyim', '🌐', 'Orgs', 'https://etzhayyim.com', 'etzhayyim.com', 'etzhayyim portal'),

    // ── Security ──
    row('kiyome', 'Kiyome', '🔍', 'Services', 'https://smishing.etzhayyim.com', 'smishing.etzhayyim.com:actor:kiyome', 'SMS phishing analysis & threat intelligence'),
    row('harai', 'Harai', '🚫', 'Services', 'https://smishing.etzhayyim.com', 'smishing.etzhayyim.com:actor:harai', 'Smishing enforcement & takedown coordinator'),

    // ── Services ──
    row('news', 'News', '📰', 'Services', 'https://news.etzhayyim.com', 'news.etzhayyim.com', 'AI-driven news portal'),
    row('search', 'Search', '🔎', 'Services', 'https://search.etzhayyim.com', 'search.etzhayyim.com', 'Unified search and discovery'),
    row('6ir', '6IR', '🧠', 'Services', 'https://6ir.etzhayyim.com', '6ir.etzhayyim.com', '6IR analytics'),
    row('maps', 'Maps', '🗺️', 'Services', 'https://maps.etzhayyim.com', 'maps.etzhayyim.com', 'Spatial maps and geolocation'),
    row('kareyanagi', 'Kareyanagi', '🦠', 'Services', 'https://kareyanagi.etzhayyim.com', 'kareyanagi.etzhayyim.com', 'Mold eradication platform with IoT sensors and maps integration'),
    row('drive', 'Drive', '📁', 'Services', 'https://drive.etzhayyim.com', 'drive.etzhayyim.com', 'Cloud storage'),
    row('organizer', 'Organizer', '🗂️', 'Services', 'https://organizer.etzhayyim.com', 'organizer.etzhayyim.com', 'Upload anything — AI auto-classifies, tags, and organizes'),
    row('sheets', 'Sheets', '📊', 'Services', 'https://sheets.etzhayyim.com', 'sheets.etzhayyim.com', 'Spreadsheets'),
    row('docs', 'Docs', '📝', 'Services', 'https://docs.etzhayyim.com', 'docs.etzhayyim.com', 'Documentation'),
    row('mailer', 'Mailer', '📧', 'Services', 'https://mailer.etzhayyim.com', 'mailer.etzhayyim.com', 'Email client'),
    row('gmail', 'Gmail', '✉️', 'Services', 'https://gmail.etzhayyim.com', 'gmail.etzhayyim.com', 'Gmail sync + AI triage + contact DID messenger bridge'),
    row('outlook', 'Outlook', '📬', 'Services', 'https://outlook.etzhayyim.com', 'outlook.etzhayyim.com', 'Outlook sync + calendar + contact DID bridge'),
    row('oshikatsu', 'Oshikatsu', '🍚', 'Services', 'https://oshikatsu.etzhayyim.com', 'oshikatsu.etzhayyim.com', 'Career support'),
    row('oshinobi', 'Oshinobi', '🥷', 'Services', 'https://oshinobi.etzhayyim.com', 'oshinobi.etzhayyim.com', 'Creator subscription platform (tiers, tips, posts)'),
    row('calendar', 'Calendar', '📅', 'Services', 'https://calendar.etzhayyim.com', 'calendar.etzhayyim.com', 'Calendar'),
    row('forms', 'Forms', '📋', 'Services', 'https://forms.etzhayyim.com', 'forms.etzhayyim.com', 'Forms builder'),
    row('threads', 'Matrix', '💬', 'Services', 'https://etzhayyim.com', 'etzhayyim.com', 'Matrix messaging'),
    row('hub', 'Hub', '🏠', 'Services', 'https://hub.etzhayyim.com', 'hub.etzhayyim.com', 'Git-compatible project hub'),
    row('translate', 'Translate', '🌍', 'Services', 'https://translate.etzhayyim.com', 'translate.etzhayyim.com', 'Translation service'),
    row('images', 'Images', '🖼️', 'Services', 'https://images.etzhayyim.com', 'images.etzhayyim.com', 'Image processing'),
    row('videos', 'Videos', '🎬', 'Services', 'https://douga.etzhayyim.com', 'douga.etzhayyim.com', 'Video platform'),
    row('videos-legacy', 'Videos2', '🎥', 'Services', 'https://videos.etzhayyim.com', 'videos.etzhayyim.com', 'Video platform'),
    row('music', 'Music', '🎵', 'Services', 'https://music.etzhayyim.com', 'music.etzhayyim.com', 'Music streaming'),
    row('manga', 'Manga', '📚', 'Services', 'https://manga.etzhayyim.com', 'manga.etzhayyim.com', 'Manga reader'),
    row('anime', 'Anime', '🎞️', 'Services', 'https://anime.etzhayyim.com', 'anime.etzhayyim.com', 'Anime platform'),
    row('games', 'Games', '🎮', 'Services', 'https://games.etzhayyim.com', 'games.etzhayyim.com', 'Games'),
    row('narou', 'Narou', '📖', 'Services', 'https://narou.etzhayyim.com', 'narou.etzhayyim.com', 'Novel platform'),
    row('cards', 'Cards', '💳', 'Services', 'https://cards.etzhayyim.com', 'cards.etzhayyim.com', 'Stripe Issuing cards'),
    row('tenki', 'Tenki', '🌤️', 'Services', 'https://tenki.etzhayyim.com', 'tenki.etzhayyim.com', 'Weather'),
    row('yadoya', 'Yadoya', '🏨', 'Services', 'https://yadoya.etzhayyim.com', 'yadoya.etzhayyim.com', 'Lodging and stays'),
    row('fleamarket', 'FleaMarket', '🛍️', 'Services', 'https://fleamarket.etzhayyim.com', 'fleamarket.etzhayyim.com', 'Marketplace'),
    row('okaimono', 'Shopping', '🛒', 'Services', 'https://okaimono.etzhayyim.com', 'okaimono.etzhayyim.com', 'Shopping'),
    row('briefing', 'Briefing', '📑', 'Services', 'https://briefing.etzhayyim.com', 'briefing.etzhayyim.com', 'Content briefing'),
    row('tsukuru', 'Tsukuru', '🏭', 'Services', 'https://tsukuru.etzhayyim.com', 'tsukuru.etzhayyim.com', 'Factory-direct ordering platform'),
    row('cowork', 'Cowork', '👥', 'Services', 'https://cowork.etzhayyim.com', 'cowork.etzhayyim.com', 'Co-working'),
    row('shigotoba', 'Shigotoba', '💼', 'Services', 'https://shigotoba.etzhayyim.com', 'shigotoba.etzhayyim.com', 'Job board'),
    row('scheduler', 'Scheduler', '⏰', 'Services', 'https://scheduler.etzhayyim.com', 'scheduler.etzhayyim.com', 'Scheduler and automation'),
    row('web4', 'Web4', '🔗', 'Services', 'https://web4.etzhayyim.com', 'web4.etzhayyim.com', 'Web4 / GCC token'),
    row('society6', 'Society6', '🏛️', 'Services', 'https://society6.etzhayyim.com', 'society6.etzhayyim.com', 'COFOG access and Society6 policy portal'),
    row('lawfirm', 'Law Firm', '⚖️', 'Services', 'https://lawfirm.etzhayyim.com', 'lawfirm.etzhayyim.com', 'Law firm client portal'),
    row('lawyer', 'Lawyer', '👨‍⚖️', 'Services', 'https://lawyer.etzhayyim.com', 'lawyer.etzhayyim.com', 'Lawyer workspace'),
    row('ekyc', 'eKYC', '🪪', 'Services', 'https://ekyc.etzhayyim.com', 'ekyc.etzhayyim.com', 'Identity verification'),
    row('shomeisyashin', 'ID Photo', '📸', 'Services', 'https://shomeisyashin.etzhayyim.com', 'shomeisyashin.etzhayyim.com', 'AI証明写真メーカー'),
    row('global', 'Global', '🌏', 'Services', 'https://global.etzhayyim.com', 'global.etzhayyim.com', 'Global services'),
    row('worlds', 'Worlds', '🌌', 'Services', 'https://worlds.etzhayyim.com', 'worlds.etzhayyim.com', 'Virtual worlds'),
    row('pachinko', 'Pachinko', '🎰', 'Services', 'https://pachinko.etzhayyim.com', 'pachinko.etzhayyim.com', 'Pachinko simulation'),
    row('casino', 'Casino', '🎲', 'Services', 'https://casino.etzhayyim.com', 'casino.etzhayyim.com', 'World casino directory'),
    row('oshiete', 'Oshiete', '❓', 'Services', 'https://oshiete.etzhayyim.com', 'oshiete.etzhayyim.com', 'Q&A platform'),
    row('webpage', 'Webpage', '🌐', 'Services', 'https://webpage.etzhayyim.com', 'webpage.etzhayyim.com', 'Web page crawl and text extraction'),
    row('marketer', 'Marketer', '📣', 'Services', 'https://marketer.etzhayyim.com', 'marketer.etzhayyim.com', 'Marketing tools'),
    row('omikuji', 'Omikuji', '🎋', 'Services', 'https://omikuji.etzhayyim.com', 'omikuji.etzhayyim.com', 'Fortune telling'),
    row('aima', 'AIMA', '🤖', 'Services', 'https://aima.etzhayyim.com', 'aima.etzhayyim.com', 'AI models'),
    row('robot', 'Robot', '🦾', 'Services', 'https://robot.etzhayyim.com', 'robot.etzhayyim.com', 'Robot automation'),
    row('wire', 'Wire', '📡', 'Services', 'https://wire.etzhayyim.com', 'wire.etzhayyim.com', 'Messaging'),
    row('lawfirm-admin', 'LF Admin', '🏛️', 'Services', 'https://lawfirm-admin.etzhayyim.com', 'lawfirm-admin.etzhayyim.com', 'Law firm admin'),

    // ── Systems ──
    row('performers', 'Performers', '🚀', 'Systems', 'https://etzhayyim.com', 'etzhayyim.com', 'Platform dashboard'),
    row('analytics', 'Analytics', '📈', 'Systems', 'https://analytics.etzhayyim.com', 'analytics.etzhayyim.com', 'Analytics dashboard'),
    row('ops', 'Ops', '⚙️', 'Systems', 'https://ops.etzhayyim.com', 'ops.etzhayyim.com', 'Project operations'),
    row('sre', 'SRE', '🔧', 'Systems', 'https://sre.etzhayyim.com', 'sre.etzhayyim.com', 'Site reliability'),
    row('os', 'OS', '🖥️', 'Systems', 'https://os.etzhayyim.com', 'os.etzhayyim.com', 'Operating system UI'),
    row('po', 'PO', '📐', 'Systems', 'https://po.etzhayyim.com', 'po.etzhayyim.com', 'Projection operator'),
    row('gov', 'Gov', '🏢', 'Systems', 'https://gov.etzhayyim.com', 'gov.etzhayyim.com', 'Governance'),
    row('resources', 'Resources', '🗄️', 'Systems', 'https://resources.etzhayyim.com', 'resources.etzhayyim.com', 'JSON-LD/RDF resources'),
    row('completer', 'Completer', '✏️', 'Systems', 'https://completer.etzhayyim.com', 'completer.etzhayyim.com', 'Code completion'),
    row('har', 'HAR', '🗂️', 'Systems', 'https://har.etzhayyim.com', 'har.etzhayyim.com', 'HAR viewer'),
    row('provider-pod', 'Provider', '📦', 'Systems', 'https://provider-pod.etzhayyim.com', 'provider-pod.etzhayyim.com', 'Provider pod marketplace'),
    row('ge', 'GE', '🎓', 'Systems', 'https://ge.etzhayyim.com', 'ge.etzhayyim.com', 'General education'),
    row('lo', 'LO', '🧩', 'Systems', 'https://lo.etzhayyim.com', 'lo.etzhayyim.com', 'Learning objects'),
    row('tia', 'TIA', '🎙️', 'Systems', 'https://tia.etzhayyim.com', 'tia.etzhayyim.com', 'TIA assistant'),
    row('wvme', 'WVME', '🎛️', 'Systems', 'https://wvme.etzhayyim.com', 'wvme.etzhayyim.com', 'WVME platform'),
    row('tasklist', 'TaskList', '✅', 'Systems', 'https://tasklist.etzhayyim.com', 'tasklist.etzhayyim.com', 'Task approval'),
  ];

  for (const r of rows) {
    await db.executeQuery(
      sql`
        INSERT INTO "vertex_app" (
          "vertex_id", "handle", "display_name", "description", "icon",
          "classification", "embed_url", "app_did", "status", "performer_type",
          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"
        ) VALUES (
          ${r.vertex_id}, ${r.handle}, ${r.display_name}, ${r.description}, ${r.icon},
          ${r.classification}, ${r.embed_url}, ${r.app_did}, ${r.status}, ${r.performer_type},
          ${r.sensitivity}, ${r.sensitivity_ord}, ${r.owner_did}, ${r.collection}, ${r.repo}
        )
      `.compile(db)
    );
  }
}

export async function down(_db: Kysely<any>): Promise<void> {
  // Forward-only.
}
