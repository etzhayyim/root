# Docker Clean Room Actor

This actor provides a clean-room, API-compatible implementation of the Docker platform.

## Architecture
- **State:** Backed by Datomic for immutable, time-travel-capable record keeping.
- **Schema:** Defined in `schema/docker.kotoba`.
- **Execution:** Runs in `Py Kotodama WASM`, intercepting inbound REST requests.
