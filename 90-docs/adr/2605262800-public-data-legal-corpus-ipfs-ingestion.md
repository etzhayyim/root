---
id: adr-2605262800-public-data-legal-corpus-ipfs-ingestion
title: "ADR-2605262800: Global legal-corpus ingestion (statutes / case law / treaties / procedures / templates) via IPFS-pinned DataLad subdatasets — extends ADR-2605262400; powers chigiri / hanrei / manabi / baien-distill"
status: proposed
doc_type: adr
topic: public-data-legal-corpus-ingestion
authoritative: true
last_verified: 2026-05-26
priority: 6.0
axis: architecture
weight: 0.55
priority_note: "Adds the **legal** corpus family to the artificial-organism dataset substrate. Sibling of ADR-2605262400 (geo / netreg / routing / dns / web buckets); this ADR adds the `law/` bucket family: statutes / cases / treaties / procedures / templates / commentary. Five sensor families register under `kotodama.organism.sensors.legal.*`: `legal_statute_sensor` (per jurisdiction) / `legal_case_sensor` (per court system) / `legal_treaty_sensor` / `legal_procedure_sensor` (per regulatory body) / `legal_template_sensor` (chigiri-consumable templates). Most sources are Tier-A (public-domain or open-government license: OGL v3.0 / Étalab / CC0 / public-domain de facto). Tier-B includes CanLII / AustLII / Indian Kanoon (mixed CC variants). Tier-C limited (most law is public by nature); only some commercial commentary annotations land in Tier-C with G13 fleet-internal `-nc-` artifact carve-out — but the ADR PROHIBITS commentary corpora from Westlaw / LexisNexis / Bloomberg Law (proprietary feeds; Charter Rider §2(e) gatekeeping rejection + §2(c) covert-ops vendor concern). Sources include: US (USC / CFR / Federal Register / Caselaw Access Project / CourtListener / RECAP/PACER bulk) — UK (legislation.gov.uk / Find Case Law TNA) — EU (EUR-Lex / CJEU) — JP (e-Gov 法令 / 裁判所 判例 / 官報) — Canada (CanLII) — Australia (AustLII) — Council of Europe (HUDOC / ECHR) — UN (Treaty Collection / UNCITRAL / WIPO / Hague) — international (ICC documents / IMF legal / World Bank legal) — DE (Bundesgesetzblatt) — FR (Légifrance Étalab) — IT (Normattiva) — KR (Korean Law Information Center) — IN (Indian Kanoon Tier-B) — BR (Senate / STJ) — CN (NPC statutes — Charter Rider §2(g) state-aligned scrutiny applies; ingested as authoritative-source-of-record but flagged for non-substitution doctrine). Special legal-PII concern: court decisions name judges + parties + witnesses + sometimes minors. Published court records are public by nature, BUT this ADR adds a `judicial_party_redactor` policy that respects per-jurisdiction publication redaction rules (e.g., German Pseudonymisierung of party names in published BGH decisions; JP 個人情報保護法 + 裁判所 redaction practice for family-court / juvenile-court matters; CCPA + GDPR right-to-be-forgotten requests on published opinions). Default policy = pass-through for jurisdictions where publication is unredacted-by-law; redaction layer applied where jurisdiction practice is redaction. Passive-only (ADR-2605262400 §7 invariant): no live court-record scraping at organism-tick time; only pre-published archives via `e7m-dataset add`. R0 = ADR + sensor scaffold + recipe templates + 25 fetcher path-reserves; W1 ships the 5 anchor sources (USC / CFR / e-Gov / EUR-Lex / legislation.gov.uk). Powers chigiri (ADR-2605262700) procedural cells + hanrei case-law deep coverage + manabi legal-literacy curriculum + baien-distill specialist legal-reasoning artifacts (always with proper license tier propagation and G13 carve-out where any tier-C commentary creeps in)."
authoritative_for:
  - global legal-corpus ingestion policy (statutes / cases / treaties / procedures / templates / commentary)
  - `law/` bucket family under 90-docs/baien/datasets/law/<bucket>/<jurisdiction>/<rev>/
  - 5 new sensor families under kotodama.organism.sensors.legal.*
  - 25+ fetchers under 70-tools/e7m-dataset/src/e7m_dataset/fetchers/legal/
  - judicial-party redaction policy (jurisdiction-dependent)
  - legal-template corpus separate from raw-law corpus (G6)
  - chigiri (ADR-2605262700) consumer contract
  - hanrei / manabi / baien-distill cross-actor data flows
  - prohibition on Westlaw / LexisNexis / Bloomberg Law / proprietary commentary (Charter Rider §2(e) gatekeeping rejection)
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605172000-etzhayyim-kotoba-substrate
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605221411-etzhayyim-artificial-organism-ecosystem
  - adr-2605232345-unispsc-actor-as-organism
  - adr-2605240200-unispsc-organism-kaizen-self-reflection
  - adr-2605241500-etzhayyim-dataset-cid-substrate
  - adr-2605262100-baien-moemoekyun-r1-phase0-coding-train
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605262400-public-data-organism-ipfs-ingestion
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
related:
  - adr-2605262200-charter-rider-2i-baien-train-rental-carveout
  - adr-2605262300-baien-moemoekyun-r2-runpod-b200-train-architecture
supersedes: []
superseded_by: []
---

# ADR-2605262800: Global legal-corpus ingestion via IPFS-pinned DataLad subdatasets

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

ADR-2605262400 established the **public-data ingestion architecture**
for the artificial-organism ecosystem: two-path (PERCEPTION hot /
TRAINING cold), 14 gates, passive-only network discipline, PII filter
+ Charter Rider §2 scan double layer, G13 fleet-internal carve-out for
NC-licensed sources. Buckets covered: `geo/` / `netreg/` / `routing/`
/ `dns/` / `web/`.

What 2605262400 deliberately did NOT cover is **legal documents**:
statutes, regulations, case law, treaties, procedures, templates,
commentary. The user's 2026-05-26 follow-up request was explicit:

> 全世界の法律文書、手続きなどを ingest, datalad, ipfs で保存して

Concurrently, ADR-2605262700 (this session) creates **chigiri** as the
religious-corp legal procedure substrate. chigiri's cells need a
canonical, content-addressed, charter-compliant legal corpus to:

- run precedent search at mediation time (`dispute_mediation`);
- validate IP-license-claim findings against current statute
  (`ip_licensing`);
- route donation tax receipts per jurisdictional rules
  (`tax_receipt`);
- maintain L0..L6 steward labor classification correctness across
  jurisdictions (`employment_compliance`);
- handle DSAR (data subject access requests) per GDPR / CCPA / APPI /
  LGPD (`data_privacy`);
- ground Transparent Force authorization in IHL (`transparent_force_authorization`).

Two existing actors already touch the legal-data domain peripherally:

- `20-actors/hanrei/` — bibliography-style global case-law actor
  (75 jurisdictions + 8 international courts + JP deep coverage via
  courts.go.jp + e-Gov + 官報 + Wikidata). Its data model is graph-
  oriented (CaseRecord / Jurisdiction / CitationEdge / etc.).
- `20-actors/bunken/` — global literature actor with 9-scheme multi-
  DID (NDL / LCCN / OCLC / DOI / ARK / etc.) that incidentally covers
  legal commentary.

Neither is a content-addressed corpus substrate, and neither is
chigiri-ready. hanrei produces a graph projection; chigiri needs the
underlying full text addressable by CID for precedent lookup +
quotation. This ADR sits below hanrei: hanrei is the projection layer,
this ADR is the raw-bytes layer.

Constraints (inherited from ADR-2605262400 + Charter Rider):

- **Charter Rider §2(a)-(h)** scan on every shard at ingest time;
- **PII filter** runs before Charter Rider scan (but with legal-
  specific adjustments — see §6 below; published court records ARE
  public by nature, but jurisdiction-specific publication redaction
  rules vary);
- **Murakumo-only inference** (ADR-2605215000) — no vendor LLM API
  callout for classification of legal text at organism-tick time;
- **Passive-only network discipline** — no live scraping at organism
  tick; only pre-captured public archives;
- **kotoba storage substrate** (ADR-2605262130) — corpus in MST +
  IPFS + Base L2 anchor; no projection backend introduced here;
- **G13 fleet-internal `-nc-` carve-out** — for any commentary
  corpus that comes in as CC-BY-NC (very limited — most law is
  public-domain or open-government-license);
- **NO proprietary commentary** — Westlaw / LexisNexis / Bloomberg
  Law / similar feeds are PROHIBITED per Charter Rider §2(e) anti-
  gatekeeping + §2(c) covert-ops vendor concern (these vendors run
  closed-tracking on legal-research queries that could expose
  member legal posture).

User decision (2026-05-26 follow-up):

- **Ingest globally** — all major jurisdictions where open-government
  archives exist;
- **Use DataLad + IPFS** — same substrate as ADR-2605262400;
- **Powering chigiri implementation coverage** — this ADR is sibling
  to ADR-2605262700, shipped same session;
- **Implementation coverage** — gap-audit closure across actors,
  particularly the legal substrate that chigiri / manabi / hanrei
  depend on.

# Decision

Adopt a legal-corpus ingestion architecture as the `law/` bucket
family addition to ADR-2605262400, with 5 sensor families, ~25+
fetchers (path-reserved at R0; W1 ships 5 anchor sources), jurisdiction-
dependent judicial-party redaction policy, and 4-phase delivery W0..W4.

## §1. Bucket taxonomy (extends ADR-2605262400 §2)

```
90-docs/baien/datasets/law/
├── statutes/
│   ├── us-usc/<rev>/                  # US Code (public domain; Office of Law Revision Counsel)
│   ├── us-cfr/<rev>/                  # Code of Federal Regulations (public domain; GPO)
│   ├── us-federal-register/<rev>/     # Federal Register daily issuances
│   ├── uk-legislation/<rev>/          # legislation.gov.uk (OGL v3.0)
│   ├── eu-eurlex/<rev>/               # EUR-Lex consolidated treaties + regulations + directives
│   ├── jp-egov/<rev>/                 # e-Gov 法令 API (CC-BY 4.0)
│   ├── jp-kanpo/<rev>/                # 官報 (public domain)
│   ├── de-bgbl/<rev>/                 # Bundesgesetzblatt (open)
│   ├── fr-legifrance/<rev>/           # Légifrance (Étalab Open License 2.0)
│   ├── it-normattiva/<rev>/           # Normattiva (open)
│   ├── kr-klic/<rev>/                 # Korean Law Information Center (open)
│   ├── ca-canlii-statutes/<rev>/      # Canada CanLII statutes (Tier-B mixed)
│   ├── au-austlii-statutes/<rev>/     # Australia AustLII statutes (Tier-B mixed)
│   ├── br-senado/<rev>/               # Brazilian Senate / Planalto (public)
│   ├── in-india-code/<rev>/           # India Code (open)
│   └── cn-npc/<rev>/                  # China NPC statutes (public; §2(g) state-aligned flag)
├── cases/
│   ├── us-cap/<rev>/                  # Caselaw Access Project (Harvard; CC0 most volumes)
│   ├── us-courtlistener/<rev>/        # CourtListener (Free Law Project; mostly public domain)
│   ├── us-recap-pacer/<rev>/          # RECAP archive (PACER docs; public records)
│   ├── uk-find-case-law/<rev>/        # UK Find Case Law via The National Archives (OGL)
│   ├── eu-cjeu/<rev>/                 # CJEU case law (via EUR-Lex)
│   ├── jp-saibansho/<rev>/            # 裁判所 判例 (public domain via courts.go.jp)
│   ├── coe-echr-hudoc/<rev>/          # ECHR HUDOC (open)
│   ├── ca-canlii-cases/<rev>/         # Canada CanLII cases (Tier-B)
│   ├── au-austlii-cases/<rev>/        # Australia AustLII cases (Tier-B)
│   ├── in-indian-kanoon/<rev>/        # Indian Kanoon (Tier-B; mostly open)
│   ├── br-stj/<rev>/                  # Brazilian STJ jurisprudence (public)
│   └── icj-icc/<rev>/                 # ICJ + ICC public documents
├── treaties/
│   ├── un-treaty-collection/<rev>/    # UN Treaty Collection (public)
│   ├── uncitral-instruments/<rev>/    # UNCITRAL model laws + conventions
│   ├── wipo-treaties/<rev>/           # WIPO treaty corpus
│   ├── hague-conference/<rev>/        # Hague Conference instruments
│   ├── ilo-conventions/<rev>/         # ILO conventions (180+)
│   └── geneva-conventions/<rev>/      # Geneva Conventions + Additional Protocols (ICRC publication)
├── procedures/
│   ├── us-cfr-procedures/<rev>/       # CFR procedural titles (administrative procedure)
│   ├── us-federal-rules/<rev>/        # FRCP / FRCrP / FRE (public domain)
│   ├── uk-gov-procedures/<rev>/       # GOV.UK procedure pages (OGL)
│   ├── jp-koku-zei/<rev>/             # 国税庁 通達 (public)
│   ├── jp-homusho-tokki/<rev>/        # 法務省 登記 procedures
│   ├── eu-procedures-portal/<rev>/    # EU procedures (open)
│   └── international-arbitration-rules/<rev>/  # AAA / JCAA / SIAC / ICC arbitration rules (open publishing)
├── templates/                         # chigiri-consumable templates (separate from raw law)
│   ├── apache-2.0-licenses/<rev>/     # Apache 2.0 LICENSE corpus (Apache Foundation)
│   ├── creative-commons-licenses/<rev>/ # CC license corpus (Creative Commons)
│   ├── etzhayyim-charter-rider/<rev>/ # Our own Rider corpus
│   ├── covenant-ceremony/<rev>/       # Religious-corp covenant templates (Apache 2.0)
│   ├── dispute-mediation/<rev>/       # Mediation procedure templates
│   ├── donation-tax-receipt/<rev>/    # Per-jurisdiction tax-receipt templates
│   └── data-privacy-dsar/<rev>/       # DSAR templates per GDPR / CCPA / APPI / LGPD
└── commentary/                        # Annotated commentary (mostly Tier-A; some Tier-B)
    ├── oecd-legal-instruments/<rev>/  # OECD model documents
    ├── nist-publications/<rev>/       # NIST SP 800 series (cybersecurity legal-adjacent)
    └── council-of-europe-handbooks/<rev>/  # CoE handbooks (open)
```

## §2. Source ladder (license × tier × admissibility)

| Source | Coverage | License | Tier | Fetcher | Bucket | Train? | Perceive? |
|---|---|---|---|---|---|---|---|
| US USC | federal statutes | public domain | A | new `us_usc.py` | `statutes/us-usc/` | yes | yes |
| US CFR | federal regulations | public domain | A | new `us_cfr.py` | `statutes/us-cfr/` + `procedures/us-cfr-procedures/` | yes | yes |
| US Federal Register | daily regulatory issuances | public domain | A | new `us_federal_register.py` | `statutes/us-federal-register/` | yes | yes |
| US FRCP / FRCrP / FRE | federal procedural rules | public domain | A | new `us_federal_rules.py` | `procedures/us-federal-rules/` | yes | yes |
| US Caselaw Access Project | US case law (1658-2018) | CC0 (most) | A | new `caselaw_access_project.py` | `cases/us-cap/` | yes | yes |
| US CourtListener | US case law (modern) | public domain mostly | A | new `courtlistener.py` | `cases/us-courtlistener/` | yes | yes |
| US RECAP/PACER bulk | federal court docs | public record (PACER is public, fee-gated; RECAP is the open archive) | A | new `recap_pacer.py` | `cases/us-recap-pacer/` | yes | yes |
| UK legislation.gov.uk | UK statutes | OGL v3.0 | A | new `uk_legislation.py` | `statutes/uk-legislation/` | yes | yes |
| UK Find Case Law (TNA) | UK case law | OGL v3.0 | A | new `uk_find_case_law.py` | `cases/uk-find-case-law/` | yes | yes |
| UK GOV.UK procedures | procedural guidance | OGL v3.0 | A | new `uk_govuk_procedures.py` | `procedures/uk-gov-procedures/` | yes | yes |
| EU EUR-Lex | EU treaties + regs + directives + CJEU case | "free reuse, with citation" — A-compatible | A | new `eu_eurlex.py` | `statutes/eu-eurlex/` + `cases/eu-cjeu/` | yes | yes |
| JP e-Gov 法令 | JP statutes | CC-BY 4.0 (egov API) | A | new `jp_egov.py` | `statutes/jp-egov/` | yes | yes |
| JP 裁判所 判例 | JP case law | public domain | A | new `jp_saibansho.py` | `cases/jp-saibansho/` | yes | yes |
| JP 官報 | JP gazette | public domain | A | new `jp_kanpo.py` | `statutes/jp-kanpo/` | yes | yes |
| JP 国税庁 通達 | tax-procedure guidance | public | A | new `jp_kokuzei.py` | `procedures/jp-koku-zei/` | yes | yes |
| Council of Europe ECHR HUDOC | ECHR case law | open | A | new `coe_hudoc.py` | `cases/coe-echr-hudoc/` | yes | yes |
| UN Treaty Collection | global treaties | public | A | new `un_treaty.py` | `treaties/un-treaty-collection/` | yes | yes |
| UNCITRAL | model laws + conventions | public | A | new `uncitral.py` | `treaties/uncitral-instruments/` | yes | yes |
| WIPO | treaties | public | A | new `wipo.py` | `treaties/wipo-treaties/` | yes | yes |
| Hague Conference | private intl law | public | A | new `hague.py` | `treaties/hague-conference/` | yes | yes |
| ILO | conventions | public | A | new `ilo.py` | `treaties/ilo-conventions/` | yes | yes |
| ICRC Geneva Conventions | IHL | public (ICRC publication) | A | new `icrc_geneva.py` | `treaties/geneva-conventions/` | yes | yes |
| DE Bundesgesetzblatt | DE statutes | open | A | new `de_bgbl.py` | `statutes/de-bgbl/` | yes | yes |
| FR Légifrance | FR statutes + case | Étalab Open License 2.0 | A | new `fr_legifrance.py` | `statutes/fr-legifrance/` | yes | yes |
| IT Normattiva | IT statutes | open | A | new `it_normattiva.py` | `statutes/it-normattiva/` | yes | yes |
| KR KLIC | KR statutes | open | A | new `kr_klic.py` | `statutes/kr-klic/` | yes | yes |
| Canada CanLII | CA statutes + case | mixed (per jurisdiction) | **B** | new `ca_canlii.py` | `statutes/ca-canlii-statutes/` + `cases/ca-canlii-cases/` | yes (Tier-B) | yes |
| Australia AustLII | AU statutes + case | mixed | **B** | new `au_austlii.py` | `statutes/au-austlii-statutes/` + `cases/au-austlii-cases/` | yes (Tier-B) | yes |
| India Code | IN statutes | open | A | new `in_india_code.py` | `statutes/in-india-code/` | yes | yes |
| Indian Kanoon | IN case law | open mostly | **B** | new `in_indian_kanoon.py` | `cases/in-indian-kanoon/` | yes (Tier-B) | yes |
| Brazil Senate / STJ | BR statutes + jurisprudence | public | A | new `br_senado.py` + `br_stj.py` | `statutes/br-senado/` + `cases/br-stj/` | yes | yes |
| China NPC | CN statutes | public | A | new `cn_npc.py` | `statutes/cn-npc/` | yes (with §2(g) flag) | yes (with §2(g) flag) |
| ICJ / ICC | international court docs | public | A | new `icj_icc.py` | `cases/icj-icc/` | yes | yes |
| OECD legal instruments | OECD model docs | public | A | new `oecd_legal.py` | `commentary/oecd-legal-instruments/` | yes | yes |
| NIST SP 800 series | cybersecurity legal-adjacent | public (US gov) | A | new `nist_sp800.py` | `commentary/nist-publications/` | yes | yes |
| CoE handbooks | CoE legal handbooks | open | A | new `coe_handbooks.py` | `commentary/council-of-europe-handbooks/` | yes | yes |
| Apache 2.0 LICENSE corpus | OSS license texts | Apache 2.0 | A | new `apache_license_corpus.py` | `templates/apache-2.0-licenses/` | yes | yes |
| Creative Commons license corpus | CC license texts | CC | A | new `cc_license_corpus.py` | `templates/creative-commons-licenses/` | yes | yes |
| **Westlaw / LexisNexis / Bloomberg Law / Wolters Kluwer** | proprietary commentary | proprietary | **PROHIBITED** | NONE | NONE | NEVER | NEVER |

Tier-C admittance is intentionally LIMITED in this ADR — most law is
public by nature, and the cases where commentary is NC-licensed
(e.g., Beck-online for DE, individual law-school journal articles)
are explicitly out-of-scope for this ADR. If a future use case
demands NC commentary, a separate ADR with Council Lv6+ approval
+ G13 `-nc-` infix carve-out + SBT-gate ladder is required.

Proprietary commentary feeds (Westlaw / LexisNexis / Bloomberg Law /
Wolters Kluwer) are PROHIBITED per Charter Rider §2(e) anti-
gatekeeping + §2(c) covert-ops vendor concern (these vendors maintain
closed query-tracking infrastructure that could expose member legal
posture to commercial parties).

## §3. Sensor abstraction (5 families under `kotodama.organism.sensors.legal.*`)

```python
# 70-tools/e7m-dataset reuses the DatasetSensor Protocol from ADR-2605262400 §3.
# Legal sensors specialize as follows:

class LegalStatuteSensor(DatasetSensor):
    jurisdiction: str   # ISO-3 (e.g., "USA", "JPN", "DEU") OR supra ("EU", "UN", "COE", "OECD")
    statute_class: Literal["constitution", "code", "act", "regulation", "directive", "rule"]
    # Observation = (citation, title, body_excerpt, in_force_at, license_tag)

class LegalCaseSensor(DatasetSensor):
    court_system: str   # e.g., "us-supreme", "us-circuit", "jp-supreme", "echr", "icj"
    # Observation = (citation, court, decision_date, parties_redacted, holding_excerpt, license_tag)

class LegalTreatySensor(DatasetSensor):
    treaty_corpus: str  # "un-treaty" | "uncitral" | "wipo" | "hague" | "ilo" | "geneva" | "icrc"
    # Observation = (treaty_id, title, party_states, in_force_at, body_excerpt, license_tag)

class LegalProcedureSensor(DatasetSensor):
    procedural_body: str  # jurisdiction or agency
    procedure_class: Literal["administrative", "judicial", "regulatory", "tax", "registry"]
    # Observation = (procedure_id, title, steps_excerpt, jurisdiction, license_tag)

class LegalTemplateSensor(DatasetSensor):
    template_corpus: str  # "apache-licenses" | "cc-licenses" | "covenant-ceremony" | ...
    template_class: Literal["license", "ceremony", "mediation", "tax-receipt", "dsar", "ip-claim"]
    # Observation = (template_id, title, body, jurisdiction?, license_tag, chigiri_consumer_cell_hint?)
```

Wave-1 sensor implementations (5 anchor sources):

| Sensor module | Subdataset bucket | Observation shape |
|---|---|---|
| `us_usc_sensor.py` (LegalStatuteSensor[USA]) | `statutes/us-usc/` | (USC title.section.subsection, full text, public-domain) |
| `us_cfr_sensor.py` (LegalStatuteSensor[USA]) | `statutes/us-cfr/` | (CFR title.part.section, full text, public-domain) |
| `jp_egov_sensor.py` (LegalStatuteSensor[JPN]) | `statutes/jp-egov/` | (法令番号, full text, CC-BY 4.0) |
| `eu_eurlex_sensor.py` (LegalStatuteSensor[EU]) | `statutes/eu-eurlex/` | (CELEX, full text, free-reuse) |
| `uk_legislation_sensor.py` (LegalStatuteSensor[GBR]) | `statutes/uk-legislation/` | (UK statute id, full text, OGL v3.0) |

W2+ adds case-law sensors (CAP / CourtListener / 裁判所 / HUDOC / CJEU),
treaty sensors, procedure sensors, template sensors.

## §4. Training corpus assembly (cold path)

Recipe additions under `70-tools/baien-moemoekyun-train/recipes/legal/`:

- `legal-foundations-r1.toml` — Tier-A statutes + cases (USC + UK
  legislation + e-Gov + EUR-Lex + CAP) for general legal-reasoning;
- `chigiri-procedural-r1.toml` — Procedural rules + templates (CFR
  procedures + UK GOV.UK procedures + Apache 2.0 corpus + Charter
  Rider corpus + covenant ceremony templates) for chigiri-specific
  reasoning;
- `ihl-defensive-r1.toml` — IHL corpus (Geneva Conventions + Additional
  Protocols + ICCPR + ICJ jurisprudence) for transparent-force
  authorization reasoning support;
- `manabi-legal-literacy-r1.toml` — Jurisdiction-spanning rights
  framework (UDHR + ICCPR + ICESCR + GDPR + regional human rights
  conventions) for manabi public-rights education curriculum;
- `tax-receipt-multi-juris-r1.toml` — Tax statute + charity-recognition
  regulation per jurisdiction for chigiri's tax_receipt cell.

Each recipe follows ADR-2605262400 §4 `corpus-recipe.toml` schema with
source CIDs frozen, license tier propagated, Charter Rider §2 + PII
+ judicial-party-redactor scan at assembly time.

Note: Most recipes are entirely Tier-A and produce publishable
artifacts. Recipes that include any Tier-B source (CanLII / AustLII /
Indian Kanoon) carry `-tierB-` infix in `target_artifact` and respect
the appropriate license-propagation rules.

## §5. Kaizen rules (2 new — extend ADR-2605262400 R7-R9)

| Rule ID | Trigger | Proposal |
|---|---|---|
| **R10-statute-staleness** | LegalStatuteSensor `latest_pin().createdAt` older than 90 days for actively-amended jurisdictions (US / UK / EU / JP / DE / FR) OR 365 days for slower-revision sources | "re-pull + republish; alert chigiri cells that consume this jurisdiction" |
| **R11-case-law-jurisdiction-drift** | LegalCaseSensor for a given court system shows >20% citation references to statutes whose pinned version is stale | "schedule re-pull of cited statute corpora + re-run derived training recipes" |

R10 + R11 extend the R7-R9 stack from ADR-2605262400; same KaizenProposal
contract, same Council Lv6+ escalation pattern.

## §6. Judicial-party redaction policy (legal-specific, extends ADR-2605262400 §6 PII filter)

New module: `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/sensors/legal/judicial_party_redactor.py`.

Policy table (jurisdiction → publication redaction practice):

| Jurisdiction | Practice | chigiri redaction action |
|---|---|---|
| US (federal + most states) | parties named in published opinions; minors sometimes initialed | Pass-through; preserve as published. Reject reasonable de-identification requests at corpus level (out of scope; right-to-be-forgotten not US-recognized for court records). |
| UK | parties named; some family-court / immigration matters anonymized | Pass-through; honor TNA anonymization where present |
| EU CJEU | parties named in published judgments | Pass-through |
| ECHR | applicants sometimes anonymized at request | Honor HUDOC anonymization; pass-through otherwise |
| DE | BGH publishes pseudonymized party names (Pseudonymisierung) | Pass-through pseudonymized form |
| FR | similar pseudonymization practice for individuals | Pass-through |
| JP 最高裁 / 高裁 / 地裁 | parties anonymized in published 判例 (個人情報保護法 + 裁判所 redaction practice) | Pass-through anonymized form |
| JP 家庭裁判所 / 少年裁判所 | strict anonymization | Pass-through; reject if anonymization broken upstream |
| CA / AU | mixed per court | Pass-through per source |
| IN | parties typically named | Pass-through |
| BR | parties typically named in jurisprudence | Pass-through |
| CN | parties typically anonymized in NPC summaries | Pass-through |
| IHL / treaty corpus | state-party names public; victim names sometimes redacted | Pass-through |

**Policy summary**: chigiri does NOT re-identify or de-anonymize. The
`judicial_party_redactor` honors per-jurisdiction publication
redaction state. The general PII filter (ADR-2605262400 §6 —
emails / E.164 / postal addresses / WHOIS registrant blocks) ALSO
runs on legal corpora; non-party PII (e.g., random email addresses
in court exhibits) gets the standard redaction treatment.

A right-to-be-forgotten DSAR (GDPR Art. 17, CCPA) on a published court
opinion is a known difficult area. The policy at R0:

- DSAR received via chigiri's `data_privacy` cell;
- Forward to upstream publisher (TNA / HUDOC / CAP / CourtListener
  rights team);
- chigiri does NOT unilaterally remove the published opinion from
  our IPFS pin without upstream removal first;
- IF upstream removes, chigiri's W1 fetcher refresh propagates the
  removal at next cadence cycle.

This is documented in `00-contracts/lexicons/com/etzhayyim/chigiri/dataPrivacyRequest.json` (R2 schema).

## §7. Passive-only network discipline (inherits ADR-2605262400 §7)

- chigiri MUST NOT perform live scraping of courts.go.jp /
  legislation.gov.uk / EUR-Lex at organism-tick time;
- chigiri MUST NOT submit live API queries to commercial legal-research
  vendors (the prohibition is broader than ADR-2605262400 §7: it
  includes lawyer-research vendors regardless of tier);
- Pre-published archive fetches via `e7m-dataset` at ingest time only,
  same gate stack;
- WAYBACK fallback: if upstream removes a document, allow Internet
  Archive Wayback retrieval at ingest time WITH explicit
  `wayback_source=true` flag + Council attestation for the specific
  document (R3 gate).

## §8. Wave delivery plan

| Wave | Scope | Estimate |
|---|---|---|
| **W0 (this ADR)** | ADR + sensor scaffold + bucket reservation + recipe template skeletons + 25 fetcher path-reserve + Status row 68 + deps.toml entries | this commit (today) |
| **W1 (5 anchor sources, Tier-A statutes)** | US USC + US CFR + UK legislation + EU EUR-Lex + JP e-Gov fetchers (5) + corresponding 5 sensors + `legal-foundations-r1.toml` recipe + `judicial_party_redactor.py` first cut + R10 + R11 Kaizen rules | 4-5 days |
| **W2 (case law + procedures Tier-A)** | US CAP + US CourtListener + JP 裁判所 + HUDOC + CJEU fetchers (5) + sensors + US Federal Rules + UK GOV.UK procedures + JP 国税庁 fetchers (3) + `chigiri-procedural-r1.toml` recipe | 5-7 days |
| **W3 (treaties + templates)** | UN Treaty + UNCITRAL + WIPO + Hague + ILO + ICRC Geneva fetchers (6) + treaty sensors + Apache 2.0 / CC license / Charter Rider / covenant-ceremony / mediation / tax-receipt / DSAR template corpora (7) + template sensors + `ihl-defensive-r1.toml` + `manabi-legal-literacy-r1.toml` + `tax-receipt-multi-juris-r1.toml` recipes | 5-7 days |
| **W4 (regional + Tier-B + CN §2(g) flagging)** | DE BGBl + FR Légifrance + IT Normattiva + KR KLIC + India Code + Brazil Senate/STJ + ICJ/ICC + OECD + NIST + CoE handbooks fetchers (10) + sensors + Tier-B handling (CanLII + AustLII + Indian Kanoon) + China NPC with §2(g) flag | 7-10 days |

W1 lands in a follow-up commit; W2 / W3 / W4 each get their own commit
and individual Status table updates.

## §9. Gates (14)

- **G1**: Every legal corpus shard runs Charter Rider §2(a)-(h) scan
  at `e7m-dataset add` time. Fail = block.
- **G2**: PII filter (ADR-2605262400 §6) runs BEFORE Charter Rider
  scan. `judicial_party_redactor` runs in the same pass with
  jurisdiction-aware policy.
- **G3**: `replicationMin: 2` per ADR-2605241500 §D6. Legal corpora
  pin on at least 2 fleet nodes before any chigiri cell may bind to
  them.
- **G4**: `LegalStatuteSensor.refresh_cadence_sec` MUST NOT undercut
  upstream publisher cadence (US Federal Register = daily; JP e-Gov
  = ~weekly batch; UK legislation = daily; etc.). Per-source minimum
  documented in fetcher.
- **G5**: Cold-path corpus recipes with any Tier-B source MUST encode
  `-tierB-` infix in `target_artifact`. Tier-C source (if any in
  future) MUST encode `-nc-` infix per ADR-2605262100 G13 precedent.
- **G6**: Template corpus (`law/templates/`) is structurally separate
  from raw-law corpus (`law/statutes/`, `law/cases/`, etc.).
  chigiri-template-substitution flows MUST NOT mix raw statute text
  into templates (avoid accidental sub-licensing or accidental UPL).
- **G7**: Inference of any artifact derived from this ADR's data
  flows through Murakumo fleet (ADR-2605215000). NO vendor LLM
  callout for legal-text classification.
- **G8**: Sensor implementations MUST NOT perform active network
  probes (inherits ADR-2605262400 G8); legal-vendor sites (Westlaw /
  Lexis / Bloomberg Law / etc.) are explicitly added to the lint
  hook deny-list at W1.
- **G9**: Sensor `hot_sample(pin, n)` is deterministic given fixed
  `pin.cid`. Required for Kaizen delta tracking.
- **G10**: `corpus-recipe.toml` files under
  `70-tools/baien-moemoekyun-train/recipes/legal/` are committed to
  git. The recipe IS the audit trail.
- **G11**: Charter Rider scanner FP rate ≤5% over 24h sliding window
  per legal sensor; R11 threshold-revision pathway is the same as
  ADR-2605262400 R8.
- **G12**: Sensor refresh cadence MUST NOT undercut upstream cadence
  (G4 cross-ref).
- **G13**: Every ingestion emits one
  `com.etzhayyim.substrate.datasetPin` record (same contract).
- **G14**: Every commit under this ADR (W1+) appends to
  `90-docs/baien/datasets.jsonl` and additionally appends to
  `90-docs/baien/legal-corpus-manifest.jsonl` (new — chigiri-readable
  index).

## §10. Non-goals (12)

- **N1**: NOT a commercial legal-research substitute. We index public
  law; we do not replace Westlaw / Lexis / Bloomberg-style annotated
  research workflows. (Where annotation is needed, chigiri R3
  considers a Council-approved open-annotation corpus, separately
  ADR-gated.)
- **N2**: NOT a live court-record scraping system. Passive archive
  only, same as ADR-2605262400 §7.
- **N3**: NOT a de-anonymization / re-identification tool. Honoring
  upstream publication redaction is the policy (`judicial_party_redactor`).
- **N4**: NOT a commercial-vendor data-feed integrator. Westlaw /
  Lexis / Bloomberg Law / Wolters Kluwer PROHIBITED.
- **N5**: NOT a legal-advice generator. chigiri G14 (UPL) applies
  identically to corpus consumers; legal-text retrieval ≠ legal advice.
- **N6**: NOT a court-filing system. We don't file pleadings; we
  consume / cite published opinions and statutes only.
- **N7**: NOT a paywall-bypass tool. PACER access goes through the
  RECAP open archive (which is the public-record output of paid
  PACER queries by others); we do not bypass PACER fees ourselves.
- **N8**: NOT a contract-drafting AI. Templates are checked-in,
  not generated. R3 may consider a Murakumo-only template-completion
  helper, separately ADR-gated.
- **N9**: NOT a substitute for human counsel. chigiri G14 (UPL).
- **N10**: NOT a federation contract for cross-religious-corp legal
  data sharing. Internal to etzhayyim.
- **N11**: NOT a substrate engine replacement. ADR-2605262130 (Kotoba)
  is canonical; this ADR adds data, not engines.
- **N12**: NOT a vendor-LLM inference path. Inference Murakumo-only
  (ADR-2605215000); train rental amendment ADR-2605262200 is
  separate and Council-ratify-pending.

# Consequences

**Positive**:

- chigiri (ADR-2605262700) gets a real corpus to consume — without
  this ADR, chigiri's procedural cells would have no precedent
  / statute / template substrate;
- hanrei gains a content-addressed full-text layer beneath its graph
  projection; future hanrei queries can include "show me USC §17
  section 107 as cited by this 9th Circuit opinion" with both
  resolving to CIDs;
- manabi (education actor) gets jurisdictional rights-framework
  corpora for public-legal-literacy curriculum (UDHR + GDPR + CCPA
  etc.);
- baien-distill specialist legal-reasoning artifacts become feasible
  with proper license-tier propagation;
- The proprietary-feed prohibition (Westlaw / Lexis / Bloomberg)
  documents and structurally enforces a Charter Rider §2(e) +
  §2(c) constitutional concern that has been latent.

**Negative / cost**:

- Disk + IPFS pin footprint is substantial. Rough W1 estimate per
  node: USC ~ 500 MB / CFR ~ 2 GB / UK legislation ~ 500 MB / EUR-Lex
  ~ 5 GB / e-Gov ~ 1 GB → ~9 GB per node W1. W2 (case law) adds CAP
  ~ 100 GB (the largest single delta). W3 (treaties + templates) ~ 2
  GB. W4 (regional) ~ 5 GB. Total fleet-wide post-W4 ≈ 120 GB per
  node × 10 nodes = 1.2 TB (well within fleet capacity).
- Some sources require terms-of-use acceptance (CAP, CourtListener
  ToU). Acceptance flag file in `~/.etzhayyim/source-acceptance/`
  per ADR-2605262400 pattern.
- Judicial-party-redactor policy is jurisdiction-complex and will
  require legal-counsel review at W4 (German Pseudonymisierung
  practice is subtle; JP 家庭裁判所 anonymization rules vary by case
  type). Public Fund contract for jurisdictional review covering W4
  is recommended.
- CAP / CourtListener cadence is slow (CAP is largely a 2018-frozen
  archive; CourtListener is the modern living one) — chigiri must
  understand cadence per sensor.
- China NPC §2(g) flag is a known sensitivity — ingested as
  authoritative-source-of-record for jurisdictional fact, NOT as a
  doctrinal source for chigiri reasoning. Documented in
  `cn_npc.py` fetcher header and `corpus-recipe.toml` `source_note`
  field.

**Forward-compatibility**:

- Adding new jurisdictions follows the W4 pattern (per-jurisdiction
  fetcher + sensor + Council attestation row);
- Adding annotated commentary (R3+) requires separate ADR with
  G13 fleet-internal `-nc-` carve-out;
- Cross-corpus citation graph (statute ↔ case ↔ commentary) is a
  natural R3 deliverable that runs entirely off the CIDs ingested
  here (no new substrate engine).

# Alternatives Considered

1. **Cite-only architecture (no full-text ingestion)**. Rejected —
   chigiri's IP-licensing / dispute-mediation cells need full-text
   precedent for substantive grounding; citations alone are
   inadequate.

2. **Use hanrei's existing graph projection as the chigiri corpus**.
   Rejected — hanrei is a graph (CaseRecord / Jurisdiction /
   CitationEdge) without full-text addressability; mixing the two
   responsibilities violates actor SRP and complicates
   migration to a content-addressed layer.

3. **Include Westlaw / Lexis / Bloomberg under attestation-safeguard
   carve-out**. Rejected — Charter Rider §2(e) + §2(c). The vendor
   tracking exposure on member legal posture is a structural risk;
   no attestation can mitigate it within the religious-corp's
   data-sovereignty discipline.

4. **Use vendor LLM for legal text classification at ingest time**.
   Rejected — ADR-2605215000 Murakumo-only.

5. **Defer this ADR until W1 of ADR-2605262400 ships**. Considered.
   Rejected — both ADRs share the same DatasetSensor protocol;
   shipping the law/ bucket scaffold in parallel allows chigiri R1
   to consume law/ bucket without waiting for two sequential ADR
   cycles.

6. **Skip judicial-party-redactor — published court records are
   public**. Rejected — German + French + JP + ECHR pseudonymization
   practice is jurisdiction-dependent, and importing pseudonymized
   text and re-publishing the un-pseudonymized variant (if we had
   one) would be a regression. Pass-through honoring upstream
   redaction is the correct discipline.

7. **Bundle templates into the same recipe as raw statutes**. Rejected
   per G6 — separating templates from raw law avoids accidental
   sub-licensing of statute text into chigiri-generated documents
   and protects against UPL drift.

# References

- ADR-2605170900 — etzhayyim/root canonical home for ADRs
- ADR-2605172000 — kotoba substrate
- ADR-2605192100 — Mission Charter (Wellbecoming, 反個人主義, 非終末論)
- ADR-2605192200 — Charter Compliance Rider v2.0
- ADR-2605215000 — Inference Murakumo-only
- ADR-2605221411 — Artificial Organism Ecosystem
- ADR-2605232345 — UNSPSC actor as organism
- ADR-2605240200 — UNSPSC organism Kaizen self-reflection
- ADR-2605241500 — Dataset CID substrate (DataLad + annex + IPFS)
- ADR-2605262100 — baien-moemoekyun R1 Phase 0 (G13 NC carve-out precedent)
- ADR-2605262130 — Kotoba storage substrate unification
- ADR-2605262400 — Public-data organism IPFS ingestion (parent — geo/netreg/routing/dns/web buckets)
- ADR-2605262700 — chigiri legal procedure substrate R0 (sibling — primary consumer)
- CHARTER-RIDER.md §2 — 8 prohibited categories; §2(c) covert-ops + §2(e) anti-gatekeeping ground the Westlaw/Lexis/Bloomberg prohibition
- `70-tools/e7m-dataset/README.md` — fetcher + publish-ipfs + datasetPin contract
- `20-actors/hanrei/CLAUDE.md` — case-law graph actor (upstream graph consumer of this corpus)
- `20-actors/bunken/CLAUDE.md` — literature actor (overlap on commentary corpus)
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/sensors/` — Wave 1 sensor home
