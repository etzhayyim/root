"""Yatabase lead-CRM surface — vertex_lead writes + reads.

Owns the top-of-funnel CRM operations the CF Worker used to call
createKyselyDb for. Per ADR-2605111200 the pod is the only writer.

Surface (mirrors src/leads.ts function set):

  POST /xrpc/com.etzhayyim.apps.yata.leadIngest            handleLeadIngest
  GET  /xrpc/com.etzhayyim.apps.yata.leadList              listLeads
  GET  /xrpc/com.etzhayyim.apps.yata.leadGet               getLeadByVertexId
  POST /xrpc/com.etzhayyim.apps.yata.leadSetOutreachStatus setLeadOutreachStatus
  POST /xrpc/com.etzhayyim.apps.yata.leadSetContactEmail   setLeadContactEmail
  POST /xrpc/com.etzhayyim.apps.yata.leadSetEnrichment     setLeadEnrichment
  POST /xrpc/com.etzhayyim.apps.yata.leadMarkDrafted       markLeadDrafted
  GET  /xrpc/com.etzhayyim.apps.yata.leadReady             leadsReadyForOutreach
  GET  /xrpc/com.etzhayyim.apps.yata.leadSendable          leadsSendable
  GET  /xrpc/com.etzhayyim.apps.yata.leadNeedsEnrichment   leadsNeedingEnrichment

Unlike vertex_bmc_* / vertex_api_key, vertex_lead IS update-able in
place (operator triages a single row across many days; PK upsert is
the wrong semantic for status transitions). UPDATEs are explicit and
isolated to a small set of columns.
"""
