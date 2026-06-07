---
id: adr-2606081500-kotoba-erp-crm-prototype-pywasm
title: "ADR-2606081500: Kotoba ERP and Salesforce CRM Prototype in PyWasm"
status: accepted
doc_type: adr
topic: kotoba-erp-crm-prototype-pywasm
---

# ADR-2606081500: Kotoba ERP and Salesforce CRM Prototype in PyWasm

## Status
Accepted

## Context
We need to demonstrate that the Kotoba canonical substrate (`kotoba-kqe` Datomic-isomorphic log) and PyWasm execution environment (`kotoba-runtime` via `componentize-py` + `kotoba_langgraph`) are capable of hosting massive, complex, enterprise-grade business logic conventionally handled by SAP and Salesforce, without relying on external relational databases.

## Decision
We implemented a true SAP-scale ERP prototype and a Salesforce CRM prototype completely within the Kotoba WASM architecture:

1. **SAP Conformance (Clean Architecture)**
   - **FI (Financials)**: Modeled standard SAP tables `BKPF` (Accounting Document Header) and `BSEG` (Accounting Document Segment).
   - **MM (Materials Management)**: Modeled `EKKO/EKPO` (Purchase Order) and `MKPF/MSEG` (Material Document / Goods Receipt).
   - **SD (Sales and Distribution)**: Modeled `VBAK/VBAP` (Sales Order) and `VBRK/VBRP` (Billing Document).

2. **Salesforce Conformance**
   - **CRM Module**: Modeled standard Salesforce sObjects `Account`, `Contact`, and `Opportunity`.

3. **True Datalog (KQE) API Integration**
   - All modules use the `kqe.assert_quad` host function to persist data directly to the content-addressed Datom log.
   - We migrated away from hardcoded mocks to use `kqe.get_objects(graph, subject, predicate)` for all Read paths, dynamically reconstructing Python domain entities from the returned CBOR bytes.

4. **Multi-Cloud Event Orchestration (KSE)**
   - Modules communicate asynchronously via the Kotoba Stream Engine (`kse.publish`).
   - *Use Case*: A Salesforce `Opportunity` moving to "Closed Won" publishes an event that triggers the SAP SD module.
   - *Use Case*: An SAP MM `GoodsReceipt` publishes an event that triggers the SAP FI module to post the corresponding inventory accounting journal entry.

5. **PyWasm Compilation**
   - Each bounded context (FI, MM, SD, CRM) is compiled into a standalone `app.wasm` Component Model binary using `componentize-py`, proving that Python's high-level expressiveness can be safely executed at the edge.

## Consequences
- **Positive**: Proves the architecture can handle the most rigorous enterprise data models (SAP/Salesforce) in a serverless, database-less, WASM-isolated environment.
- **Positive**: Achieves true implementation coverage of the `kotoba:kais` WIT host API (`kqe`, `kse`).
- **Negative**: The PyWasm binaries are large (~18MB each) due to the bundled CPython interpreter. This is an accepted trade-off for developer velocity, as per existing `kotoba_langgraph` strategy.
