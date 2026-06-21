# Salesforce Cleanroom Implementation via py kotodama

## 1. Context and Problem Statement
The Open SaaS project requires a Salesforce-equivalent CRM API implementation. The previous architecture utilized TypeScript with internal logic. To improve system modularity, ensure deterministic data logging, and better integrate with our Datalog-based graph state, we need a cleanroom implementation of the core Salesforce REST API that speaks natively to the kotoba Datomic substrate.

## 2. Decision
We have implemented a cleanroom Salesforce CRM REST API (v58.0 equivalent) using Python and the `py kotodama` (`kotoba_datomic`) client.

### Key Architectural Choices:
- **Substrate:** Relies exclusively on `kotoba_datomic.q` and `kotoba_datomic.transact` for all state queries and mutations. The underlying graph `did:web:salesforce-opensaas.etzhayyim.com` acts as the canonical source of truth.
- **SObject Mapping:** Standard SObjects (Account, Contact, Lead, Opportunity, Case) are mapped dynamically from CamelCase (Salesforce standard) to snake_case (Kotoba EDN schema) and vice versa.
- **API Coverage:**
  - **CRUD:** Complete support for `GET`, `POST`, `PATCH` (Upsert via `:db.unique/identity`), and `DELETE`.
  - **Metadata:** Implemented `GET /services/data/v58.0/sobjects/` (Global Describe) and `GET /services/data/v58.0/sobjects/{sobject_name}/describe` (Object Describe) returning schema metadata essential for client integrations.
  - **SOQL:** Built a regex-based transpiler mapping basic `SELECT ... FROM ... WHERE ... LIMIT` queries directly to Datalog `[:find (pull ?e [*]) ...]` queries with parameterized `args`.
  - **Batching:** Implemented `POST /services/data/v58.0/composite/` to support sequential execution of batched sub-requests, critical for integration throughput.

## 3. Consequences
- **Positive:** Full alignment with the kotoba architecture (ADR-2605172000) while presenting a surface that standard Salesforce integration tools can interact with.
- **Negative/Risk:** The SOQL parser currently supports simple equality conditions; complex queries (AND/OR, LIKE, nested relationships) will require a more sophisticated transpiler/AST approach in future iterations.
- **Deployment:** The Python service (`salesforce_py_kotodama.py`) acts as the active router and must be deployed alongside or in front of the existing TypeScript handlers if a full cutover is executed.
