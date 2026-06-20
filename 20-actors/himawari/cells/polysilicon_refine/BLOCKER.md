# polysilicon_refine — Port Blocker

**Status**: NOT PORTED (complex logic with kotoba/cryptographic dependencies)

**Reason**: This cell (390 lines) has similar blockers to module_assembly:

1. **JSON canonicalization for CID generation** (`_cid()` function): Produces deterministic `bafy~sha256-{digest}` content addresses. The JSON structure passed to `_cid()` must be byte-identical across Python ↔ Clojure. Python's `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False)` has subtle encoding rules (e.g., Unicode normalization) that must be replicated exactly.

2. **Chain-of-custody object modeling**: The `chainOfCustody` is an array of complex `#custodyHop` objects with conditional field population. The Python code has intricate defaulting logic (`hop.setdefault()` chains) that is easy to diverge from in Clojure without careful equivalence testing.

3. **Nested kotoba entity structure** (`_write_provenance()`): Transacts a complex multi-level EAVT datom set (lot entity + indexed hops + robot signatures). The attribute namespace (`:himawari.polysilicon/*`) and entity nesting must map exactly to the Python semantics.

4. **Multi-robot attestation quorum** (`_robot_signatures()`): Similar to module_assembly — normalizes bare DIDs / dicts / full objects into a lexicon-shaped #robotSignature array.

**Recommendation**: Defer to next wave with module_assembly. Requires:
- Shared JSON canonicalization utility tested against Python reference
- EAVT datom structure equivalence tests
- CID round-trip verification (Python → Clojure → Python → identical digest)

**Accepted for next wave**: polysilicon_refine (also cell_process complete, but module_assembly + outbound_logistics + supply_procurement).
