# Dynamics365 Clean Room Actor

This actor provides a clean-room, API-compatible implementation of the Dynamics365 platform.

## Architecture
- **State:** Backed by Datomic for immutable, time-travel-capable record keeping.
- **Schema:** Defined in `schema/dynamics365.kotoba`.
- **Execution:** Runs in `Py Kotodama WASM`, intercepting inbound REST requests.
