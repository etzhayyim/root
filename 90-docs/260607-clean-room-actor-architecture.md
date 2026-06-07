# Clean Room Actor Architecture Design

## 1. Objective
Design a universal "Clean Room" architecture to implement 100 dominant enterprise software platforms and API ecosystems (Salesforce, SAP, AWS, MS 365, etc.). These implementations will act as drop-in, API-compatible replacements ("Actors") using our local tech stack.

## 2. Core Constraints (Clean Room)
- **No Proprietary Code:** We will reverse-engineer the API surface solely from public documentation and observable HTTP/gRPC behavior.
- **Protocol Emulation:** Emulate the REST/GraphQL/SOAP/Proprietary endpoints of the target systems.
- **State Emulation:** Transparently convert the proprietary state models (e.g., Salesforce Objects, SAP BAPIs) into our immutable Datomic backend.

## 3. Technology Stack & Roles

### 3.1 Datomic (Immutable State Layer)
Datomic will replace the traditional relational databases (like Oracle DB for Salesforce or HANA for SAP).
- **Fact-Based Storage:** Every state mutation via the emulated APIs will be recorded as Datomic facts (EAVT).
- **Time-Travel:** Native support for auditing, which is critical for ERP, CRM, and Financial actors.

### 3.2 Kotoba (Domain Logic & Schema Mapping)
Kotoba will define the domain rules, schema mappings, and validation logic for each actor.
- **Schema Definition:** Translate proprietary object models (e.g., Salesforce `Account`, `Contact`, `Opportunity`) into Kotoba schema definitions.
- **Query Translation:** Translate proprietary query languages (like Salesforce SOQL or SAP OpenSQL) into Datalog queries executed against Datomic.

### 3.3 Py Kotodama WASM (Execution Sandbox)
Python-based Kotodama compiled to WASM will provide the secure execution environment for the Actors.
- **API Endpoints:** Fastapi/Starlette equivalent running inside WASM to handle inbound HTTP requests mirroring the proprietary platform.
- **Sandboxing:** Ensures each enterprise actor operates in strict isolation, crucial for multi-tenant emulation.
- **Custom Business Logic:** Emulate proprietary extension languages (e.g., Salesforce Apex or SAP ABAP) by translating user-defined logic into Py Kotodama WASM scripts that interact with the Kotoba domain layer.

## 4. Directory Structure
All implementations will be housed under `20-actors/`.

```text
20-actors/
├── salesforce-compat/
│   ├── src/
│   │   ├── main.py (Py Kotodama entrypoint)
│   │   ├── soql_parser.py (SOQL to Datalog)
│   │   └── api/ (REST API emulators)
│   ├── schema/
│   │   └── sforce.kotoba (Kotoba schema mapping to Datomic)
│   ├── deps.toml
│   └── README.md
├── sap-compat/
│   ├── src/
│   │   └── rfc_handler.py
│   └── schema/
│       └── bapi.kotoba
└── ... (repeat for all 100 platforms)
```

## 5. Execution Flow
1. **Inbound Request:** The client sends an API request (e.g., a Salesforce REST API call to create an Account) to the Actor's endpoint.
2. **WASM Interception:** `Py Kotodama WASM` receives the request.
3. **Translation:** The Python layer parses the payload and uses the Kotoba schema (`sforce.kotoba`) to map the payload to our internal structure.
4. **State Mutation:** A transaction is submitted to Datomic.
5. **Response:** Datomic confirms the transaction; Py Kotodama WASM translates the Datomic entity back into the proprietary JSON/XML response format and returns it to the client.

## 6. Phased Rollout Plan
- **Phase 1:** ERP/CRM (Salesforce, SAP, Oracle, etc.)
- **Phase 2:** Office/Productivity (M365, Google Workspace, etc.)
- **Phase 3:** Design/Creative (Adobe API equivs, etc.)
- **Phase 4:** Cloud/Infra (AWS, Azure control planes)
- **Phase 5-10:** Data/BI, Finance, Healthcare, Retail, DevTools, Niche.
