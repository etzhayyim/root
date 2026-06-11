# Gitlab Clean Room Actor

This actor provides a clean-room, API-compatible implementation of the Gitlab platform.

## Architecture
- **State:** Backed by Datomic for immutable, time-travel-capable record keeping.
- **Schema:** Defined in `schema/gitlab.kotoba`.
- **Execution:** Runs in `Py Kotodama WASM`, intercepting inbound REST requests.
