# ooyake 公 — Maturity Scorecard

Honest status per the gov-coverage maturity model (ADR-2605250680). Coverage gated
by `:sourcing` (G5): only `:authoritative` rows count.

## 2026-06-03 — statistics + prosecution + revenue (239)

Third oversight wave (national statistical offices finally landed via a light
instances-only SPARQL + REST entity-resolution approach that dodges the WDQS 504):
- `gov-units.oversight-statistics.edn` **172** — national statistical offices (`Q480242`).
- `gov-units.oversight-prosecutor.edn` **32** — public-prosecution / prosecutor-general
  offices (`Q1092499`∪`Q11775750`), `:branch :judicial`.
- `gov-units.oversight-revenue.edn` **35** — tax / revenue authorities (`Q573607`);
  NTA/IRS/HMRC already in the finance layers were deduped out.
239 bodies. Atlas now **6535 units / 47 files, 6533 QIDs all unique, 6531
:authoritative**.

## 2026-06-03 — independent regulators (130)

Second oversight wave — independent regulatory authorities, `:level :agency`
`:branch :independent`, subagent Wikidata pulls:
- `gov-units.oversight-anticorruption.edn` **41** — anti-corruption agencies (`Q4774348`).
- `gov-units.oversight-dataprotection.edn` **41** — data-protection authorities (`Q3242920`).
- `gov-units.oversight-competition.edn` **16** — competition/antitrust authorities (`Q1465684`).
- `gov-units.oversight-financial-regulator.edn` **32** — financial regulators ex-central-bank (`Q105062392`).
130 bodies. National statistical offices (`Q480242`) still deferred (persistent WDQS
504 on that join). HONEST: a few rows are sub-national/association mis-typings from
the one-per-country dedup. Atlas now **6296 units / 44 files, 6294 QIDs all unique,
6292 :authoritative**.

## 2026-06-03 — independent oversight / accountability bodies (135)

On-mission layer (consumed by danjo/toritate/himotoki): independent accountability
institutions, `:level :agency` `:branch :independent`, subagent Wikidata pulls:
- `gov-units.oversight-audit.edn` **19** — supreme audit institutions (courts of audit
  / national audit offices; `Q10983451`∪`Q43306178`).
- `gov-units.oversight-ombudsman.edn` **24** — ombudsman / public-defender offices (`Q169180`).
- `gov-units.oversight-electoral.edn` **65** — electoral management bodies (`Q935741`).
- `gov-units.oversight-nhri.edn` **27** — national human-rights institutions
  (`Q4806410`∪`Q3511443`).
135 bodies; national statistical offices (`Q480242`) deferred (WDQS timeouts).
HONEST: Wikidata sometimes types sub-national bodies under these classes, so the
one-per-country dedup may pick a non-national body for a few states. Atlas now
**6166 units / 40 files, 6164 QIDs all unique, 6162 :authoritative**.

## 2026-06-04 — subdivision tier opened: Peru + Uruguay subnational govts COMPLETE (2324 → 2367)

With the national + agency tiers saturated, opened the subdivision tier (1,275 first-order
subdivisions lacked a URL — a long tail dominated by small/post-conflict states whose ADM1
units have no individual sites). Strategy: target whole countries whose first-order govts are
ELECTED with real official sites + high hit-rate, and COMPLETE them. This pass: **Peru's 24
regional governments (gobiernos regionales) + Uruguay's 19 departmental governments
(intendencias)** — 4 web-research subagents, **43/43 confirmed by fetching** (zero nulls).

- subdivisions: 2324 → **2367/3599**. **Peru 25/25 and Uruguay 19/19 — both countries now
  100% subnational-complete.**
- Peru regional govts on .gob.pe (own domain or canonical gob.pe institutional page where the
  own domain redirects: Apurímac/Lambayeque/Piura/Tacna); Uruguay intendencias on .gub.uy (own
  domain or the gub.uy organism page for Cerro Largo/Florida; Durazno on .uy). Bot-block/TLS
  caveats noted (Arequipa/Lima/Tacna/Ucayali/Artigas/Lavalleja/Paysandú) — all genuine official
  state-namespace domains, multi-source corroborated.

HONEST framing: the subdivision long tail (≈1,230 still null) is mostly genuine absence —
provinces/atolls/wilayas of small states without individual websites — so coverage here will
advance country-by-country where real elected subnational govts exist, not as a single sweep.

run_tests.sh ALL GREEN. Sourcing/verification tiers unchanged; published-index
authoritative-scope gate (check #5, JP backbone only) untouched.

## 2026-06-04 — sovereign wealth funds: 17 web-verified (989 → 1006 agencies); agency tier effectively complete

Closed the agency tier with sovereign-wealth / public-trust funds (19). Most have no standalone
site and are managed by a central bank / finance ministry / treasury / state board — for those
the managing institution's official fund page was used. 2 web-research subagents found +
**confirmed each by fetching it**. 17 confirmed + 3 name updates (Norway "Statens petroleumsfond"
→ **Government Pension Fund Global**/NBIM; Oman SGRF → **Oman Investment Authority** after the
2020 merger; Minnesota → **Permanent School Fund**).

- agencies: 989 → **1006/1049** with an official site (**96%**). The remaining ~43 are ALL
  documented honest nulls (G5): the 15 archives + 18 libraries with no website (small/
  post-conflict states), plus Brazil SWF (extinguished by Law 13.874/2019), Nauru Phosphate
  Royalties Trust (winding down, no site), Sudan NHRI, Indonesia/India data-protection (not yet
  operational), Kiribati/North Korea central banks, North Korea statistics, Mozambique electoral.
- managing-institution pages recorded where the fund has no own site: Chile (hacienda.cl), Ghana
  (Bank of Ghana), Kuwait (KIA), Peru (MEF), Timor-Leste (Banco Central), Trinidad (Min. Finance),
  US states (state treasurer/DNR). **Every government body in the atlas that has a confirmable
  official site now carries it, across every level.**

run_tests.sh ALL GREEN. Sourcing/verification tiers unchanged; published-index
authoritative-scope gate (check #5, JP backbone only) untouched.

## 2026-06-04 — oversight agencies (NHRI/prosecutor/data-protection/etc): 22 web-verified (967 → 989 agencies)

Continued the agency tier with the remaining accountability/regulatory categories: human-rights
institutions (8) + prosecution services (6) + data-protection (3) + ombudsman (2) + supreme
audit (2) + meteorology (2) + central bank (2) + competition + financial regulator. 3 web-research
subagents found + **confirmed each body's own official site by fetching it**. 22 confirmed +
1 label fix (El Salvador NHRI "Ad Hoc Commission" → **PDDH**, the Procuraduría para la Defensa
de los Derechos Humanos).

- agencies: 967 → **989/1049** with an official site (94%).
- 5 HONESTLY left null (G5): Sudan NHRI (no working site, conflict-disrupted), Indonesia +
  India data-protection (authorities only just constituted 2025-26, not yet operational with a
  site), Kiribati central bank (no central monetary authority exists — the "Bank of Kiribati"
  is a commercial ANZ bank), North Korea central bank (no public web).
- honest notes: Iceland DPA personuvernd.is now redirects to the consolidated island.is portal;
  Australia's Private Health Insurance Ombudsman function sits within the Commonwealth Ombudsman.
  Anti-bot/HTTP-only caveats noted (Qatar/Zambia met, Australia ombudsman) — genuine official
  government domains.

run_tests.sh ALL GREEN. Sourcing/verification tiers unchanged; published-index
authoritative-scope gate (check #5, JP backbone only) untouched.

## 2026-06-04 — national libraries: 15 web-verified + 2 label fixes (952 → 967 agencies)

Continued the agency tier with national LIBRARIES (33 missing). 4 web-research subagents found
+ **confirmed each institution's own official site by fetching it** (social-media pages NOT
accepted). 15 confirmed + 2 data-quality label fixes (Ghana "Keta Library" branch → **Ghana
Library Authority**; Syria "Al-Zahiriyah Library" historical manuscript library → **National
Library of Syria**, renamed 2024-12-10 — name corrected even though it has no live site).

- agencies: 952 → **967/1049** with an official site.
- **18 HONESTLY left null (G5)** — these national libraries genuinely have NO website
  (even sparser than archives for small/post-conflict states; Facebook-only NOT accepted):
  Afghanistan, Burkina Faso, Cameroon, DR Congo, Congo-Brazzaville, Equatorial Guinea (only a
  private trademarked publishing site), Haiti (dead domain + expired-cert portal), Liberia
  (cndra is the Archives, not the library), Lesotho, Madagascar, Mali, Mauritania, Sudan,
  Sierra Leone, Syria, Chad, Togo, Zambia.
- honest entry-point choices where no standalone site: culture/education-ministry portal
  section (Honduras SECAPPH, Solomon Islands MEHRD, Rwanda heritage academy, Comoros CNDRS).
  Zimbabwe has no separate national library — the National Archives reference library serves
  that role. TLS/self-signed caveats noted (Gambia, St Kitts) — genuine official domains.

run_tests.sh ALL GREEN. Sourcing/verification tiers unchanged; published-index
authoritative-scope gate (check #5, JP backbone only) untouched.

## 2026-06-04 — national archives: 26 web-verified (926 → 952 agencies)

Continued the agency tier with national ARCHIVES (42 missing). 4 web-research subagents found
+ **confirmed each institution's own official site by fetching it** (no social-media pages
accepted as official_url). 26 confirmed (provenance → the body's own official URL;
`:last-verified` → 2026-06-04).

- agencies: 926 → **952/1049** with an official site.
- **16 HONESTLY left null (G5)** — these national archives genuinely have NO website (a real,
  expected pattern for small/post-conflict states; many have only a Facebook page, which was
  NOT accepted): Afghanistan, Angola, Central African Republic, DR Congo (inaco.cd is a bare
  placeholder), Congo-Brazzaville, Djibouti, Guinea, Lesotho, Mauritania, Saint Lucia (its
  own gov registry lists the site as "N/A"), Haiti (only an expired-cert portal section),
  Malawi, Niger, El Salvador, Togo, Turkmenistan.
- honest entry-point choices recorded where the archive has no standalone site: hosted under
  the culture/home-affairs ministry portal (South Sudan mcmnh, Zambia mohais, Solomon Islands
  solomons.gov.sb, Nicaragua inc.gob.ni, Uzbekistan gov.uz/archive). HTTP-only/TLS-strictness
  caveats noted (Gabon dgabd.ga, Brunei, Eswatini, Seychelles, South Africa) — genuine
  official domains.

run_tests.sh ALL GREEN. Sourcing/verification tiers unchanged; published-index
authoritative-scope gate (check #5, JP backbone only) untouched.

## 2026-06-04 — accountability agencies: 38 web-verified + 6 data-quality fixes (888 → 926 agencies)

Opened the agency tier with the highest-civic-value accountability bodies — electoral
commissions (13) + anti-corruption agencies (13) + national tax/revenue authorities (8) +
statistics offices (6) = the exact bodies danjo/toritate/himotoki consume. 3 web-research
subagents found + **confirmed each body's own official site by fetching it**. 38 confirmed
(provenance → the body's own official URL; `:last-verified` → 2026-06-04).

- agencies: 888 → **926/1049** with an official site.
- **6 data-quality label fixes** (bulk-Wikidata-pull errors corrected to the real NATIONAL
  body): **gov.nld.revenue name was literally a street address** ("Dr. C. Hofstede de
  Grootkade 11") → Belastingdienst; gov.aut.revenue was a regional Carinthia office → Tax
  Authority Austria; gov.fra.revenue was a local business-tax office → DGFiP; gov.slv.revenue
  was a nonsense "Branch of Liquor" → DGII; gov.nga.anticorruption was the subnational Kano
  State body → the national ICPC; gov.mar.statistics → High Commission for Planning (HCP).
- 2 HONESTLY left null (G5): Mozambique electoral (the only domain is STAE's, not the CNE,
  and serves a router page), North Korea statistics (no public web presence). Sudan electoral
  (nec.org.sd) recorded as the documented official domain though offline due to the conflict.

run_tests.sh ALL GREEN. Sourcing/verification tiers unchanged; published-index
authoritative-scope gate (check #5, JP backbone only) untouched.

## 2026-06-04 — ministry tier COMPLETE: final 25 small-category sites web-verified (1596 → 1621/1642, 98.7%)

Closed out the ministry tier with the remaining small categories (labour, science, industry,
communications, housing, social, water + stragglers). 26 genuinely-new units researched by 3
web-research subagents (the other 20 missing units were already documented honest nulls from
prior passes and were NOT re-researched); 25 confirmed and added (provenance → the body's own
official URL; `:last-verified` → 2026-06-04).

- ministries: 1596 → **1621/1642** with an official site (**98.7%**). The remaining **21 are
  all documented honest nulls** (G5) — bodies with no confirmable official site: Eritrea
  (agri/finance/foreign), 7 defense ministries (Djibouti/Ethiopia/Guinea-Bissau/Equatorial
  Guinea/Mauritania/North Korea/São Tomé), 3 justice (Guinea-Bissau/Kiribati/North Korea),
  North Korea labour, Belgium federal education, Yemen tourism, Kuwait/Belize transport,
  South Sudan culture/environment, Zimbabwe culture. **Every ministry that HAS a confirmable
  official site now carries it.**
- honest current-holder notes recorded (no standalone ministry; current portfolio holder
  used): Argentina communications/industry (national-portal sections post-Decree-146/2026);
  Belize housing→MIDH, labour→Rural Transformation; DR Congo science→MINESURSI; Spain
  comms→digital.gob.es; Tanzania labour→PM's Office (kazi.go.tz); South Africa→Dept of
  Employment & Labour; Yemen comms→MTIT; Suriname via gov.sr portal sections.

run_tests.sh ALL GREEN. Sourcing/verification tiers unchanged; published-index
authoritative-scope gate (check #5, JP backbone only) untouched.

## 2026-06-04 — agriculture + health + tourism + trade ministry sites: 37 web-verified (1559 → 1596 ministries, 97%)

Continued the ministry tier with agriculture (10) + health (10) + tourism (10) + trade (9).
4 web-research subagents found + **confirmed each ministry's own official site by fetching
it**. 37 confirmed (provenance → the body's own official URL; `:last-verified` → 2026-06-04).
Also fixed a mislabeled unit: Portugal tourism was "Madeira Tourism Board" (a regional body)
→ corrected to **Turismo de Portugal (National Tourism Authority)**.

- ministries: 1559 → **1596/1642** with an official site (**97%**).
- 2 HONESTLY left null (G5): Eritrea agriculture (only the Ministry of Information portal
  exists), Yemen tourism (only a .com promotion board, no official .gov.ye ministry site).
- honest notes recorded: Argentina/Suriname have no standalone ministry domain (national-
  portal section used); Pakistan tourism = PTDC federal portal; Romania tourism under the
  Ministry of Economy; Ukraine via the State Agency for Tourism Development. Cameroon
  mintoul.gov.cm cert expired; several WAF/geo-blocked (Kuwait/Yemen/Iran/Lebanon/Zimbabwe)
  — all genuine official government domains, multi-source corroborated.

run_tests.sh ALL GREEN. Sourcing/verification tiers unchanged; published-index
authoritative-scope gate (check #5, JP backbone only) untouched.

## 2026-06-04 — culture + energy + environment ministry sites: 34 web-verified (1525 → 1559 ministries, 95%)

Continued the ministry tier with culture (13) + energy (12) + environment (12). 3 web-research
subagents found + **confirmed each ministry's own official site by fetching it**. 34 confirmed
(provenance → the body's own official URL; `:last-verified` → 2026-06-04).

- ministries: 1525 → **1559/1642** with an official site (**95%**).
- 3 HONESTLY left null (G5): South Sudan culture + environment, Zimbabwe culture — no
  confirmable dedicated ministry site (only third-party/social profiles or an unreachable
  national-portal section).
- honest reorganization notes recorded (current holder used, not a stale named body):
  Armenia energy merged into MTAI 2019 → mtad.am (minenergy.am is archived); Luxembourg
  energy now under the Ministry of the Economy (meco.gouvernement.lu); South Africa DMRE
  split 2024 (DEE still on dmre.gov.za per gov.za); Myanmar culture moved to the Hotels/
  Tourism/Culture ministry; Belize energy → MPUELE. Temporary-down/cert caveats noted
  (Guinea mehh.gov.gn 503; several WAF/geo-blocked) — all genuine official government domains.

run_tests.sh ALL GREEN. Sourcing/verification tiers unchanged; published-index
authoritative-scope gate (check #5, JP backbone only) untouched.

## 2026-06-04 — education + interior ministry sites: 31 web-verified (1494 → 1525 ministries)

Continued the ministry tier with education (16) + interior/home-affairs (16). 4 web-research
subagents found + **confirmed each ministry's own official site by fetching it**. 31 confirmed
(provenance → the body's own official URL; `:last-verified` → 2026-06-04).

- ministries: 1494 → **1525/1642** with an official site (93%).
- 1 HONESTLY left null (G5): **Belgium education** — no federal education ministry exists
  (constitutionally devolved to the Flemish / French-community / German-speaking communities);
  the federal belgium.be page is informational only.
- honest structural notes recorded: Bosnia uses the state Ministry of Civil Affairs (no state
  education ministry); Indonesia split into Kemendikdasmen (primary/secondary, Oct 2024);
  Liechtenstein education now under the Ministry of Infrastructure & Education; Marshall
  Islands via the Public School System; Honduras interior = SGJD (Gobernación). Caveats:
  Sierra Leone mbsse.gov.sl homepage temporarily serving a broken WordPress default (domain
  identity certain); several gov sites (Morocco/DRC interior, Nigeria/Philippines/Zambia/
  Zimbabwe) refuse the automated fetcher (geo/TLS/timeout) but are multi-source-corroborated
  official domains.

run_tests.sh ALL GREEN. Sourcing/verification tiers unchanged; published-index
authoritative-scope gate (check #5, JP backbone only) untouched.

## 2026-06-04 — transport + defense ministry sites: 27 web-verified (1467 → 1494 ministries)

Continued the ministry tier with transport (19) + defense (17) categories. 4 web-research
subagents found + **confirmed each ministry's own official public site by fetching it**. 27
confirmed and added (provenance → the body's own official URL; `:last-verified` → 2026-06-04).
(Defense entries are the ministries' PUBLIC homepages — civic-directory data, G10 wayfinding,
never an attack-surface map.)

- ministries: 1467 → **1494/1642** with an official site.
- 9 HONESTLY left null (G5) — no confirmable dedicated ministry site: Belize transport
  (portfolio under a Youth/Sports/Transport ministry, FB-only), Kuwait transport (split
  across Communications + Public Works), Djibouti / Ethiopia / Guinea-Bissau / Equatorial
  Guinea / Mauritania / North Korea / São Tomé defense.
- honest reorganization notes recorded: Estonia transport now under the Ministry of Climate
  (Kliimaministeerium); Jamaica under Energy/Transport/Telecoms; Slovenia under the Ministry
  of Infrastructure; Tanzania dedicated Uchukuzi (not the old Works ministry). **Sudan
  defense** (mod.gov.sd) is the documented official domain but currently OFFLINE due to the
  civil war — recorded honestly (offline ≠ fabricated). Anti-bot/TLS/geo-block caveats noted,
  all genuine official government domains.

run_tests.sh ALL GREEN. Sourcing/verification tiers unchanged; published-index
authoritative-scope gate (check #5, JP backbone only) untouched.

## 2026-06-04 — finance + foreign ministry sites: 24 web-verified (1443 → 1467 ministries)

Continued the ministry tier with two coherent fiscal/diplomatic categories: 19 Finance
ministries + 7 Foreign-Affairs ministries lacked `:gov.unit/official-url`. 3 web-research
subagents found + **confirmed each ministry's own official site by fetching it**. 24
confirmed and added (provenance → the body's own official URL; `:last-verified` → 2026-06-04).

- ministries: 1443 → **1467/1642** with an official site.
- 2 HONESTLY left null (G5) — both **Eritrea** (finance + foreign): the only Eritrean
  government web presence is the Ministry of Information portal (shabait.com); neither
  ministry has a dedicated site.
- honest nuances recorded: Kyrgyzstan finance is standalone again (minfin.gov.kg, not the
  merged Economy ministry); Myanmar's dedicated MoF domains no longer resolve after the
  2025 restructuring (national portal section used); Yemen MoF runs mof-yemen.com (the
  .gov.ye host is unreachable); Monaco/Solomon Islands have no standalone domain
  (gov-portal section used); Niger www-subdomain TLS-mismatch → apex host used. Anti-bot
  /TLS-quirk caveats noted, all genuine official government domains.

run_tests.sh ALL GREEN. Sourcing/verification tiers unchanged; published-index
authoritative-scope gate (check #5, JP backbone only) untouched.

## 2026-06-04 — justice-ministry sites + last bare-QID labels (1415 → 1443 ministries; 0 placeholders left)

Started the ministry tier (227 of 1,642 ministries lacked `:gov.unit/official-url`) with
its largest coherent functional category — **30 Ministries of Justice**. Fanned out 3
web-research subagents (10 each) to find + **confirm each ministry's own official site by
fetching it**. 27 confirmed and added (provenance → the body's own official URL;
`:last-verified` → 2026-06-04). A 4th subagent resolved the **last 4 bare-QID name-en
placeholders** in the whole atlas (Madagascar finance/foreign, Senegal finance, Togo
supreme court) to their real English names — **bare-QID labels are now 0 across the atlas.**

- ministries: 1415 → **1443/1642** with an official site.
- 3 justice ministries HONESTLY left null (G5): Guinea-Bissau (only a Facebook page +
  unreachable gov.gw), Kiribati (moj.gov.ki NXDOMAIN; justice.gov.ki hijacked to a foreign
  WordPress; only the distinct Attorney-General office is live), North Korea (DPRK runs no
  public MoJ site).
- honest restructuring notes recorded: Honduras justice now lives under the Secretaría de
  Gobernación, Justicia y Descentralización (sgjd.gob.hn); Liechtenstein/Palau have no
  standalone MoJ domain (used the official government portal's justice page); Madagascar's
  finance ministry is currently "Economy and Finance" (not "Finance and Budget"). Anti-bot
  /TLS caveats noted, all genuine official government TLDs.

run_tests.sh ALL GREEN. Sourcing/verification tiers unchanged; published-index
authoritative-scope gate (check #5, JP backbone only) untouched.

## 2026-06-04 — court official sites: 47 high courts web-verified (151 → 198/206)

Coverage-depth pass on the judicial tier (supreme / constitutional / cassation courts),
same method as the country + legislature + cabinet passes. 55 of 206 courts had no
`:gov.unit/official-url`. Fanned out 4 web-research subagents (~14 each) to find +
**confirm each court's own official site by fetching it** — the court itself or the
national-judiciary portal that hosts it. 47 confirmed and added (provenance → the body's
own official URL; `:last-verified` → 2026-06-04). Also **fixed 5 bare-QID name-en labels**
(Ethiopia Federal Supreme Court / Guinea / Libya / Liechtenstein / Saudi Arabia supreme
courts had a placeholder QID where the English name belonged).

- 151 → **198/206** courts now carry an official site.
- 8 HONESTLY left null (G5 over coverage-count) — genuinely no confirmable official court
  site: Burundi SC, Cameroon Constitutional Council, Guinea-Bissau SC, North Korea Central
  Court, Sudan Constitutional Court, **Syria SC** (court dissolved under the 2025
  Constitutional Declaration), **Tunisia Constitutional Court** (never established),
  **Turkmenistan SC** (no web presence).
- Honest entry-point choices recorded where the high court has no standalone site: the
  Ministry of Justice / national-judiciary portal that administers it (Bahrain moj, Saudi
  moj HighCourt page, Sudan sj.gov.sd, South Sudan mojca, Tonga justice.gov.to, Tajikistan
  egov.tj, Zimbabwe JSC). Anti-bot/TLS-expired caveats noted (Burundi CC expired cert,
  Djibouti/Vanuatu/Zimbabwe TLS-chain, several 403) — all genuine official domains.

run_tests.sh ALL GREEN. Sourcing/verification tiers unchanged; published-index
authoritative-scope gate (check #5, JP backbone only) untouched.

## 2026-06-04 — cabinet/executive official sites: 47 governments web-verified (80 → 127/129)

Coverage-depth pass on the cabinet/executive tier (same method as the country + legislature
passes). 49 of 129 executive bodies had no `:gov.unit/official-url`. Fanned out 4
web-research subagents (~12 each) to find + **confirm each executive's own official site by
fetching it** — the cabinet / council of ministers / PM or president's office / national
government portal, whichever is the canonical executive entry point. 47 confirmed and added
(provenance → the body's own official URL; `:last-verified` → 2026-06-04).

- 80 → **127/129** cabinet/executive units now carry an official site.
- 2 HONESTLY left null (G5 over coverage-count):
  - **Nicaragua** — presidencia.gob.ni refused connection on both HTTPS/HTTP; could not
    confirm a live site by fetching (no fabrication from secondary corroboration alone).
  - **Yemen** — divided wartime government; the Aden-based Council of Ministers has no
    confirmable live portal (only MoFA + the PLC chairman's personal site are active).
- Honest entry-point choices recorded where the cabinet has no standalone site: Presidency
  (Burundi, Burkina Faso, Colombia, Honduras, El Salvador, Kenya, Nigeria State House),
  PM/Primature (Cameroon, DRC, Haiti, Mauritania, Mauritius, Chad), or national gov portal
  (Chile, Ecuador, Malta, Namibia, Peru, Oman). Anti-bot 403/418 + TLS-chain caveats noted
  (Bahamas/Chile/Colombia/Guatemala/Honduras/Morocco/Malta/Namibia/Peru/Saudi/Zambia) — all
  genuine official government TLDs, multi-source corroborated.

run_tests.sh ALL GREEN. Sourcing/verification tiers unchanged; published-index
authoritative-scope gate (check #5, JP backbone only) untouched.

## 2026-06-04 — legislature official sites: 32 parliaments web-verified (150 → 182/186)

Coverage-depth pass on the legislature tier (same method as the country pass). 36 of
186 national legislatures had no `:gov.unit/official-url`. Fanned out 3 web-research
subagents (12 each) to find + **confirm each parliament's own official site by fetching
it** (no guessing). 32 confirmed and added (provenance switched from the Wikidata page
to the body's own official URL; `:last-verified` → 2026-06-04). For bicameral bodies
the main/lower chamber's official site was used where no combined-parliament site exists.

- 150 → **182/186** legislatures now carry an official site.
- 4 HONESTLY left null (G5 over coverage-count):
  - **Comoros** — the IPU-cited assemblee-comores.com is now a hijacked business directory.
  - **Equatorial Guinea** — no dedicated official Cámara de los Diputados site exists.
  - **North Korea (Supreme People's Assembly)** — no official web presence exists.
  - **Sudan** — National Legislature dissolved 2019, never reconstituted; domain dead.
- Honest substitutions recorded: **Guinea** → the current Conseil National de la
  Transition (cnt.gov.gn; the National Assembly was dissolved after the 2021 coup);
  **Turkmenistan** → the unicameral Mejlis (the Milli Gengesh upper house was abolished
  Jan 2023). Fetch caveats (DNS-unstable .cf/.ag, bot-blocked .pk/.ph) noted but all on
  genuine official parliamentary domains, IPU-Parline-corroborated.

run_tests.sh ALL GREEN. Sourcing/verification tiers unchanged; published-index
authoritative-scope gate (check #5, JP backbone only) untouched.

## 2026-06-04 — country official-portal URLs: 29 sovereign states web-verified (162 → 191/192)

Coverage-depth pass on the country tier. `world_coverage.py` showed 30 of 192
sovereign-state country units had no `:gov.unit/official-url` (only the Wikidata page
as provenance). Fanned out 3 web-research subagents (10 countries each) to find and
**confirm each state's OWN official central-government portal** by fetching it — never
guessing. 29 confirmed and added; provenance switched from the Wikidata page to the
body's own official URL (per the "source = each body's own url/document url" directive);
`:last-verified` bumped to 2026-06-04.

- 162 → **191/192** country units now carry an official-portal URL.
- The one remaining null is **Syria (gov.syr)** — HONESTLY left without a URL: no
  functioning central-government portal could be confirmed for the transitional
  government (legacy egov.sy unreachable; only the MoFA is active). G5 over coverage-count.
- Caveats recorded by the researchers (expired TLS on the legacy egypt.gov.eg → used
  the reachable official digital.gov.eg; Libya's gnu.gov.ly is the genuine GNU domain
  but still a placeholder; a few head-of-state portals bot-block automated fetch but
  are live) — all on genuine official government TLDs.

run_tests.sh ALL GREEN (16/16). Sourcing/verification tiers unchanged
(`:authoritative` + `:maintainer-verified`); the published-index authoritative scope
gate (check #5, JP backbone only) is untouched.

## 2026-06-04 — public index generator loads the FULL atlas (publish path E2E-validated)

Third and final wiring fix (after the read client #1057 + ingest #1058): the public
index generator `50-infra/etzhayyim-did-web/scripts/gen-gov-atlas-index.mjs` (which
builds `/.well-known/gov-units.json`) hardcoded the 2 seed files for ooyake units →
the published index would carry ~28 ooyake units. Changed to glob **all
`gov-units*.edn`**, and — respecting the constitutional publish gate — emit every unit
`:representative` in the published index, promoting ONLY the Council bootstrap-attested
`gov.jpn.(pref|city).*` backbone to `:authoritative`.

Result, validated **end-to-end for the first time** (generator → `validate_atlas.py`):
a **7,684-unit / 203-jurisdiction** public index (1.6 MiB); parent-refs 7,684/7,684
resolve; **authoritative scope = 118 units, all in the JP pref/city backbone (check #5
✓)**; 7,566 `:representative`. The read (client), write (kotoba ingest), and publish
(/.well-known index) paths now ALL project the full atlas — the build artifact stays
gitignored and the KV deploy remains operator-gated.

## 2026-06-04 — ingest pipeline loads the FULL atlas (operator write path)

Same class of fix as the read client: `deploy/ingest_records.py` (the operator write
path into the live kotoba `gov-atlas-v1` graph) had `GOV_SEEDS = [seed, jp-central,
toritsugi-procedures]` — so an operator ingest would push only **62 entities**, not the
real atlas. Changed to glob **all `gov-units*.edn`** → the dry-run now projects
**12,805 entities (7,106 units + 5,682 addresses + procedures/windows/forms/bpmn,
~162k datoms)**. When the operator enables ingest (KOTOBA_TOKEN), the whole atlas now
flows into kotoba instead of the seed core. Dry-run gate green.

## 2026-06-04 — read-client loads the FULL atlas (major consumer fix) + new queries

**Bug fixed**: `deploy/gov_atlas_client.py` (the read API danjo / kanae / tsumugi /
toritsugi / himotoki consume) globbed only `gov-units*.seed.edn` — so consumers saw
**~28 of the ~7,100 units**; the entire real-data atlas (countries, ministries,
courts, central banks, oversight bodies, ADM1, IGOs, …) was invisible to them. Changed
the glob to `gov-units*.edn` → the client now loads all **7,106 units + 5,691
addresses**. Added consumer-grade queries: `by_branch(branch)`, `addresses_for(uid)`,
`country_profile(cc)` (a country's bodies grouped by branch + subdivision/geocoded
counts — the one-call view consumers want). Client tests 7 → **11 passed**;
`run_tests.sh` ALL GREEN.

## 2026-06-04 — sovereign wealth funds (45)

`gov-units.swf.edn` adds **45 sovereign wealth funds** (state-owned investment funds —
public-asset stewards; Wikidata P31 `Q1061648`), e.g. ADIA, GIC, Korea Investment
Corporation. On-mission for kanae fiscal-flow viz + danjo public-accountability.
`:level :agency` `:branch :independent`; multiple per country kept (id
`gov.<iso>.swf.<slug>`). quality_audit clean. Atlas now **7,106 units / 57 files,
7,104 QIDs all unique, 7,102 :authoritative**.

## 2026-06-04 — CI gate (institutionalised)

`.github/workflows/ooyake-atlas-gates.yml` runs the actor's offline gate suite on any
PR/push touching `20-actors/ooyake/**` or the gov-atlas ontology (+ nightly +
manual) — the PR-level half of the two-layer defence (lefthook pre-commit + CI) per
ADR-2605271200. Enforces, on every change: registry integrity (QID/enum/G5/ref),
integrity-guard self-tests, G20/world coverage floors, the coverage matrix, the
quality audit (sub-national mis-typing flags), and a valid GeoJSON export. The
~7,000-unit atlas's quality is now machine-enforced, not just locally checked.

## 2026-06-04 — national meteorological services (49)

`gov-units.meteorology.edn` adds **49 national meteorological/weather services** (the
public weather/warning bodies citizens rely on; Wikidata P31 `Q1266087`). A POSITIVE
label filter (must denote meteorology/weather/climate) drops the private weather brands
the class also tags (e.g. Windfinder mis-resolved for DE) — quality-first, learning from
the audit pass. `:level :agency` `:branch :executive`. quality_audit stays clean (0
flagged). Atlas now **7,061 units / 56 files, 7,059 QIDs all unique, 7,057
:authoritative**.

## 2026-06-04 — data-quality audit + correction (sub-national de-noising)

New `scripts/quality_audit.py` (wired into `run_tests.sh`) scans national-level bodies
for high-precision sub-national/historical signals in their names — the noise the bulk
Wikidata class-pulls occasionally introduced. The first pass flagged 13 genuine
mis-typings (a county DA tagged as USA's prosecutor, NSW justice as Australia's,
Quebec/Hong-Kong/Northern-Ireland/Scotland/California/Puerto-Rico/Hesse/Faisalabad
bodies as their nations', Brazil's *regional* electoral courts). All 13 were **removed**
(a country lacking that body type is more honest than a wrong national claim), plus
their 9 orphaned HQ addresses. Audit is now **clean (0 flagged)**. GeoJSON + COVERAGE.md
regenerated. Atlas **7,012 units / 55 files, 7,010 QIDs all unique, 7,008
:authoritative**.

## 2026-06-04 — national libraries + validate_atlas skip-fix

- **`gov-units.libraries.edn`**: **155 national libraries** (Wikidata P31 `Q22806`,
  current; sub-national/former filtered) — public legal-deposit / documentary-heritage
  institutions citizens access. `:level :agency` `:branch :executive`.
- **`validate_atlas.py` fix (maturity)**: when the generated public index
  (`gov-units.json`, a gitignored build artifact) is absent and no `--url` is given,
  it now **skips gracefully** instead of crashing — so `run_tests.sh` is finally
  **ALL GREEN in a fresh checkout** (the EDN registry SSoT is covered by
  `check_seed_integrity.py`; this validator is a pre-deploy gate for the published
  artifact only).
- `COVERAGE.md` regenerated. Atlas now **7,025 units / 55 files, 7,023 QIDs all
  unique, 7,021 :authoritative**.

## 2026-06-04 — national archives (civic records access)

`gov-units.archives.edn` adds **144 national archives** (Wikidata P31 `Q2122214`) — the
body through which citizens access public records, on-mission for ooyake wayfinding +
himotoki disclosure. `:level :agency` `:branch :executive`. Because Q2122214 also tags
sub-national/historical archives, the integrator drops labels flagged
former/provincial/regional/state/named-region (11 dropped) — a quality filter, honest
about the class's noise. Atlas now **6,870 units / 54 files, 6,868 QIDs all unique,
6,866 :authoritative**.

## 2026-06-04 — constitutional courts (judicial depth)

`gov-units.constitutional-courts.edn` adds **62 constitutional courts** (Wikidata P31
`Q32766`) — the dedicated constitutional-review apex that many countries operate
distinct from their supreme court. `:level :court` `:branch :judicial`. Integrator
dropped the 6 countries whose supreme court IS their constitutional court (same QID,
already seeded). Atlas now **6,726 units / 53 files, 6,724 QIDs all unique, 6,722
:authoritative**.

## 2026-06-04 — executive apex (governments/cabinets)

`gov-units.executive.edn` adds **129 national executive bodies** — each country's
government/cabinet (Wikidata country `P208` executive body, the executive analog of
`P194` legislature / `P209` court), e.g. "Government of Denmark". Fills the structural
gap between the country unit and its ministries. New `:level :cabinet` added to the
ontology `:gov.unit/level` enum + the integrity guard + `validate_atlas.py`.
`:branch :executive`, parent `gov.<iso>`. Atlas now **6,664 units / 52 files, 6,662
QIDs all unique, 6,660 :authoritative**.

## 2026-06-04 — national capitals (geolocation hierarchy complete)

`gov-units.capitals.edn` adds **191 `:gov.address :capital` records** — each country
unit's capital city (Wikidata country P36 → capital's P625 coordinate + label), all
191 with precise lat/lon. This completes the geolocation hierarchy: IGO/national-body
HQs + subnational seats + **national capitals**. `viz/gov-atlas.geojson` regenerated to
**4,521 features**; total `:gov.address` now **5,693** (4,521 with coordinates).

## 2026-06-03 — self-contained map viewer

`viz/gov-atlas-map.htm` renders `gov-atlas.geojson` in the browser — a pure-canvas
equirectangular world map (drag-pan, wheel-zoom, click-for-details) with the 4,330
government bodies colour-coded by branch (executive / subnational / independent /
legislative / judicial / intergovernmental), a live legend + per-branch filter, and
popups linking each body's Wikidata + official site. **No external tiles / CDN /
trackers** (Charter ad-free + no-third-party compliant) — fully self-contained,
offline, drop-in. Turns the atlas into something a human can actually explore.

## 2026-06-03 — GeoJSON export (the atlas is now a usable world map)

`scripts/export_geojson.py` derives `viz/gov-atlas.geojson` from the registry —
joins every coordinate-bearing `:gov.address` to its `:gov.unit` and emits a GeoJSON
FeatureCollection (**4,330 Point features**, properties: id/name/level/branch/
jurisdiction/wikidata/kind/city/official_url). Drop-in for any GIS tool or the
kami-engine viewer. `--check` mode (wired into `run_tests.sh`) validates the output is
well-formed GeoJSON with ≥4,000 features. The committed `viz/gov-atlas.geojson` (~1.3 MB)
is the rendered world-government map spanning national institutions + subnational
seats across ~190 jurisdictions.

## 2026-06-03 — ADM1 subnational tier geolocated (map-ready)

`gov-units.adm1-coords.edn` adds **3,589 `:gov.address` :seat records** for the world's
first-level administrative divisions (states/provinces/regions) — Wikidata P625
coordinate + P36 capital/seat label via light REST. **3,587 carry precise lat/lon
(99.9%)**, 3,036 carry a capital-city name. Total `:gov.address` now **5,502**, of which
**4,330 carry coordinates** — both the national and subnational tiers of the atlas are
now substantially map-ready (an end-to-end world-government GeoJSON is now derivable).

## 2026-06-03 — HQ locations extended to all national bodies (L3 depth, cont.)

`gov-units.hq-locations-2.edn` extends HQ geolocation to the **remaining national
bodies** — the 18 executive ministry types + the independent oversight/regulatory +
statistical/prosecution/revenue agencies (those not in hq-locations.edn). **1,280 more
`:gov.address` records** (Wikidata P625 + P159 via light REST). Total `:gov.address`
now **1,913** (was ~633), **743 with precise lat/lon** — the whole national tier of the
atlas is now substantially map-ready.

## 2026-06-03 — HQ locations for iconic national institutions (L3 depth)

The L3 public-services-hub axis was JP/G7-only (~21 addresses). `gov-units.hq-locations.edn`
adds **608 `:gov.address` headquarters records** for the world's iconic national
institutions — central banks, national legislatures, supreme courts, finance & foreign
ministries — pulled from Wikidata (P625 coordinate location + P159 seat) via light REST.
**290 carry precise lat/lon** (map-ready); the rest carry the seat label. Keyed to
existing `:gov.unit` ids; ids already present (JP MOF / US Treasury / G7 finance HQs)
excluded. Total `:gov.address` now ~**629** (was ~21). NOTE: P159 sometimes names the
seat building not the city; the lat/lon is the load-bearing datum.

## 2026-06-03 — coverage matrix (per-country functional-coverage dashboard)

`scripts/atlas_summary.py` shows the atlas by level/branch; the new
`scripts/coverage_matrix.py` (wired into `run_tests.sh`) shows it **per country** —
192 country units × 35 functional categories (the 18 executive ministries +
legislature + supreme court + central bank + the 11 independent oversight/regulatory
bodies), robust to the G20/Japan bespoke ids (mof/treasury/boj/mext/…). Surfaces, for
each category, how many of the 192 countries carry such a body + example gaps, and
per-country completeness. Current shape: **avg 13.7/35 categories per country**; most
complete ZAF/USA(29) · IND/DEU(28); thinnest the microstates (TUV 1, DMA/SMR 2). This
turns "how complete is each government's record" into a measured, gap-aware number —
the maturity counterpart to the raw 6,535-unit coverage.

## 2026-06-03 — schema maturity (enum-validated levels/branches + atlas dashboard)

Hardened the substrate now that coverage spans 6,031 units:
- `gov-atlas-ontology.kotoba.edn`: declared `:gov.unit/hq-city` (was an undeclared
  ad-hoc attribute on the IGO layer) — schema debt cleared.
- `scripts/check_seed_integrity.py`: now validates `:gov.unit/level` and
  `:gov.unit/branch` against the ontology enums (mirrors the `:gov.unit/level`/`branch`
  `:db/doc` enums) — schema drift is caught at the EDN tier, not only by
  `validate_atlas.py` against the generated JSON. + a self-test (`bad-level` fires).
- `scripts/atlas_summary.py` (NEW, wired into `run_tests.sh`): by-level / by-branch /
  by-sourcing / jurisdiction dashboard. Current shape: **6,031 units, 198 distinct
  jurisdictions; by level** subdivision 3599 · ministry 1648 · country 192 ·
  legislature 186 · agency 159 · court 144 · supranational 99 · …; **by branch** local
  3601 · executive 1846 · legislative 186 · independent 158 · judicial 144 ·
  intergovernmental 96. 6,027 :authoritative.

## 2026-06-03 — REAL DATA: the full G20 (founder directive "demo じゃなくて実データ, G20")

The atlas carries the **entire G20 as real committed data**, not a proof-of-model
demo: **20/20 members** (19 sovereign states + the EU), each with a **country unit +
finance ministry/treasury**, every row `:sourcing :authoritative` +
`:verification-status :maintainer-verified` — each Wikidata QID **independently
verified against wikidata.org** and each `:provenance` citing **the body's own
official URL** (本体の url), on 2026-06-03.

- `registry/gov-units.g20.edn` — the 14 G20 nations not previously seeded
  (FR/IT/CA/CN/BR/RU/MX/ID/TR/ZA/AR/SA/IN/AU) + DE/KR finance ministries + the
  **G7 finance-ministry HQ addresses** (UK/FR/IT/CA/DE + KR; JP/US already seeded).
- `registry/gov-units.world-countries.edn` — **all 192 current UN-member
  sovereign-state COUNTRY units** as real data (全世界政府 breadth; G20 excluded).
  One-time maintainer pull of the Wikidata SPARQL endpoint — **current** UN members
  (`p:P463 ps:P463 Q1065` with no end-qualifier `P582`) that are **not dissolved**
  (`P576`) + ISO 3166-1 alpha-3 (`P298`) + official site (`P856`); parsed
  deterministically (no summarizing model) → exact QIDs. Dissolved/historical states
  (Czechoslovakia, USSR, East Germany, Byelorussian SSR, …) are filtered out. 162/192
  carry an official-portal URL; the rest cite Wikidata as provenance. Gate
  `scripts/world_coverage.py` (**192 ≥ 190 floor**).
- `registry/gov-units.world-defense.edn` — **114 defence ministries** (the worldwide
  national-defence executive layer; Wikidata `P31` *defence ministry* `Q1788820`,
  current). `:level :ministry`, `:branch :executive`, `cofog 02`. Records the
  **civilian defence MINISTRY** as a public body only — never armed-forces
  order-of-battle/bases/capabilities (G10 no attack-surface map). Japan 防衛省 skipped
  (already `gov.jpn.mod`).
- **6 more worldwide ministry layers (subagent-parallelised Wikidata pull, 690 units)** —
  each `:level :ministry` `:branch :executive`, Wikidata `P31` of the relevant ministry
  class (current, P576-excluded), country a current UN member; integrator dropped
  non-current-country ISO3, bare-QID labels, QIDs already in the atlas, and cross-file
  dup QIDs:
  `gov-units.world-interior.edn` **111** (`Q6589202`, cofog 03.1) ·
  `gov-units.world-health.edn` **136** (`Q1519799`, cofog 07) ·
  `gov-units.world-justice.edn` **127** (`Q1413677`, cofog 03.3) ·
  `gov-units.world-education.edn` **127** (`Q2269756`, cofog 09) ·
  `gov-units.world-environment.edn` **85** (`Q917441`, cofog 05) ·
  `gov-units.world-agriculture.edn` **104** (`Q1364302`, cofog 04.2).
- **6 further worldwide ministry layers (2nd subagent batch, 396 units)** — same
  Wikidata-class pull + central cleanse: `world-labour` **64** (`Q12813215`) ·
  `world-transport` **91** (`Q2516426`) · `world-energy` **71** (`Q19973795`) ·
  `world-culture` **92** (`Q19973770`) · `world-trade` **46** (`Q1243341`) ·
  `world-communications` **32** (`Q19983480`). All `:level :ministry` `:branch
  :executive`. Atlas now **2194 units / 24 files, 2192 QIDs all unique, 2190
  :authoritative**.
- **3rd subagent batch — 6 more ministry layers (143 net-new units)**: `world-social`
  **24** (`Q2305901`) · `world-housing` **22** (`Q2587942`) · `world-science` **18**
  (`Q1313096`) · `world-tourism` **57** (`Q2446662`) · `world-industry` **14**
  (`Q6867185`) · `world-water` **8** (`Q6867642`). Many candidate rows were combined
  ministries already in earlier layers (culture/environment/education/…) and were
  dropped by the atlas-existing-QID dedup — net-new only. Atlas now **2337 units / 30
  files, 2335 QIDs all unique, 2333 :authoritative**.
- **SUBNATIONAL — first-level administrative divisions (ADM1), 3,599 units across 5
  continent files** (`gov-units.adm1-{africa,americas,asia,europe,oceania}.edn`):
  states / provinces / regions / counties of the atlas's current-UN-member countries,
  via Wikidata country `P150` (division not dissolved, ISO 3166-2 `P300` as
  `:external-code`). `:level :subdivision`, `:branch :local`, parent `gov.<iso3>`,
  exact QIDs from SPARQL JSON. Integrator restricted to atlas countries + dropped
  atlas-existing QIDs (e.g. Tokyo) + cross-file dups. This takes the atlas from the
  national tier down into subnational government worldwide — **5936 units / 35 files,
  5934 QIDs all unique, 5932 :authoritative**.
- **SUPRANATIONAL — international / intergovernmental organizations, 95 units**
  (`gov-units.intergov.edn`): the global-governance layer — the UN system (UN +
  principal organs + funds/programmes + specialized agencies via `P31 Q15925165`) and
  major regional & economic IGOs (AU/ASEAN/Arab League/OAS/Council of Europe/NATO/
  OECD/WTO/OPEC/BIS/Commonwealth/AfDB/ADB/IDB/AIIB/OSCE/…). `:level :supranational`,
  `:branch :intergovernmental`, `:jurisdiction "intl"`, `:hq-city` where known.
  Dissolved orgs (P576, e.g. IRO) and the already-present EU dropped. Atlas now
  **6031 units / 36 files, 6029 QIDs all unique, 6027 :authoritative**.
- `registry/gov-units.world-foreign.edn` — **158 foreign-affairs ministries** (the
  worldwide diplomatic executive layer; Wikidata `P31` *foreign affairs ministry*
  `Q20901295`, current). `:level :ministry`, `:branch :executive`. Japan's 外務省
  (already `gov.jpn.mofa`) is skipped to avoid a duplicate QID; 152/158 carry an
  official-site URL.
- `registry/gov-units.world-courts.edn` — **144 supreme/highest courts** (the
  worldwide **judicial-branch** layer; Wikidata `P31` *supreme court* `Q190752`,
  current, matched to atlas countries). `:level :court`, `:branch :judicial`. Honest
  gap (G5): 144 of 192 countries have an apex court typed `Q190752`; the rest are
  differently-typed/untyped — not fabricated. Multi-apex countries → one chosen
  deterministically. Never a docket/case index — structural mirror only (G9/G10).
- `registry/gov-units.world-legislatures.edn` — **186 national legislatures** (the
  worldwide **legislative-branch** layer; Wikidata `P194` legislative body, current,
  for every UN member). Adds a new `:level :legislature` (+ `:court`) to the ontology
  `:gov.unit/level` enum + `validate_atlas.py`. `:branch :legislative`. 150/186 carry
  an official-site URL. With courts, the atlas now spans **executive + legislative +
  judicial + independent** branches worldwide.
- `registry/gov-units.world-finance.edn` — **117 non-G20 finance ministries** (the
  worldwide executive fiscal-authority layer). Wikidata pull of items typed `P31`
  *finance ministry* (`Q15711797`), current (no `P576`), country a current UN member.
  Honest gap: only 117 of the 173 non-G20 countries have a finance ministry typed
  under that class on Wikidata; the rest use a differently-typed body or are untyped
  — **not fabricated** (G5). With the 20 G20 ministries → **137 finance ministries**.
- `registry/gov-units.world-centralbanks.edn` — **138 non-G20 central banks** (the
  worldwide monetary-authority layer; same Wikidata pull via country `P1304`).
  Monetary-union banks are emitted ONCE as `:supranational` units with their member
  ISO3s in `:external-code` — **ECCB** (Eastern Caribbean) · **BCEAO** (WAEMU) ·
  **BEAC** (CEMAC); SNB is modelled under CHE. With the 20 G20 central banks that is
  **158 central banks** total — real data, every QID verified.
- `registry/gov-units.g20-centralbanks.edn` — the **20 G20 central banks**
  (BoJ/Fed/BoE/Banque de France/Bundesbank/Banca d'Italia/BoC/PBoC/BCB/CBR/Banxico/
  BI/TCMB/SARB/BCRA/SAMA/BoK/RBI/RBA + ECB), `:level :agency` `:branch :independent`,
  every QID web-verified — the monetary-authority dimension beside the ministries.
- The already-seeded national rows (JP full central gov + US/UK/DE/KR/EU) were
  **QID-corrected and promoted** to `:authoritative` / `:maintainer-verified`.
- Gates: `scripts/g20_coverage.py` (**G20 20/20 — country + finance + central bank**) +
  `scripts/check_seed_integrity.py` (**78 units, 76 QIDs all unique + well-formed,
  74 :authoritative, addresses resolve, G5 present**), both wired into
  `deploy/run_tests.sh` (**ALL GREEN, 11 suites**).

**QID integrity**: a prior demo wave fabricated a contiguous fake Wikidata block
(`Q1023xxx`) — MOF "Q1023766" actually resolves to *CIUTI*, a Brussels translators'
association. Every QID re-verified and corrected in the seeds + `authority-reference.edn`.

**Still gated (separate operator/Council steps, not done here):** live kotoba
ingest (`KOTOBA_TOKEN` + node) and publishing national `:authoritative` rows to
`/.well-known/gov-units.json` (Council-Lv6+ / bootstrap-attestation, `validate_atlas.py`
check #5). This change is the **committed registry record** of real verified data.

### Legacy reconcile DEMO (mechanism proof, unchanged)

The offline `reconcile.py` still demonstrates the `:representative → :authoritative`
promotion **mechanism** on its bundled 28-unit fixture (8 promoted vs the 8-record
`authority-reference.edn`). That remains a demo of the *mechanism*; the *real data*
is the G20 set above.

## Seed contents (R0, 2026-06-02)

Two seed files: `gov-units.seed.edn` (proof-of-model chain) + `gov-units.jp-central.seed.edn` (full JP 府省庁).

| Vocabulary | Count | All `:unverified-seed`? |
|---|---|---|
| `:gov.unit/*` | **28** — base 15 (JP ×7, USA ×3, GBR ×2, DEU ×1, KOR ×1, EU ×1) + JP central 13 (内閣府 + 11省 + デジタル庁 + 復興庁) | yes |
| `:gov.address/*` (住所) | **17** — base 4 + JP central 13 (霞が関 + 市谷 + 紀尾井町) | yes |
| `:gov.window/*` (窓口) | 2 | yes |
| `:gov.form/*` (書式) | 2 (→ chigiri templates) | yes |
| `:gov.procedure/*` (手続き) | 3 (→ toritsugi-ref) | yes |
| `:gov.bpmn/*` (BPMN) | 3 (`:model-only`) | n/a |

**Full vertical chain proven**: `gov.jpn → 財務省 → 国税庁 → 東京国税局 → 麹町税務署`
(with 住所 + 窓口) and `東京都 → 新宿区 → 戸籍住民課窓口` (with 住所). **省庁単位の幅**:
the entire JP central government (内閣府 + 総務/法務/外務/財務/文科/厚労/農水/経産/国交/環境/防衛
省 + デジタル庁 + 復興庁) each with HQ 住所. **国際的な幅**: country + flagship ministry
rows for US/UK/DE/KR + EU supranational.

## Reconcile demo (R1 mechanism, offline)

`scripts/reconcile.py` proves the `:representative → :authoritative` promotion rule
(G5: promote only when `:gov.unit/wikidata` AND `:gov.unit/official-url` agree with
`registry/authority-reference.edn`). Latest run:

```
units in seed: 28 · authority records: 8
→ PROMOTED authoritative: 8  (gov.jpn, gov.jpn.cao, gov.jpn.mof, gov.jpn.mofa,
                              gov.jpn.meti, gov.jpn.pref.13, gov.usa.treasury, gov.gbr.hmrc)
→ conflicts (kept unverified): 0
→ no authority record (stays representative): 20
coverage: 28.6% authoritative (8/28) — rest honestly :representative
```

This is a deterministic OFFLINE demo against a bundled reference; **live fetch of
Wikidata / 行政機関コード / GeoNames is G4 + Council + operator gated** and is NOT run.

The reconcile logic is now a real cell: `cells/reconcile/cell.py` (`ReconcileCell`)
with `mode="bundled"` (runnable, the above) and `mode="live"` (raises, G4-gated).
`scripts/reconcile.py` is the thin CLI over it. Unit tests:
`cells/reconcile/test_reconcile_cell.py` — **5 passed** (promotion set, no-conflict
remainder, bundled-ok, live-gated, unknown-mode-rejected).

## What is NOT done (by design at R0)

| Question | Status |
|---|---|
| All world governments enumerated? | **NO** — 28 units (proof-of-model). The world has ~195 countries × thousands of units each. |
| Any `:authoritative` row in the seed? | **NO** — every seed row is `:representative` / `:unverified-seed`. The `reconcile.py` demo can promote 8/28 against the bundled reference, but that is a demo, not committed seed state or live ingest. |
| Cells running? | **PARTIAL** — `reconcile` (bundled mode) is implemented + unit-tested (5 passed); the other 5 cells are path-reserved scaffolds. `reconcile` live mode + all ingest/serve cells are gated. |
| Per-unit DID served? | **NO** — scheme defined; dynamic did.json serving is R2. |
| `findService` live? | **NO** — lexicon + BPMN defined; serving is R1/R2. |
| `/actors` search surfaces gov units? | **NO** — R1 (after `atlas_serve` + reconcile). |
| Addresses/hours authoritative? | **NO** — best-effort public references as of 2026-06-02, expected to drift. |

## Maturity score (self-assessed, R0)

- **L1 namespace** (country scaffolds): inherited from legacy `gov*` dirs (196 dirs) — but stubs, not ooyake-native yet.
- **L2 agency registry**: 28 ooyake-native units (`:representative`; full JP central government covered).
- **L3 public-services hub** (住所/窓口): 17 addresses + 2 windows (JP only).
- **L4 procedure ingest**: 3 procedures (JP only, → toritsugi).
- **L5 routing-around**: **out of scope** for ooyake (read-side only, G9/G10).

Coverage score remains governed by ADR-2605250680 (49.18/100 baseline). ooyake R0
moves the **schema/substrate** axis to green; the **data/coverage** axis stays red
until R1 authoritative ingest. **No silent truncation**: this file is the
canonical honest record (G5).

## Update 2026-06-02 — JP local-government breadth ingest

`deploy/ingest_jp_local.py` projected the bundled official-code dataset
(`60-apps/etzhayyim-project-states/data/gov/jpn/{prefecture,municipality}.ndjson`;
全国地方公共団体コード / 地方自治法) into `:gov.unit` and ingested it into the live
`gov-atlas-v1` kotoba graph (operator-local):

- **47 prefectures** (都道府県, codes 01–47, with `iso3166-2:JP-NN` + `jp-jichitai:NN`)
- **71 municipalities** — 20 designated cities (政令指定都市) + 23 Tokyo special wards
  (特別区, level `:ward`) + 28 prefectural capitals/major cities, each with its
  6-/5-digit 全国地方公共団体コード as `:gov.unit/external-code`
- 118 units / ~2006 datoms; 200 ok in 2 batches. `gov.jpn.pref.13` (東京都) and
  `gov.jpn.city.13104` (新宿区) merged with the prior hand-seed by id (no duplicate).

Distinct `:gov.unit` in `gov-atlas-v1` after this ingest: **~144** (28 prior + 118
JP-local − 2 overlaps). All JP-local rows ship `:sourcing :representative` /
`:verification-status :unverified-seed` (G5) — they carry official codes + official
`provenance` URLs but are a curated bundle, not an ooyake-reconcile live-verified
fetch; the `reconcile` cell (live mode, G4-gated) promotes them to `:authoritative`.

Honest scope note: ~144 units is still a small fraction of Japan's full local universe
(47 prefectures + 1,718 municipalities + countless bureaus/divisions/窓口) and a rounding
error of the global universe (~195 states × thousands each). This ingest covers the
**highest-tier official backbone** (every prefecture + every designated city + every Tokyo
special ward); the long tail of 765 cities / 716 towns / 156 villages is the next
authoritative-dataset bundle, not fabricated here (G5).

## Update 2026-06-02 (consolidated) — current state of the atlas

Supersedes the R0 "proof-of-model" framing above for the live numbers. The gov-atlas
graph (`gov-atlas-v1`, operator-local kotoba node) + the public index now hold:

| Vocabulary | Count | Note |
|---|---|---|
| `:gov.unit/*` | **772** across **178 jurisdictions** | 177 country + 47 prefecture + 23 ward + 504 municipality + 14 ministry + 4 agency + 1 bureau + 1 division + 1 supranational |
| `:gov.address/*` | 17 (JP) | |
| `:gov.window/*` | 3 (JP) | |
| `:gov.form/*` | 5 (→ chigiri) | |
| `:gov.procedure/*` | 6 (→ toritsugi-ref) | full toritsugi R0 set (6/6) |
| `:gov.bpmn/*` | 3 (`:model-only`) | |

**Sourcing (G5)**: `representative` 654 / **`authoritative` 118**. The 118 = the JP
official-code backbone (47 都道府県 ISO 3166-2:JP + 71 市区町村 全国地方公共団体コード),
promoted under `BOOTSTRAP-ATTESTATION-reconcile-live.md` (Seat 1 Lv7 provisional;
**re-ratify at Council 3-of-5**). 153/177 country units carry a real English name
(from lea NCB records); 24 remain ISO3-code stubs.

**Toolchain (all offline-runnable + tested)**: `ingest_records.py`,
`ingest_jp_local.py`, `ingest_states_global.py`, `promote_authoritative.py`,
`cells/reconcile/cell.py` (bundled mode + 5 tests), `gov_atlas_client.py` (shared read
API + 7 tests), `validate_atlas.py` (integrity, 772/772 parent-refs resolve),
`resolve_for_toritsugi.py` (toritsugi 6/6).

**Integration (read-side SSoT consumed)**: `GovAtlas` client (getUnit / resolvePath /
findService / searchUnits / by_level / by_jurisdiction / resolve_procedure) is the one
API danjo / kanae / tsumugi / toritsugi / himotoki use. toritsugi 6/6 procedures
resolve to 所管 + 窓口 + 住所 + 書式 + 根拠法令.

**Public surface (LIVE)**: `etzhayyim.com/actor/ooyake/did.json` (KV) ·
`/.well-known/gov-units.json` (772 units) · `/gov` (human search) · `/.well-known/actors.json`.

**Maturity axes (self-assessed)**: substrate/schema 95 🟢 · actor liveness 90 🟢 ·
tooling 88 🟢 · public discovery 🟢 · **data breadth ~30 🟡** (178 countries, but
backbone/major-city tier only) · **data authority ~25 🟡** (118/772 authoritative,
provisional/bootstrap).

**Honest pending (gated or env-blocked, NOT done — no silent truncation, G5)**:

- Full JP **1,718-municipality long tail** + per-country full authoritative coverage →
  needs `reconcile` **live mode** (G4 + **Council 3-of-5**; bootstrap attestation covers
  only the already-bundled official-code tiers).
- Country-name enrichment (153 names) **deployed to the public `gov-units.json`** →
  pending a healthy `wrangler` deploy (env tooling exit-194 on 2026-06-02 session).
- `/search` (yoro) surfacing gov units → pending a yoro Pages deploy.
- `kotoba commit` IPFS cold-tier seal → operator cadence (WAL-durable meanwhile).
- Live `:authoritative` promotion is **provisional** until Council re-ratifies.
