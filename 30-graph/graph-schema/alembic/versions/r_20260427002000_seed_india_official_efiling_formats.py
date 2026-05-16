"""Captured from Kysely migration 20260427002000_seed_india_official_efiling_formats."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427002000_seed_india_official_efiling_formats"
down_revision = 'r_20260427001000_vector_embedding_project_tables'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_ind_efiling_format (\n'
         '      vertex_id              varchar PRIMARY KEY,\n'
         '      _seq                   bigint,\n'
         '      created_date           date,\n'
         '      sensitivity_ord        int,\n'
         '      owner_did              varchar,\n'
         '      format_key             varchar NOT NULL,\n'
         '      jurisdiction           varchar NOT NULL,\n'
         '      actor_did              varchar NOT NULL,\n'
         '      format_kind            varchar NOT NULL,\n'
         '      status                 varchar NOT NULL,\n'
         '      official_source_url    varchar NOT NULL,\n'
         '      source_page_url        varchar,\n'
         '      local_descriptor_path  varchar NOT NULL,\n'
         '      internal_form_keys     varchar,\n'
         '      field_map_json         varchar,\n'
         '      descriptor_json        varchar NOT NULL,\n'
         '      last_verified_at       varchar,\n'
         '      created_at             varchar,\n'
         '      org_id                 varchar,\n'
         '      user_id                varchar,\n'
         '      actor_id               varchar\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'DELETE FROM vertex_ind_efiling_format WHERE format_key = $1',
  'parameters': ['ind.itr1.eriSubmitFlow.v1_1']},
 {'sql': '\n'
         '      INSERT INTO vertex_ind_efiling_format (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        format_key, jurisdiction, actor_did, format_kind, status,\n'
         '        official_source_url, source_page_url, local_descriptor_path,\n'
         '        internal_form_keys, field_map_json, descriptor_json,\n'
         '        last_verified_at, created_at, org_id, user_id, actor_id\n'
         '      ) VALUES (\n'
         "        $1, $2, DATE '2026-04-27', 2, $3,\n"
         '        $4, $5, $6,\n'
         '        $7, $8, $9,\n'
         '        $10, $11,\n'
         '        $12,\n'
         '        $13,\n'
         '        $14,\n'
         "        $15, '2026-04-27T00:20:00Z',\n"
         "        'ind', 'system', 'sys.ind.efiling.format'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:ind-union.gftd.ai:cbdt:itr1/ai.gftd.apps.ind.efiling.format/ind.itr1.eriSubmitFlow.v1_1',
                 20260427002000,
                 'did:web:ind-union.gftd.ai:cbdt:itr1',
                 'ind.itr1.eriSubmitFlow.v1_1',
                 'itr1',
                 'did:web:ind-union.gftd.ai:cbdt:itr1',
                 'official_api_payload',
                 'active',
                 'https://www.incometax.gov.in/iec/foportal/sites/default/files/2021-11/API_SubmitFlow_v1.1.pdf',
                 'https://www.incometax.gov.in/iec/foportal/api-specifications',
                 '00-contracts/formats/ai/gftd/ind/itr1/eri-submit-flow-v1.1.json',
                 'itr1-form-v1,itr1-self-review-v1,itr1-amend-v1',
                 '[{"internal":"applicant.pan","official":"Pan / Header.entityNum / '
                 'formData.ITR.ITR1.PersonalInfo.PAN"},{"internal":"assessmentYear","official":"Header.Ay '
                 '/ '
                 'formData.ITR.ITR1.Form_ITR1.AssessmentYear"},{"internal":"applicant.name","official":"formData.ITR.ITR1.PersonalInfo.AssesseeName"},{"internal":"applicant.dob","official":"formData.ITR.ITR1.PersonalInfo.DOB"},{"internal":"applicant.aadhaar","official":"formData.ITR.ITR1.PersonalInfo.AadhaarCardNo"},{"internal":"applicant.mobile","official":"formData.ITR.ITR1.PersonalInfo.Address.MobileNo"},{"internal":"applicant.email","official":"formData.ITR.ITR1.PersonalInfo.Address.EmailAddress"},{"internal":"income.grossSalaryInrPaise","official":"formData.ITR.ITR1.ITR1_IncomeDeductions.Salary"},{"internal":"income.otherSourcesInrPaise","official":"formData.ITR.ITR1.ITR1_IncomeDeductions.OthersInc"},{"internal":"deductions.*","official":"formData.ITR.ITR1.ITR1_IncomeDeductions.UsrDeductUndChapVIA"},{"internal":"tax.*","official":"formData.ITR.ITR1.TaxComputation '
                 '/ '
                 'TaxPaid"},{"internal":"bank.*","official":"formData.ITR.ITR1.Refund.BankAccountDtls"}]',
                 '{"formatKey":"ind.itr1.eriSubmitFlow.v1_1","jurisdiction":"itr1","actorDid":"did:web:ind-union.gftd.ai:cbdt:itr1","formatKind":"official_api_payload","officialSourceUrl":"https://www.incometax.gov.in/iec/foportal/sites/default/files/2021-11/API_SubmitFlow_v1.1.pdf","sourcePageUrl":"https://www.incometax.gov.in/iec/foportal/api-specifications","lastVerified":"2026-04-26","status":"active","api":{"provider":"ItrWeb","serviceName":"ItrService","mode":"real_time","endpoints":[{"name":"validateItr","effect":"validate_only"},{"name":"submitItr","effect":"validate_and_submit"}],"headers":["Content-type","clientId","clientSecret","authToken","accessMode"],"bodyEnvelope":{"data":"base64 '
                 'encoded request json","sign":"DSC signature over data","eriUserId":"ERI user '
                 'id"}},"officialRequestData":{"serviceName":{"required":true,"values":["EriValidateItr","EriItrSubmit"]},"Pan":{"required":false,"maxLength":10},"Header":{"required":true,"fields":{"formName":{"required":true,"values":["ITR-1"]},"formCode":{"required":true,"value":"1"},"mimeType":{"required":true,"value":"json"},"entityNum":{"required":true,"mapsFrom":"applicant.pan"},"entityType":{"required":true,"value":"P"},"Ay":{"required":true,"mapsFrom":"assessmentYear"},"createdBy":{"required":true,"mapsFrom":"eriUserId"},"filingTypeCd":{"required":true,"values":["O","R"]},"filingMode":{"required":true,"value":"OF"},"incomeTaxSecCd":{"required":true,"values":["11","17","12"]},"submittedBy":{"required":true,"values":["ERI","SLF"]}}},"formData":{"required":true,"description":"ITR '
                 'form JSON as published by Income Tax Department schema for the assessment '
                 'year."}},"internalFormKeys":["itr1-form-v1","itr1-self-review-v1","itr1-amend-v1"],"fieldMap":[{"internal":"applicant.pan","official":"Pan '
                 '/ Header.entityNum / '
                 'formData.ITR.ITR1.PersonalInfo.PAN"},{"internal":"assessmentYear","official":"Header.Ay '
                 '/ '
                 'formData.ITR.ITR1.Form_ITR1.AssessmentYear"},{"internal":"applicant.name","official":"formData.ITR.ITR1.PersonalInfo.AssesseeName"},{"internal":"applicant.dob","official":"formData.ITR.ITR1.PersonalInfo.DOB"},{"internal":"applicant.aadhaar","official":"formData.ITR.ITR1.PersonalInfo.AadhaarCardNo"},{"internal":"applicant.mobile","official":"formData.ITR.ITR1.PersonalInfo.Address.MobileNo"},{"internal":"applicant.email","official":"formData.ITR.ITR1.PersonalInfo.Address.EmailAddress"},{"internal":"income.grossSalaryInrPaise","official":"formData.ITR.ITR1.ITR1_IncomeDeductions.Salary"},{"internal":"income.otherSourcesInrPaise","official":"formData.ITR.ITR1.ITR1_IncomeDeductions.OthersInc"},{"internal":"deductions.*","official":"formData.ITR.ITR1.ITR1_IncomeDeductions.UsrDeductUndChapVIA"},{"internal":"tax.*","official":"formData.ITR.ITR1.TaxComputation '
                 '/ '
                 'TaxPaid"},{"internal":"bank.*","official":"formData.ITR.ITR1.Refund.BankAccountDtls"}],"liveFilingGate":"ind.efiling.submit '
                 'with providerKind=eri_type2_api or authorized_eri"}',
                 '2026-04-26']},
 {'sql': 'DELETE FROM vertex_ind_efiling_format WHERE format_key = $1',
  'parameters': ['ind.itr1.prefillSchema.v6_5']},
 {'sql': '\n'
         '      INSERT INTO vertex_ind_efiling_format (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        format_key, jurisdiction, actor_did, format_kind, status,\n'
         '        official_source_url, source_page_url, local_descriptor_path,\n'
         '        internal_form_keys, field_map_json, descriptor_json,\n'
         '        last_verified_at, created_at, org_id, user_id, actor_id\n'
         '      ) VALUES (\n'
         "        $1, $2, DATE '2026-04-27', 2, $3,\n"
         '        $4, $5, $6,\n'
         '        $7, $8, $9,\n'
         '        $10, $11,\n'
         '        $12,\n'
         '        $13,\n'
         '        $14,\n'
         "        $15, '2026-04-27T00:20:00Z',\n"
         "        'ind', 'system', 'sys.ind.efiling.format'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:ind-union.gftd.ai:cbdt:itr1/ai.gftd.apps.ind.efiling.format/ind.itr1.prefillSchema.v6_5',
                 20260427002001,
                 'did:web:ind-union.gftd.ai:cbdt:itr1',
                 'ind.itr1.prefillSchema.v6_5',
                 'itr1',
                 'did:web:ind-union.gftd.ai:cbdt:itr1',
                 'official_json_schema',
                 'active',
                 'https://www.incometax.gov.in/iec/foportal/sites/default/files/2021-11/PreFillSchemaJSON_V6.5.zip',
                 'https://www.incometax.gov.in/iec/foportal/api-specifications',
                 '00-contracts/formats/ai/gftd/ind/itr1/prefill-schema-v6.5.manifest.json',
                 'itr1-form-v1',
                 '[]',
                 '{"formatKey":"ind.itr1.prefillSchema.v6_5","jurisdiction":"itr1","actorDid":"did:web:ind-union.gftd.ai:cbdt:itr1","formatKind":"official_json_schema","officialSourceUrl":"https://www.incometax.gov.in/iec/foportal/sites/default/files/2021-11/PreFillSchemaJSON_V6.5.zip","sourcePageUrl":"https://www.incometax.gov.in/iec/foportal/api-specifications","lastVerified":"2026-04-26","status":"active","downloadedArtifact":{"zipName":"PreFillSchemaJSON_V6.5.zip","jsonName":"PreFillSchemaJSON_V6.5.json","jsonSchemaDefs":45,"topLevelProperties":["ais","assesseeRep","auditInfo","bankAccountDtls","filingReturn","filingStatus","form26as","insights","lastFiledITR","personalInfo","scheduleAL","scheduleCFL","verification"]},"internalFormKeys":["itr1-form-v1"],"usage":"Prefill '
                 'source schema for mapping taxpayer, AIS/26AS, bank, filing status, and prior '
                 'return data into itr1-form-v1 before review."}',
                 '2026-04-26']},
 {'sql': 'DELETE FROM vertex_ind_efiling_format WHERE format_key = $1',
  'parameters': ['ind.gstr3b.gspFramework.v3']},
 {'sql': '\n'
         '      INSERT INTO vertex_ind_efiling_format (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        format_key, jurisdiction, actor_did, format_kind, status,\n'
         '        official_source_url, source_page_url, local_descriptor_path,\n'
         '        internal_form_keys, field_map_json, descriptor_json,\n'
         '        last_verified_at, created_at, org_id, user_id, actor_id\n'
         '      ) VALUES (\n'
         "        $1, $2, DATE '2026-04-27', 2, $3,\n"
         '        $4, $5, $6,\n'
         '        $7, $8, $9,\n'
         '        $10, $11,\n'
         '        $12,\n'
         '        $13,\n'
         '        $14,\n'
         "        $15, '2026-04-27T00:20:00Z',\n"
         "        'ind', 'system', 'sys.ind.efiling.format'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:ind-union.gftd.ai:cbic:gstr3b/ai.gftd.apps.ind.efiling.format/ind.gstr3b.gspFramework.v3',
                 20260427002002,
                 'did:web:ind-union.gftd.ai:cbic:gstr3b',
                 'ind.gstr3b.gspFramework.v3',
                 'gstr3b',
                 'did:web:ind-union.gftd.ai:cbic:gstr3b',
                 'official_provider_framework',
                 'provider_required',
                 'https://www.gstn.org.in/assets/mainDashboard/Pdf/GSP_Implementation_Framework_V_3.0.pdf',
                 '',
                 '00-contracts/formats/ai/gftd/ind/gstr3b/gsp-framework-v3.manifest.json',
                 'gstr3b-form-v1,gstr3b-review-v1,gstr3b-amend-v1',
                 '[{"internal":"applicant.gstin","official":"GSTIN"},{"internal":"taxPeriod","official":"return '
                 'period"},{"internal":"supplies.*","official":"GSTR-3B outward and inward supply '
                 'sections"},{"internal":"itc.*","official":"GSTR-3B ITC '
                 'section"},{"internal":"taxPayment.*","official":"GSTR-3B payment/ledger '
                 'section"},{"internal":"arn","official":"Acknowledgement Reference Number"}]',
                 '{"formatKey":"ind.gstr3b.gspFramework.v3","jurisdiction":"gstr3b","actorDid":"did:web:ind-union.gftd.ai:cbic:gstr3b","formatKind":"official_provider_framework","officialSourceUrl":"https://www.gstn.org.in/assets/mainDashboard/Pdf/GSP_Implementation_Framework_V_3.0.pdf","lastVerified":"2026-04-26","status":"provider_required","internalFormKeys":["gstr3b-form-v1","gstr3b-review-v1","gstr3b-amend-v1"],"fieldMap":[{"internal":"applicant.gstin","official":"GSTIN"},{"internal":"taxPeriod","official":"return '
                 'period"},{"internal":"supplies.*","official":"GSTR-3B outward and inward supply '
                 'sections"},{"internal":"itc.*","official":"GSTR-3B ITC '
                 'section"},{"internal":"taxPayment.*","official":"GSTR-3B payment/ledger '
                 'section"},{"internal":"arn","official":"Acknowledgement Reference '
                 'Number"}],"notes":["Detailed GSTR-3B API payload is provider/GSP contract '
                 'material and must be supplied by the configured authorized_gsp adapter.","This '
                 'manifest records the official GSP framework boundary and keeps GFTD '
                 'provider-agnostic."],"liveFilingGate":"ind.efiling.submit with '
                 'providerKind=gsp_api or authorized_gsp"}',
                 '2026-04-26']},
 {'sql': 'DELETE FROM vertex_ind_efiling_format WHERE format_key = $1',
  'parameters': ['ind.epfo.ecrFile.forEmployers']},
 {'sql': '\n'
         '      INSERT INTO vertex_ind_efiling_format (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        format_key, jurisdiction, actor_did, format_kind, status,\n'
         '        official_source_url, source_page_url, local_descriptor_path,\n'
         '        internal_form_keys, field_map_json, descriptor_json,\n'
         '        last_verified_at, created_at, org_id, user_id, actor_id\n'
         '      ) VALUES (\n'
         "        $1, $2, DATE '2026-04-27', 2, $3,\n"
         '        $4, $5, $6,\n'
         '        $7, $8, $9,\n'
         '        $10, $11,\n'
         '        $12,\n'
         '        $13,\n'
         '        $14,\n'
         "        $15, '2026-04-27T00:20:00Z',\n"
         "        'ind', 'system', 'sys.ind.efiling.format'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:ind-payroll.gftd.ai:epfo/ai.gftd.apps.ind.efiling.format/ind.epfo.ecrFile.forEmployers',
                 20260427002003,
                 'did:web:ind-payroll.gftd.ai:epfo',
                 'ind.epfo.ecrFile.forEmployers',
                 'epfo',
                 'did:web:ind-payroll.gftd.ai:epfo',
                 'official_plain_text_upload',
                 'active',
                 'https://www.epfindia.gov.in/site_docs/PDFs/OnlineECR_PDFs/ECR_ForEmployers_FileStructure.pdf',
                 '',
                 '00-contracts/formats/ai/gftd/ind/epfo/ecr-file-format.json',
                 'epfo-ecr-form-v1,epfo-review-v1',
                 '[]',
                 '{"formatKey":"ind.epfo.ecrFile.forEmployers","jurisdiction":"epfo","actorDid":"did:web:ind-payroll.gftd.ai:epfo","formatKind":"official_plain_text_upload","officialSourceUrl":"https://www.epfindia.gov.in/site_docs/PDFs/OnlineECR_PDFs/ECR_ForEmployers_FileStructure.pdf","lastVerified":"2026-04-26","status":"active","file":{"recordKind":"one '
                 'detailed line per '
                 'member","delimiter":"#~#","encoding":"plain_text","csvPreparationHint":"Prepare '
                 'as spreadsheet/CSV, then replace commas with #~# and save as '
                 'TXT."},"columns":[{"index":1,"name":"Member '
                 'ID","type":"number","width":7,"required":true,"mapsFrom":"employees[].memberUan"},{"index":2,"name":"Member '
                 'Name","type":"string","width":85,"required":true,"mapsFrom":"employees[].memberName"},{"index":3,"name":"EPF '
                 'Wages","type":"number","width":10,"mapsFrom":"employees[].epfWageInrPaise"},{"index":4,"name":"EPS '
                 'Wages","type":"number","width":10,"mapsFrom":"employees[].epsWageInrPaise"},{"index":5,"name":"EPF '
                 'Contribution EE Share '
                 'due","type":"number","width":10,"mapsFrom":"employees[].employeePfInrPaise"},{"index":6,"name":"EPF '
                 'Contribution EE Share being '
                 'remitted","type":"number","width":10,"mapsFrom":"employees[].employeePfInrPaise"},{"index":7,"name":"EPS '
                 'Contribution '
                 'due","type":"number","width":10,"mapsFrom":"employees[].epsContributionInrPaise"},{"index":8,"name":"EPS '
                 'Contribution being '
                 'remitted","type":"number","width":10,"mapsFrom":"employees[].epsContributionInrPaise"},{"index":9,"name":"Diff '
                 'EPF and EPS Contribution ER Share '
                 'due","type":"number","width":10,"mapsFrom":"employees[].employerPfInrPaise - '
                 'employees[].epsContributionInrPaise"},{"index":10,"name":"Diff EPF and EPS '
                 'Contribution ER Share being '
                 'remitted","type":"number","width":10,"mapsFrom":"employees[].employerPfInrPaise '
                 '- employees[].epsContributionInrPaise"},{"index":11,"name":"NCP '
                 'Days","type":"number","width":2,"mapsFrom":"employees[].ncpDays"},{"index":12,"name":"Refund '
                 'of '
                 'Advances","type":"number","width":10,"mapsFrom":"employees[].refundOfAdvancesInrPaise"},{"index":13,"name":"Arrear '
                 'EPF Wages","type":"number","width":10},{"index":14,"name":"Arrear EPF EE '
                 'Share","type":"number","width":10},{"index":15,"name":"Arrear EPF ER '
                 'Share","type":"number","width":10},{"index":16,"name":"Arrear EPS '
                 'Share","type":"number","width":10},{"index":17,"name":"Father/Husband '
                 'Name","type":"string","width":85,"mapsFrom":"employees[].fatherOrSpouseName"},{"index":18,"name":"Relationship '
                 'with Member","type":"string","width":1},{"index":19,"name":"Date of '
                 'Birth","type":"date","format":"dd/mm/yyyy"},{"index":20,"name":"Gender","type":"string","width":1},{"index":21,"name":"Date '
                 'of Joining '
                 'EPF","type":"date","format":"dd/mm/yyyy","mapsFrom":"employees[].joiningDate"},{"index":22,"name":"Date '
                 'of Joining '
                 'EPS","type":"date","format":"dd/mm/yyyy","mapsFrom":"employees[].joiningDate"},{"index":23,"name":"Date '
                 'of Exit from '
                 'EPF","type":"date","format":"dd/mm/yyyy","mapsFrom":"employees[].exitDate"},{"index":24,"name":"Date '
                 'of Exit from '
                 'EPS","type":"date","format":"dd/mm/yyyy","mapsFrom":"employees[].exitDate"},{"index":25,"name":"Reason '
                 'for '
                 'leaving","type":"string","width":1}],"internalFormKeys":["epfo-ecr-form-v1","epfo-review-v1"],"liveFilingGate":"ind.efiling.submit '
                 'with providerKind=authorized_epfo_integrator"}',
                 '2026-04-26']},
 {'sql': 'DELETE FROM vertex_ind_efiling_format WHERE format_key = $1',
  'parameters': ['ind.esic.monthlyContribution.portal']},
 {'sql': '\n'
         '      INSERT INTO vertex_ind_efiling_format (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        format_key, jurisdiction, actor_did, format_kind, status,\n'
         '        official_source_url, source_page_url, local_descriptor_path,\n'
         '        internal_form_keys, field_map_json, descriptor_json,\n'
         '        last_verified_at, created_at, org_id, user_id, actor_id\n'
         '      ) VALUES (\n'
         "        $1, $2, DATE '2026-04-27', 2, $3,\n"
         '        $4, $5, $6,\n'
         '        $7, $8, $9,\n'
         '        $10, $11,\n'
         '        $12,\n'
         '        $13,\n'
         '        $14,\n'
         "        $15, '2026-04-27T00:20:00Z',\n"
         "        'ind', 'system', 'sys.ind.efiling.format'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:ind-payroll.gftd.ai:esic/ai.gftd.apps.ind.efiling.format/ind.esic.monthlyContribution.portal',
                 20260427002004,
                 'did:web:ind-payroll.gftd.ai:esic',
                 'ind.esic.monthlyContribution.portal',
                 'esic',
                 'did:web:ind-payroll.gftd.ai:esic',
                 'official_portal_or_integrator_payload',
                 'adapter_required',
                 'https://www.esic.gov.in/',
                 '',
                 '00-contracts/formats/ai/gftd/ind/esic/monthly-contribution-format.manifest.json',
                 'esic-monthly-form-v1,esic-review-v1,esic-amend-v1',
                 '[{"internal":"establishment.establishmentEsiCode","official":"employer / '
                 'establishment ESI code"},{"internal":"wageMonth","official":"contribution '
                 'period"},{"internal":"members[].ipNumber","official":"insured person '
                 'number"},{"internal":"members[].grossWageInrPaise","official":"gross '
                 'wages"},{"internal":"members[].employeeContribInrPaise","official":"employee '
                 'contribution"},{"internal":"members[].employerContribInrPaise","official":"employer '
                 'contribution"},{"internal":"challanReference","official":"bank challan '
                 'reference"}]',
                 '{"formatKey":"ind.esic.monthlyContribution.portal","jurisdiction":"esic","actorDid":"did:web:ind-payroll.gftd.ai:esic","formatKind":"official_portal_or_integrator_payload","officialSourceUrl":"https://www.esic.gov.in/","lastVerified":"2026-04-26","status":"adapter_required","internalFormKeys":["esic-monthly-form-v1","esic-review-v1","esic-amend-v1"],"fieldMap":[{"internal":"establishment.establishmentEsiCode","official":"employer '
                 '/ establishment ESI code"},{"internal":"wageMonth","official":"contribution '
                 'period"},{"internal":"members[].ipNumber","official":"insured person '
                 'number"},{"internal":"members[].grossWageInrPaise","official":"gross '
                 'wages"},{"internal":"members[].employeeContribInrPaise","official":"employee '
                 'contribution"},{"internal":"members[].employerContribInrPaise","official":"employer '
                 'contribution"},{"internal":"challanReference","official":"bank challan '
                 'reference"}],"notes":["Public machine-readable ESIC contribution upload schema '
                 'was not available from official sources during 2026-04-26 verification.","Live '
                 'submission remains gated behind '
                 'authorized_esic_integrator."],"liveFilingGate":"ind.efiling.submit with '
                 'providerKind=authorized_esic_integrator"}',
                 '2026-04-26']}]

DOWN = [{'sql': 'DELETE FROM vertex_ind_efiling_format WHERE format_key = $1',
  'parameters': ['ind.itr1.eriSubmitFlow.v1_1']},
 {'sql': 'DELETE FROM vertex_ind_efiling_format WHERE format_key = $1',
  'parameters': ['ind.itr1.prefillSchema.v6_5']},
 {'sql': 'DELETE FROM vertex_ind_efiling_format WHERE format_key = $1',
  'parameters': ['ind.gstr3b.gspFramework.v3']},
 {'sql': 'DELETE FROM vertex_ind_efiling_format WHERE format_key = $1',
  'parameters': ['ind.epfo.ecrFile.forEmployers']},
 {'sql': 'DELETE FROM vertex_ind_efiling_format WHERE format_key = $1',
  'parameters': ['ind.esic.monthlyContribution.portal']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
