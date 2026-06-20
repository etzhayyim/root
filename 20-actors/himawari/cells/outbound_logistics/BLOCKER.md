# outbound_logistics — Port Blocker

**Status**: NOT PORTED (complex file I/O + BPMN composition)

**Reason**: This cell (351 lines) has structural blockers that require multi-actor coordination:

1. **Dynamic file parsing** (`_load_kami_autodrive_vehicle_classes()`): Reads and regex-parses the actual Rust source (`kami-autodrive/src/classes.rs`) at runtime to extract the `VehicleClass` enum variants. This is a build-time coupling that requires:
   - The Rust file path resolution to be identical in cljc (classpath relative paths)
   - Regex matching to be byte-identical
   - Fallback to the lexicon knownValues when the file is unreachable (must preserve exact fallback logic)

2. **Customs BPMN composition** (`_customs_clear()`, `_lodgeDeclaration` record building): The cell builds input records for an external customs-clearance BPMN. The lexicon for `com.etzhayyim.etzhayyim.apps.customsClearance.lodgeDeclaration` is real (not a placeholder), and the record shape must conform exactly (required fields: declarationId, hsCode, declaredValueUsd, lodgedAt). Divergence breaks the downstream BPMN invocation.

3. **Multi-leg telemetry + route composition** (`_plan_route()`): Builds a `routeRequest` for the kami-autodrive GNC stack (ADR-2606010600). The GNC API contract is in Rust; divergence in the route request shape breaks the composition seam.

4. **kami-autodrive class composition dependency**: Composes the actual kami-engine's autonomy layer. Changes to kami-autodrive's VehicleClass or route API require coordinated updates to this cell.

**Recommendation**: Defer to a follow-up wave that coordinates with:
- kami-engine codebase review (ensure file paths work in cljc context)
- Rust→Clojure file parsing equivalence testing
- Customs BPMN contract verification (lexicon round-trip)
- GNC route API contract testing

**Accepted for next wave**: outbound_logistics.
