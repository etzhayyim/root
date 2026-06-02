"""Captured from Kysely migration 20260507230100_seed_domain_catalog_and_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507230100_seed_domain_catalog_and_bpmn"
down_revision = 'r_20260507230000_vertex_domain_schema'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_domain_tld (vertex_id, owner_did, sensitivity_ord, tld, operator, '
         'restricted, eligibility_summary, eligibility_policy_url, verification_required, '
         'typical_uses, notes, status, created_at, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, 0, $3, $4, CAST($5 AS boolean), $6, $7, CAST($8 AS boolean), $9, $10, '
         "'active', $11, $12, $13, $14\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_tld WHERE vertex_id = $15)\n'
         '  ',
  'parameters': ['at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/law',
                 'did:web:domain.etzhayyim.com',
                 '.law',
                 'GoDaddy Registry (Registry Services, LLC)',
                 True,
                 'Restricted to legal professionals (lawyers / barristers / solicitors / law firms '
                 '/ law schools / courts / legal regulators) appropriately licensed by a '
                 'recognized accredited body or authorized government authority. Independent '
                 'verification agent may request supporting documentation; failure to remain '
                 'eligible is grounds for cancellation without refund.',
                 'https://domains.registry.godaddy/policiespdf/LAW-POL-001-Eligibility_Policy-1.0.pdf',
                 True,
                 'law-firm primary domain, individual lawyer brand, bar-association portal',
                 'Policy §1.1 uses jurisdiction-neutral language (no approved-regulator '
                 'allow-list); JP bengoshi via JFBA, UK solicitor via SRA, US lawyer via state bar '
                 'all qualify. Continuing-eligibility rule §1.1: contact registrar within 14 days '
                 'if license lapses.',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/law']},
 {'sql': '\n'
         '    INSERT INTO vertex_domain_tld (vertex_id, owner_did, sensitivity_ord, tld, operator, '
         'restricted, eligibility_summary, eligibility_policy_url, verification_required, '
         'typical_uses, notes, status, created_at, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, 0, $3, $4, CAST($5 AS boolean), $6, $7, CAST($8 AS boolean), $9, $10, '
         "'active', $11, $12, $13, $14\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_tld WHERE vertex_id = $15)\n'
         '  ',
  'parameters': ['at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/lawyer',
                 'did:web:domain.etzhayyim.com',
                 '.lawyer',
                 'Identity Digital (formerly Donuts/Afilias)',
                 False,
                 'Open generic TLD — no occupational eligibility requirement. Anyone may register. '
                 'Trademark / UDRP rights protections apply but no licensing-of-law check.',
                 'https://www.identity.digital/policies',
                 False,
                 'lawyer marketing site, legal-tech product brand, podcast',
                 'Despite the suggestive name, registry policy is open. Use case is closer to .com '
                 'than to .law.',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/lawyer']},
 {'sql': '\n'
         '    INSERT INTO vertex_domain_tld (vertex_id, owner_did, sensitivity_ord, tld, operator, '
         'restricted, eligibility_summary, eligibility_policy_url, verification_required, '
         'typical_uses, notes, status, created_at, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, 0, $3, $4, CAST($5 AS boolean), $6, $7, CAST($8 AS boolean), $9, $10, '
         "'active', $11, $12, $13, $14\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_tld WHERE vertex_id = $15)\n'
         '  ',
  'parameters': ['at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/legal',
                 'did:web:domain.etzhayyim.com',
                 '.legal',
                 'Identity Digital',
                 False,
                 'Open generic TLD — no occupational eligibility requirement. Anyone may register.',
                 'https://www.identity.digital/policies',
                 False,
                 'law-firm marketing, legal information site, citizens-advice service',
                 'Companion to .lawyer; same operator and policy regime.',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/legal']},
 {'sql': '\n'
         '    INSERT INTO vertex_domain_tld (vertex_id, owner_did, sensitivity_ord, tld, operator, '
         'restricted, eligibility_summary, eligibility_policy_url, verification_required, '
         'typical_uses, notes, status, created_at, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, 0, $3, $4, CAST($5 AS boolean), $6, $7, CAST($8 AS boolean), $9, $10, '
         "'active', $11, $12, $13, $14\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_tld WHERE vertex_id = $15)\n'
         '  ',
  'parameters': ['at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/attorney',
                 'did:web:domain.etzhayyim.com',
                 '.attorney',
                 'Identity Digital',
                 False,
                 'Open generic TLD — no occupational eligibility requirement. Anyone may register.',
                 'https://www.identity.digital/policies',
                 False,
                 'US-style attorney marketing site',
                 'Companion to .lawyer/.legal; same operator and policy regime.',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/attorney']},
 {'sql': '\n'
         '    INSERT INTO vertex_domain_registrar (vertex_id, owner_did, sensitivity_ord, '
         'registrar_slug, name, homepage_url, iana_id, jp_friendly, notes, status, created_at, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, 0, $3, $4, $5, NULL, CAST($6 AS boolean), $7, 'active', $8, $9, $10, "
         '$11\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_registrar WHERE vertex_id = $12)\n'
         '  ',
  'parameters': ['at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/cloudflare',
                 'did:web:domain.etzhayyim.com',
                 'cloudflare',
                 'Cloudflare Registrar',
                 'https://domains.cloudflare.com/',
                 True,
                 'Wholesale-priced, ~400 TLDs supported. Does NOT currently support .law (verified '
                 'TLD). Open-policy .lawyer/.legal/.attorney also not on the supported list as of '
                 '2026-05. NS / DNS / proxy can still front a domain registered elsewhere.',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/cloudflare']},
 {'sql': '\n'
         '    INSERT INTO vertex_domain_registrar (vertex_id, owner_did, sensitivity_ord, '
         'registrar_slug, name, homepage_url, iana_id, jp_friendly, notes, status, created_at, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, 0, $3, $4, $5, NULL, CAST($6 AS boolean), $7, 'active', $8, $9, $10, "
         '$11\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_registrar WHERE vertex_id = $12)\n'
         '  ',
  'parameters': ['at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/namecheap',
                 'did:web:domain.etzhayyim.com',
                 'namecheap',
                 'Namecheap',
                 'https://www.namecheap.com/domains/registration/gtld/law/',
                 True,
                 'Handles .law verification flow (requests bar admission documentation when '
                 'needed). Standard registrar for .lawyer/.legal/.attorney. JP customers '
                 'supported.',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/namecheap']},
 {'sql': '\n'
         '    INSERT INTO vertex_domain_registrar (vertex_id, owner_did, sensitivity_ord, '
         'registrar_slug, name, homepage_url, iana_id, jp_friendly, notes, status, created_at, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, 0, $3, $4, $5, NULL, CAST($6 AS boolean), $7, 'active', $8, $9, $10, "
         '$11\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_registrar WHERE vertex_id = $12)\n'
         '  ',
  'parameters': ['at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/godaddy',
                 'did:web:domain.etzhayyim.com',
                 'godaddy',
                 'GoDaddy',
                 'https://www.godaddy.com/tlds/law-domain',
                 True,
                 'Owns the .law registry (Registry Services LLC) and is the default reseller. JP '
                 'localization available.',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/godaddy']},
 {'sql': '\n'
         '    INSERT INTO vertex_domain_registrar (vertex_id, owner_did, sensitivity_ord, '
         'registrar_slug, name, homepage_url, iana_id, jp_friendly, notes, status, created_at, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, 0, $3, $4, $5, NULL, CAST($6 AS boolean), $7, 'active', $8, $9, $10, "
         '$11\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_registrar WHERE vertex_id = $12)\n'
         '  ',
  'parameters': ['at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/eurodns',
                 'did:web:domain.etzhayyim.com',
                 'eurodns',
                 'EuroDNS',
                 'https://www.eurodns.com/domain-extensions/law-domain-registration',
                 True,
                 'EU-based; carries .law and the open-policy legal TLDs. Useful for EU registrant '
                 'compliance.',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/eurodns']},
 {'sql': '\n'
         '    INSERT INTO vertex_domain_registrar (vertex_id, owner_did, sensitivity_ord, '
         'registrar_slug, name, homepage_url, iana_id, jp_friendly, notes, status, created_at, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, 0, $3, $4, $5, NULL, CAST($6 AS boolean), $7, 'active', $8, $9, $10, "
         '$11\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_registrar WHERE vertex_id = $12)\n'
         '  ',
  'parameters': ['at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/dynadot',
                 'did:web:domain.etzhayyim.com',
                 'dynadot',
                 'Dynadot',
                 'https://www.dynadot.com/domain/law',
                 True,
                 'Carries .law plus open-policy legal TLDs.',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/dynadot']},
 {'sql': '\n'
         '    INSERT INTO vertex_domain_registrar (vertex_id, owner_did, sensitivity_ord, '
         'registrar_slug, name, homepage_url, iana_id, jp_friendly, notes, status, created_at, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, 0, $3, $4, $5, NULL, CAST($6 AS boolean), $7, 'active', $8, $9, $10, "
         '$11\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_registrar WHERE vertex_id = $12)\n'
         '  ',
  'parameters': ['at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/join-law',
                 'did:web:domain.etzhayyim.com',
                 'join-law',
                 'Join.Law',
                 'https://www.join.law/',
                 False,
                 'Specialty .law-only registrar with bar-verification workflow built into the '
                 'signup. Geared toward US/UK bar admissions; JP credential acceptance requires '
                 'direct conversation.',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/join-law']},
 {'sql': '\n'
         '    INSERT INTO vertex_domain_registrar (vertex_id, owner_did, sensitivity_ord, '
         'registrar_slug, name, homepage_url, iana_id, jp_friendly, notes, status, created_at, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, 0, $3, $4, $5, NULL, CAST($6 AS boolean), $7, 'active', $8, $9, $10, "
         '$11\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_registrar WHERE vertex_id = $12)\n'
         '  ',
  'parameters': ['at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/squarespace',
                 'did:web:domain.etzhayyim.com',
                 'squarespace',
                 'Squarespace Domains (formerly Google Domains)',
                 'https://domains.squarespace.com/',
                 True,
                 'Generalist registrar; carries .lawyer/.legal/.attorney but not .law verified '
                 'TLD.',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/squarespace']},
 {'sql': '\n'
         '    INSERT INTO vertex_domain_legal_regulator (vertex_id, owner_did, sensitivity_ord, '
         'regulator_slug, name, jurisdiction, kind, public_register_url, notes, status, '
         'created_at, org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, 0, $3, $4, $5, $6, $7, $8, 'active', $9, $10, $11, $12\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_legal_regulator WHERE vertex_id = '
         '$13)\n'
         '  ',
  'parameters': ['at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.legalRegulator/jfba',
                 'did:web:domain.etzhayyim.com',
                 'jfba',
                 'Japan Federation of Bar Associations (日本弁護士連合会 / 日弁連)',
                 'JP',
                 'national-bar',
                 'https://www.nichibenren.or.jp/library/ja/member/search/',
                 'Sole supreme legal regulator in Japan under 弁護士法. Registers bengoshi (弁護士), '
                 'Gaikokuho-Jimu-Bengoshi (外国法事務弁護士 / GJB), legal-professional corporations '
                 '(弁護士法人), and supervises local bar associations. Independent of government '
                 'supervision.',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.legalRegulator/jfba']},
 {'sql': '\n'
         '    INSERT INTO vertex_domain_legal_regulator (vertex_id, owner_did, sensitivity_ord, '
         'regulator_slug, name, jurisdiction, kind, public_register_url, notes, status, '
         'created_at, org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, 0, $3, $4, $5, $6, $7, $8, 'active', $9, $10, $11, $12\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_legal_regulator WHERE vertex_id = '
         '$13)\n'
         '  ',
  'parameters': ['at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.legalRegulator/aba-state-bars',
                 'did:web:domain.etzhayyim.com',
                 'aba-state-bars',
                 'US State Bar Associations (admitted via state supreme courts; ABA accreditation)',
                 'US',
                 'state-bar-network',
                 None,
                 'US lawyer licensure is per-state. Each state bar is the Legal Regulator. ABA '
                 'itself accredits law schools but does not license lawyers.',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.legalRegulator/aba-state-bars']},
 {'sql': '\n'
         '    INSERT INTO vertex_domain_legal_regulator (vertex_id, owner_did, sensitivity_ord, '
         'regulator_slug, name, jurisdiction, kind, public_register_url, notes, status, '
         'created_at, org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, 0, $3, $4, $5, $6, $7, $8, 'active', $9, $10, $11, $12\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_legal_regulator WHERE vertex_id = '
         '$13)\n'
         '  ',
  'parameters': ['at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.legalRegulator/sra-england-wales',
                 'did:web:domain.etzhayyim.com',
                 'sra-england-wales',
                 'Solicitors Regulation Authority (SRA, England & Wales)',
                 'GB-EAW',
                 'national-bar',
                 'https://www.sra.org.uk/consumers/register/',
                 'Statutory regulator of solicitors in England & Wales.',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.legalRegulator/sra-england-wales']},
 {'sql': '\n'
         '    INSERT INTO vertex_domain_legal_regulator (vertex_id, owner_did, sensitivity_ord, '
         'regulator_slug, name, jurisdiction, kind, public_register_url, notes, status, '
         'created_at, org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, 0, $3, $4, $5, $6, $7, $8, 'active', $9, $10, $11, $12\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_legal_regulator WHERE vertex_id = '
         '$13)\n'
         '  ',
  'parameters': ['at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.legalRegulator/iba',
                 'did:web:domain.etzhayyim.com',
                 'iba',
                 'International Bar Association (IBA)',
                 'INTL',
                 'international-association',
                 None,
                 'Not a Legal Regulator in the .law policy sense, but referenced by some '
                 'registrars as a corroborating source for cross-border verification.',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.legalRegulator/iba']},
 {'sql': '\n'
         '    INSERT INTO vertex_domain_eligibility_advice (vertex_id, owner_did, sensitivity_ord, '
         'tld, jurisdiction, regulator_slug, actor_kind, eligible, basis, policy_excerpt, '
         'source_url, effective_at, status, created_at, org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, 0, $3, $4, $5, $6, CAST($7 AS boolean), $8, $9, $10, $11, 'active', "
         '$12, $13, $14, $15\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_eligibility_advice WHERE vertex_id = '
         '$16)\n'
         '  ',
  'parameters': ['at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.eligibilityAdvice/law-jp-bengoshi',
                 'did:web:domain.etzhayyim.com',
                 '.law',
                 'JP',
                 'jfba',
                 'individual-lawyer',
                 True,
                 'JFBA は弁護士法に基づく recognized accredited body であり、日本の bengoshi は currently-licensed '
                 'practitioner として JFBA 弁護士検索 (公開 registry) で identifiable。policy §1.1 の要件 '
                 '(recognized accredited body or authorized government authority) を満たす。',
                 'Registration of domain names in the TLD is restricted to legal professionals '
                 '(e.g., lawyers, barristers, solicitors, law firms, and other practitioners of '
                 'law) appropriately licensed to practice law by a recognized accredited body or '
                 'authorized government authority.',
                 'https://domains.registry.godaddy/policiespdf/LAW-POL-001-Eligibility_Policy-1.0.pdf',
                 '2022-01-01',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.eligibilityAdvice/law-jp-bengoshi']},
 {'sql': '\n'
         '    INSERT INTO vertex_domain_eligibility_advice (vertex_id, owner_did, sensitivity_ord, '
         'tld, jurisdiction, regulator_slug, actor_kind, eligible, basis, policy_excerpt, '
         'source_url, effective_at, status, created_at, org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, 0, $3, $4, $5, $6, CAST($7 AS boolean), $8, $9, $10, $11, 'active', "
         '$12, $13, $14, $15\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_eligibility_advice WHERE vertex_id = '
         '$16)\n'
         '  ',
  'parameters': ['at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.eligibilityAdvice/law-jp-gaikokuho-jimu-bengoshi',
                 'did:web:domain.etzhayyim.com',
                 '.law',
                 'JP',
                 'jfba',
                 'registered-foreign-lawyer',
                 True,
                 'Gaikokuho-Jimu-Bengoshi (外国法事務弁護士 / GJB) は法務大臣承認 + JFBA special member '
                 'registration で確立される recognized status。policy §1.1 の other practitioners of law '
                 'に該当。',
                 '(法的根拠) Foreign Lawyers Act §3-§7 + JFBA 入会手続。承認後は JFBA special member '
                 'として公開登録される。',
                 'https://www.toben.or.jp/english/f-lawyer/flra.html',
                 '2022-01-01',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.eligibilityAdvice/law-jp-gaikokuho-jimu-bengoshi']},
 {'sql': '\n'
         '    INSERT INTO vertex_domain_eligibility_advice (vertex_id, owner_did, sensitivity_ord, '
         'tld, jurisdiction, regulator_slug, actor_kind, eligible, basis, policy_excerpt, '
         'source_url, effective_at, status, created_at, org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, 0, $3, $4, $5, $6, CAST($7 AS boolean), $8, $9, $10, $11, 'active', "
         '$12, $13, $14, $15\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_eligibility_advice WHERE vertex_id = '
         '$16)\n'
         '  ',
  'parameters': ['at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.eligibilityAdvice/law-jp-bengoshi-houjin',
                 'did:web:domain.etzhayyim.com',
                 '.law',
                 'JP',
                 'jfba',
                 'law-firm',
                 True,
                 '弁護士法人 (legal-professional corporation) は弁護士法 §30 以降に基づき JFBA registration '
                 'が要求される。policy §1.1 列挙の law firm に直接該当。',
                 'Eligible categories include law firms — partnerships or entities formed by '
                 'qualified lawyers.',
                 'https://domains.registry.godaddy/policiespdf/LAW-POL-001-Eligibility_Policy-1.0.pdf',
                 '2022-01-01',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.eligibilityAdvice/law-jp-bengoshi-houjin']},
 {'sql': '\n'
         '    INSERT INTO vertex_domain_eligibility_advice (vertex_id, owner_did, sensitivity_ord, '
         'tld, jurisdiction, regulator_slug, actor_kind, eligible, basis, policy_excerpt, '
         'source_url, effective_at, status, created_at, org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, 0, $3, $4, $5, $6, CAST($7 AS boolean), $8, $9, $10, $11, 'active', "
         '$12, $13, $14, $15\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_eligibility_advice WHERE vertex_id = '
         '$16)\n'
         '  ',
  'parameters': ['at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.eligibilityAdvice/law-uk-solicitor',
                 'did:web:domain.etzhayyim.com',
                 '.law',
                 'GB-EAW',
                 'sra-england-wales',
                 'individual-lawyer',
                 True,
                 'SRA は statutory Legal Regulator。Solicitor は SRA roll で identifiable。',
                 'Registration of domain names in the TLD is restricted to legal professionals '
                 'appropriately licensed to practice law by a recognized accredited body or '
                 'authorized government authority.',
                 'https://www.sra.org.uk/consumers/register/',
                 '2022-01-01',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.eligibilityAdvice/law-uk-solicitor']},
 {'sql': '\n'
         '    INSERT INTO vertex_domain_eligibility_advice (vertex_id, owner_did, sensitivity_ord, '
         'tld, jurisdiction, regulator_slug, actor_kind, eligible, basis, policy_excerpt, '
         'source_url, effective_at, status, created_at, org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, 0, $3, $4, $5, $6, CAST($7 AS boolean), $8, $9, $10, $11, 'active', "
         '$12, $13, $14, $15\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_eligibility_advice WHERE vertex_id = '
         '$16)\n'
         '  ',
  'parameters': ['at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.eligibilityAdvice/law-us-bar',
                 'did:web:domain.etzhayyim.com',
                 '.law',
                 'US',
                 'aba-state-bars',
                 'individual-lawyer',
                 True,
                 'Each US state bar is the Legal Regulator. Active member status is required; '
                 'inactive / non-practicing is excluded per §1.1.',
                 'A lawyer with inactive or non-practicing status who is not authorized to provide '
                 'regulated legal services under the rules of their Legal Regulator is not '
                 'eligible.',
                 'https://domains.registry.godaddy/policiespdf/LAW-POL-001-Eligibility_Policy-1.0.pdf',
                 '2022-01-01',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.eligibilityAdvice/law-us-bar']},
 {'sql': '\n'
         '    INSERT INTO vertex_domain_eligibility_advice (vertex_id, owner_did, sensitivity_ord, '
         'tld, jurisdiction, regulator_slug, actor_kind, eligible, basis, policy_excerpt, '
         'source_url, effective_at, status, created_at, org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, 0, $3, $4, $5, $6, CAST($7 AS boolean), $8, $9, $10, $11, 'active', "
         '$12, $13, $14, $15\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_eligibility_advice WHERE vertex_id = '
         '$16)\n'
         '  ',
  'parameters': ['at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.eligibilityAdvice/law-non-practicing-corp',
                 'did:web:domain.etzhayyim.com',
                 '.law',
                 'JP',
                 None,
                 'non-legal-corporation',
                 False,
                 'etzhayyim Japan株式会社 のような非弁護士法人は §1.1 の eligible categories に該当しない。提携弁護士または弁護士法人名義での登録 '
                 'or .lawyer/.legal への切り替えが代替路。',
                 'Registration of domain names in the TLD is restricted to legal professionals '
                 '(e.g., lawyers, barristers, solicitors, law firms, and other practitioners of '
                 'law) appropriately licensed to practice law by a recognized accredited body or '
                 'authorized government authority.',
                 'https://domains.registry.godaddy/policiespdf/LAW-POL-001-Eligibility_Policy-1.0.pdf',
                 '2022-01-01',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.eligibilityAdvice/law-non-practicing-corp']},
 {'sql': '\n'
         '    INSERT INTO vertex_domain_eligibility_advice (vertex_id, owner_did, sensitivity_ord, '
         'tld, jurisdiction, regulator_slug, actor_kind, eligible, basis, policy_excerpt, '
         'source_url, effective_at, status, created_at, org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, 0, $3, $4, $5, $6, CAST($7 AS boolean), $8, $9, $10, $11, 'active', "
         '$12, $13, $14, $15\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_eligibility_advice WHERE vertex_id = '
         '$16)\n'
         '  ',
  'parameters': ['at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.eligibilityAdvice/lawyer-jp-open',
                 'did:web:domain.etzhayyim.com',
                 '.lawyer',
                 'JP',
                 None,
                 'any',
                 True,
                 '.lawyer は Identity Digital の open generic TLD。occupational requirement '
                 'なし。誰でも登録可。',
                 'No occupational eligibility requirement.',
                 'https://www.identity.digital/policies',
                 '2014-04-01',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.eligibilityAdvice/lawyer-jp-open']},
 {'sql': '\n'
         '    INSERT INTO vertex_domain_eligibility_advice (vertex_id, owner_did, sensitivity_ord, '
         'tld, jurisdiction, regulator_slug, actor_kind, eligible, basis, policy_excerpt, '
         'source_url, effective_at, status, created_at, org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, 0, $3, $4, $5, $6, CAST($7 AS boolean), $8, $9, $10, $11, 'active', "
         '$12, $13, $14, $15\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_domain_eligibility_advice WHERE vertex_id = '
         '$16)\n'
         '  ',
  'parameters': ['at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.eligibilityAdvice/legal-jp-open',
                 'did:web:domain.etzhayyim.com',
                 '.legal',
                 'JP',
                 None,
                 'any',
                 True,
                 '.legal は Identity Digital の open generic TLD。occupational requirement なし。',
                 'No occupational eligibility requirement.',
                 'https://www.identity.digital/policies',
                 '2014-04-01',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.eligibilityAdvice/legal-jp-open']},
 {'sql': '\n'
         '    INSERT INTO edge_domain_registrar_supports_tld (edge_id, owner_did, sensitivity_ord, '
         'src_vid, dst_vid, registrar_slug, tld, verified_at, handles_verification, notes, '
         'created_at, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, 0, $3, $4, $5, $6, $7, CAST($8 AS boolean), $9, $10, $11, $12, $13\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM edge_domain_registrar_supports_tld WHERE edge_id = '
         '$14)\n'
         '  ',
  'parameters': ['edge:domain:supports:namecheap:law',
                 'did:web:domain.etzhayyim.com',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/namecheap',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/law',
                 'namecheap',
                 '.law',
                 '2026-05-07T23:00:00Z',
                 True,
                 'Handles registry verification flow.',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'edge:domain:supports:namecheap:law']},
 {'sql': '\n'
         '    INSERT INTO edge_domain_registrar_supports_tld (edge_id, owner_did, sensitivity_ord, '
         'src_vid, dst_vid, registrar_slug, tld, verified_at, handles_verification, notes, '
         'created_at, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, 0, $3, $4, $5, $6, $7, CAST($8 AS boolean), $9, $10, $11, $12, $13\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM edge_domain_registrar_supports_tld WHERE edge_id = '
         '$14)\n'
         '  ',
  'parameters': ['edge:domain:supports:godaddy:law',
                 'did:web:domain.etzhayyim.com',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/godaddy',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/law',
                 'godaddy',
                 '.law',
                 '2026-05-07T23:00:00Z',
                 True,
                 'Default reseller (operator-aligned).',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'edge:domain:supports:godaddy:law']},
 {'sql': '\n'
         '    INSERT INTO edge_domain_registrar_supports_tld (edge_id, owner_did, sensitivity_ord, '
         'src_vid, dst_vid, registrar_slug, tld, verified_at, handles_verification, notes, '
         'created_at, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, 0, $3, $4, $5, $6, $7, CAST($8 AS boolean), $9, $10, $11, $12, $13\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM edge_domain_registrar_supports_tld WHERE edge_id = '
         '$14)\n'
         '  ',
  'parameters': ['edge:domain:supports:eurodns:law',
                 'did:web:domain.etzhayyim.com',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/eurodns',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/law',
                 'eurodns',
                 '.law',
                 '2026-05-07T23:00:00Z',
                 True,
                 None,
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'edge:domain:supports:eurodns:law']},
 {'sql': '\n'
         '    INSERT INTO edge_domain_registrar_supports_tld (edge_id, owner_did, sensitivity_ord, '
         'src_vid, dst_vid, registrar_slug, tld, verified_at, handles_verification, notes, '
         'created_at, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, 0, $3, $4, $5, $6, $7, CAST($8 AS boolean), $9, $10, $11, $12, $13\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM edge_domain_registrar_supports_tld WHERE edge_id = '
         '$14)\n'
         '  ',
  'parameters': ['edge:domain:supports:dynadot:law',
                 'did:web:domain.etzhayyim.com',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/dynadot',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/law',
                 'dynadot',
                 '.law',
                 '2026-05-07T23:00:00Z',
                 True,
                 None,
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'edge:domain:supports:dynadot:law']},
 {'sql': '\n'
         '    INSERT INTO edge_domain_registrar_supports_tld (edge_id, owner_did, sensitivity_ord, '
         'src_vid, dst_vid, registrar_slug, tld, verified_at, handles_verification, notes, '
         'created_at, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, 0, $3, $4, $5, $6, $7, CAST($8 AS boolean), $9, $10, $11, $12, $13\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM edge_domain_registrar_supports_tld WHERE edge_id = '
         '$14)\n'
         '  ',
  'parameters': ['edge:domain:supports:join-law:law',
                 'did:web:domain.etzhayyim.com',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/join-law',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/law',
                 'join-law',
                 '.law',
                 '2026-05-07T23:00:00Z',
                 True,
                 'Specialty .law registrar.',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'edge:domain:supports:join-law:law']},
 {'sql': '\n'
         '    INSERT INTO edge_domain_registrar_supports_tld (edge_id, owner_did, sensitivity_ord, '
         'src_vid, dst_vid, registrar_slug, tld, verified_at, handles_verification, notes, '
         'created_at, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, 0, $3, $4, $5, $6, $7, CAST($8 AS boolean), $9, $10, $11, $12, $13\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM edge_domain_registrar_supports_tld WHERE edge_id = '
         '$14)\n'
         '  ',
  'parameters': ['edge:domain:supports:namecheap:lawyer',
                 'did:web:domain.etzhayyim.com',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/namecheap',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/lawyer',
                 'namecheap',
                 '.lawyer',
                 '2026-05-07T23:00:00Z',
                 False,
                 None,
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'edge:domain:supports:namecheap:lawyer']},
 {'sql': '\n'
         '    INSERT INTO edge_domain_registrar_supports_tld (edge_id, owner_did, sensitivity_ord, '
         'src_vid, dst_vid, registrar_slug, tld, verified_at, handles_verification, notes, '
         'created_at, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, 0, $3, $4, $5, $6, $7, CAST($8 AS boolean), $9, $10, $11, $12, $13\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM edge_domain_registrar_supports_tld WHERE edge_id = '
         '$14)\n'
         '  ',
  'parameters': ['edge:domain:supports:godaddy:lawyer',
                 'did:web:domain.etzhayyim.com',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/godaddy',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/lawyer',
                 'godaddy',
                 '.lawyer',
                 '2026-05-07T23:00:00Z',
                 False,
                 None,
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'edge:domain:supports:godaddy:lawyer']},
 {'sql': '\n'
         '    INSERT INTO edge_domain_registrar_supports_tld (edge_id, owner_did, sensitivity_ord, '
         'src_vid, dst_vid, registrar_slug, tld, verified_at, handles_verification, notes, '
         'created_at, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, 0, $3, $4, $5, $6, $7, CAST($8 AS boolean), $9, $10, $11, $12, $13\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM edge_domain_registrar_supports_tld WHERE edge_id = '
         '$14)\n'
         '  ',
  'parameters': ['edge:domain:supports:eurodns:lawyer',
                 'did:web:domain.etzhayyim.com',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/eurodns',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/lawyer',
                 'eurodns',
                 '.lawyer',
                 '2026-05-07T23:00:00Z',
                 False,
                 None,
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'edge:domain:supports:eurodns:lawyer']},
 {'sql': '\n'
         '    INSERT INTO edge_domain_registrar_supports_tld (edge_id, owner_did, sensitivity_ord, '
         'src_vid, dst_vid, registrar_slug, tld, verified_at, handles_verification, notes, '
         'created_at, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, 0, $3, $4, $5, $6, $7, CAST($8 AS boolean), $9, $10, $11, $12, $13\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM edge_domain_registrar_supports_tld WHERE edge_id = '
         '$14)\n'
         '  ',
  'parameters': ['edge:domain:supports:dynadot:lawyer',
                 'did:web:domain.etzhayyim.com',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/dynadot',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/lawyer',
                 'dynadot',
                 '.lawyer',
                 '2026-05-07T23:00:00Z',
                 False,
                 None,
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'edge:domain:supports:dynadot:lawyer']},
 {'sql': '\n'
         '    INSERT INTO edge_domain_registrar_supports_tld (edge_id, owner_did, sensitivity_ord, '
         'src_vid, dst_vid, registrar_slug, tld, verified_at, handles_verification, notes, '
         'created_at, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, 0, $3, $4, $5, $6, $7, CAST($8 AS boolean), $9, $10, $11, $12, $13\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM edge_domain_registrar_supports_tld WHERE edge_id = '
         '$14)\n'
         '  ',
  'parameters': ['edge:domain:supports:squarespace:lawyer',
                 'did:web:domain.etzhayyim.com',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/squarespace',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/lawyer',
                 'squarespace',
                 '.lawyer',
                 '2026-05-07T23:00:00Z',
                 False,
                 None,
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'edge:domain:supports:squarespace:lawyer']},
 {'sql': '\n'
         '    INSERT INTO edge_domain_registrar_supports_tld (edge_id, owner_did, sensitivity_ord, '
         'src_vid, dst_vid, registrar_slug, tld, verified_at, handles_verification, notes, '
         'created_at, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, 0, $3, $4, $5, $6, $7, CAST($8 AS boolean), $9, $10, $11, $12, $13\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM edge_domain_registrar_supports_tld WHERE edge_id = '
         '$14)\n'
         '  ',
  'parameters': ['edge:domain:supports:namecheap:legal',
                 'did:web:domain.etzhayyim.com',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/namecheap',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/legal',
                 'namecheap',
                 '.legal',
                 '2026-05-07T23:00:00Z',
                 False,
                 None,
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'edge:domain:supports:namecheap:legal']},
 {'sql': '\n'
         '    INSERT INTO edge_domain_registrar_supports_tld (edge_id, owner_did, sensitivity_ord, '
         'src_vid, dst_vid, registrar_slug, tld, verified_at, handles_verification, notes, '
         'created_at, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, 0, $3, $4, $5, $6, $7, CAST($8 AS boolean), $9, $10, $11, $12, $13\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM edge_domain_registrar_supports_tld WHERE edge_id = '
         '$14)\n'
         '  ',
  'parameters': ['edge:domain:supports:godaddy:legal',
                 'did:web:domain.etzhayyim.com',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/godaddy',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/legal',
                 'godaddy',
                 '.legal',
                 '2026-05-07T23:00:00Z',
                 False,
                 None,
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'edge:domain:supports:godaddy:legal']},
 {'sql': '\n'
         '    INSERT INTO edge_domain_registrar_supports_tld (edge_id, owner_did, sensitivity_ord, '
         'src_vid, dst_vid, registrar_slug, tld, verified_at, handles_verification, notes, '
         'created_at, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, 0, $3, $4, $5, $6, $7, CAST($8 AS boolean), $9, $10, $11, $12, $13\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM edge_domain_registrar_supports_tld WHERE edge_id = '
         '$14)\n'
         '  ',
  'parameters': ['edge:domain:supports:eurodns:legal',
                 'did:web:domain.etzhayyim.com',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/eurodns',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/legal',
                 'eurodns',
                 '.legal',
                 '2026-05-07T23:00:00Z',
                 False,
                 None,
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'edge:domain:supports:eurodns:legal']},
 {'sql': '\n'
         '    INSERT INTO edge_domain_registrar_supports_tld (edge_id, owner_did, sensitivity_ord, '
         'src_vid, dst_vid, registrar_slug, tld, verified_at, handles_verification, notes, '
         'created_at, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, 0, $3, $4, $5, $6, $7, CAST($8 AS boolean), $9, $10, $11, $12, $13\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM edge_domain_registrar_supports_tld WHERE edge_id = '
         '$14)\n'
         '  ',
  'parameters': ['edge:domain:supports:squarespace:legal',
                 'did:web:domain.etzhayyim.com',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/squarespace',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/legal',
                 'squarespace',
                 '.legal',
                 '2026-05-07T23:00:00Z',
                 False,
                 None,
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'edge:domain:supports:squarespace:legal']},
 {'sql': '\n'
         '    INSERT INTO edge_domain_registrar_supports_tld (edge_id, owner_did, sensitivity_ord, '
         'src_vid, dst_vid, registrar_slug, tld, verified_at, handles_verification, notes, '
         'created_at, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, 0, $3, $4, $5, $6, $7, CAST($8 AS boolean), $9, $10, $11, $12, $13\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM edge_domain_registrar_supports_tld WHERE edge_id = '
         '$14)\n'
         '  ',
  'parameters': ['edge:domain:supports:namecheap:attorney',
                 'did:web:domain.etzhayyim.com',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/namecheap',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/attorney',
                 'namecheap',
                 '.attorney',
                 '2026-05-07T23:00:00Z',
                 False,
                 None,
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'edge:domain:supports:namecheap:attorney']},
 {'sql': '\n'
         '    INSERT INTO edge_domain_registrar_supports_tld (edge_id, owner_did, sensitivity_ord, '
         'src_vid, dst_vid, registrar_slug, tld, verified_at, handles_verification, notes, '
         'created_at, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, 0, $3, $4, $5, $6, $7, CAST($8 AS boolean), $9, $10, $11, $12, $13\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM edge_domain_registrar_supports_tld WHERE edge_id = '
         '$14)\n'
         '  ',
  'parameters': ['edge:domain:supports:godaddy:attorney',
                 'did:web:domain.etzhayyim.com',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.registrar/godaddy',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/attorney',
                 'godaddy',
                 '.attorney',
                 '2026-05-07T23:00:00Z',
                 False,
                 None,
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'edge:domain:supports:godaddy:attorney']},
 {'sql': '\n'
         '    INSERT INTO edge_domain_tld_accepts_regulator (edge_id, owner_did, sensitivity_ord, '
         'src_vid, dst_vid, tld, regulator_slug, basis, created_at, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, 0, $3, $4, $5, $6, $7, $8, $9, $10, $11\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM edge_domain_tld_accepts_regulator WHERE edge_id = '
         '$12)\n'
         '  ',
  'parameters': ['edge:domain:accepts:law:jfba',
                 'did:web:domain.etzhayyim.com',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/law',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.legalRegulator/jfba',
                 '.law',
                 'jfba',
                 "Policy §1.1 jurisdiction-neutral 'recognized accredited body' wording covers "
                 'JFBA (弁護士法に基づく自治団体).',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'edge:domain:accepts:law:jfba']},
 {'sql': '\n'
         '    INSERT INTO edge_domain_tld_accepts_regulator (edge_id, owner_did, sensitivity_ord, '
         'src_vid, dst_vid, tld, regulator_slug, basis, created_at, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, 0, $3, $4, $5, $6, $7, $8, $9, $10, $11\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM edge_domain_tld_accepts_regulator WHERE edge_id = '
         '$12)\n'
         '  ',
  'parameters': ['edge:domain:accepts:law:aba-state-bars',
                 'did:web:domain.etzhayyim.com',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/law',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.legalRegulator/aba-state-bars',
                 '.law',
                 'aba-state-bars',
                 'Policy §1.1 covers US state bars (each is an authorized government authority via '
                 'state supreme court).',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'edge:domain:accepts:law:aba-state-bars']},
 {'sql': '\n'
         '    INSERT INTO edge_domain_tld_accepts_regulator (edge_id, owner_did, sensitivity_ord, '
         'src_vid, dst_vid, tld, regulator_slug, basis, created_at, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, 0, $3, $4, $5, $6, $7, $8, $9, $10, $11\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM edge_domain_tld_accepts_regulator WHERE edge_id = '
         '$12)\n'
         '  ',
  'parameters': ['edge:domain:accepts:law:sra-england-wales',
                 'did:web:domain.etzhayyim.com',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.tld/law',
                 'at://did:web:domain.etzhayyim.com/com.etzhayyim.apps.domain.legalRegulator/sra-england-wales',
                 '.law',
                 'sra-england-wales',
                 'Policy §1.1 covers SRA as statutory Legal Regulator.',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'edge:domain:accepts:law:sra-england-wales']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/domain-eligibility-check-v1',
                 'did:web:domain.etzhayyim.com',
                 'domain_eligibility_check',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  domain.etzhayyim.com eligibilityCheck (XRPC com.etzhayyim.apps.domain.eligibilityCheck).\n'
                 '\n'
                 '  Resolves (tld, jurisdiction, actorKind) against '
                 'vertex_domain_eligibility_advice\n'
                 '  and returns the matched advice row. Audit emit captures the lookup.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_domain_eligibility_check"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/domain"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="domain_eligibility_check" name="domain eligibility check" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.domain.eligibilityCheck", "version": 1, '
                 '"resultTimeoutMs": 30000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="eligibilityCheck">\n'
                 '      <bpmn:outgoing>Flow_ToCheck</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Check" name="resolve eligibility advice">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="domain.eligibility.check"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=tld" target="tld"/>\n'
                 '          <zeebe:input source="=jurisdiction" target="jurisdiction"/>\n'
                 '          <zeebe:input source="=actorKind" target="actorKind"/>\n'
                 '          <zeebe:input source="=regulatorSlug" target="regulatorSlug"/>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=eligible" target="eligible"/>\n'
                 '          <zeebe:output source="=matchedAdviceSlug" '
                 'target="matchedAdviceSlug"/>\n'
                 '          <zeebe:output source="=basis" target="basis"/>\n'
                 '          <zeebe:output source="=policyExcerpt" target="policyExcerpt"/>\n'
                 '          <zeebe:output source="=verificationRequired" '
                 'target="verificationRequired"/>\n'
                 '          <zeebe:output source="=regulatorName" target="regulatorName"/>\n'
                 '          <zeebe:output source="=sourceUrl" target="sourceUrl"/>\n'
                 '          <zeebe:output source="=alternatives" target="alternatives"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToCheck</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToCheck" sourceRef="Start" '
                 'targetRef="Task_Check"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:domain.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;com.etzhayyim.apps.domain.eligibilityCheck&quot;" target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;tld&quot;: tld, '
                 '&quot;jurisdiction&quot;: jurisdiction, &quot;actorKind&quot;: actorKind, '
                 '&quot;eligible&quot;: eligible }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Check" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3389,
                 '00-contracts/bpmn/com/etzhayyim/domain/eligibilityCheck.bpmn',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/domain-eligibility-check-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/domain-register-assist-v1',
                 'did:web:domain.etzhayyim.com',
                 'domain_register_assist',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  domain.etzhayyim.com registerAssist (XRPC com.etzhayyim.apps.domain.registerAssist).\n'
                 '\n'
                 '  Single-task BPMN: domain.register.assist runs eligibility check + registrar\n'
                 '  recommendation + draft ledger INSERT in one primitive (the ledger write\n'
                 '  needs the eligibility verdict atomically). Audit step records the outcome.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_domain_register_assist"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/domain"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="domain_register_assist" name="domain register assist" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.domain.registerAssist", "version": 1, '
                 '"resultTimeoutMs": 30000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="registerAssist">\n'
                 '      <bpmn:outgoing>Flow_ToAssist</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Assist" name="evaluate + draft registration">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="domain.register.assist"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=domainName" target="domainName"/>\n'
                 '          <zeebe:input source="=tld" target="tld"/>\n'
                 '          <zeebe:input source="=registrantDid" target="registrantDid"/>\n'
                 '          <zeebe:input source="=registrantName" target="registrantName"/>\n'
                 '          <zeebe:input source="=actorKind" target="actorKind"/>\n'
                 '          <zeebe:input source="=jurisdiction" target="jurisdiction"/>\n'
                 '          <zeebe:input source="=regulatorSlug" target="regulatorSlug"/>\n'
                 '          <zeebe:input source="=preferredRegistrar" '
                 'target="preferredRegistrar"/>\n'
                 '          <zeebe:input source="=nsProvider" target="nsProvider"/>\n'
                 '          <zeebe:input source="=evidenceUrl" target="evidenceUrl"/>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=eligible" target="eligible"/>\n'
                 '          <zeebe:output source="=registrationVid" target="registrationVid"/>\n'
                 '          <zeebe:output source="=registrarRecommendation" '
                 'target="registrarRecommendation"/>\n'
                 '          <zeebe:output source="=verificationRequired" '
                 'target="verificationRequired"/>\n'
                 '          <zeebe:output source="=verificationNotes" '
                 'target="verificationNotes"/>\n'
                 '          <zeebe:output source="=alternativesIfBlocked" '
                 'target="alternativesIfBlocked"/>\n'
                 '          <zeebe:output source="=policyExcerpt" target="policyExcerpt"/>\n'
                 '          <zeebe:output source="=sourceUrl" target="sourceUrl"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAssist</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAssist" sourceRef="Start" '
                 'targetRef="Task_Assist"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:domain.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;com.etzhayyim.apps.domain.registerAssist&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;domainName&quot;: domainName, '
                 '&quot;tld&quot;: tld, &quot;registrantDid&quot;: registrantDid, '
                 '&quot;eligible&quot;: eligible, &quot;registrationVid&quot;: registrationVid }" '
                 'target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Assist" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3992,
                 '00-contracts/bpmn/com/etzhayyim/domain/registerAssist.bpmn',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/domain-register-assist-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/domain-refresh-tld-catalog-v1',
                 'did:web:domain.etzhayyim.com',
                 'domain_refresh_tld_catalog',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  domain.etzhayyim.com refreshTldCatalog (timer-start, autonomous).\n'
                 '\n'
                 "  Phase 1: stub primitive (no-op). Phase 2 will fetch each TLD's\n"
                 '  eligibility policy URL, diff against the stored excerpt, and bump\n'
                 '  effective_at on vertex_domain_eligibility_advice when the policy changes.\n'
                 '\n'
                 '  cron 0 0 0 7 * ?  (monthly day 7 — staggered from shosha/isbn).\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_domain_refresh_tld_catalog"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/domain"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="domain_refresh_tld_catalog" name="domain refresh TLD '
                 'catalog" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "version": 1 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="cron 07:00 UTC monthly day 7">\n'
                 '      <bpmn:outgoing>Flow_ToRefresh</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_MonthlyDay7">\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression">0 0 0 7 * '
                 '?</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Refresh" name="refresh TLD policy excerpts">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="domain.tld.catalog.refresh"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=tldsChecked" target="tldsChecked"/>\n'
                 '          <zeebe:output source="=tldsUpdated" target="tldsUpdated"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToRefresh</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToRefresh" sourceRef="Start" '
                 'targetRef="Task_Refresh"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:domain.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;com.etzhayyim.apps.domain.refreshTldCatalog&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;tldsChecked&quot;: tldsChecked, '
                 '&quot;tldsUpdated&quot;: tldsUpdated }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Refresh" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2894,
                 '00-contracts/bpmn/com/etzhayyim/domain/refreshTldCatalog.bpmn',
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/domain-refresh-tld-catalog-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/domain-eligibilityCheck-v1',
                 'did:web:domain.etzhayyim.com',
                 'com.etzhayyim.apps.domain.eligibilityCheck',
                 'domain_eligibility_check',
                 30000,
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/domain-eligibilityCheck-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/domain-registerAssist-v1',
                 'did:web:domain.etzhayyim.com',
                 'com.etzhayyim.apps.domain.registerAssist',
                 'domain_register_assist',
                 30000,
                 '2026-05-07T23:00:00Z',
                 'did:web:domain.etzhayyim.com',
                 'did:web:domain.etzhayyim.com',
                 'sys.bpmn.seed.domain',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/domain-registerAssist-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/domain-eligibilityCheck-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/domain-registerAssist-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/domain-eligibility-check-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/domain-register-assist-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/domain-refresh-tld-catalog-v1']},
 {'sql': 'DELETE FROM edge_domain_tld_accepts_regulator WHERE owner_did = $1',
  'parameters': ['did:web:domain.etzhayyim.com']},
 {'sql': 'DELETE FROM edge_domain_registrar_supports_tld WHERE owner_did = $1',
  'parameters': ['did:web:domain.etzhayyim.com']},
 {'sql': 'DELETE FROM vertex_domain_eligibility_advice WHERE owner_did = $1',
  'parameters': ['did:web:domain.etzhayyim.com']},
 {'sql': 'DELETE FROM vertex_domain_legal_regulator WHERE owner_did = $1',
  'parameters': ['did:web:domain.etzhayyim.com']},
 {'sql': 'DELETE FROM vertex_domain_registrar WHERE owner_did = $1',
  'parameters': ['did:web:domain.etzhayyim.com']},
 {'sql': 'DELETE FROM vertex_domain_tld WHERE owner_did = $1',
  'parameters': ['did:web:domain.etzhayyim.com']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
