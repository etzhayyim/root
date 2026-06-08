# Root Router

The **Root Router** acts as the single, unified ingress point for the entire Etz Hayyim Clean Room ecosystem (1000 Actors).

## Architecture
- **Dynamic Routing**: Inspects incoming requests and dynamically forwards them to the appropriate Py Kotodama WASM actor endpoint.
- **Protocol Translation**: Translates unified GraphQL/REST requests into specific proprietary payload structures expected by each Clean Room actor (e.g., SOQL for Salesforce, SAP BAPI, FIX for HFT).
- **Global Auth & Tracing**: Injects global tracing IDs and manages unified identity/authentication before hitting the actor sandbox.
