# Kubernetes Clean Room Actor

This actor provides a clean-room, API-compatible implementation of the Kubernetes platform.

## Architecture
- **State:** Backed by Datomic for immutable, time-travel-capable record keeping.
- **Schema:** Defined in `schema/kubernetes.kotoba`.
- **Execution:** Runs in `Py Kotodama WASM`, intercepting inbound REST requests.
