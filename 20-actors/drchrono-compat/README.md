# Drchrono Clean Room Actor

This actor provides a clean-room, API-compatible implementation of the Drchrono platform.

## Architecture
- **State:** Backed by Datomic for immutable, time-travel-capable record keeping.
- **Schema:** Defined in `schema/drchrono.kotoba`.
- **Execution:** Runs in `Py Kotodama WASM`, intercepting inbound REST requests.
