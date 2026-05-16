import { Kysely, sql } from 'kysely';

/**
 * Migration 20260427210000 — icon column + yoro /apps registry backfill
 *
 * 1. ADD COLUMN icon VARCHAR to vertex_app
 * 2. INSERT 74 platform app entries from apps.ts into vertex_app
 *    owner_did = did:web:yoro.gftd.ai so listApps can scope by owner
 *
 * RisingWave PK implicit upsert: same vertex_id re-INSERT = overwrite.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await db.executeQuery(
    sql`ALTER TABLE "vertex_app" ADD COLUMN IF NOT EXISTS "icon" VARCHAR`.compile(db)
  );

  // Helper to build a canonical vertex_id for a yoro app registration
  const vid = (id: string) =>
    `at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/${id}`;

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
  const OWNER = 'did:web:yoro.gftd.ai';
  const COL = 'ai.gftd.apps.yoro.appRegistry';
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
    row('gftd', 'GFTD', '🌐', 'Orgs', 'https://gftd.ai', 'gftd.ai', 'GFTD portal'),

    // ── Security ──
    row('kiyome', 'Kiyome', '🔍', 'Services', 'https://smishing.gftd.ai', 'smishing.gftd.ai:actor:kiyome', 'SMS phishing analysis & threat intelligence'),
    row('harai', 'Harai', '🚫', 'Services', 'https://smishing.gftd.ai', 'smishing.gftd.ai:actor:harai', 'Smishing enforcement & takedown coordinator'),

    // ── Services ──
    row('news', 'News', '📰', 'Services', 'https://news.gftd.ai', 'news.gftd.ai', 'AI-driven news portal'),
    row('search', 'Search', '🔎', 'Services', 'https://search.gftd.ai', 'search.gftd.ai', 'Unified search and discovery'),
    row('6ir', '6IR', '🧠', 'Services', 'https://6ir.gftd.ai', '6ir.gftd.ai', '6IR analytics'),
    row('maps', 'Maps', '🗺️', 'Services', 'https://maps.gftd.ai', 'maps.gftd.ai', 'Spatial maps and geolocation'),
    row('kareyanagi', 'Kareyanagi', '🦠', 'Services', 'https://kareyanagi.gftd.ai', 'kareyanagi.gftd.ai', 'Mold eradication platform with IoT sensors and maps integration'),
    row('drive', 'Drive', '📁', 'Services', 'https://drive.gftd.ai', 'drive.gftd.ai', 'Cloud storage'),
    row('organizer', 'Organizer', '🗂️', 'Services', 'https://organizer.gftd.ai', 'organizer.gftd.ai', 'Upload anything — AI auto-classifies, tags, and organizes'),
    row('sheets', 'Sheets', '📊', 'Services', 'https://sheets.gftd.ai', 'sheets.gftd.ai', 'Spreadsheets'),
    row('docs', 'Docs', '📝', 'Services', 'https://docs.gftd.ai', 'docs.gftd.ai', 'Documentation'),
    row('mailer', 'Mailer', '📧', 'Services', 'https://mailer.gftd.ai', 'mailer.gftd.ai', 'Email client'),
    row('gmail', 'Gmail', '✉️', 'Services', 'https://gmail.gftd.ai', 'gmail.gftd.ai', 'Gmail sync + AI triage + contact DID messenger bridge'),
    row('outlook', 'Outlook', '📬', 'Services', 'https://outlook.gftd.ai', 'outlook.gftd.ai', 'Outlook sync + calendar + contact DID bridge'),
    row('oshikatsu', 'Oshikatsu', '🍚', 'Services', 'https://oshikatsu.gftd.ai', 'oshikatsu.gftd.ai', 'Career support'),
    row('oshinobi', 'Oshinobi', '🥷', 'Services', 'https://oshinobi.gftd.ai', 'oshinobi.gftd.ai', 'Creator subscription platform (tiers, tips, posts)'),
    row('calendar', 'Calendar', '📅', 'Services', 'https://calendar.gftd.ai', 'calendar.gftd.ai', 'Calendar'),
    row('forms', 'Forms', '📋', 'Services', 'https://forms.gftd.ai', 'forms.gftd.ai', 'Forms builder'),
    row('threads', 'Matrix', '💬', 'Services', 'https://gftd.ai', 'gftd.ai', 'Matrix messaging'),
    row('hub', 'Hub', '🏠', 'Services', 'https://hub.gftd.ai', 'hub.gftd.ai', 'Git-compatible project hub'),
    row('translate', 'Translate', '🌍', 'Services', 'https://translate.gftd.ai', 'translate.gftd.ai', 'Translation service'),
    row('images', 'Images', '🖼️', 'Services', 'https://images.gftd.ai', 'images.gftd.ai', 'Image processing'),
    row('videos', 'Videos', '🎬', 'Services', 'https://douga.gftd.ai', 'douga.gftd.ai', 'Video platform'),
    row('videos-legacy', 'Videos2', '🎥', 'Services', 'https://videos.gftd.ai', 'videos.gftd.ai', 'Video platform'),
    row('music', 'Music', '🎵', 'Services', 'https://music.gftd.ai', 'music.gftd.ai', 'Music streaming'),
    row('manga', 'Manga', '📚', 'Services', 'https://manga.gftd.ai', 'manga.gftd.ai', 'Manga reader'),
    row('anime', 'Anime', '🎞️', 'Services', 'https://anime.gftd.ai', 'anime.gftd.ai', 'Anime platform'),
    row('games', 'Games', '🎮', 'Services', 'https://games.gftd.ai', 'games.gftd.ai', 'Games'),
    row('narou', 'Narou', '📖', 'Services', 'https://narou.gftd.ai', 'narou.gftd.ai', 'Novel platform'),
    row('cards', 'Cards', '💳', 'Services', 'https://cards.gftd.ai', 'cards.gftd.ai', 'Stripe Issuing cards'),
    row('tenki', 'Tenki', '🌤️', 'Services', 'https://tenki.gftd.ai', 'tenki.gftd.ai', 'Weather'),
    row('yadoya', 'Yadoya', '🏨', 'Services', 'https://yadoya.gftd.ai', 'yadoya.gftd.ai', 'Lodging and stays'),
    row('fleamarket', 'FleaMarket', '🛍️', 'Services', 'https://fleamarket.gftd.ai', 'fleamarket.gftd.ai', 'Marketplace'),
    row('okaimono', 'Shopping', '🛒', 'Services', 'https://okaimono.gftd.ai', 'okaimono.gftd.ai', 'Shopping'),
    row('briefing', 'Briefing', '📑', 'Services', 'https://briefing.gftd.ai', 'briefing.gftd.ai', 'Content briefing'),
    row('tsukuru', 'Tsukuru', '🏭', 'Services', 'https://tsukuru.gftd.ai', 'tsukuru.gftd.ai', 'Factory-direct ordering platform'),
    row('cowork', 'Cowork', '👥', 'Services', 'https://cowork.gftd.ai', 'cowork.gftd.ai', 'Co-working'),
    row('shigotoba', 'Shigotoba', '💼', 'Services', 'https://shigotoba.gftd.ai', 'shigotoba.gftd.ai', 'Job board'),
    row('scheduler', 'Scheduler', '⏰', 'Services', 'https://scheduler.gftd.ai', 'scheduler.gftd.ai', 'Scheduler and automation'),
    row('web4', 'Web4', '🔗', 'Services', 'https://web4.gftd.ai', 'web4.gftd.ai', 'Web4 / GCC token'),
    row('society6', 'Society6', '🏛️', 'Services', 'https://society6.gftd.ai', 'society6.gftd.ai', 'COFOG access and Society6 policy portal'),
    row('lawfirm', 'Law Firm', '⚖️', 'Services', 'https://lawfirm.gftd.ai', 'lawfirm.gftd.ai', 'Law firm client portal'),
    row('lawyer', 'Lawyer', '👨‍⚖️', 'Services', 'https://lawyer.gftd.ai', 'lawyer.gftd.ai', 'Lawyer workspace'),
    row('ekyc', 'eKYC', '🪪', 'Services', 'https://ekyc.gftd.ai', 'ekyc.gftd.ai', 'Identity verification'),
    row('shomeisyashin', 'ID Photo', '📸', 'Services', 'https://shomeisyashin.gftd.ai', 'shomeisyashin.gftd.ai', 'AI証明写真メーカー'),
    row('global', 'Global', '🌏', 'Services', 'https://global.gftd.ai', 'global.gftd.ai', 'Global services'),
    row('worlds', 'Worlds', '🌌', 'Services', 'https://worlds.gftd.ai', 'worlds.gftd.ai', 'Virtual worlds'),
    row('pachinko', 'Pachinko', '🎰', 'Services', 'https://pachinko.gftd.ai', 'pachinko.gftd.ai', 'Pachinko simulation'),
    row('casino', 'Casino', '🎲', 'Services', 'https://casino.gftd.ai', 'casino.gftd.ai', 'World casino directory'),
    row('oshiete', 'Oshiete', '❓', 'Services', 'https://oshiete.gftd.ai', 'oshiete.gftd.ai', 'Q&A platform'),
    row('webpage', 'Webpage', '🌐', 'Services', 'https://webpage.gftd.ai', 'webpage.gftd.ai', 'Web page crawl and text extraction'),
    row('marketer', 'Marketer', '📣', 'Services', 'https://marketer.gftd.ai', 'marketer.gftd.ai', 'Marketing tools'),
    row('omikuji', 'Omikuji', '🎋', 'Services', 'https://omikuji.gftd.ai', 'omikuji.gftd.ai', 'Fortune telling'),
    row('aima', 'AIMA', '🤖', 'Services', 'https://aima.gftd.ai', 'aima.gftd.ai', 'AI models'),
    row('robot', 'Robot', '🦾', 'Services', 'https://robot.gftd.ai', 'robot.gftd.ai', 'Robot automation'),
    row('wire', 'Wire', '📡', 'Services', 'https://wire.gftd.ai', 'wire.gftd.ai', 'Messaging'),
    row('lawfirm-admin', 'LF Admin', '🏛️', 'Services', 'https://lawfirm-admin.gftd.ai', 'lawfirm-admin.gftd.ai', 'Law firm admin'),

    // ── Systems ──
    row('performers', 'Performers', '🚀', 'Systems', 'https://gftd.ai', 'gftd.ai', 'Platform dashboard'),
    row('analytics', 'Analytics', '📈', 'Systems', 'https://analytics.gftd.ai', 'analytics.gftd.ai', 'Analytics dashboard'),
    row('ops', 'Ops', '⚙️', 'Systems', 'https://ops.gftd.ai', 'ops.gftd.ai', 'Project operations'),
    row('sre', 'SRE', '🔧', 'Systems', 'https://sre.gftd.ai', 'sre.gftd.ai', 'Site reliability'),
    row('os', 'OS', '🖥️', 'Systems', 'https://os.gftd.ai', 'os.gftd.ai', 'Operating system UI'),
    row('po', 'PO', '📐', 'Systems', 'https://po.gftd.ai', 'po.gftd.ai', 'Projection operator'),
    row('gov', 'Gov', '🏢', 'Systems', 'https://gov.gftd.ai', 'gov.gftd.ai', 'Governance'),
    row('resources', 'Resources', '🗄️', 'Systems', 'https://resources.gftd.ai', 'resources.gftd.ai', 'JSON-LD/RDF resources'),
    row('completer', 'Completer', '✏️', 'Systems', 'https://completer.gftd.ai', 'completer.gftd.ai', 'Code completion'),
    row('har', 'HAR', '🗂️', 'Systems', 'https://har.gftd.ai', 'har.gftd.ai', 'HAR viewer'),
    row('provider-pod', 'Provider', '📦', 'Systems', 'https://provider-pod.gftd.ai', 'provider-pod.gftd.ai', 'Provider pod marketplace'),
    row('ge', 'GE', '🎓', 'Systems', 'https://ge.gftd.ai', 'ge.gftd.ai', 'General education'),
    row('lo', 'LO', '🧩', 'Systems', 'https://lo.gftd.ai', 'lo.gftd.ai', 'Learning objects'),
    row('tia', 'TIA', '🎙️', 'Systems', 'https://tia.gftd.ai', 'tia.gftd.ai', 'TIA assistant'),
    row('wvme', 'WVME', '🎛️', 'Systems', 'https://wvme.gftd.ai', 'wvme.gftd.ai', 'WVME platform'),
    row('tasklist', 'TaskList', '✅', 'Systems', 'https://tasklist.gftd.ai', 'tasklist.gftd.ai', 'Task approval'),
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
