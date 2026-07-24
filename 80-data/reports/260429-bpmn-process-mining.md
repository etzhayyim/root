# BPMN Process Mining Snapshot

- generatedAt: 2026-04-29T11:03:06.027Z
- BPMN files scanned: 2298
- parsed processes: 2298
- parse failures: 0
- executable processes: 2298

## Process Model

- variants: straight-through=2148, gateway-controlled=150
- starts: timer=155, message=1, manual/plain=2142, multiple-start=65
- service tasks: total=5122, p50/process=2, p95/process=4, max/process=23
- control flow: gateways=183, sequenceFlows=8000, processesWithGateways=150, processesWithSplits=150
- observability: generic.audit.emit present=2110, missing=188, auditTaskCount=2240

## Top Projects

| Project | Processes |
| --- | ---: |
| open-us-state-dept | 151 |
| telecom | 142 |
| open-jp-mofa | 116 |
| open-us-treasury-dept | 59 |
| open-cn-state-council | 57 |
| open-jp-meti | 49 |
| open-jp-mlit | 42 |
| open-jp-mext | 31 |
| tsukuru | 26 |
| open-jp-mhlw | 25 |
| legal-entity | 16 |
| mangaka | 16 |
| maps | 16 |
| animeka | 15 |
| arb | 15 |

## Top Task Types

| Task type | Count |
| --- | ---: |
| generic.audit.emit | 2240 |
| generic.db.insert | 1874 |
| generic.db.select | 196 |
| generic.http.fetch | 78 |
| generic.llm.json | 37 |
| generic.pds.dispatch | 37 |
| rw.health.probe | 21 |
| generic.comfyui.call | 18 |
| generic.db.bulkInsert | 11 |
| generic.llm.chat | 11 |
| generic.rules.evaluate | 11 |
| generic.xrpc.invoke | 9 |
| ingest.run.markCompleted | 7 |
| gyosei.source.link | 5 |
| site.commonCrawl.runPhase | 4 |

## Task Families

| Family | Count |
| --- | ---: |
| generic | 4535 |
| telecom | 142 |
| xrpc | 68 |
| businessPerson | 28 |
| rw | 21 |
| robotics | 19 |
| jpCorpFinance | 17 |
| legalEntity | 16 |
| arms | 12 |
| calendar | 12 |
| flight | 12 |
| intel | 11 |
| openPatent | 11 |
| site | 11 |
| ma | 10 |

## Findings

| Severity | Type | Process | Project | Tasks | Gateways | Source |
| --- | --- | --- | --- | ---: | ---: | --- |
| medium | long_straight_through_flow | gstr3b_amend | gstr3b | 5 | 0 | etzhayyim-root/00-contracts/bpmn/com/etzhayyim/gstr3b/amend.bpmn |
| medium | long_straight_through_flow | mangaka_compose_page | mangaka | 5 | 0 | etzhayyim-root/00-contracts/bpmn/com/etzhayyim/mangaka/composePage.bpmn |
| medium | long_straight_through_flow | natural_person_generate_cohort_batch_v1 | natural-person | 5 | 0 | etzhayyim-root/00-contracts/bpmn/com/etzhayyim/natural-person/generateCohortBatch.bpmn |
| medium | long_straight_through_flow | open_lei_collect_gleif_global_lei | open-lei | 5 | 0 | etzhayyim-root/00-contracts/bpmn/com/etzhayyim/open-lei/collectGleifGlobalLei.bpmn |
| medium | long_straight_through_flow | open_ossekai_generate_wellbecoming_plan | open-ossekai | 5 | 0 | etzhayyim-root/00-contracts/bpmn/com/etzhayyim/open-ossekai/generateWellBecomingPlan.bpmn |
| medium | long_straight_through_flow | open_ossekai_score_jocho | open-ossekai | 5 | 0 | etzhayyim-root/00-contracts/bpmn/com/etzhayyim/open-ossekai/scoreJocho.bpmn |
| medium | missing_audit_emit | business_person_enrich_org_lei | business-person | 4 | 0 | etzhayyim-root/00-contracts/bpmn/com/etzhayyim/business-person/enrichOrgLei.bpmn |
| medium | missing_audit_emit | lawfirm_issue_invoice | lawfirm | 4 | 0 | etzhayyim-root/00-contracts/bpmn/com/etzhayyim/lawfirm/issueInvoice.bpmn |
| medium | missing_audit_emit | legal_corpus_fetch_and_embed | legal-corpus | 4 | 0 | etzhayyim-root/00-contracts/bpmn/com/etzhayyim/legal-corpus/fetchAndEmbed.bpmn |
| medium | missing_audit_emit | projector_agent_loop | projector | 4 | 0 | etzhayyim-root/00-contracts/bpmn/com/etzhayyim/projector/agentLoop.bpmn |
| medium | missing_audit_emit | business_person_enrich_global_persons | business-person | 3 | 0 | etzhayyim-root/00-contracts/bpmn/com/etzhayyim/business-person/enrichGlobalPersons.bpmn |
| medium | missing_audit_emit | lawfirm_run_conflict_check | lawfirm | 3 | 0 | etzhayyim-root/00-contracts/bpmn/com/etzhayyim/lawfirm/runConflictCheck.bpmn |
| medium | missing_audit_emit | legal_corpus_embed_document | legal-corpus | 3 | 0 | etzhayyim-root/00-contracts/bpmn/com/etzhayyim/legal-corpus/embedDocument.bpmn |
| medium | missing_audit_emit | legal_corpus_fetch_courtlistener_delta | legal-corpus | 3 | 0 | etzhayyim-root/00-contracts/bpmn/com/etzhayyim/legal-corpus/fetchCourtListenerDelta.bpmn |
| medium | missing_audit_emit | open_cyber_vuln_fetch_nvd_delta | open-cyber-vuln | 3 | 0 | etzhayyim-root/00-contracts/bpmn/com/etzhayyim/open-cyber-vuln/fetchNvdDelta.bpmn |
| medium | missing_audit_emit | open_oss_vuln_fetch_ghsa_delta | open-oss-vuln | 3 | 0 | etzhayyim-root/00-contracts/bpmn/com/etzhayyim/open-oss-vuln/fetchGhsaDelta.bpmn |
| medium | missing_audit_emit | open_sales_compute_forecast | open-sales | 3 | 0 | etzhayyim-root/00-contracts/bpmn/com/etzhayyim/open-sales/computeForecast.bpmn |
| medium | missing_audit_emit | kakaku_ingest_offer_from_url | kakaku | 2 | 0 | etzhayyim-root/orgs/etzhayyim/com-etzhayyim-kakaku/wire/contracts/bpmn/ingestOfferFromUrl.bpmn |
| medium | missing_audit_emit | legal_corpus_fetch_canlii_delta | legal-corpus | 2 | 0 | etzhayyim-root/00-contracts/bpmn/com/etzhayyim/legal-corpus/fetchCanLiiDelta.bpmn |
| medium | missing_audit_emit | llm_answer_with_knowledge | llm | 2 | 0 | etzhayyim-root/00-contracts/bpmn/com/etzhayyim/llm/answerWithKnowledge.bpmn |
| medium | missing_audit_emit | malak_get_threat_graph | malak | 2 | 0 | etzhayyim-root/00-contracts/bpmn/com/etzhayyim/malak/getThreatGraph.bpmn |
| medium | missing_audit_emit | malak_query_risk_chain | malak | 2 | 0 | etzhayyim-root/00-contracts/bpmn/com/etzhayyim/malak/queryRiskChain.bpmn |
| medium | missing_audit_emit | open_cyber_soc_fetch_cisa_alert_delta | open-cyber-soc | 2 | 0 | etzhayyim-root/00-contracts/bpmn/com/etzhayyim/open-cyber-soc/fetchCisaAlertDelta.bpmn |
| medium | missing_audit_emit | open_cyber_threat_fetch_mitre_attack_delta | open-cyber-threat | 2 | 0 | etzhayyim-root/00-contracts/bpmn/com/etzhayyim/open-cyber-threat/fetchMitreAttackDelta.bpmn |
| medium | missing_audit_emit | open_kev_catalog_fetch_kev_delta | open-kev-catalog | 2 | 0 | etzhayyim-root/00-contracts/bpmn/com/etzhayyim/open-kev-catalog/fetchKevDelta.bpmn |

## Interpretation

This is model mining from the checked-in BPMN contracts, not runtime event-log mining. Runtime conformance and duration analysis still require OCEL/BPMN activity rows from the deployed workers. The strongest static signal is observability coverage: processes without `generic.audit.emit` can run but are harder to mine later from aggregate logs.
