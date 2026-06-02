"""Captured from Kysely migration 20260427001000_seed_india_form_definitions."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427001000_seed_india_form_definitions"
down_revision = 'r_20260426235500_vertex_ind_efiling'
branch_labels = None
depends_on = None

UP = [{'sql': '\n      DELETE FROM vertex_form_task WHERE form_key = $1\n    ',
  'parameters': ['itr1-form-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_form_task (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        rkey, repo, did, form_key, name, display_name, description,\n'
         '        form_type, schema_version, components_json, variable_mappings_json,\n'
         '        status, updated_at\n'
         '      ) VALUES (\n'
         "        $1, $2, DATE '2026-04-27', 2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11,\n'
         '        $12, $13, $14,\n'
         "        'active', '2026-04-27T00:10:00Z'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:ind-union.etzhayyim.com:cbdt:itr1/com.etzhayyim.form.task/itr1-form-v1',
                 20260427001000,
                 'did:web:ind-union.etzhayyim.com:cbdt:itr1',
                 'itr1-form-v1',
                 'did:web:ind-union.etzhayyim.com:cbdt:itr1',
                 'did:web:ind-union.etzhayyim.com:cbdt:itr1',
                 'itr1-form-v1',
                 'ITR-1 Sahaj — Individual Income Tax Return',
                 'ITR-1 Sahaj — Individual Income Tax Return',
                 '',
                 'camunda',
                 1,
                 '[{"key":"applicant","type":"fieldset","label":"Personal Details (Part '
                 'A)","x-encryptedSection":"applicantPayload","components":[{"key":"pan","label":"PAN","type":"textfield","required":true,"pattern":"^[A-Z]{5}[0-9]{4}[A-Z]$","x-piiTier":3,"x-encrypt":"signal:v1"},{"key":"aadhaar","label":"Aadhaar","type":"textfield","pattern":"^[0-9]{12}$","x-piiTier":3,"x-encrypt":"signal:v1"},{"key":"name","label":"Name '
                 '(as in PAN)","type":"textfield","required":true},{"key":"dob","label":"Date of '
                 'birth","type":"datepicker","required":true},{"key":"fatherName","label":"Father\'s '
                 'name","type":"textfield"},{"key":"residentialStatus","label":"Residential '
                 'status","type":"select","required":true,"options":[{"value":"resident","label":"Resident"},{"value":"rnor","label":"Resident '
                 'but Not Ordinarily Resident"}]},{"key":"mobile","label":"Mobile '
                 'number","type":"textfield","pattern":"^[0-9]{10}$","x-piiTier":3,"x-encrypt":"signal:v1"},{"key":"email","label":"Email","type":"textfield","x-piiTier":3,"x-encrypt":"signal:v1"},{"key":"address","label":"Address","type":"textarea","x-piiTier":3,"x-encrypt":"signal:v1"},{"key":"pincode","label":"PIN '
                 'code","type":"textfield","pattern":"^[0-9]{6}$"},{"key":"assessmentYear","label":"Assessment '
                 'Year","type":"textfield","required":true,"pattern":"^AY[0-9]{4}-[0-9]{2}$"},{"key":"regimeSelected","label":"Tax '
                 'regime","type":"select","required":true,"options":[{"value":"new","label":"New '
                 'regime (§115BAC) — DEFAULT for AY2024-25 onwards"},{"value":"old","label":"Old '
                 'regime (Form 10-IEA opt-out '
                 'filed)"}]}]},{"key":"income","type":"fieldset","label":"Gross Total Income (Part '
                 'B-TI)","x-encryptedSection":"incomePayload","components":[{"key":"employerTan","label":"Employer '
                 'TAN","type":"textfield","pattern":"^[A-Z]{4}[0-9]{5}[A-Z]$","x-piiTier":3,"x-encrypt":"signal:v1"},{"key":"employerName","label":"Employer '
                 'name","type":"textfield"},{"key":"grossSalaryInrPaise","label":"Gross salary '
                 '(paise)","type":"number","required":true,"description":"Section 17(1) gross '
                 'salary"},{"key":"exemptAllowancesInrPaise","label":"Exempt allowances '
                 '(paise)","type":"number","description":"HRA / LTA etc. under '
                 '§10"},{"key":"standardDeductionInrPaise","label":"Standard deduction '
                 '(paise)","type":"number","description":"₹50,000 / ₹75,000 (new regime '
                 'AY2024-25+)"},{"key":"professionalTaxInrPaise","label":"Professional tax '
                 '(paise)","type":"number"},{"key":"netSalaryInrPaise","label":"Net salary income '
                 '(paise)","type":"number","readOnly":true},{"key":"houseAnnualValueInrPaise","label":"House '
                 '— annual value '
                 '(paise)","type":"number"},{"key":"houseInterestInrPaise","label":"Interest on '
                 'housing loan (paise)","type":"number","description":"§24(b) up to ₹2 lakh '
                 'self-occupied"},{"key":"houseNetIncomeInrPaise","label":"House property net '
                 '(paise)","type":"number","readOnly":true},{"key":"savingInterestInrPaise","label":"Bank '
                 'savings interest '
                 '(paise)","type":"number"},{"key":"fdInterestInrPaise","label":"FD / RD / '
                 'corporate FD interest '
                 '(paise)","type":"number"},{"key":"dividendInrPaise","label":"Dividend income '
                 '(paise)","type":"number"},{"key":"otherSourcesInrPaise","label":"Other sources '
                 'total '
                 '(paise)","type":"number","readOnly":true},{"key":"agriIncomeInrPaise","label":"Agricultural '
                 'income (paise, ≤ '
                 '₹5,000)","type":"number"},{"key":"grossTotalIncomeInrPaise","label":"Gross Total '
                 'Income (paise)","type":"number","readOnly":true,"description":"Sum: salary + '
                 'house + other '
                 'sources"}]},{"key":"deductions","type":"fieldset","label":"Deductions (Chapter '
                 'VI-A)","x-encryptedSection":"deductionsPayload","components":[{"key":"deduction80cInrPaise","label":"§80C '
                 '(PF/PPF/LIC/ELSS, max ₹1.5L) '
                 '(paise)","type":"number"},{"key":"deduction80ccd1bInrPaise","label":"§80CCD(1B) '
                 'NPS additional ₹50K '
                 '(paise)","type":"number"},{"key":"deduction80dInrPaise","label":"§80D (medical '
                 'insurance, paise)","type":"number"},{"key":"deduction80gInrPaise","label":"§80G '
                 '(donations, '
                 'paise)","type":"number"},{"key":"deduction80ttaInrPaise","label":"§80TTA '
                 '(savings interest ≤ ₹10K, '
                 'paise)","type":"number"},{"key":"deduction80ttbInrPaise","label":"§80TTB (senior '
                 'citizens ≤ ₹50K, '
                 'paise)","type":"number"},{"key":"deduction80uInrPaise","label":"§80U '
                 '(disability, '
                 'paise)","type":"number"},{"key":"deductionOtherInrPaise","label":"Other Chapter '
                 'VI-A deductions '
                 '(paise)","type":"number"},{"key":"totalDeductionInrPaise","label":"Total '
                 'deductions '
                 '(paise)","type":"number","readOnly":true},{"key":"totalIncomeInrPaise","label":"Total '
                 'Income (paise, Gross − '
                 'Deductions)","type":"number","readOnly":true,"description":"Must be ≤ ₹50 lakh = '
                 '₹50,00,00,000 paise for ITR-1 '
                 'eligibility"}]},{"key":"tax","type":"fieldset","label":"Tax Computation & '
                 'Payment","x-encryptedSection":"taxPayload","components":[{"key":"taxOnTotalIncomeInrPaise","label":"Tax '
                 'on total income '
                 '(paise)","type":"number","readOnly":true},{"key":"rebate87aInrPaise","label":"§87A '
                 'rebate (paise)","type":"number","description":"₹12,500 (old) / ₹25,000 (new, '
                 'income ≤ ₹7L)"},{"key":"surchargeInrPaise","label":"Surcharge '
                 '(paise)","type":"number"},{"key":"cessInrPaise","label":"Health & Education Cess '
                 '4% (paise)","type":"number"},{"key":"totalTaxInrPaise","label":"Total tax + cess '
                 '(paise)","type":"number","readOnly":true},{"key":"tdsFrom16InrPaise","label":"TDS '
                 'from Form 16 '
                 '(paise)","type":"number"},{"key":"tdsFromOtherInrPaise","label":"TDS other (Form '
                 '16A, paise)","type":"number"},{"key":"advanceTaxInrPaise","label":"Advance tax '
                 'paid '
                 '(paise)","type":"number"},{"key":"selfAssessmentTaxInrPaise","label":"Self-assessment '
                 'tax paid (paise)","type":"number"},{"key":"totalTaxPaidInrPaise","label":"Total '
                 'tax paid '
                 '(paise)","type":"number","readOnly":true},{"key":"refundInrPaise","label":"Refund '
                 '(paise)","type":"number","readOnly":true,"description":"If total paid > total '
                 'tax"},{"key":"taxPayableInrPaise","label":"Tax payable '
                 '(paise)","type":"number","readOnly":true,"description":"If total tax > total '
                 'paid, pay before filing"},{"key":"refundBankAccount","label":"Refund bank '
                 'A/C","type":"textfield","x-piiTier":3,"x-encrypt":"signal:v1"},{"key":"refundBankIfsc","label":"Refund '
                 'bank '
                 'IFSC","type":"textfield","pattern":"^[A-Z]{4}0[A-Z0-9]{6}$"}]},{"key":"declaration","type":"fieldset","label":"Verification","components":[{"key":"consentTier3","type":"checkbox","required":true,"label":"I '
                 'declare the information is true and complete. I authorize 7-year retention per '
                 'IT Act §44AA + DPDP '
                 '§8(7)."},{"key":"place","label":"Place","type":"textfield","required":true},{"key":"verificationDate","label":"Verification '
                 'date","type":"datepicker","required":true}]}]',
                 '{}']},
 {'sql': '\n      DELETE FROM vertex_form_task WHERE form_key = $1\n    ',
  'parameters': ['itr1-self-review-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_form_task (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        rkey, repo, did, form_key, name, display_name, description,\n'
         '        form_type, schema_version, components_json, variable_mappings_json,\n'
         '        status, updated_at\n'
         '      ) VALUES (\n'
         "        $1, $2, DATE '2026-04-27', 2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11,\n'
         '        $12, $13, $14,\n'
         "        'active', '2026-04-27T00:10:00Z'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:ind-union.etzhayyim.com:cbdt:itr1/com.etzhayyim.form.task/itr1-self-review-v1',
                 20260427001001,
                 'did:web:ind-union.etzhayyim.com:cbdt:itr1',
                 'itr1-self-review-v1',
                 'did:web:ind-union.etzhayyim.com:cbdt:itr1',
                 'did:web:ind-union.etzhayyim.com:cbdt:itr1',
                 'itr1-self-review-v1',
                 'ITR-1 Self Review (before e-File)',
                 'ITR-1 Self Review (before e-File)',
                 '',
                 'camunda',
                 1,
                 '[{"key":"summary","type":"fieldset","label":"Summary '
                 '(read-only)","components":[{"key":"assessmentYear","label":"Assessment '
                 'Year","type":"textfield","readOnly":true},{"key":"totalIncomeInrPaise","label":"Total '
                 'Income '
                 '(paise)","type":"number","readOnly":true},{"key":"totalTaxInrPaise","label":"Total '
                 'Tax + Cess '
                 '(paise)","type":"number","readOnly":true},{"key":"totalTaxPaidInrPaise","label":"Total '
                 'Tax Paid '
                 '(paise)","type":"number","readOnly":true},{"key":"refundInrPaise","label":"Refund '
                 '(paise)","type":"number","readOnly":true},{"key":"taxPayableInrPaise","label":"Tax '
                 'Payable '
                 '(paise)","type":"number","readOnly":true}]},{"key":"eligibility","type":"fieldset","label":"ITR-1 '
                 'eligibility checks","components":[{"key":"totalIncomeBelowCap","label":"Total '
                 'income ≤ ₹50 '
                 'lakh","type":"checkbox","required":true},{"key":"noCapitalGains","label":"No '
                 'capital gains '
                 'income","type":"checkbox","required":true},{"key":"noForeignAssets","label":"No '
                 'foreign assets / '
                 'income","type":"checkbox","required":true},{"key":"notDirector","label":"Not a '
                 'company '
                 'director","type":"checkbox","required":true},{"key":"noUnlistedEquity","label":"No '
                 'unlisted equity '
                 'holdings","type":"checkbox","required":true},{"key":"agriBelowCap","label":"Agricultural '
                 'income ≤ '
                 '₹5,000","type":"checkbox","required":true}]},{"key":"reconciliation","type":"fieldset","label":"Reconciliation","components":[{"key":"tdsMatches26asAis","label":"TDS '
                 'amount matches Form 26AS / '
                 'AIS","type":"checkbox","required":true},{"key":"panAadhaarLinked","label":"PAN '
                 'linked to Aadhaar '
                 '(mandatory)","type":"checkbox","required":true},{"key":"bankAccountValidated","label":"Refund '
                 'bank A/C pre-validated on '
                 'portal","type":"checkbox","required":true},{"key":"regimeChosen","label":"Tax '
                 'regime explicitly chosen (new vs '
                 'old)","type":"checkbox","required":true}]},{"key":"verdict","type":"fieldset","label":"Decision","components":[{"key":"decision","label":"Action","type":"select","required":true,"options":[{"value":"approve","label":"All '
                 'checks pass — proceed to e-File"},{"value":"reject","label":"Issues found — '
                 'return to form for '
                 'correction"}]},{"key":"comment","label":"Notes","type":"textarea","validate":{"maxLength":1500}}]}]',
                 '{}']},
 {'sql': '\n      DELETE FROM vertex_form_task WHERE form_key = $1\n    ',
  'parameters': ['itr1-amend-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_form_task (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        rkey, repo, did, form_key, name, display_name, description,\n'
         '        form_type, schema_version, components_json, variable_mappings_json,\n'
         '        status, updated_at\n'
         '      ) VALUES (\n'
         "        $1, $2, DATE '2026-04-27', 2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11,\n'
         '        $12, $13, $14,\n'
         "        'active', '2026-04-27T00:10:00Z'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:ind-union.etzhayyim.com:cbdt:itr1/com.etzhayyim.form.task/itr1-amend-v1',
                 20260427001002,
                 'did:web:ind-union.etzhayyim.com:cbdt:itr1',
                 'itr1-amend-v1',
                 'did:web:ind-union.etzhayyim.com:cbdt:itr1',
                 'did:web:ind-union.etzhayyim.com:cbdt:itr1',
                 'itr1-amend-v1',
                 'ITR-1 §139(5) Revised Return',
                 'ITR-1 §139(5) Revised Return',
                 '',
                 'camunda',
                 1,
                 '[{"key":"revisedMeta","type":"fieldset","label":"Revised Return '
                 'Header","components":[{"key":"predecessorAckNumber","label":"Original ack '
                 'number","type":"textfield","required":true},{"key":"revisedReason","label":"Reason","type":"select","required":true,"options":[{"value":"correctWageIncome","label":"Correct '
                 'wage / employer income"},{"value":"correctTdsClaim","label":"Correct TDS claim '
                 '(mismatch with 26AS)"},{"value":"correctDeduction","label":"Correct Chapter VI-A '
                 'deduction"},{"value":"correctBank","label":"Correct refund bank '
                 'A/C"},{"value":"correctAddress","label":"Correct '
                 'address"},{"value":"other","label":"Other"}]},{"key":"revisedDescription","label":"Description","type":"textarea","validate":{"maxLength":1500}}]},{"key":"deltas","type":"fieldset","label":"Delta '
                 'values (set only the fields that '
                 'changed)","x-encryptedSection":"amendmentPayload","components":[{"key":"newGrossSalaryInrPaise","label":"New '
                 'gross salary '
                 '(paise)","type":"number"},{"key":"newTdsFrom16InrPaise","label":"New TDS from '
                 'Form 16 (paise)","type":"number"},{"key":"newDeduction80cInrPaise","label":"New '
                 '§80C (paise)","type":"number"},{"key":"newDeduction80dInrPaise","label":"New '
                 '§80D (paise)","type":"number"},{"key":"newRefundBankAccount","label":"New refund '
                 'bank '
                 'A/C","type":"textfield","x-piiTier":3,"x-encrypt":"signal:v1"},{"key":"newRefundBankIfsc","label":"New '
                 'refund '
                 'IFSC","type":"textfield","pattern":"^[A-Z]{4}0[A-Z0-9]{6}$"},{"key":"newAddress","label":"New '
                 'address","type":"textarea","x-piiTier":3,"x-encrypt":"signal:v1"}]},{"key":"declaration","type":"fieldset","label":"Verification","components":[{"key":"consentTier3","type":"checkbox","required":true,"label":"Revised '
                 'return data may be retained for 7 years per IT Act '
                 '§44AA."},{"key":"verificationDate","label":"Date","type":"datepicker","required":true}]}]',
                 '{}']},
 {'sql': '\n      DELETE FROM vertex_form_task WHERE form_key = $1\n    ',
  'parameters': ['gstr3b-form-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_form_task (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        rkey, repo, did, form_key, name, display_name, description,\n'
         '        form_type, schema_version, components_json, variable_mappings_json,\n'
         '        status, updated_at\n'
         '      ) VALUES (\n'
         "        $1, $2, DATE '2026-04-27', 2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11,\n'
         '        $12, $13, $14,\n'
         "        'active', '2026-04-27T00:10:00Z'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:ind-union.etzhayyim.com:cbic:gstr3b/com.etzhayyim.form.task/gstr3b-form-v1',
                 20260427001003,
                 'did:web:ind-union.etzhayyim.com:cbic:gstr3b',
                 'gstr3b-form-v1',
                 'did:web:ind-union.etzhayyim.com:cbic:gstr3b',
                 'did:web:ind-union.etzhayyim.com:cbic:gstr3b',
                 'gstr3b-form-v1',
                 'GSTR-3B Monthly Summary Return',
                 'GSTR-3B Monthly Summary Return',
                 '',
                 'camunda',
                 1,
                 '[{"key":"applicant","type":"fieldset","label":"Header","x-encryptedSection":"applicantPayload","components":[{"key":"gstin","label":"GSTIN","type":"textfield","required":true,"pattern":"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$","x-piiTier":3,"x-encrypt":"signal:v1"},{"key":"legalName","label":"Legal '
                 'name","type":"textfield","required":true},{"key":"tradeName","label":"Trade '
                 'name","type":"textfield"},{"key":"pan","label":"PAN","type":"textfield","pattern":"^[A-Z]{5}[0-9]{4}[A-Z]$","x-piiTier":3,"x-encrypt":"signal:v1"},{"key":"address","label":"Principal '
                 'place of '
                 'business","type":"textarea","x-piiTier":3,"x-encrypt":"signal:v1"},{"key":"stateCode","label":"State '
                 'code","type":"textfield","pattern":"^[0-9]{2}$"},{"key":"taxPeriod","label":"Tax '
                 'period","type":"textfield","required":true,"pattern":"^[0-9]{4}-(0[1-9]|1[0-2])$"},{"key":"filingFrequency","label":"Filing '
                 'frequency","type":"select","required":true,"options":[{"value":"monthly","label":"Monthly"},{"value":"qrmpFinal","label":"QRMP '
                 '— quarterly final"}]}]},{"key":"supplies","type":"fieldset","label":"3.1 '
                 'Supplies summary '
                 '(paise)","x-encryptedSection":"suppliesPayload","components":[{"key":"outwardTaxableValueInrPaise","label":"(a) '
                 'Outward taxable supplies — '
                 'value","type":"number"},{"key":"outwardTaxableIgstInrPaise","label":"(a) Outward '
                 'taxable — '
                 'IGST","type":"number"},{"key":"outwardTaxableCgstInrPaise","label":"(a) Outward '
                 'taxable — '
                 'CGST","type":"number"},{"key":"outwardTaxableSgstInrPaise","label":"(a) Outward '
                 'taxable — '
                 'SGST/UTGST","type":"number"},{"key":"outwardTaxableCessInrPaise","label":"(a) '
                 'Outward taxable — '
                 'Cess","type":"number"},{"key":"outwardZeroRatedValueInrPaise","label":"(b) '
                 'Outward zero-rated — '
                 'value","type":"number"},{"key":"outwardZeroRatedIgstInrPaise","label":"(b) '
                 'Outward zero-rated — '
                 'IGST","type":"number"},{"key":"outwardNilRatedValueInrPaise","label":"(c) '
                 'Outward nil-rated / exempt — '
                 'value","type":"number"},{"key":"inwardRcmValueInrPaise","label":"(d) Inward RCM '
                 '— value","type":"number"},{"key":"inwardRcmIgstInrPaise","label":"(d) Inward RCM '
                 '— IGST","type":"number"},{"key":"inwardRcmCgstInrPaise","label":"(d) Inward RCM '
                 '— CGST","type":"number"},{"key":"inwardRcmSgstInrPaise","label":"(d) Inward RCM '
                 '— SGST/UTGST","type":"number"},{"key":"outwardNonGstValueInrPaise","label":"(e) '
                 'Non-GST outward — '
                 'value","type":"number"},{"key":"interState32UrpValueInrPaise","label":"3.2 '
                 'Inter-state to URP — '
                 'value","type":"number"},{"key":"interState32UrpIgstInrPaise","label":"3.2 '
                 'Inter-state to URP — '
                 'IGST","type":"number"},{"key":"interState32CompValueInrPaise","label":"3.2 '
                 'Inter-state to Composition — '
                 'value","type":"number"},{"key":"interState32UinValueInrPaise","label":"3.2 '
                 'Inter-state to UIN — '
                 'value","type":"number"}]},{"key":"itc","type":"fieldset","label":"4 Input Tax '
                 'Credit '
                 '(paise)","x-encryptedSection":"itcPayload","components":[{"key":"itcImportGoodsIgstInrPaise","label":"(A.1) '
                 'Import of goods — '
                 'IGST","type":"number"},{"key":"itcImportServicesIgstInrPaise","label":"(A.2) '
                 'Import of services — '
                 'IGST","type":"number"},{"key":"itcInwardRcmCgstInrPaise","label":"(A.3) Inward '
                 'RCM — CGST","type":"number"},{"key":"itcInwardRcmSgstInrPaise","label":"(A.3) '
                 'Inward RCM — '
                 'SGST/UTGST","type":"number"},{"key":"itcOtherIgstInrPaise","label":"(A.5) All '
                 'other ITC — IGST","type":"number"},{"key":"itcOtherCgstInrPaise","label":"(A.5) '
                 'All other ITC — '
                 'CGST","type":"number"},{"key":"itcOtherSgstInrPaise","label":"(A.5) All other '
                 'ITC — '
                 'SGST/UTGST","type":"number"},{"key":"itcReverseRule42IgstInrPaise","label":"(B.1) '
                 'Reversed Rule 42/43 — '
                 'IGST","type":"number"},{"key":"itcReverseRule42CgstInrPaise","label":"(B.1) '
                 'Reversed Rule 42/43 — '
                 'CGST","type":"number"},{"key":"itcReverseOtherInrPaise","label":"(B.2) Other '
                 'reversal","type":"number"},{"key":"itcNetIgstInrPaise","label":"(C) Net ITC '
                 'available — '
                 'IGST","type":"number","readOnly":true},{"key":"itcNetCgstInrPaise","label":"(C) '
                 'Net ITC available — '
                 'CGST","type":"number","readOnly":true},{"key":"itcNetSgstInrPaise","label":"(C) '
                 'Net ITC available — '
                 'SGST","type":"number","readOnly":true},{"key":"itcIneligibleSection17InrPaise","label":"(D) '
                 'Ineligible '
                 '§17(5)","type":"number"}]},{"key":"exempt","type":"fieldset","label":"5 Exempt / '
                 'nil-rated / non-GST inward '
                 '(paise)","components":[{"key":"compositionFromInrPaise","label":"(a) From '
                 'Composition / exempt / nil-rated — '
                 'inter-state","type":"number"},{"key":"compositionFromIntraInrPaise","label":"(a) '
                 'From Composition / exempt / nil-rated — '
                 'intra-state","type":"number"},{"key":"nonGstInwardInterInrPaise","label":"(b) '
                 'Non-GST supply — '
                 'inter-state","type":"number"},{"key":"nonGstInwardIntraInrPaise","label":"(b) '
                 'Non-GST supply — '
                 'intra-state","type":"number"}]},{"key":"tax","type":"fieldset","label":"6.1 Tax '
                 'payment '
                 '(paise)","x-encryptedSection":"taxPaymentPayload","components":[{"key":"taxPayableIgstInrPaise","label":"Tax '
                 'payable — '
                 'IGST","type":"number","readOnly":true},{"key":"taxPayableCgstInrPaise","label":"Tax '
                 'payable — '
                 'CGST","type":"number","readOnly":true},{"key":"taxPayableSgstInrPaise","label":"Tax '
                 'payable — '
                 'SGST/UTGST","type":"number","readOnly":true},{"key":"taxPayableCessInrPaise","label":"Tax '
                 'payable — '
                 'Cess","type":"number","readOnly":true},{"key":"paidByItcIgstInrPaise","label":"Paid '
                 'by ITC — IGST","type":"number"},{"key":"paidByItcCgstInrPaise","label":"Paid by '
                 'ITC — CGST","type":"number"},{"key":"paidByItcSgstInrPaise","label":"Paid by ITC '
                 '— SGST/UTGST","type":"number"},{"key":"paidByCashIgstInrPaise","label":"Paid by '
                 'cash — IGST","type":"number"},{"key":"paidByCashCgstInrPaise","label":"Paid by '
                 'cash — CGST","type":"number"},{"key":"paidByCashSgstInrPaise","label":"Paid by '
                 'cash — '
                 'SGST/UTGST","type":"number"},{"key":"paidByCashCessInrPaise","label":"Paid by '
                 'cash — Cess","type":"number"},{"key":"interestInrPaise","label":"Interest '
                 '§50","type":"number"},{"key":"lateFeeInrPaise","label":"Late fee '
                 '§47","type":"number"}]},{"key":"totals","type":"fieldset","label":"Totals '
                 '(computed)","components":[{"key":"totalOutwardTaxInrPaise","label":"Total '
                 'outward tax '
                 '(IGST+CGST+SGST+Cess)","type":"number","readOnly":true},{"key":"totalInwardItcInrPaise","label":"Total '
                 'ITC '
                 'available","type":"number","readOnly":true},{"key":"totalNetTaxInrPaise","label":"Net '
                 'tax payable '
                 '(cash)","type":"number","readOnly":true}]},{"key":"declaration","type":"fieldset","label":"Verification","components":[{"key":"consentTier3","type":"checkbox","required":true,"label":"Verified '
                 'true and complete. 6-year retention per CGST §35(1) + Rule '
                 '56."},{"key":"verificationDate","label":"Date","type":"datepicker","required":true}]}]',
                 '{}']},
 {'sql': '\n      DELETE FROM vertex_form_task WHERE form_key = $1\n    ',
  'parameters': ['gstr3b-review-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_form_task (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        rkey, repo, did, form_key, name, display_name, description,\n'
         '        form_type, schema_version, components_json, variable_mappings_json,\n'
         '        status, updated_at\n'
         '      ) VALUES (\n'
         "        $1, $2, DATE '2026-04-27', 2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11,\n'
         '        $12, $13, $14,\n'
         "        'active', '2026-04-27T00:10:00Z'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:ind-union.etzhayyim.com:cbic:gstr3b/com.etzhayyim.form.task/gstr3b-review-v1',
                 20260427001004,
                 'did:web:ind-union.etzhayyim.com:cbic:gstr3b',
                 'gstr3b-review-v1',
                 'did:web:ind-union.etzhayyim.com:cbic:gstr3b',
                 'did:web:ind-union.etzhayyim.com:cbic:gstr3b',
                 'gstr3b-review-v1',
                 'GSTR-3B Finance Review',
                 'GSTR-3B Finance Review',
                 '',
                 'camunda',
                 1,
                 '[{"key":"summary","type":"fieldset","label":"Summary '
                 '(read-only)","components":[{"key":"taxPeriod","label":"Tax '
                 'period","type":"textfield","readOnly":true},{"key":"totalOutwardTaxInrPaise","label":"Total '
                 'outward '
                 'tax","type":"number","readOnly":true},{"key":"totalInwardItcInrPaise","label":"Total '
                 'ITC","type":"number","readOnly":true},{"key":"totalNetTaxInrPaise","label":"Net '
                 'tax payable '
                 '(cash)","type":"number","readOnly":true}]},{"key":"checks","type":"fieldset","label":"Control '
                 'checks","components":[{"key":"gstinFormatValid","label":"GSTIN 15-char format '
                 'valid","type":"checkbox","required":true},{"key":"outwardSumIntegrity","label":"3.1 '
                 'sums match P/L '
                 'revenue","type":"checkbox","required":true},{"key":"itcEligibility","label":"ITC '
                 '§17(5) ineligible items '
                 'excluded","type":"checkbox","required":true},{"key":"rule36ItcMatch","label":"ITC '
                 '≤ GSTR-2B (Rule '
                 '36(4))","type":"checkbox","required":true},{"key":"ledgerReconciled","label":"Cash '
                 '+ credit ledger balances '
                 'reconciled","type":"checkbox","required":true},{"key":"rcmDeclared","label":"All '
                 'RCM liabilities declared in '
                 '3.1(d)","type":"checkbox","required":true}]},{"key":"verdict","type":"fieldset","label":"Decision","components":[{"key":"decision","label":"Decision","type":"select","required":true,"options":[{"value":"approve","label":"Approve '
                 '— proceed to portal file"},{"value":"reject","label":"Return to gst-officer for '
                 'correction"}]},{"key":"comment","label":"Comment","type":"textarea","validate":{"maxLength":1500}},{"key":"reviewedAt","label":"Reviewed '
                 'at","type":"datepicker","required":true}]}]',
                 '{}']},
 {'sql': '\n      DELETE FROM vertex_form_task WHERE form_key = $1\n    ',
  'parameters': ['gstr3b-amend-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_form_task (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        rkey, repo, did, form_key, name, display_name, description,\n'
         '        form_type, schema_version, components_json, variable_mappings_json,\n'
         '        status, updated_at\n'
         '      ) VALUES (\n'
         "        $1, $2, DATE '2026-04-27', 2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11,\n'
         '        $12, $13, $14,\n'
         "        'active', '2026-04-27T00:10:00Z'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:ind-union.etzhayyim.com:cbic:gstr3b/com.etzhayyim.form.task/gstr3b-amend-v1',
                 20260427001005,
                 'did:web:ind-union.etzhayyim.com:cbic:gstr3b',
                 'gstr3b-amend-v1',
                 'did:web:ind-union.etzhayyim.com:cbic:gstr3b',
                 'did:web:ind-union.etzhayyim.com:cbic:gstr3b',
                 'gstr3b-amend-v1',
                 'GSTR-3B DRC-03 Amendment',
                 'GSTR-3B DRC-03 Amendment',
                 '',
                 'camunda',
                 1,
                 '[{"key":"amendmentMeta","type":"fieldset","label":"Amendment Header '
                 '(DRC-03)","components":[{"key":"predecessorArn","label":"Predecessor '
                 'ARN","type":"textfield","required":true},{"key":"amendmentDate","label":"Effective '
                 'date","type":"datepicker","required":true},{"key":"amendmentReason","label":"Reason","type":"select","required":true,"options":[{"value":"undeclaredOutward","label":"Undeclared '
                 'outward supply"},{"value":"excessItc","label":"Excess ITC '
                 'claimed"},{"value":"wrongItc","label":"Wrong ITC '
                 '(ineligible)"},{"value":"rateError","label":"Wrong tax rate / '
                 'classification"},{"value":"rcmOmission","label":"RCM liability '
                 'omission"},{"value":"other","label":"Other"}]},{"key":"amendmentDescription","label":"Description","type":"textarea","validate":{"maxLength":1500}}]},{"key":"deltas","type":"fieldset","label":"Delta '
                 'values '
                 '(paise)","x-encryptedSection":"amendmentPayload","components":[{"key":"deltaIgstInrPaise","label":"Delta '
                 'IGST","type":"number"},{"key":"deltaCgstInrPaise","label":"Delta '
                 'CGST","type":"number"},{"key":"deltaSgstInrPaise","label":"Delta '
                 'SGST/UTGST","type":"number"},{"key":"deltaCessInrPaise","label":"Delta '
                 'Cess","type":"number"},{"key":"interestInrPaise","label":"Interest §50 (18% '
                 'pa)","type":"number"},{"key":"lateFeeInrPaise","label":"Late fee '
                 '§47","type":"number"},{"key":"totalDeltaInrPaise","label":"Total to pay via '
                 'DRC-03","type":"number","readOnly":true}]},{"key":"declaration","type":"fieldset","label":"Verification","components":[{"key":"consentTier3","type":"checkbox","required":true,"label":"Voluntary '
                 'disclosure under §73(5) / §74(5). 6-year '
                 'retention."},{"key":"verificationDate","label":"Date","type":"datepicker","required":true}]}]',
                 '{}']},
 {'sql': '\n      DELETE FROM vertex_form_task WHERE form_key = $1\n    ',
  'parameters': ['epfo-ecr-form-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_form_task (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        rkey, repo, did, form_key, name, display_name, description,\n'
         '        form_type, schema_version, components_json, variable_mappings_json,\n'
         '        status, updated_at\n'
         '      ) VALUES (\n'
         "        $1, $2, DATE '2026-04-27', 2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11,\n'
         '        $12, $13, $14,\n'
         "        'active', '2026-04-27T00:10:00Z'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:ind-payroll.etzhayyim.com:epfo/com.etzhayyim.form.task/epfo-ecr-form-v1',
                 20260427001006,
                 'did:web:ind-payroll.etzhayyim.com:epfo',
                 'epfo-ecr-form-v1',
                 'did:web:ind-payroll.etzhayyim.com:epfo',
                 'did:web:ind-payroll.etzhayyim.com:epfo',
                 'epfo-ecr-form-v1',
                 'EPFO Electronic Challan-cum-Return (Monthly)',
                 'EPFO Electronic Challan-cum-Return (Monthly)',
                 '',
                 'camunda',
                 1,
                 '[{"key":"establishment","type":"fieldset","label":"Establishment '
                 'Header","components":[{"key":"employerName","label":"Employer '
                 'name","type":"textfield","required":true},{"key":"establishmentPfCode","label":"PF '
                 'code","type":"textfield","required":true},{"key":"wageMonth","label":"Wage '
                 'month","type":"textfield","required":true,"description":"YYYY-MM"},{"key":"totalMembers","label":"Total '
                 'members","type":"number","required":true},{"key":"totalWageInrPaise","label":"Total '
                 'wages '
                 '(paise)","type":"number","required":true},{"key":"totalEmployerPfInrPaise","label":"Employer '
                 'PF '
                 '(paise)","type":"number","required":true},{"key":"totalEmployeePfInrPaise","label":"Employee '
                 'PF '
                 '(paise)","type":"number","required":true},{"key":"totalEpsInrPaise","label":"EPS '
                 '(paise)","type":"number","required":true},{"key":"totalAdminInrPaise","label":"Admin '
                 'charges '
                 '(paise)","type":"number"}]},{"key":"employees","type":"datagrid","label":"Employee '
                 'Roster","x-encryptedSection":"rosterPayload","components":[{"key":"memberUan","label":"UAN","type":"textfield","required":true,"pattern":"^[0-9]{12}$","x-piiTier":3,"x-encrypt":"signal:v1"},{"key":"memberName","label":"Member '
                 'name","type":"textfield","required":true},{"key":"fatherOrSpouseName","label":"Father/Spouse '
                 'name","type":"textfield"},{"key":"aadhaar","label":"Aadhaar","type":"textfield","pattern":"^[0-9]{12}$","x-piiTier":3,"x-encrypt":"signal:v1"},{"key":"pan","label":"PAN","type":"textfield","pattern":"^[A-Z]{5}[0-9]{4}[A-Z]$","x-piiTier":3,"x-encrypt":"signal:v1"},{"key":"bankAccount","label":"Bank '
                 'account '
                 'number","type":"textfield","x-piiTier":3,"x-encrypt":"signal:v1"},{"key":"joiningDate","label":"Joining '
                 'date","type":"datepicker","required":true},{"key":"exitDate","label":"Exit '
                 'date","type":"datepicker"},{"key":"grossWageInrPaise","label":"Gross wage '
                 '(paise)","type":"number","required":true},{"key":"epfWageInrPaise","label":"EPF '
                 'wage '
                 '(paise)","type":"number","required":true},{"key":"epsWageInrPaise","label":"EPS '
                 'wage '
                 '(paise)","type":"number","required":true},{"key":"edliWageInrPaise","label":"EDLI '
                 'wage (paise)","type":"number"},{"key":"employeePfInrPaise","label":"Employee PF '
                 '(paise)","type":"number","required":true},{"key":"employerPfInrPaise","label":"Employer '
                 'PF '
                 '(paise)","type":"number","required":true},{"key":"epsContributionInrPaise","label":"EPS '
                 'contribution '
                 '(paise)","type":"number","required":true},{"key":"ncpDays","label":"NCP '
                 'days","type":"number"},{"key":"refundOfAdvancesInrPaise","label":"Refund of '
                 'advances '
                 '(paise)","type":"number"}]},{"key":"declaration","type":"fieldset","label":"Declaration","components":[{"key":"consentTier3","type":"checkbox","required":true,"label":"Sensitive '
                 'payroll identifiers and wage records may be stored for 7 years for EPFO '
                 'compliance and '
                 'audit."},{"key":"signatureDate","type":"datepicker","required":true,"label":"Signature '
                 'date"}]}]',
                 '{}']},
 {'sql': '\n      DELETE FROM vertex_form_task WHERE form_key = $1\n    ',
  'parameters': ['epfo-review-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_form_task (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        rkey, repo, did, form_key, name, display_name, description,\n'
         '        form_type, schema_version, components_json, variable_mappings_json,\n'
         '        status, updated_at\n'
         '      ) VALUES (\n'
         "        $1, $2, DATE '2026-04-27', 2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11,\n'
         '        $12, $13, $14,\n'
         "        'active', '2026-04-27T00:10:00Z'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:ind-payroll.etzhayyim.com:epfo/com.etzhayyim.form.task/epfo-review-v1',
                 20260427001007,
                 'did:web:ind-payroll.etzhayyim.com:epfo',
                 'epfo-review-v1',
                 'did:web:ind-payroll.etzhayyim.com:epfo',
                 'did:web:ind-payroll.etzhayyim.com:epfo',
                 'epfo-review-v1',
                 'EPFO ECR Review',
                 'EPFO ECR Review',
                 '',
                 'camunda',
                 1,
                 '[{"key":"summary","type":"fieldset","label":"Submission '
                 'Summary","components":[{"key":"establishmentPfCode","label":"PF '
                 'code","type":"textfield","readOnly":true},{"key":"wageMonth","label":"Wage '
                 'month","type":"textfield","readOnly":true},{"key":"submittedAt","label":"Submitted '
                 'at","type":"textfield","readOnly":true},{"key":"totalMembers","label":"Total '
                 'members","type":"number","readOnly":true},{"key":"totalEmployerPfInrPaise","label":"Employer '
                 'PF '
                 '(paise)","type":"number","readOnly":true},{"key":"totalEmployeePfInrPaise","label":"Employee '
                 'PF '
                 '(paise)","type":"number","readOnly":true},{"key":"totalEpsInrPaise","label":"EPS '
                 '(paise)","type":"number","readOnly":true}]},{"key":"checks","type":"fieldset","label":"Control '
                 'Checks","components":[{"key":"sumMatches","label":"Roster sums match monthly '
                 'totals","type":"checkbox","required":true},{"key":"uanFormatValid","label":"UAN '
                 'values are 12 '
                 'digits","type":"checkbox","required":true},{"key":"pfFormulaValid","label":"PF/EPS '
                 'calculations are '
                 'correct","type":"checkbox","required":true},{"key":"bankDataValidated","label":"Bank '
                 'and DBT details '
                 'reconciled","type":"checkbox","required":true}]},{"key":"verdict","type":"fieldset","label":"Decision","components":[{"key":"decision","label":"Decision","type":"select","required":true,"options":[{"value":"approve","label":"Approve"},{"value":"reject","label":"Reject"}]},{"key":"trrn","label":"TRRN","type":"textfield","description":"Required '
                 'when the portal filing has '
                 'completed."},{"key":"comment","label":"Comment","type":"textarea","validate":{"maxLength":1000}},{"key":"reviewedAt","label":"Reviewed '
                 'at","type":"datepicker","required":true}]}]',
                 '{}']},
 {'sql': '\n      DELETE FROM vertex_form_task WHERE form_key = $1\n    ',
  'parameters': ['epfo-amend-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_form_task (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        rkey, repo, did, form_key, name, display_name, description,\n'
         '        form_type, schema_version, components_json, variable_mappings_json,\n'
         '        status, updated_at\n'
         '      ) VALUES (\n'
         "        $1, $2, DATE '2026-04-27', 2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11,\n'
         '        $12, $13, $14,\n'
         "        'active', '2026-04-27T00:10:00Z'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:ind-payroll.etzhayyim.com:epfo/com.etzhayyim.form.task/epfo-amend-v1',
                 20260427001008,
                 'did:web:ind-payroll.etzhayyim.com:epfo',
                 'epfo-amend-v1',
                 'did:web:ind-payroll.etzhayyim.com:epfo',
                 'did:web:ind-payroll.etzhayyim.com:epfo',
                 'epfo-amend-v1',
                 'EPFO ECR Amendment',
                 'EPFO ECR Amendment',
                 '',
                 'camunda',
                 1,
                 '[{"key":"amendmentMeta","type":"fieldset","label":"Correction '
                 'Summary","components":[{"key":"amendmentDate","label":"Correction '
                 'date","type":"datepicker","required":true},{"key":"amendmentReason","label":"Reason","type":"select","required":true,"options":[{"value":"joinedMember","label":"Joined '
                 'member"},{"value":"leftMember","label":"Left '
                 'member"},{"value":"wageRevision","label":"Wage '
                 'revision"},{"value":"uanCorrection","label":"UAN '
                 'correction"},{"value":"rateOverride","label":"Rate '
                 'override"}]},{"key":"amendmentDescription","label":"Details","type":"textarea","validate":{"maxLength":1000}}]},{"key":"memberChange","type":"datagrid","label":"Affected '
                 'Members","x-encryptedSection":"rosterPayload","components":[{"key":"operation","label":"Operation","type":"select","required":true,"options":[{"value":"add","label":"Add"},{"value":"remove","label":"Remove"},{"value":"update","label":"Update"}]},{"key":"memberUan","label":"UAN","type":"textfield","pattern":"^[0-9]{12}$","required":true,"x-piiTier":3,"x-encrypt":"signal:v1"},{"key":"memberName","label":"Member '
                 'name","type":"textfield","required":true},{"key":"aadhaar","label":"Aadhaar","type":"textfield","pattern":"^[0-9]{12}$","x-piiTier":3,"x-encrypt":"signal:v1"},{"key":"pan","label":"PAN","type":"textfield","pattern":"^[A-Z]{5}[0-9]{4}[A-Z]$","x-piiTier":3,"x-encrypt":"signal:v1"},{"key":"grossWageInrPaise","label":"Gross '
                 'wage (paise)","type":"number"},{"key":"epfWageInrPaise","label":"EPF wage '
                 '(paise)","type":"number"},{"key":"employeePfInrPaise","label":"Employee PF '
                 '(paise)","type":"number"},{"key":"employerPfInrPaise","label":"Employer PF '
                 '(paise)","type":"number"}]},{"key":"declaration","type":"fieldset","label":"Declaration","components":[{"key":"consentTier3","type":"checkbox","required":true,"label":"The '
                 'amended payroll identifiers and contribution values may be retained for EPFO '
                 'compliance and '
                 'audit."},{"key":"signatureDate","type":"datepicker","required":true,"label":"Signature '
                 'date"}]}]',
                 '{}']},
 {'sql': '\n      DELETE FROM vertex_form_task WHERE form_key = $1\n    ',
  'parameters': ['esic-monthly-form-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_form_task (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        rkey, repo, did, form_key, name, display_name, description,\n'
         '        form_type, schema_version, components_json, variable_mappings_json,\n'
         '        status, updated_at\n'
         '      ) VALUES (\n'
         "        $1, $2, DATE '2026-04-27', 2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11,\n'
         '        $12, $13, $14,\n'
         "        'active', '2026-04-27T00:10:00Z'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:ind-payroll.etzhayyim.com:esic/com.etzhayyim.form.task/esic-monthly-form-v1',
                 20260427001009,
                 'did:web:ind-payroll.etzhayyim.com:esic',
                 'esic-monthly-form-v1',
                 'did:web:ind-payroll.etzhayyim.com:esic',
                 'did:web:ind-payroll.etzhayyim.com:esic',
                 'esic-monthly-form-v1',
                 'ESIC Monthly Contribution',
                 'ESIC Monthly Contribution',
                 '',
                 'camunda',
                 1,
                 '[{"key":"establishment","type":"fieldset","label":"Establishment '
                 'Header","components":[{"key":"employerName","label":"Employer '
                 'name","type":"textfield","required":true},{"key":"establishmentEsiCode","label":"ESI '
                 'code","type":"textfield","required":true,"pattern":"^[0-9]{17}$","description":"17-digit '
                 'ESIC code, e.g. 41000123450001000"},{"key":"branchOffice","label":"Branch office '
                 '(regional)","type":"textfield"},{"key":"wageMonth","label":"Wage '
                 'month","type":"textfield","required":true,"pattern":"^[0-9]{4}-(0[1-9]|1[0-2])$"},{"key":"totalMembers","label":"Total '
                 'members","type":"number","required":true},{"key":"totalWageInrPaise","label":"Total '
                 'wages '
                 '(paise)","type":"number","required":true},{"key":"totalEmployeeContributionInrPaise","label":"Employee '
                 '0.75% '
                 '(paise)","type":"number","required":true},{"key":"totalEmployerContributionInrPaise","label":"Employer '
                 '3.25% '
                 '(paise)","type":"number","required":true},{"key":"totalContributionInrPaise","label":"Total '
                 'contribution 4% '
                 '(paise)","type":"number","required":true}]},{"key":"members","type":"datagrid","label":"Member '
                 'Roster","x-encryptedSection":"rosterPayload","components":[{"key":"ipNumber","label":"IP '
                 'Number","type":"textfield","required":true,"pattern":"^[0-9]{10}$","x-piiTier":3,"x-encrypt":"signal:v1"},{"key":"memberName","label":"Member '
                 'name","type":"textfield","required":true},{"key":"fatherSpouse","label":"Father/Spouse","type":"textfield"},{"key":"aadhaar","label":"Aadhaar","type":"textfield","pattern":"^[0-9]{12}$","x-piiTier":3,"x-encrypt":"signal:v1"},{"key":"dispensaryCode","label":"Dispensary '
                 'code","type":"textfield"},{"key":"joiningDate","label":"Joining '
                 'date","type":"datepicker"},{"key":"exitDate","label":"Exit '
                 'date","type":"datepicker"},{"key":"exitReason","label":"Exit '
                 'reason","type":"select","options":[{"value":"resignation","label":"Resignation"},{"value":"termination","label":"Termination"},{"value":"retirement","label":"Retirement"},{"value":"death","label":"Death"},{"value":"wageBoundary","label":"Crossed '
                 '₹21K wage threshold"}]},{"key":"daysWorked","label":"Days '
                 'worked","type":"number"},{"key":"grossWageInrPaise","label":"Gross wages '
                 '(paise)","type":"number","required":true,"description":"≤ ₹21,000 = ₹21,00,000 '
                 'paise for ESIC eligibility"},{"key":"employeeContribInrPaise","label":"Employee '
                 '0.75% '
                 '(paise)","type":"number","required":true},{"key":"employerContribInrPaise","label":"Employer '
                 '3.25% '
                 '(paise)","type":"number","required":true},{"key":"isDisabled","label":"Disabled '
                 'member (PWBD)","type":"checkbox"},{"key":"isWomanWorker","label":"Woman worker '
                 '(maternity benefit '
                 'eligibility)","type":"checkbox"}]},{"key":"nominees","type":"datagrid","label":"Nominees '
                 '(one per IP, optional '
                 'update)","x-encryptedSection":"nomineePayload","components":[{"key":"ipNumber","label":"IP '
                 'Number","type":"textfield","pattern":"^[0-9]{10}$","x-piiTier":3,"x-encrypt":"signal:v1"},{"key":"nomineeName","label":"Nominee '
                 'name","type":"textfield"},{"key":"nomineeRelation","label":"Relation","type":"select","options":[{"value":"spouse","label":"Spouse"},{"value":"child","label":"Child"},{"value":"parent","label":"Parent"},{"value":"sibling","label":"Sibling"},{"value":"other","label":"Other"}]},{"key":"nomineeShare","label":"Share '
                 '%","type":"number"}]},{"key":"declaration","type":"fieldset","label":"Declaration","components":[{"key":"consentTier3","type":"checkbox","required":true,"label":"IP '
                 'Number, Aadhaar and wage roster may be retained for 7 years per ESI Reg §32 + '
                 'DPDP §8(7)."},{"key":"filerName","label":"Filer '
                 'name","type":"textfield","required":true},{"key":"signatureDate","label":"Date","type":"datepicker","required":true}]}]',
                 '{}']},
 {'sql': '\n      DELETE FROM vertex_form_task WHERE form_key = $1\n    ',
  'parameters': ['esic-review-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_form_task (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        rkey, repo, did, form_key, name, display_name, description,\n'
         '        form_type, schema_version, components_json, variable_mappings_json,\n'
         '        status, updated_at\n'
         '      ) VALUES (\n'
         "        $1, $2, DATE '2026-04-27', 2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11,\n'
         '        $12, $13, $14,\n'
         "        'active', '2026-04-27T00:10:00Z'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:ind-payroll.etzhayyim.com:esic/com.etzhayyim.form.task/esic-review-v1',
                 20260427001010,
                 'did:web:ind-payroll.etzhayyim.com:esic',
                 'esic-review-v1',
                 'did:web:ind-payroll.etzhayyim.com:esic',
                 'did:web:ind-payroll.etzhayyim.com:esic',
                 'esic-review-v1',
                 'ESIC Contribution Review',
                 'ESIC Contribution Review',
                 '',
                 'camunda',
                 1,
                 '[{"key":"summary","type":"fieldset","label":"Submission Summary '
                 '(read-only)","components":[{"key":"establishmentEsiCode","label":"ESI '
                 'code","type":"textfield","readOnly":true},{"key":"wageMonth","label":"Wage '
                 'month","type":"textfield","readOnly":true},{"key":"totalMembers","label":"Total '
                 'members","type":"number","readOnly":true},{"key":"totalEmployeeContributionInrPaise","label":"Employee '
                 '0.75% '
                 '(paise)","type":"number","readOnly":true},{"key":"totalEmployerContributionInrPaise","label":"Employer '
                 '3.25% '
                 '(paise)","type":"number","readOnly":true},{"key":"totalContributionInrPaise","label":"Total '
                 '4% '
                 '(paise)","type":"number","readOnly":true}]},{"key":"checks","type":"fieldset","label":"Control '
                 'Checks","components":[{"key":"ipFormatValid","label":"All IP Numbers are 10 '
                 'digits","type":"checkbox","required":true},{"key":"wageBoundaryRespected","label":"All '
                 'wages ≤ ₹21,000 (or '
                 'excluded)","type":"checkbox","required":true},{"key":"rateValid","label":"0.75% '
                 '/ 3.25% rates correctly '
                 'applied","type":"checkbox","required":true},{"key":"sumIntegrity","label":"Per-member '
                 'sums match '
                 'totals","type":"checkbox","required":true},{"key":"dispensaryMapped","label":"All '
                 'members have a dispensary '
                 'code","type":"checkbox","required":true}]},{"key":"verdict","type":"fieldset","label":"Decision","components":[{"key":"decision","label":"Decision","type":"select","required":true,"options":[{"value":"approve","label":"Approve"},{"value":"reject","label":"Reject"}]},{"key":"challanReference","label":"Bank '
                 'challan reference (set when '
                 'paid)","type":"textfield"},{"key":"comment","label":"Comment","type":"textarea","validate":{"maxLength":1000}},{"key":"reviewedAt","label":"Reviewed '
                 'at","type":"datepicker","required":true}]}]',
                 '{}']},
 {'sql': '\n      DELETE FROM vertex_form_task WHERE form_key = $1\n    ',
  'parameters': ['esic-amend-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_form_task (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        rkey, repo, did, form_key, name, display_name, description,\n'
         '        form_type, schema_version, components_json, variable_mappings_json,\n'
         '        status, updated_at\n'
         '      ) VALUES (\n'
         "        $1, $2, DATE '2026-04-27', 2, $3,\n"
         '        $4, $5, $6, $7, $8,\n'
         '        $9, $10, $11,\n'
         '        $12, $13, $14,\n'
         "        'active', '2026-04-27T00:10:00Z'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:ind-payroll.etzhayyim.com:esic/com.etzhayyim.form.task/esic-amend-v1',
                 20260427001011,
                 'did:web:ind-payroll.etzhayyim.com:esic',
                 'esic-amend-v1',
                 'did:web:ind-payroll.etzhayyim.com:esic',
                 'did:web:ind-payroll.etzhayyim.com:esic',
                 'esic-amend-v1',
                 'ESIC Contribution Amendment',
                 'ESIC Contribution Amendment',
                 '',
                 'camunda',
                 1,
                 '[{"key":"amendmentMeta","type":"fieldset","label":"Correction '
                 'Summary","components":[{"key":"amendmentDate","label":"Effective '
                 'date","type":"datepicker","required":true},{"key":"amendmentReason","label":"Reason","type":"select","required":true,"options":[{"value":"joinedMember","label":"Joined '
                 'member"},{"value":"leftMember","label":"Left '
                 'member"},{"value":"wageRevision","label":"Wage '
                 'revision"},{"value":"ipCorrection","label":"IP Number / Aadhaar '
                 'correction"},{"value":"wageBoundaryToggle","label":"Crossed ₹21K '
                 'threshold"},{"value":"rateOverride","label":"Rate override '
                 '(rare)"}]},{"key":"amendmentDescription","label":"Details","type":"textarea","validate":{"maxLength":1000}}]},{"key":"memberChange","type":"datagrid","label":"Affected '
                 'Members","x-encryptedSection":"rosterPayload","components":[{"key":"operation","label":"Operation","type":"select","required":true,"options":[{"value":"add","label":"Add"},{"value":"remove","label":"Remove"},{"value":"update","label":"Update"}]},{"key":"ipNumber","label":"IP '
                 'Number","type":"textfield","pattern":"^[0-9]{10}$","required":true,"x-piiTier":3,"x-encrypt":"signal:v1"},{"key":"memberName","label":"Member '
                 'name","type":"textfield","required":true},{"key":"aadhaar","label":"Aadhaar","type":"textfield","pattern":"^[0-9]{12}$","x-piiTier":3,"x-encrypt":"signal:v1"},{"key":"newGrossWageInrPaise","label":"New '
                 'gross wage '
                 '(paise)","type":"number"},{"key":"newEmployeeContribInrPaise","label":"New '
                 'employee 0.75% '
                 '(paise)","type":"number"},{"key":"newEmployerContribInrPaise","label":"New '
                 'employer 3.25% (paise)","type":"number"},{"key":"newJoinDate","label":"Joining '
                 'date (if add)","type":"datepicker"},{"key":"newExitDate","label":"Exit date (if '
                 'remove)","type":"datepicker"}]},{"key":"declaration","type":"fieldset","label":"Declaration","components":[{"key":"consentTier3","type":"checkbox","required":true,"label":"Amendment '
                 'data may be retained for 7 years per ESI Reg '
                 '§32."},{"key":"filerName","label":"Filer '
                 'name","type":"textfield","required":true},{"key":"signatureDate","label":"Date","type":"datepicker","required":true}]}]',
                 '{}']}]

DOWN = [{'sql': 'DELETE FROM vertex_form_task WHERE form_key = $1', 'parameters': ['itr1-form-v1']},
 {'sql': 'DELETE FROM vertex_form_task WHERE form_key = $1', 'parameters': ['itr1-self-review-v1']},
 {'sql': 'DELETE FROM vertex_form_task WHERE form_key = $1', 'parameters': ['itr1-amend-v1']},
 {'sql': 'DELETE FROM vertex_form_task WHERE form_key = $1', 'parameters': ['gstr3b-form-v1']},
 {'sql': 'DELETE FROM vertex_form_task WHERE form_key = $1', 'parameters': ['gstr3b-review-v1']},
 {'sql': 'DELETE FROM vertex_form_task WHERE form_key = $1', 'parameters': ['gstr3b-amend-v1']},
 {'sql': 'DELETE FROM vertex_form_task WHERE form_key = $1', 'parameters': ['epfo-ecr-form-v1']},
 {'sql': 'DELETE FROM vertex_form_task WHERE form_key = $1', 'parameters': ['epfo-review-v1']},
 {'sql': 'DELETE FROM vertex_form_task WHERE form_key = $1', 'parameters': ['epfo-amend-v1']},
 {'sql': 'DELETE FROM vertex_form_task WHERE form_key = $1',
  'parameters': ['esic-monthly-form-v1']},
 {'sql': 'DELETE FROM vertex_form_task WHERE form_key = $1', 'parameters': ['esic-review-v1']},
 {'sql': 'DELETE FROM vertex_form_task WHERE form_key = $1', 'parameters': ['esic-amend-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
