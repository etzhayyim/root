# Autodesk Clean Room Actor

This actor provides a clean-room, API-compatible implementation of the Autodesk platform.

## Architecture
- **State:** Backed by Datomic for immutable, time-travel-capable record keeping.
- **Schema:** Defined in `schema/autodesk.kotoba`.
- **Execution:** Runs in `Py Kotodama WASM`, intercepting inbound REST requests.
